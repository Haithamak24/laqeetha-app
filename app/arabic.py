"""Palestinian-dialect glossary for lost-item descriptions.

Why: the multilingual CLIP text model learned mostly formal Arabic. On real tests it ranked
"جزدان صغير اسود بسحاب" 16th of 16, while "small black zipper purse" ranked 1st. English queries hit
100% top-1, so we translate the words that matter (item, colour, material, details) into English
and search with that, keeping the Arabic vector as a minor signal.
"""
import re

_NORM = str.maketrans({"أ": "ا", "إ": "ا", "آ": "ا", "ة": "ه", "ى": "ي", "ؤ": "و", "ئ": "ي", "ـ": ""})


def norm(w: str) -> str:
    return re.sub(r"[ً-ْ]", "", w).translate(_NORM)


_RAW = {
    # items
    "مفتاح": "key", "مفاتيح": "keys", "مفتاحين": "keys", "ميداليه": "keychain", "علاقه": "keychain",
    "جزدان": "purse wallet", "جزادين": "purse wallet", "محفظه": "wallet", "بوك": "wallet", "بورتمونيه": "wallet",
    "شنته": "bag", "شنطه": "bag", "حقيبه": "bag", "كيس": "pouch", "ظهر": "backpack",
    "جوال": "phone", "موبايل": "phone", "تلفون": "phone", "هاتف": "phone", "ايفون": "iphone",
    "سماعات": "earbuds case", "سماعه": "earbuds", "ايربودز": "airpods earbuds", "اير": "airpods",
    "ساعه": "watch", "اسواره": "bracelet", "سوار": "bracelet", "غويشه": "bracelet", "اساور": "bracelet",
    "خاتم": "ring", "سلسله": "necklace chain", "قلاده": "necklace", "عقد": "necklace", "حلق": "earrings",
    "نظاره": "glasses", "نضاره": "glasses", "نظارات": "glasses", "شمسيه": "umbrella", "مظله": "umbrella",
    "لابتوب": "laptop", "لاب": "laptop", "ايباد": "ipad tablet", "تابلت": "tablet",
    "جراب": "case cover", "كفر": "case cover", "غطا": "cover", "غطاء": "cover",
    "شاحن": "charger", "كيبل": "cable", "وصله": "cable", "سلك": "cable", "باور": "power bank", "بنك": "bank",
    "فلاشه": "usb flash drive", "قنينه": "water bottle", "قاروره": "water bottle", "مطاره": "water bottle",
    "زجاجه": "bottle", "جاكيت": "jacket", "جاكيته": "jacket", "جكيت": "jacket", "معطف": "coat",
    "هودي": "hoodie", "كنزه": "sweater", "بلوزه": "sweater", "شال": "scarf", "وشاح": "scarf", "لفحه": "scarf",
    "دفتر": "notebook", "كشكول": "notebook", "كتاب": "book", "مقلمه": "pencil case", "قلم": "pen",
    "حاسبه": "calculator", "اله": "calculator", "هويه": "ID card", "بطاقه": "card", "كرت": "card",
    "جامعيه": "student university", "رخصه": "driving licence",
    # colours
    "اسود": "black", "سودا": "black", "سوداء": "black", "ابيض": "white", "بيضا": "white", "بيضاء": "white",
    "احمر": "red", "حمرا": "red", "حمراء": "red", "ازرق": "blue", "زرقا": "blue", "زرقاء": "blue",
    "كحلي": "navy blue", "اخضر": "green", "خضرا": "green", "خضراء": "green", "اصفر": "yellow",
    "صفرا": "yellow", "صفراء": "yellow", "بني": "brown", "بنيه": "brown", "رمادي": "gray", "رماديه": "gray",
    "سكني": "gray", "فضي": "silver", "فضيه": "silver", "ذهبي": "gold", "ذهبيه": "gold", "دهبي": "gold",
    "زهري": "pink", "زهريه": "pink", "وردي": "pink", "بنفسجي": "purple", "بنفسجيه": "purple", "موف": "purple",
    "برتقالي": "orange", "بيج": "beige", "شفاف": "transparent", "شفافه": "transparent",
    # materials and details
    "صغير": "small", "صغيره": "small", "كبير": "big", "كبيره": "big", "جلد": "leather", "جلدي": "leather",
    "معدن": "metal", "حديد": "metal", "بلاستيك": "plastic", "قماش": "fabric",
    "سحاب": "zipper", "سحابات": "zipper", "سوسته": "zipper", "ملصق": "sticker", "ستيكر": "sticker",
    "لزقه": "sticker", "علامه": "tag", "تاغ": "tag", "شكل": "shape", "مسمار": "nail", "وجه": "face",
    "وجهها": "face", "حزام": "strap", "سير": "strap", "جنزير": "metal strap", "مكسور": "broken",
    "مكسوره": "broken", "مخدوش": "scratched", "قلب": "heart", "نجمه": "star", "حرف": "letter", "اسم": "name",
    # added after booth testing: words visitors actually use
    "ايربود": "airpods earbuds", "بودز": "earbuds", "بلوتوث": "wireless", "هيدفون": "headphones",
    "هدفون": "headphones", "هيدسيت": "headset", "فلاش": "usb flash drive", "ميموري": "usb flash drive",
    "مي": "water", "ميه": "water", "مطره": "water bottle", "محبس": "ring", "سلسال": "necklace chain",
    "مسبحه": "prayer beads", "جواز": "passport", "سياره": "car", "شعار": "logo", "لوجو": "logo",
    "رسمه": "drawing", "مكتوب": "written", "مخطط": "striped", "منقط": "dotted", "مدور": "round",
    "مربع": "square", "جديد": "new", "جديده": "new", "قديم": "old", "قديمه": "old", "طويل": "long",
    "قصير": "short", "خمري": "maroon", "نبيتي": "maroon", "زيتي": "olive green", "سماوي": "light blue",
    "فوشي": "pink", "كريمي": "cream", "رصاصي": "gray", "فاتح": "light", "غامق": "dark",
    "علبه": "case", "رجالي": "men's", "نسائي": "women's", "بيت": "house", "اقلام": "pens", "كتب": "books",
}
GLOSS = {norm(k): v for k, v in _RAW.items()}
_PREFIXES = ("وبال", "بال", "وال", "فال", "كال", "لل", "ال", "و", "ب", "ل")


