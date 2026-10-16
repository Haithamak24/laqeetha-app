# Requirements: Campus Lost & Found (PPU)

**Team:** Haitham Abu Khaled · Mustafa Al-Natsheh · Osama Abu Al-Halaweh
**Supervisor:** Ezdehar Jawabreh · **Course:** Graduation Project Introduction (Fall 2026)
**Status legend:** ✅ in the demo · 🔜 planned for implementation (Spring 2027)

---

## 1. Problem

At PPU, found items are photographed by security or students and posted in WhatsApp groups.
From 16 items posted between 16 Aug and 8 Oct 2026 (`evidence/whatsapp_posts.csv`):

| Finding | Count |
|---|---|
| Items that were identity documents (national ID / student card) | **11 of 16** |
| ID posts with the owner's name visible | **11 of 11** |
| ID posts with date of birth visible | 7 of 11 |
| ID posts with the face photo visible | 4 of 11 |
| ID posts with the full national ID number visible | 1 |
| Same item posted twice | 1 |

So the current process has three failures:
1. **Privacy:** personal ID data is broadcast to hundreds of people.
2. **Search:** there's no way to search; you scroll and hope.
3. **Verification:** whoever messages first can claim an item.

## 2. Users

| User | Goal |
|---|---|
| **Student (owner)** | Find a lost item fast; get alerted if it turns up later |
| **Security officer** (Gate B / Gate C rooms) | Log items in seconds; hand them to the right person |
| **Admin** (later) | See volumes, unclaimed items, returns |

## 3. Functional requirements

| ID | Requirement | Status |
|---|---|---|
| FR-1 | Officer logs a found item with a photo and storage location (Gate B / Gate C / other) | ✅ |
| FR-2 | AI auto-tags the item's category and colour from the photo | ✅ |
| FR-3 | Student reports a lost item by text (Arabic or English), photo, or the name on a lost ID | ✅ |
| FR-4 | System ranks found items by match % to the report | ✅ |
| FR-5 | Two-way matching: a newly logged item alerts every open report it matches (≥55%) | ✅ |
| FR-6 | Public feed of found items replaces the WhatsApp group | ✅ |
| FR-7 | Claim requires proof of ownership (see PR-3, PR-4); 3 wrong tries lock the item | ✅ |
| FR-8 | Officer dashboard: all items, reports, statuses; mark returned / unlock | ✅ |
| FR-9 | Duplicate warning when the same item is logged twice | ✅ |
| FR-10 | Arabic UI by default with English toggle, full RTL | ✅ |
| FR-11 | Login with PPU accounts (SSO) for students and staff | 🔜 |
| FR-12 | Direct notification to a student card's owner via the student directory, with no report needed | 🔜 |
| FR-13 | Push / SMS / email notifications (demo uses in-page alerts) | 🔜 |
| FR-14 | Mobile app (Flutter) for students and officers | 🔜 |
| FR-15 | Unclaimed-item policy: reminder after N days, donation/disposal workflow | 🔜 |

## 4. Privacy requirements (the core differentiator)

| ID | Requirement | Status |
|---|---|---|
| PR-1 | ID documents are detected automatically from the photo, with officer override | ✅ |
| PR-2 | ID photos are **never** shown publicly, not even blurred. Server returns 403 | ✅ |
| PR-3 | IDs are matched by owner name; claim needs the **last 4 digits** of the ID/student number | ✅ |
| PR-4 | Normal items show a blurred photo only; claim needs a hidden detail the officer recorded | ✅ |
| PR-5 | Sharp photos visible to staff only | ✅ (shared PIN in demo, 🔜 SSO) |
| PR-6 | Items and reports deleted after the item is returned + retention period | 🔜 |

## 5. Non-functional requirements

| ID | Requirement | Measured (11 Oct 2026, `real_test.py`) |
|---|---|---|
| NFR-1 | Photo processing < 1 s on a normal laptop CPU | **76–226 ms** per photo (3 runs) ✅ |
| NFR-2 | English search: correct item in top 3 ≥ 90% | **6/6 at #1** ✅ |
| NFR-3 | Arabic search (incl. Palestinian dialect): correct item in top 3 ≥ 80% | **12/12 at #1** (16 Oct 2026, real model; 10/12 on 15 Oct before the جزدان fix) ✅ · without the glossary: 6/12 in top 3, 3/12 at #1 |
| NFR-4 | ID detection ≥ 95% with ≤ 5% false alarms | **10/10 detected, 0/6 false alarms** ✅ |
| NFR-5 | Runs fully offline once models are downloaded | ✅ |
| NFR-6 | Works on phone browsers (responsive) | ✅ |

Test set is small (6 items + 10 IDs). Before final submission it must grow to 50+ items.

## 6. How it works (short)

Photo → **CLIP** image encoder → 512-number vector.
Description → **multilingual CLIP** text encoder → vector in the same space. Arabic dialect words are first translated by our glossary (`app/arabic.py`).
Match % = cosine similarity, calibrated on our test set. Details for the team: `docs/HOW_IT_WORKS.md`.

Stack: Python · FastAPI · sentence-transformers (CLIP ViT-B/32 + multilingual text model) · SQLite · vanilla JS.
Planned: PostgreSQL + pgvector, Flutter app, PPU SSO.

## 7. Out of scope (for now)

Payments, items outside campus, lost pets/people, OCR of ID text (officer types the name; 🔜 later).

## 8. Business model (for the forum)

The **institution** pays, not the student: a monthly subscription per site (universities, malls, hospitals, hotels).
PPU is the free pilot. Validation in progress: interviews with PPU security and one mall/hotel.
