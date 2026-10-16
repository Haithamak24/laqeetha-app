"""Real accuracy test on the photos from PPU's WhatsApp groups. Run once on your laptop:

    python real_test.py

It answers three questions with real numbers for the pitch:
  1. Search: when a student describes an item (Arabic or English), is the right photo ranked #1 / top 3?
     The 10 ID-card photos are included as distractors, so it's not an easy 6-photo test.
  2. Privacy: does the AI recognise ID documents on its own (so they get hidden automatically)?
  3. Speed: how long tagging one photo takes on this laptop.
Output is also saved to real_test_results.txt (not committed): the source of every number we quote.
"""
import csv
import sys
import time
from pathlib import Path

import numpy as np
from PIL import Image

from app.embedder import CATEGORIES, ID_CATEGORIES, PROMPT_SETS, Embedder

SEED, PRIVATE = Path("seed_photos"), Path("private_test_photos")
lines = []
def out(s=""):
    print(s); lines.append(s)

# ---- find the ID photos first. Without them the test is a different (easier) test: the search gallery
# drops from 16 photos to 6 and there is nothing to check ID detection on. So stop instead of printing
# numbers that look comparable but aren't. Also accept the folder one level deeper, which is what you
# get when the zip is extracted with "Extract All" (private_test_photos/private_test_photos/...).
PICS = {".jpg", ".jpeg", ".png", ".webp"}
id_files = sorted(p for p in PRIVATE.rglob("*") if p.suffix.lower() in PICS) if PRIVATE.is_dir() else []
if not id_files:
    here = Path.cwd()
    near = [p for p in list(here.parent.rglob("private_test_photos"))[:20] if p.is_dir() and p.resolve() != PRIVATE.resolve()]
    print("\n!! No ID photos found in", (here / PRIVATE).resolve())
    print("   The test needs them (they are never in the main zip, on purpose).")
    print("   Fix: unzip private_test_photos.zip HERE, so you get:")
    print("        " + str(here / "private_test_photos" / "id_01.jpg"))
    if near:
        print("   I found a folder with that name somewhere else, copy its photos here:")
        for p in near: print("        " + str(p))
    if (here / "private_test_photos.zip").exists() or (here.parent / "private_test_photos.zip").exists():
        print("   private_test_photos.zip is next to the app but not extracted yet: right-click it > Extract All.")
    print("\nNothing was measured and real_test_results.txt was not changed.")
    sys.exit(1)

t0 = time.time()
emb = Embedder()
out(f"model load: {time.time() - t0:.1f}s")

items = [r["filename"] for r in csv.DictReader(open(SEED / "items.csv", encoding="utf-8"))]
gallery = [SEED / f for f in items] + id_files

t0 = time.time()
vecs = np.stack([emb.image(Image.open(p)) for p in gallery])
per_img = (time.time() - t0) / len(gallery)
out(f"embedding speed: {per_img * 1000:.0f} ms per photo ({len(gallery)} photos)")

# ---- 1. search accuracy
queries = list(csv.DictReader(open(SEED / "test_queries.csv", encoding="utf-8")))
res = {"ar": [], "ar_raw": [], "en": []}
right, wrong = [], []
out(f"\nSEARCH (gallery = {len(items)} items + {len(id_files)} ID cards as distractors)")
for q in queries:
    target = gallery.index(SEED / q["filename"])
    sims = vecs @ emb.query_vec(q["query"])
    rank = int((sims > sims[target]).sum()) + 1
    lang = "ar" if any("؀" <= c <= "ۿ" for c in q["query"]) else "en"
    res[lang].append(rank)
    right.append(sims[target]); wrong.extend(np.delete(sims, target))
    if lang == "ar":
        raw_sims = vecs @ emb.text([emb.query_prompt(q["query"])])[0]  # without the dialect glossary
        raw = int((raw_sims > raw_sims[target]).sum()) + 1
        res["ar_raw"].append(raw)
        out(f"  #{rank}  (was #{raw} without glossary)  {q['query']}")
    else:
        out(f"  #{rank}  {q['query']}")
for lang, ranks in res.items():
    r = np.array(ranks)
    if not ranks: continue
    out(f"  {lang.upper()}: top-1 {np.mean(r == 1):.0%}, top-3 {np.mean(r <= 3):.0%}  (n={len(r)})")