def _stems(w: str):
    """Possessive suffixes: جزداني -> جزدان, هويتي -> هويه, ساعتها -> ساعه."""
    yield w
    for suf, rep in (("تها", "ه"), ("تنا", "ه"), ("تي", "ه"), ("تك", "ه"), ("ته", "ه"),
                     ("ها", ""), ("نا", ""), ("كم", ""), ("ي", ""), ("ك", ""), ("ه", "")):
        if w.endswith(suf) and len(w) - len(suf) >= 2:
            yield w[: -len(suf)] + rep


def _lookup(w: str):
    for p in ("",) + _PREFIXES:  # الساعه / بسحاب / والمفتاح
        if p and not (w.startswith(p) and len(w) - len(p) >= 2):
            continue
        for s in _stems(w[len(p):]):
            if s in GLOSS:
                return GLOSS[s]
    return None


def _units(text: str):
    """(english, kind) per recognised word, in order. kind: 'latin' for brand names / numbers kept as typed."""
    out = []
    for raw in re.findall(r"[\u0621-\u064A\u064B-\u0652]+|[A-Za-z0-9]+", text):
        if re.match(r"[A-Za-z0-9]", raw):
            out.append((raw, "latin"))
        elif (en := _lookup(norm(raw))):
            out.append((en, "word"))
    return out


def to_english(text: str) -> str:
    """Translate the known words; keep Latin tokens (brand names like IIK, AirPods). '' if nothing known."""
    units = _units(text)
    return " ".join(u for u, _ in units) if any(k == "word" for _, k in units) else ""


_COLOR_WORDS = {"black", "white", "gray", "silver", "red", "blue", "green", "yellow", "pink",
                "purple", "brown", "orange", "gold", "beige", "transparent", "navy", "olive", "maroon", "cream"}
