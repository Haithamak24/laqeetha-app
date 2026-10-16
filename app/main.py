"""Laqeetha (لقيتها) · Campus Lost & Found — AI matching demo.

Flows:
  1. Security logs a FOUND item (photo + gate + hidden detail)   -> AI tags it, flags ID documents,
     warns on duplicates, and alerts every open lost report it matches.
  2. Student reports a LOST item (Arabic/English text and/or photo) -> ranked matches.
  3. Student CLAIMS by proving ownership                          -> security releases it.

ID documents (national IDs, student cards) get a stricter path, because today they are posted in
WhatsApp groups with names, birth dates and sometimes ID numbers visible:
  - their photo is NEVER shown publicly (not even blurred),
  - they are matched by the owner's name instead of by looks,
  - the claim requires the last 4 digits of the ID/student number.

Run:  uvicorn app.main:app --host 0.0.0.0 --port 8000
"""
import io
import json
import os
import re
import sqlite3
import time
import uuid
from difflib import SequenceMatcher
from pathlib import Path

import numpy as np
from fastapi import FastAPI, File, Form, Header, HTTPException, UploadFile
from fastapi.responses import FileResponse, HTMLResponse, Response
from fastapi.staticfiles import StaticFiles
from PIL import Image, ImageFilter, ImageOps

from .arabic import booth_safe, readable, to_english
from .embedder import CATEGORIES, Embedder

# Where security keeps found items (keys must match the app, booth and seed data).
LOCATIONS = ("gate_a", "gate_b", "gate_c", "abu_romman", "other")

ROOT = Path(__file__).resolve().parent.parent
DATA = Path(os.environ.get("LF_DATA", ROOT / "data"))
IMG_DIR = DATA / "images"
IMG_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = DATA / "lostfound.db"
STAFF_PIN = os.environ.get("LF_PIN", "1234")
MAX_CLAIM_ATTEMPTS = 3
NOTIFY_THRESHOLD = 55   # match % that triggers an alert to a lost-item reporter
DUPLICATE_COS = 0.95    # image-image cosine above this = probably the same item logged twice

app = FastAPI(title="Laqeetha · Campus Lost & Found")
app.mount("/static", StaticFiles(directory=ROOT / "app" / "static"), name="static")
emb = Embedder()


# ---------------------------------------------------------------- storage
def db():
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    return con


with db() as con:
    con.executescript("""
    CREATE TABLE IF NOT EXISTS found (
        id TEXT PRIMARY KEY, created REAL, location TEXT, note TEXT,
        secret TEXT, tags TEXT, vec BLOB, status TEXT DEFAULT 'available',
        failed_claims INTEGER DEFAULT 0, claimant TEXT,
        is_id INTEGER DEFAULT 0, owner_name TEXT);
    CREATE TABLE IF NOT EXISTS lost (
        id TEXT PRIMARY KEY, created REAL, description TEXT, owner_name TEXT, contact TEXT,
        has_photo INTEGER, vec_text BLOB, vec_img BLOB, status TEXT DEFAULT 'open');
    CREATE TABLE IF NOT EXISTS notif (
        lost_id TEXT, found_id TEXT, score INTEGER, created REAL,
        PRIMARY KEY (lost_id, found_id));
    CREATE TABLE IF NOT EXISTS events (
        id INTEGER PRIMARY KEY AUTOINCREMENT, ts REAL, kind TEXT, data TEXT);
    """)


def log_event(con, kind: str, **data):
    """Feed for the live booth screen. Privacy rule: never put names, hidden details or contacts here."""
    con.execute("INSERT INTO events (ts, kind, data) VALUES (?,?,?)", (time.time(), kind, json.dumps(data, ensure_ascii=False)))


def to_blob(v): return None if v is None else v.astype(np.float32).tobytes()
def from_blob(b): return None if b is None else np.frombuffer(b, dtype=np.float32)


# ---------------------------------------------------------------- text helpers
_AR_NORM = str.maketrans({"أ": "ا", "إ": "ا", "آ": "ا", "ة": "ه", "ى": "ي", "ؤ": "و", "ئ": "ي"})
_STOP = {"a", "the", "an", "of", "with", "and", "on", "it", "is", "my", "في", "على", "من", "و", "عليها", "عليه"}


def words(s: str) -> set[str]:
    s = re.sub(r"[ً-ْ]", "", (s or "").lower()).translate(_AR_NORM)  # strip harakat, unify letters
    return {w for w in re.findall(r"[\w؀-ۿ]+", s) if w not in _STOP}