# ---- 2. ID detection + tagging
out("\nID DETECTION (should be YES for all private_test_photos, NO for seed photos)")
tp = 0
for p in id_files:
    t = emb.tag(emb.image(Image.open(p)))
    tp += t["is_id"]
    out(f"  {p.name}: {'YES' if t['is_id'] else 'no '}  id_prob={t['id_prob']:.2f}  top={t['category']}")
fp = 0
for f in items:
    t = emb.tag(emb.image(Image.open(SEED / f)))
    fp += t["is_id"]
    out(f"  {f}: {'YES' if t['is_id'] else 'no '}  tagged as {t['color']} {t['category']} ({t['category_conf']:.0%})")
out(f"  IDs detected: {tp}/{len(id_files)}   false alarms on normal items: {fp}/{len(items)}")

# ---- 3. which label prompts name things better: v1 (one caption) or v2 (ensembled captions)
SHORT = {"earbuds": "earbuds case", "flash": "USB flash drive", "wallet": "wallet or purse", "phone": "phone",
         "keys": "keys", "headphones": "headphones", "laptop": "laptop", "tablet": "tablet or tablet case",
         "charger": "charger or cable", "bottle": "water bottle", "backpack": "backpack", "handbag": "handbag",
         "glasses": "glasses", "watch": "watch", "bracelet": "bracelet or jewelry", "notebook": "notebook or book",
         "umbrella": "umbrella", "jacket": "jacket or hoodie", "scarf": "scarf", "calculator": "calculator",
         "pencilcase": "pencil case", "powerbank": "power bank"}
EXPECT = {"ipad_case.jpg": {"tablet or tablet case"}, "watch_black_gold.jpg": {"watch"},
          "watch_blue_silver.jpg": {"watch"}, "gold_bracelet.jpg": {"bracelet or jewelry"},
          "key_purple_tag.jpg": {"keys"}, "black_purse.jpg": {"wallet or purse", "handbag"}}
labelled = [(SEED / f, EXPECT[f]) for f in items if f in EXPECT]
for p in sorted(Path("my_test_photos").glob("*.*")):
    key = p.stem.split("__")[0].lower()
    if key in SHORT and p.suffix.lower() in (".jpg", ".jpeg", ".png", ".webp"):
        labelled.append((p, {SHORT[key]}))
out(f"\nLABELS: v1 vs v2 prompt sets on {len(labelled)} labelled photos + {len(id_files)} ID cards")
lvecs = {p: emb.image(Image.open(p)) for p, _ in labelled}
ivecs = [emb.image(Image.open(p)) for p in id_files]
score = {}
for name in PROMPT_SETS:
    cv = emb.label_vecs(name)
    ok = 0
    for p, want in labelled:
        t = emb.tag(lvecs[p], cv)
        ok += t["category"] in want
        out(f"  {name}  {'ok ' if t['category'] in want else 'BAD'}  {p.name}: {t['category']} ({t['category_conf']:.0%})"
            + ("" if t["category"] in want else f"   should be {sorted(want)[0]}"))
    ids = sum(emb.tag(v, cv)["is_id"] for v in ivecs)
    fps = sum(emb.tag(lvecs[p], cv)["is_id"] for p, _ in labelled)
    score[name] = (ids, -fps, ok)
    out(f"  {name}: labels right {ok}/{len(labelled)}, IDs detected {ids}/{len(id_files)}, false ID alarms {fps}")
# ID safety first, then fewer false alarms, then label accuracy. A full tie keeps v2 (the measured default).
best = max(PROMPT_SETS, key=lambda n: (score[n], n == "v2"))
Path("prompt_choice.txt").write_text(best)
out(f"  -> using {best} from now on (saved in prompt_choice.txt; restart start.bat to apply)")

# ---- 4. calibration for the % shown in the app
right, wrong = np.array(right), np.array(wrong)
lo, hi = np.percentile(wrong, 50), np.percentile(right, 75)
out(f"\nCOSINE  correct: median {np.median(right):.3f}   wrong: median {np.median(wrong):.3f}")
out(f"Suggested: set LF_TEXT_LO={lo:.2f} and LF_TEXT_HI={hi:.2f} before starting the server")

Path("real_test_results.txt").write_text("\n".join(lines), encoding="utf-8")
print("\nSaved to real_test_results.txt")
