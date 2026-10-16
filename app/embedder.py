"""CLIP embedder: images AND text land in the same vector space.

Why this works for lost & found:
  - Found item's photo                         -> 512-d vector  (clip-ViT-B-32 image encoder)
  - "علبة سماعات سوداء عليها ملصق" or English text -> 512-d vector (multilingual text encoder)
  - Cosine similarity between them = how well the description fits the photo.

The multilingual text model was trained (knowledge distillation) to put a sentence in 50+
languages, Arabic included, at the same point the original English CLIP text encoder puts
its English translation. So Arabic text can search English-trained image vectors directly.
No training on our side.

Set LF_FAKE=1 to run without downloading weights (deterministic dummy vectors, tests only).
"""
import hashlib
import os
import re
from pathlib import Path

import numpy as np
from PIL import Image

from .arabic import to_english

CATEGORIES = [
    "keys", "wallet or purse", "phone", "earbuds case", "headphones", "laptop", "tablet or tablet case",
    "charger or cable", "water bottle", "backpack", "handbag", "glasses", "watch", "bracelet or jewelry",
    "student ID card", "national ID card in a plastic holder", "notebook or book", "umbrella",
    "jacket or hoodie", "scarf", "calculator", "USB flash drive", "pencil case", "power bank",
]
ID_CATEGORIES = {"student ID card", "national ID card in a plastic holder"}

# Two label-prompt sets. v1 = one caption per label (what was measured in the first tests).
# v2 = prompt ensembling, the standard CLIP trick: several phrasings per label, averaged into one vector.
# It should fix labels whose single caption was weak (v1 says "a photo of a earbuds case", and a white
# earbuds case came out as "USB flash drive"). The ID-card captions are identical in both sets.
# real_test.py compares both on real photos and keeps v2 only if ID detection is at least as good.
V1 = {c: [f"a photo of a {c}"] for c in CATEGORIES}
V1["keys"] = ["a photo of a metal door key on a keyring"]
_NAMES = {
    "keys": ["a metal door key on a keyring", "a bunch of keys", "a single key with a colored plastic key tag"],
    "wallet or purse": ["a wallet", "a purse"],
    "phone": ["a smartphone", "a mobile phone"],
    "earbuds case": ["an earbuds charging case", "AirPods in their charging case",
                     "wireless earbuds in a small white case", "a pair of wireless earphones"],
    "headphones": ["over-ear headphones", "a headset"],
    "laptop": ["a laptop computer"],
    "tablet or tablet case": ["a tablet", "an iPad in a protective case", "an iPad in a leather folio case",
                              "a tablet in a book-style cover"],
    "charger or cable": ["a phone charger", "a charging cable"],
    "water bottle": ["a water bottle"],
    "backpack": ["a backpack", "a school bag"],
    "handbag": ["a handbag", "a shoulder bag"],
    "glasses": ["a pair of glasses", "sunglasses"],
    "watch": ["a wristwatch", "a smartwatch"],
    "bracelet or jewelry": ["a bracelet", "a piece of jewelry", "a necklace"],
    "notebook or book": ["a notebook", "a book"],
    "umbrella": ["an umbrella"],
    "jacket or hoodie": ["a jacket", "a hoodie"],
    "scarf": ["a scarf"],
    "calculator": ["a calculator"],
    "USB flash drive": ["a USB flash drive", "a USB memory stick"],
    "pencil case": ["a pencil case"],
    "power bank": ["a power bank", "a portable battery charger"],
}
_TEMPLATES = ["a photo of {}.", "a close-up photo of {}.", "a photo of {} held in someone's hand."]
V2 = {c: ([t.format(n) for n in _NAMES[c] for t in _TEMPLATES] if c in _NAMES else V1[c]) for c in CATEGORIES}
PROMPT_SETS = {"v1": V1, "v2": V2}


def prompt_choice() -> str:
    """LF_PROMPTS=v1/v2 wins; else the choice real_test.py saved after measuring; else v2.
    v2 is the default because it was measured on the real model twice (15 and 16 Oct 2026): IDs 10/10,
    0 false alarms (same as v1) and better item names (6/7 vs 4/7, incl. earbuds and the iPad case)."""
    env = os.environ.get("LF_PROMPTS", "").strip()
    if env in PROMPT_SETS:
        return env
    f = Path(__file__).resolve().parent.parent / "prompt_choice.txt"
    if f.exists() and f.read_text().strip() in PROMPT_SETS:
        return f.read_text().strip()
    return "v2"