def name_score(owner_name: str, *texts: str) -> int:
    """How many of the owner's name parts appear in what the student typed."""
    parts = {w for w in words(owner_name) if len(w) > 1}
    if not parts: return 0
    said = set().union(*(words(t) for t in texts))
    hits = len(parts & said)
    return 97 if hits >= 2 else 50 if hits == 1 else 0  # first name alone is too common to be sure


# ---------------------------------------------------------------- scoring
# Raw cosine ranges differ by modality, so each is mapped to 0-100 separately.
# Calibrated on PPU WhatsApp photos (real_test.py, 11 Oct 2026): wrong-match median 0.22, correct 75th pct 0.32.
TEXT_LO, TEXT_HI = float(os.environ.get("LF_TEXT_LO", 0.22)), float(os.environ.get("LF_TEXT_HI", 0.32))
IMG_LO, IMG_HI = 0.50, 0.90


def pct(cos, lo, hi): return int(round(100 * min(1.0, max(0.0, (cos - lo) / (hi - lo)))))


def match_score(found_row, text_vec=None, img_vec=None, owner_name="", description=""):
    fv = from_blob(found_row["vec"])
    parts = []
    if text_vec is not None: parts.append(pct(float(fv @ text_vec), TEXT_LO, TEXT_HI))
    if img_vec is not None: parts.append(pct(float(fv @ img_vec), IMG_LO, IMG_HI))
    if found_row["is_id"]:
        # All ID cards look alike to the AI, so for IDs the name decides.
        parts = [min(p, 40) for p in parts] + [name_score(found_row["owner_name"], owner_name, description)]
    return max(parts) if parts else 0


def load_image(raw: bytes) -> Image.Image:
    try:
        img = ImageOps.exif_transpose(Image.open(io.BytesIO(raw))).convert("RGB")
    except Exception:
        raise HTTPException(400, "Not a valid image")
    img.thumbnail((1024, 1024))
    return img


def public_item(r, score=None):
    tags = json.loads(r["tags"])
    out = {"id": r["id"], "category": tags["category"], "color": tags["color"], "is_id": bool(r["is_id"]),
           "location": r["location"], "status": r["status"],
           "found_at": time.strftime("%Y-%m-%d %H:%M", time.localtime(r["created"])),
           # Public view: blurred photo for normal items, no photo at all for ID documents.
           "image": None if r["is_id"] else f"/img/{r['id']}"}
    if score is not None: out["score"] = score
    return out


def require_staff(pin):
    if pin != STAFF_PIN: raise HTTPException(401, "Staff PIN required")


# ---------------------------------------------------------------- API
@app.post("/api/analyze")
async def analyze(photo: UploadFile = File(...), x_staff_pin: str = Header(None)):
    """Instant AI read of a photo before saving: category, colour, and whether it's an ID document."""
    require_staff(x_staff_pin)
    t0 = time.perf_counter()
    tags = emb.tag(emb.image(load_image(await photo.read())))
    ms = int((time.perf_counter() - t0) * 1000)
    with db() as con:
        log_event(con, "analyzed", category=tags["category"], color=tags["color"],
                  conf=round(tags["category_conf"], 3), is_id=bool(tags["is_id"]), ms=ms)
    return dict(tags, ms=ms)


@app.post("/api/found")
async def add_found(photo: UploadFile = File(...), location: str = Form(""), note: str = Form(""),
                    secret: str = Form(""), is_id: str = Form(""), owner_name: str = Form(""),
                    category: str = Form(""), x_staff_pin: str = Header(None)):
    require_staff(x_staff_pin)
    if location not in LOCATIONS: location = "other"
    img = load_image(await photo.read())
    vec = emb.image(img)
    tags = emb.tag(vec)
    # Security can correct the AI's label with one tap. The photo vector (what search uses) is unchanged;
    # the label is what people see, so a human gets the last word on it.
    if category in CATEGORIES and category != tags["category"]:
        tags = dict(tags, ai_category=tags["category"], category=category, corrected=True)
    # Officer decides when they've said so ("1" / "no"); otherwise the AI decides.
    doc = {"1": True, "no": False}.get(is_id, tags["is_id"])
    secret = secret.strip()
    if doc:
        secret = re.sub(r"\D", "", secret)[-4:]
        if len(secret) != 4:
            # AI says it's an ID card: tell the officer what we need instead of guessing.
            return {"needs_id_details": True, "tags": tags}
        if not owner_name.strip():
            return {"needs_id_details": True, "tags": tags}
    elif not secret:
        raise HTTPException(400, "Add a hidden detail (something only the owner would know)")

    with db() as con:
        dup = None
        for r in con.execute("SELECT id, vec FROM found WHERE status='available'"):
            if float(from_blob(r["vec"]) @ vec) >= DUPLICATE_COS:
                dup = r["id"]; break
        fid = uuid.uuid4().hex[:8]
        img.save(IMG_DIR / f"{fid}.jpg", quality=88)
        con.execute("""INSERT INTO found (id, created, location, note, secret, tags, vec, is_id, owner_name)
                       VALUES (?,?,?,?,?,?,?,?,?)""",
                    (fid, time.time(), location, note, secret, json.dumps(tags), to_blob(vec), int(doc), owner_name.strip()))
        row = con.execute("SELECT * FROM found WHERE id=?", (fid,)).fetchone()
        alerts = 0
        for r in con.execute("SELECT * FROM lost WHERE status='open'"):
            s = match_score(row, from_blob(r["vec_text"]), from_blob(r["vec_img"]), r["owner_name"], r["description"])
            if s >= NOTIFY_THRESHOLD:
                con.execute("INSERT OR IGNORE INTO notif VALUES (?,?,?,?)", (r["id"], fid, s, time.time()))
                alerts += 1
        log_event(con, "logged", category=tags["category"], color=tags["color"], location=location,
                  is_id=bool(doc), alerts=alerts, duplicate=bool(dup), corrected=bool(tags.get("corrected")))
    return {"id": fid, "tags": tags, "is_id": doc, "alerts_sent": alerts, "possible_duplicate_of": dup}