# Arabic puts adjectives after the noun; English wants them before, in a fixed order:
# size, age, shape, colour, material, purpose ("small old round black leather men's wallet").
_ADJ = {"small": 0, "big": 0, "long": 0, "short": 0, "new": 1, "old": 1, "round": 2, "square": 2,
        "striped": 2, "dotted": 2, "broken": 2, "scratched": 2,
        "leather": 4, "metal": 4, "plastic": 4, "fabric": 4, "men's": 5, "women's": 5}
_SHADE = {"light", "dark"}
_COMPOUNDS = [("card student_university", "university_student_card"), ("card university", "university_card"),
              ("card student", "student_card"), ("bag backpack", "backpack"), ("bag hand", "handbag"),
              ("case earbuds_case", "earbuds_case"), ("case case_cover", "case"),
              ("case_cover ipad_tablet", "ipad_case"), ("case_cover phone", "phone_case"), ("case_cover iphone", "iphone_case"),
              ("cover ipad_tablet", "ipad_cover"), ("water_bottle water", "water_bottle"), ("bottle water", "water_bottle"),
              ("glasses umbrella", "sunglasses"), ("key house", "house_key"), ("key car", "car_key"),
              ("keys car", "car_keys"), ("keys house", "house_keys"), ("usb_flash_drive usb_flash_drive", "usb_flash_drive"),
              ("purse_wallet", "wallet")]   # جزدان means purse or wallet: both go to search, "wallet" is displayed
# things an item has: rendered "with a ..." after the item ("black wallet with a zipper")
_DETAIL = {"zipper", "logo", "sticker", "strap", "metal_strap", "tag", "keychain", "name", "letter", "heart",
           "star", "drawing", "face"}


def _adj_class(tok: str):
    words = tok.split("_")
    if all(w in _COLOR_WORDS or w in _SHADE for w in words):
        return 3
    return _ADJ.get(tok)


def readable(text: str) -> str:
    """Display only: what the AI understood, in English word order. The search vector still uses to_english.
    "شنتة سودا" -> raw gloss "bag black" -> "black bag"; "ساعة رجالي فضي وجهها كحلي" -> "silver men's watch,
    navy blue face"; "ازرق فاتح" -> "light blue"; brand names stay after the noun ("silver watch IIK")."""
    units = _units(text)
    if not any(k == "word" for _, k in units):
        return ""
    # one token per unit ("earbuds case" stays together), then fix compounds that read back-to-front
    line = " ".join(u.replace(" ", "_") if k == "word" else "~" + u for u, k in units)
    for a, b in _COMPOUNDS:
        line = re.sub(rf"(?<!\S){a}(?!\S)", b, line)
    segs = []  # [noun, [(class, adjective)], brands]
    line = re.sub(r"(?<!\S)shape (\w+)", r"\1-shaped", line)            # "shape nail" -> "nail-shaped"
    for tok in line.split():
        if tok.endswith("-shaped"):
            (segs[-1][1].append((2, tok)) if segs else segs.append(["", [(2, tok)], []]))
            continue
        if tok.startswith("~"):
            (segs[-1][2].append(tok[1:]) if segs else segs.append([tok[1:], [], []]))
            continue
        c = _adj_class(tok)
        if c is None or not segs:
            segs.append([tok, [], []] if c is None else ["", [(c, tok)], []])
            continue
        adjs = segs[-1][1]
        if tok in _SHADE and adjs and adjs[-1][0] == 3:          # "blue light" -> "light blue"
            adjs[-1] = (3, f"{tok}_{adjs[-1][1]}")
        else:
            adjs.append((c, tok))
    out = []
    for noun, adjs, brands in segs:
        if noun in _DETAIL and out:
            parts = [a for _, a in sorted(adjs, key=lambda a: a[0])]
            out.append(("with a " + " ".join(parts + [noun]), None))
            continue
        adjs = sorted(adjs, key=lambda a: a[0])
        colours = [a for _, a in adjs if _ == 3]
        parts = [a for c, a in adjs if c < 3]
        if colours: parts.append(" and ".join(colours))
        parts += [a for c, a in adjs if c > 3]
        out.append(((" ".join(parts + ([noun] if noun else []) + brands)).strip(), bool(adjs)))
    txt = ""
    for i, (t, has_adj) in enumerate(out):
        txt += t if i == 0 else (" " if has_adj is None or not has_adj else ", ") + t
    txt = txt.replace("_", " ")
    for a, b in (("ipad", "iPad"), ("iphone", "iPhone"), ("airpods", "AirPods"), ("usb", "USB")):
        txt = re.sub(rf"\b{a}\b", b, txt)
    return txt