COLORS = ["black", "white", "gray", "silver", "red", "blue", "green", "yellow", "pink",
          "purple", "brown", "orange", "gold", "beige", "transparent"]

FAKE = os.environ.get("LF_FAKE") == "1"
DIM = 512
IMAGE_MODEL = "clip-ViT-B-32"
TEXT_MODEL = "sentence-transformers/clip-ViT-B-32-multilingual-v1"


def _norm(v: np.ndarray) -> np.ndarray:
    return v / (np.linalg.norm(v, axis=-1, keepdims=True) + 1e-9)


def _fake(seed_bytes: bytes) -> np.ndarray:
    h = hashlib.sha256(seed_bytes).digest()
    return _norm(np.random.default_rng(int.from_bytes(h[:8], "big")).normal(size=DIM))


class Embedder:
    def __init__(self):
        if not FAKE:
            from sentence_transformers import SentenceTransformer
            # First run downloads ~600MB total, then it's cached in ~/.cache.
            self.img_model = SentenceTransformer(IMAGE_MODEL)
            self.txt_model = SentenceTransformer(TEXT_MODEL)
        self.prompt_set = prompt_choice()
        self.cat_vecs = self.label_vecs(self.prompt_set)
        self.color_vecs = self.text([f"a photo of a {c} object" for c in COLORS])

    def label_vecs(self, name: str) -> np.ndarray:
        """One vector per category: the mean of its prompt vectors, re-normalised."""
        ps = PROMPT_SETS[name]
        return np.stack([_norm(self.text(ps[c]).mean(0)) for c in CATEGORIES]).astype(np.float32)

    def image(self, img: Image.Image) -> np.ndarray:
        if FAKE:
            return _fake(img.convert("RGB").resize((8, 8)).tobytes()).astype(np.float32)
        v = self.img_model.encode([img.convert("RGB")], convert_to_numpy=True)[0]
        return _norm(v).astype(np.float32)

    def text(self, texts: list[str]) -> np.ndarray:
        if FAKE:
            return np.array([_fake(t.lower().encode()) for t in texts], dtype=np.float32)
        v = self.txt_model.encode(texts, convert_to_numpy=True)
        return _norm(v).astype(np.float32)

    @staticmethod
    def query_prompt(desc: str) -> str:
        """CLIP was trained on captions, so 'a photo of X' matches better than bare 'X'.
        Only prefix Latin-script text; Arabic gets its own phrasing."""
        desc = desc.strip()
        if re.search(r"[؀-ۿ]", desc):
            return f"صورة {desc}"
        return f"a photo of {desc}"

    def query_vec(self, desc: str) -> np.ndarray:
        """Vector for a student's description. Arabic: mostly the English gloss of the
        dialect words (accurate), plus a little of the raw Arabic (catches words not in the glossary)."""
        ar = self.text([self.query_prompt(desc)])[0]
        en = to_english(desc)
        if not en:
            return ar
        env = self.text([f"a photo of {en}"])[0]
        return _norm(0.2 * ar + 0.8 * env).astype(np.float32)

    def tag(self, img_vec: np.ndarray, cat_vecs: np.ndarray | None = None) -> dict:
        """Zero-shot classification: softmax over similarity to each label (CLIP logit scale ~100)."""
        cat_vecs = self.cat_vecs if cat_vecs is None else cat_vecs
        def top(vecs, labels, k):
            logits = 100.0 * vecs @ img_vec
            p = np.exp(logits - logits.max()); p /= p.sum()
            idx = np.argsort(-p)[:k]
            return [{"label": labels[i], "p": round(float(p[i]), 3)} for i in idx]
        cats = top(cat_vecs, CATEGORIES, len(CATEGORIES))
        colors = top(self.color_vecs, COLORS, 2)
        id_prob = sum(c["p"] for c in cats if c["label"] in ID_CATEGORIES)
        return {"category": cats[0]["label"], "category_conf": cats[0]["p"],
                "color": colors[0]["label"], "alternatives": cats[1:4],
                "id_prob": round(id_prob, 3), "is_id": id_prob >= 0.5}
