"""Download Pepper&Carrot (CC BY 4.0, David Revoy, peppercarrot.com) episodes 1-5 in English + Hindi,
convert to WebP into site/public/series/pepper-and-carrot/<lang>/ch-<n>/NN.webp and write site/src/data/series.json."""
import io, json, pathlib, re, datetime, urllib.request
from PIL import Image
ROOT = pathlib.Path(__file__).resolve().parent.parent
BASE = "https://www.peppercarrot.com/0_sources/"
EPS = [(1, "ep01_Potion-of-Flight", "Potion of Flight"), (2, "ep02_Rainbow-potions", "Rainbow Potions"),
       (3, "ep03_The-secret-ingredients", "The Secret Ingredients"), (4, "ep04_Stroke-of-genius", "Stroke of Genius"),
       (5, "ep05_Special-holiday-episode", "Special Holiday Episode")]
LANGS = ["en", "hi"]
OUT = ROOT / "site" / "public" / "series" / "pepper-and-carrot"
get = lambda u: urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0"}), timeout=60).read()
chapters = []
for n, folder, title in EPS:
    listing = get(f"{BASE}{folder}/hi-res/").decode()
    langs = {}
    for lang in LANGS:
        files = sorted(set(re.findall(rf'href="({lang}_Pepper-and-Carrot_by-David-Revoy_E\d+P\d+\.jpg)"', listing)))
        dims = []
        for i, f in enumerate(files):
            im = Image.open(io.BytesIO(get(f"{BASE}{folder}/hi-res/{f}"))).convert("RGB")
            if im.width > 1200: im = im.resize((1200, round(im.height * 1200 / im.width)), Image.LANCZOS)
            d = OUT / lang / f"ch-{n}"; d.mkdir(parents=True, exist_ok=True)
            im.save(d / f"{i:02d}.webp", "WEBP", quality=82, method=6)
            dims.append([im.width, im.height])
            if lang == "en" and n == 1 and i == 0:
                c = im.copy(); c.thumbnail((600, 840)); c.save(OUT / "cover.webp", "WEBP", quality=85)
        langs[lang] = dims
        print(n, lang, len(files), flush=True)
    chapters.append({"n": n, "title": title, "date": "2015-05-08" if n == 1 else "2015-06-01", "langs": langs})
series = [{"slug": "pepper-and-carrot", "title": "Pepper&Carrot", "genres": ["Fantasy", "Comedy", "Adventure"], "status": "Ongoing",
           "langs": LANGS,
           "synopsis": "A young witch, Pepper, and her cat Carrot stumble through magical mishaps in the world of Hereva. "
                       "An open webcomic by David Revoy, free to read and share under a Creative Commons license.",
           "credit": "Pepper&Carrot by David Revoy, www.peppercarrot.com, licensed CC BY 4.0",
           "chapters": chapters}]
(ROOT / "site" / "src" / "data" / "series.json").write_text(json.dumps(series, indent=1))
print("done", sum(len(l) for c in chapters for l in c["langs"].values()), "pages")
