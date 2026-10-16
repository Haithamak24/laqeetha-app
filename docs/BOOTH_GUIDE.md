# Booth guide: running the Laqeetha demo at Palestine XI

The hands-on guide for the team on the booth laptop. For what the project is and how it works, see the [main README](../README.md).

## Setup on Windows (do it at home, needs good internet once)
1. Install Python 3.11 from python.org and tick **"Add python.exe to PATH"**.
2. Unzip this folder, double-click **`setup.bat`** (10–15 min: installs packages, downloads the AI models ~600 MB, loads 6 demo items).
3. Unzip `private_test_photos.zip` (sent separately, never in this zip) into this folder so you have `private_test_photos\id_01.jpg` … `id_10.jpg` (a folder nested one level deeper also works), then double-click **`test.bat`**. It writes `real_test_results.txt`, the source of every number we quote. (It also measures the two AI label sets and keeps the better one; restart `start.bat` after.)
4. Double-click **`start.bat`** and open http://localhost:8000. Staff PIN: `1234`.
5. Before every rehearsal: **`reset.bat`** (clean slate + the 6 demo items).

After setup, it runs **fully offline**. Don't depend on venue Wi-Fi.
Phone as the "student": connect the phone and laptop to your phone's hotspot, run `ipconfig` on the laptop,
open `http://<IPv4 address>:8000` on the phone. If it doesn't load, allow Python through Windows Firewall.

