# How it works: the 15-minute version

Goal: either of us can answer any question on stage, so we don't need to look at each other for help.

## The one idea behind everything

The AI turns **any photo** and **any sentence** into a list of 512 numbers (a *vector*).
It was trained on ~400 million photos with captions, so a photo of a blue watch and the sentence
"silver watch with a blue face" end up with **similar numbers**.

Search = compare the numbers. The closer they are, the higher the match %.

```
photo of found item ──► image encoder ──► [0.12, -0.40, …]  (512 numbers)
                                                    │ compare (cosine similarity)
"ساعة فضية وجهها ازرق" ──► glossary ──► "watch silver face blue" ──► text encoder ──► [0.10, -0.38, …]
```

The model is called **CLIP** (by OpenAI, open source). We use it as-is: **no training on our side**.
That's why it works with only a handful of photos.

## Why the Arabic glossary

The text model learned mostly formal Arabic. In our test, `جزدان صغير اسود بسحاب` ranked the purse
**16th of 16**, while the English version ranked it **1st**. So `app/arabic.py` translates
196 Palestinian lost-item words (جزدان, شنتة, ميدالية, سودا, موف…) to English before searching.
English scored 6/6 at #1 in our test.

## The ID-card privacy flow

1. Officer photographs the item. The AI says how likely it is to be an ID card (it caught **10/10** in our test, with **0** false alarms).
2. If it's an ID, the officer types the **name** and the **last 4 digits** of the number.
3. The photo is **never** shown to students, not even blurred.
4. A student who lost it types their name, which matches → alert.
5. To claim: the last 4 digits. 3 wrong tries lock it.

Normal items: public photo is **blurred**. The officer records a hidden detail (e.g. "scratch on the back") and the claimant must describe it.

## Numbers to remember (from `real_test_results.txt`, 15–16 Oct 2026)

| What | Result |
|---|---|
| English search, right item at #1 | 6 / 6 |
| Palestinian-Arabic search, right item at #1 | 12 / 12; 3 / 12 without our glossary |
| ID detection | 10 / 10, 0 false alarms |
| Time to process one photo | 76–226 ms (laptop CPU, three runs) |
| Our evidence | 16 WhatsApp items → 11 IDs → all 11 with the name visible |

## Hard questions and our answers

| Question | Answer |
|---|---|
| "Can't someone fake a claim?" | Photos are blurred or hidden, and the claim needs a detail only the owner knows. 3 tries then lock. Final hand-over is in person, against a student ID. |
| "What if the AI is wrong?" | It ranks; it doesn't decide. The student picks from the top results, and a human hands the item over. |
| "Why not just use the WhatsApp group?" | Because it publishes students' IDs. Show the collage. |
| "How do you make money?" | The institution pays a monthly subscription. PPU is the free pilot. Next: malls, hospitals, hotels. |
| "How big is the test?" | Small: 6 items + 10 IDs. The point was to prove it works on real PPU photos. Next step is 50+ items with security's help. |
| "Does it need internet?" | No. It runs offline once installed. |
| "What did you build vs. use?" | We used an open-source AI model. We built the matching, the dialect glossary, the privacy flow, and the whole app. |

## Where things are in the code

| File | What it does |
|---|---|
| `app/embedder.py` | Loads the AI; photo → vector, text → vector, auto-tags |
| `app/arabic.py` | Dialect glossary |
| `app/main.py` | The API: log item, report lost, claim, dashboard, privacy rules |
| `app/static/index.html` | The whole UI (Arabic/English) |
| `app/static/booth.html` | The live booth screen (public, privacy-filtered) |
| `real_test.py` | The accuracy test that produced our numbers |
| `try_photo.py` | Shows what the AI sees in any one photo |
