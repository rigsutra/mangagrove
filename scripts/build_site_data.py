"""Copy translated chapters into site/public as WebP and write site/src/data/series.json.
usage: python scripts/build_site_data.py   (edit SERIES below to add chapters)"""
import json, pathlib, datetime
from PIL import Image

ROOT = pathlib.Path(__file__).resolve().parent.parent
PUB = ROOT / "site" / "public" / "series"
SERIES = [{
    "slug": "soul-land",
    "title": "Soul Land (Hinglish)",
    "cover_src": ROOT / "raw_en" / "cover.jpg",
    "genres": ["Action", "Adventure", "Fantasy"],
    "status": "Ongoing",
    "synopsis": "Tang San, a disciple of the Tang Sect, gives up his life to protect its forbidden art, "
                "and is reborn in Combat Continent, a world where everyone awakens a Spirit. "
                "Translated to Hinglish as a personal translation experiment.",
    "chapters": [{"n": 1, "title": "The Tang Apprentice", "src": ROOT / "out" / "Vol. 1 Ch. 1" / "translated"}],
}]

def webp(src, dst, q=88):
    dst.parent.mkdir(parents=True, exist_ok=True)
    Image.open(src).convert("RGB").save(dst, "WEBP", quality=q, method=6)

out = []
for s in SERIES:
    d = PUB / s["slug"]
    webp(s["cover_src"], d / "cover.webp")
    chs = []
    for c in s["chapters"]:
        pages = sorted(c["src"].glob("*.jpg"))
        for i, p in enumerate(pages):
            webp(p, d / f"ch-{c['n']}" / f"{i:02d}.webp")
        chs.append({"n": c["n"], "title": c["title"], "pages": len(pages),
                    "date": datetime.date.today().isoformat()})
    out.append({k: s[k] for k in ("slug", "title", "genres", "status", "synopsis")} | {"chapters": chs})
dst = ROOT / "site" / "src" / "data" / "series.json"
dst.parent.mkdir(parents=True, exist_ok=True)
dst.write_text(json.dumps(out, indent=1))
print("series:", len(out), "chapters:", sum(len(s["chapters"]) for s in out))