**Make it look like an installed app on the phone:**
- Android (Chrome): tap the **⛶ button** in the top bar → full screen, no browser bar.
  ("Install app" won't appear: Android only allows that on https sites. Full screen looks the same.)
- iPhone (Safari): Share → **Add to Home Screen** → open it from the icon. It opens full screen with the navy لقيتها icon.
- Test both at home on the hotspot first, then again at the booth (the laptop IP can change, so check `ipconfig` each morning).

## The booth screen
On the **laptop**, open **http://localhost:8000/booth** and press **F11** (full screen). Or tap *"Open the live booth screen"* on the Dashboard.
- It shows what's happening live: every item logged, every search (with what the AI understood from the Arabic), every claim.
- When security photographs an ID card, a big **"hidden"** card takes over the screen for a few seconds.
- When someone verifies a claim, the logo's amber dot snaps into place and turns green: **"لقيتها! ولقت صاحبها"** (found it, and it found its owner).
- Visitors use **your phone** (or theirs, on the hotspot) and watch the result appear on the big screen. That's the hook.
- Privacy: the screen never shows names, hidden details, phone numbers or ID photos. Only categories, colours and counts.
- `reset.bat` clears the feed too, so each rehearsal starts empty.
- **Idle loop:** if nothing happens for 45 s, Mostafa's explainer (48 s, bilingual version) plays full screen (muted), then the live screen comes back. Any real action (a search, a logged item, a claim) cuts straight back to live.
  - Press **V** to play it now, **Esc** (or click) to go back to live.
  - Sound is off by default (it loops every minute). Press **S** to turn it on or off. If the browser asks first, click the screen once.
  - Change the wait: `http://localhost:8000/booth?idle=90`. Turn it off: `?idle=0`.
  - The video lives in `app/static/media/`. To swap in a new cut, replace `laqeetha-explainer.mp4` with the new file under the same name (Chrome and Edge play the .mp4; the .webm is only a fallback).

## When the AI names something wrong
The AI can mislabel an item (a white earbuds case came out as "flash drive"). Two fixes:
- **In the app:** when the AI is under 60% sure, the Security screen shows its top guesses as buttons
  ("مش متأكد. هل هو…؟"). Tap the right one, or pick from "غير هيك…". Above 60% there's a small
  "مش هيك؟ صحّحه" link. The booth screen then shows "الأمن صحّح اسم الغرض". Search is not affected:
  it matches on the photo itself, not on the label.
- **Better labels:** the AI now describes each kind of item several ways (prompt ensembling, "v2").
  The app uses v2 by default: on your laptop (15 and 16 Oct) it caught the same 10/10 IDs with 0 false
  alarms as v1, and named 6/7 items right against v1's 4/7. `test.bat` re-measures both on real photos
  (the 6 demo items, your ID cards, and anything in `my_test_photos/`) and saves the winner in
  `prompt_choice.txt`, so if v1 ever does better it switches back on its own.
- **Check any photo:** drag a photo onto **`try_photo.bat`**. It prints what the AI sees (top guesses, v1 and v2).

## Locations
Gate A, Gate B, Gate C, Abu Romman Building, Other. Same list in the app, the booth screen and the server.

## What's in it
| Screen | What it shows |
|---|---|
| **Found items** (public) | The WhatsApp-group replacement. Photos blurred; **ID documents never shown at all**. |
| **I lost something** | Arabic or English description, optional photo, or the name on a lost ID → ranked matches + live alerts. |
| **Security: log item** | Photo → AI tags it, **detects ID cards automatically** and switches to the private ID flow, flags duplicates. |
| **Dashboard** | Everything, incl. "IDs kept off WhatsApp" counter. |

## Measured results (real model, booth laptop, 15–16 Oct 2026)
| Test | Result |
|---|---|
| ID cards detected automatically | **10/10**, 0 false alarms on the 6 normal items |
| Palestinian-Arabic descriptions, right item first | **12/12** (16 Oct; 10/12 on 15 Oct, before the جزدان fix). Without our glossary: 3/12 |
| English descriptions, right item first | **6/6** |
| Time per photo | **76–226 ms** across 3 runs. The slow run also took 36 s to load the model, so the laptop was likely on battery/power-saving: plug it in at the booth |
| AI labels (v2 prompt set, chosen by test.bat) | 6/7 right (earbuds and iPad case fixed; the key photo still reads as jewellery, one-tap fix covers it); ID detection unchanged |
Small sample: say so. The جزدان fix was made after seeing these same 12 descriptions, so 12/12 is optimistic until a fresh set is tested. These are the only numbers to quote.

## The privacy rules (your strongest pitch point)
From 16 items posted in PPU WhatsApp groups (16 Aug – 8 Oct 2026, see `evidence/whatsapp_posts.csv`):
11 were identity documents. All 11 were posted with the owner's name visible, 7 with date of birth,
4 with the face photo, 1 with the full national ID number. The same card was even posted twice.
In this system:
- ID documents are never shown publicly, not even blurred.
- They're matched by **name**, not by looks (all ID cards look alike to the AI).
- To claim one you need the **last 4 digits** of the ID/student number. 3 wrong tries lock it.
- Normal items: blurred photo + a hidden detail only the owner knows.

## Demo script (2 minutes)
**Before each round:** `reset.bat`, then `start.bat`. Laptop: `http://localhost:8000/booth`, F11.
Two phones on the hotspot: the **visitor phone** (you hold it) and the **security phone** (a teammate,
staff PIN 1234 already entered). When nobody is touching anything, the booth screen plays Mostafa's film.

| Time | Who | Do | Say |
|---|---|---|---|
| 0:00 | You | Point at the big screen / the WhatsApp evidence | "11 of 16 lost-item posts in our groups were ID cards, with names and birth dates." |
| 0:15 | Visitor phone | "ضيّعت شي" → type `ساعة فضية وجهها ازرق` → search | "Written the way we talk. Look: it understood *silver watch with a blue face*." (the booth shows the search live) |
| 0:40 | Visitor phone | "هذا إلي" on the top result → type `ماركة IIK` → verify | "The public photo is blurred, so only the owner knows this detail." The logo's dot turns green on the phone and on the big screen. |
| 1:00 | Visitor phone | New search: tick "ضاعت هوية؟", type **your own** name → search | "No match yet. It saved my report and will alert me." |
| 1:10 | Security phone | Photograph **your own** student card → AI says ID → enter your name + last 4 digits → log | "The AI spotted an ID by itself. Its photo is never shown, not even blurred." (big screen: the "hidden" card) |
| 1:30 | Visitor phone | The alert arrives (no photo) → claim with the last 4 digits | "I prove it's mine with 4 digits. Pickup is at the security room with my student card." |
| 1:45 | Visitor phone | "الموجودات" tab | "Items go back to their owners. IDs never get posted again." |

**If the AI names something wrong** (it called a white earbuds case a "flash drive"): don't hide it, use it.
"When the AI isn't sure, it asks security. A person gets the last word." Tap the right button; the big
screen shows "الأمن صحّح اسم الغرض". Search wasn't affected: it matches on the photo, not the name.

**When visitors try it themselves:** hand them the visitor phone. What they type appears on the big screen
only if every word is a normal item / colour / place word. Names, numbers, anything about IDs, and anything
rude never reach the screen (it shows "حدا وصف بكلامه شي ضيّعه" instead). Their own phone still shows everything.

Use **your own** card for the ID part, never someone else's.

## Files
- `private_test_photos/`: ID cards from the WhatsApp groups. **Only for `real_test.py` on your laptop. Never show them, never commit them** (already in `.gitignore`).
- `seed_photos/`: the 6 non-ID items used in the demo.
- `evidence/whatsapp_posts.csv`: one row per WhatsApp post, no names, for the problem slide.

## Known limits (be ready for them in Q&A)
- "What if someone types something rude, or a name, and it shows on your screen?" Allow-list: the big screen
  only shows descriptions made entirely of known item/colour/place words; nothing about IDs, no numbers.
- "What if the AI names an item wrong?" Under 60% sure, it shows its top guesses and security taps the right one.
  The label is cosmetic for search: matching uses the photo itself.
- Match % thresholds are calibrated on a small test set (6 items + 10 IDs); re-run `real_test.py` as it grows.
- Claim check for normal items is word-overlap, not semantic. Final hand-over is by a human against a student ID.
- Brute-force vector search is fine up to ~100k items; beyond that, pgvector/FAISS on the same vectors.
- Shared staff PIN, no real login. Production: PPU SSO, and for student cards a direct notification to the owner via the student directory, with no report needed.

## Other docs
- [`REQUIREMENTS.md`](REQUIREMENTS.md): what the system does, privacy rules, measured results
- [`HOW_IT_WORKS.md`](HOW_IT_WORKS.md): plain explanation + answers to hard questions
