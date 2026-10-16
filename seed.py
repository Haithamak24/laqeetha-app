"""Load the demo's found items (seed_photos/items.csv) into the app. Server does NOT need to be running.

    python seed.py          # wipe data/ first if you want a clean demo:  rm -r data   (Windows: rmdir /s data)
"""
import csv
import sys
from pathlib import Path

from fastapi.testclient import TestClient

from app.main import STAFF_PIN, app

folder = Path(sys.argv[1] if len(sys.argv) > 1 else "seed_photos")
client = TestClient(app)
for row in csv.DictReader(open(folder / "items.csv", encoding="utf-8")):
    with open(folder / row["filename"], "rb") as img:
        r = client.post("/api/found", headers={"x-staff-pin": STAFF_PIN},
                        files={"photo": (row["filename"], img, "image/jpeg")},
                        data={"location": row["location"], "secret": row["secret"],
                              "owner_name": row.get("owner_name", ""), "is_id": row.get("is_id", ""),
                              # the demo items' names, as security would confirm them (the AI's own guess is kept in the tags)
                              "category": row.get("category", "")})
    j = r.json()
    if not r.is_success or j.get("needs_id_details"):
        print(f"SKIP {row['filename']}: {j}")
    else:
        t = j["tags"]
        print(f"OK   {row['filename']:<24} -> {t['color']} {t['category']} ({t['category_conf']:.0%})"
              + ("  [ID: hidden]" if j["is_id"] else ""))

# Start the booth screen's live feed clean: the 6 demo items count in the totals, but the feed
# should only show what visitors do.
from app.main import db
with db() as con:
    con.execute("DELETE FROM events")
print("Booth feed cleared. Open http://localhost:8000/booth on the laptop screen.")