@app.post("/api/lost")
async def report_lost(description: str = Form(""), owner_name: str = Form(""), contact: str = Form(""),
                      photo: UploadFile | None = File(None)):
    tv = emb.query_vec(description) if description.strip() else None
    iv = emb.image(load_image(await photo.read())) if photo is not None and photo.filename else None
    if tv is None and iv is None and not owner_name.strip():
        raise HTTPException(400, "Describe the item, upload a photo, or give the name on your ID")
    lid = uuid.uuid4().hex[:8]
    with db() as con:
        con.execute("""INSERT INTO lost (id, created, description, owner_name, contact, has_photo, vec_text, vec_img)
                       VALUES (?,?,?,?,?,?,?,?)""",
                    (lid, time.time(), description, owner_name, contact, int(iv is not None), to_blob(tv), to_blob(iv)))
        rows = con.execute("SELECT * FROM found WHERE status='available'").fetchall()
    ranked = sorted(((match_score(r, tv, iv, owner_name, description), r) for r in rows), key=lambda x: -x[0])
    matches = [public_item(r, s) for s, r in ranked[:6] if s >= 20]
    understood = readable(description) if re.search(r"[\u0600-\u06FF]", description) else ""
    # The booth's big screen only gets words that are safe to show in public (see arabic.booth_safe):
    # nothing rude, no names, no numbers, nothing about IDs. The student's own phone still shows everything.
    safe = booth_safe(description) if description.strip() else {"show": "", "understood": "", "id_like": False}
    with db() as con:
        log_event(con, "searched", query=safe["show"], understood=safe["understood"],
                  id_report=bool(owner_name.strip()) or safe["id_like"], described=bool(description.strip()),
                  photo=iv is not None, matches=len(matches), top=(matches[0]["score"] if matches else 0))
    return {"report_id": lid, "matches": matches, "understood": understood}


@app.get("/api/lost/{lid}/alerts")
def alerts(lid: str):
    with db() as con:
        rows = con.execute("""SELECT f.*, n.score FROM notif n JOIN found f ON f.id = n.found_id
                              WHERE n.lost_id=? AND f.status='available' ORDER BY n.score DESC""", (lid,)).fetchall()
    return [public_item(r, r["score"]) for r in rows]


@app.get("/api/feed")
def feed():
    """Public replacement for the WhatsApp group: every found item, privacy-safe."""
    with db() as con:
        return [public_item(r) for r in con.execute("SELECT * FROM found WHERE status='available' ORDER BY created DESC")]


def secret_ok(answer: str, secret: str, is_id: bool) -> bool:
    if is_id:
        return re.sub(r"\D", "", answer)[-4:] == secret
    a, s = words(answer), words(secret)
    overlap = len(a & s) / max(1, len(s))  # share of the hidden detail the claimant got right
    fuzzy = SequenceMatcher(None, answer.lower().strip(), secret.lower().strip()).ratio()
    return max(overlap, fuzzy) >= 0.5