# ---------------------------------------------------------------- booth screen safety
# The booth's big screen shows what visitors typed. An allow-list, not a block-list: a description is shown
# only if EVERY word is a known item/colour/detail word or an ordinary filler word. Anything else (a rude
# word, a person's name, a phone number) means the screen shows "someone described an item" instead.
# Anything about IDs is never shown at all.
_FILLER_AR = {norm(w) for w in """من على عليه عليها عليهم في فيه فيها فيهم مع او و لون لونه لونها بلون الي اللي هاد هاي هذا
هذه هاذا كان كانت ضاع ضاعت ضاعو ضيعت ضيعته ضيعتها لقيت شي اشي تبعي تبعتي عندي بدي بس كتير كثير شوي نوع ماركه
عند جنب قدام ورا الجامعه بالجامعه مكتبه المكتبه قاعه كافتيريا البوابه بوابه مبنى اليوم امبارح مبارح الصبح حجم
تقريبا يمكن لونين زي مثل كمان حدا ساحه ملعب الكليه كليه الدرج المصلى مصلى وين وقع وقعت نسيت نسيته نسيتها
ضايع ضايعه صار صارت لما كنت بالمحاضره المحاضره""".split()}
_EN_OK = set("""a an the my your his her with and or of on in at for to from near some small big large little old new
lost found it its is was has have i me this that one two light dark round square long short
keys wallet purse phone earbuds case headphones laptop tablet charger cable water bottle backpack handbag bag
glasses watch bracelet jewelry notebook book umbrella jacket hoodie scarf calculator usb flash drive pencil
power bank keyring keychain zipper strap men mens women womens cover airpods iphone ipad black white gray grey
silver red blue green yellow pink purple brown orange gold beige transparent navy""".split())
for _v in GLOSS.values():
    _EN_OK.update(_v.lower().split())
_ID_WORDS = {"id", "card", "licence", "passport", "student"}


def _known_ar(w: str) -> bool:
    n = norm(w)
    if _lookup(n) or n in _FILLER_AR:
        return True
    for p in _PREFIXES:
        if n.startswith(p) and len(n) - len(p) >= 2 and n[len(p):] in _FILLER_AR:
            return True
    return False


def booth_safe(text: str) -> dict:
    """What the booth may show for a visitor's description: {"show": str, "understood": str, "id_like": bool}."""
    toks = re.findall(r"[\u0621-\u064A\u064B-\u0652]+|[A-Za-z]+|\d+", text)
    understood = readable(text) if re.search(r"[\u0600-\u06FF]", text) else ""
    words = set(" ".join([text.lower(), to_english(text).lower()]).split())
    id_like = bool(_ID_WORDS & {w.strip(".,!?") for w in words})
    ok = bool(toks) and all(
        _known_ar(t) if re.match(r"[\u0621-\u064A]", t) else (t.lower() in _EN_OK) for t in toks if not t.isdigit())
    if any(t.isdigit() and len(t) >= 4 for t in toks):   # could be part of an ID or phone number
        ok = False
    # the gloss itself may carry a raw Latin word through; keep only known words
    understood = " ".join(w for w in understood.replace(",", " ,").split() if w == "," or w.lower() in _EN_OK or w == "and").replace(" ,", ",")
    return {"show": text.strip()[:80] if ok and not id_like else "", "understood": understood, "id_like": id_like}
