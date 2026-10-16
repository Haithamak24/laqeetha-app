"""Drag a photo onto try_photo.bat to see what the AI thinks it is (top 5), with the label set in use."""
import sys
from PIL import Image, ImageOps
from app.embedder import Embedder
emb = Embedder()
for path in sys.argv[1:]:
    img = ImageOps.exif_transpose(Image.open(path)).convert("RGB")
    v = emb.image(img); t = emb.tag(v)
    print(f"\n{path}\n  prompt set: {emb.prompt_set}   colour: {t['color']}   ID card: {'YES' if t['is_id'] else 'no'} ({t['id_prob']:.0%})")
    for name in ("v1", "v2"):
        tt = emb.tag(v, emb.label_vecs(name))
        alts = ", ".join(f"{a['label']} {a['p']:.0%}" for a in tt["alternatives"])
        print(f"  {name}: {tt['category']} {tt['category_conf']:.0%}   then: {alts}")