@app.post("/api/claim/{fid}")
def claim(fid: str, answer: str = Form(...), contact: str = Form("")):
    with db() as con:
        r = con.execute("SELECT * FROM found WHERE id=?", (fid,)).fetchone()
        if not r: raise HTTPException(404, "Item not found")
        if r["status"] != "available": raise HTTPException(409, "Item already claimed or locked")
        tags = json.loads(r["tags"])
        if secret_ok(answer, r["secret"], bool(r["is_id"])):
            con.execute("UPDATE found SET status='pending_pickup', claimant=? WHERE id=?", (contact, fid))
            log_event(con, "verified", category=tags["category"], color=tags["color"], location=r["location"], is_id=bool(r["is_id"]))
            return {"verified": True, "location": r["location"]}
        fails = r["failed_claims"] + 1
        con.execute("UPDATE found SET failed_claims=?, status=? WHERE id=?",
                    (fails, "locked" if fails >= MAX_CLAIM_ATTEMPTS else "available", fid))
        log_event(con, "locked" if fails >= MAX_CLAIM_ATTEMPTS else "rejected",
                  category=tags["category"], color=tags["color"], is_id=bool(r["is_id"]), left=MAX_CLAIM_ATTEMPTS - fails)
    return {"verified": False, "attempts_left": MAX_CLAIM_ATTEMPTS - fails}


@app.get("/api/dashboard")
def dashboard(x_staff_pin: str = Header(None)):
    require_staff(x_staff_pin)
    with db() as con:
        found = [dict(public_item(r), secret=r["secret"], owner_name=r["owner_name"], claimant=r["claimant"],
                      image=f"/img/{r['id']}?full=1", failed_claims=r["failed_claims"])
                 for r in con.execute("SELECT * FROM found ORDER BY created DESC")]
        lost = [dict(id=r["id"], description=r["description"], owner_name=r["owner_name"], contact=r["contact"],
                     created=time.strftime("%Y-%m-%d %H:%M", time.localtime(r["created"])))
                for r in con.execute("SELECT * FROM lost ORDER BY created DESC")]
    stats = {"found": len(found), "lost": len(lost),
             "returned": sum(f["status"] in ("pending_pickup", "returned") for f in found),
             "ids_protected": sum(f["is_id"] for f in found)}
    return {"stats": stats, "found": found, "lost": lost}


@app.post("/api/found/{fid}/status")
def set_status(fid: str, status: str = Form(...), x_staff_pin: str = Header(None)):
    require_staff(x_staff_pin)
    if status not in ("available", "pending_pickup", "returned", "locked"): raise HTTPException(400)
    with db() as con:
        con.execute("UPDATE found SET status=?, failed_claims=CASE WHEN ?='available' THEN 0 ELSE failed_claims END WHERE id=?",
                    (status, status, fid))
        if status == "returned":
            r = con.execute("SELECT tags, is_id FROM found WHERE id=?", (fid,)).fetchone()
            if r:
                t = json.loads(r["tags"])
                log_event(con, "returned", category=t["category"], color=t["color"], is_id=bool(r["is_id"]))
    return {"ok": True}


@app.get("/img/{fid}")
def image(fid: str, full: int = 0, pin: str = ""):
    fid = re.sub(r"[^0-9a-f]", "", fid)
    p = IMG_DIR / f"{fid}.jpg"
    if not p.exists(): raise HTTPException(404)
    if full and pin == STAFF_PIN: return FileResponse(p)  # sharp photo: staff only
    with db() as con:
        r = con.execute("SELECT is_id FROM found WHERE id=?", (fid,)).fetchone()
    if r and r["is_id"]: raise HTTPException(403, "ID documents are never shown publicly")
    img = Image.open(p); img.thumbnail((360, 360))
    buf = io.BytesIO(); img.filter(ImageFilter.GaussianBlur(9)).save(buf, "JPEG", quality=80)
    return Response(buf.getvalue(), media_type="image/jpeg")


@app.get("/api/events")
def events(after: int = 0):
    """Live feed + counters for the booth screen. Public, so it carries no personal data."""
    with db() as con:
        rows = con.execute("SELECT * FROM events WHERE id>? ORDER BY id DESC LIMIT 40", (after,)).fetchall()
        f = con.execute("""SELECT COUNT(*) n, SUM(is_id) ids,
                                  SUM(status IN ('pending_pickup','returned')) back FROM found""").fetchone()
        searches = con.execute("SELECT COUNT(*) FROM lost").fetchone()[0]
    return {"events": [dict(id=r["id"], ts=r["ts"], kind=r["kind"], **json.loads(r["data"])) for r in reversed(rows)],
            "stats": {"found": f["n"] or 0, "ids_protected": f["ids"] or 0, "returned": f["back"] or 0, "searches": searches}}


@app.get("/booth", response_class=HTMLResponse)
def booth():
    return (ROOT / "app" / "static" / "booth.html").read_text(encoding="utf-8")


@app.get("/", response_class=HTMLResponse)
def index():
    return (ROOT / "app" / "static" / "index.html").read_text(encoding="utf-8")


@app.get("/manifest.webmanifest")
def manifest():
    return FileResponse(ROOT / "app" / "static" / "manifest.webmanifest", media_type="application/manifest+json")
