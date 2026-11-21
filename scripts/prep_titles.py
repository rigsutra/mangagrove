"""Download chapters 1-10 of each title, then enhance (2x) + OCR every chapter.
usage: nohup .venv/bin/python scripts/prep_titles.py > /tmp/prep.log 2>&1 &"""
import os, pathlib, subprocess, requests
ROOT = pathlib.Path(__file__).resolve().parent.parent; os.chdir(ROOT)
PY, B = str(ROOT / ".venv/bin/python"), "https://api.mangadex.org"
TITLES = [("battle-through-the-heavens", "Doupo Cangqiong", "cee2ab81"),
          ("martial-universe", "Martial Universe", "d7862895"),
          ("against-the-gods", "Against the Gods", "a9eb39e6"),
          ("reverend-insanity", "Reverend Insanity", "bb71e1b9")]
def find_id(name, prefix):
    for q in (name, name.split()[0]):
        for m in requests.get(B + "/manga", params={"title": q, "limit": 25}).json()["data"]:
            if m["id"].startswith(prefix): return m["id"]
    raise SystemExit(f"id not found for {name}")
for slug, name, prefix in TITLES:
    d = ROOT / "raw_en" / slug
    if not d.exists() or not any(d.glob("*/*.jpg")):
        mid = find_id(name, prefix); d.mkdir(parents=True, exist_ok=True)
        print("DOWNLOAD", slug, mid, flush=True)
        subprocess.run([str(ROOT / ".venv/bin/mangadex-dl"), f"https://mangadex.org/title/{mid}", "-lang", "en",
                        "--start-chapter", "1", "--end-chapter", "10", "--save-as", "raw", "--no-group-name", "-d", str(d)],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for ch in sorted(p for p in d.iterdir() if p.is_dir()):
        print("PREP", slug, ch.name, flush=True)
        subprocess.run([PY, "enhance.py", str(ch)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run([PY, "ocr.py", str(ch)], env={**os.environ, "OCR_SCALE": "2", "OCR_GAP": "9", "OCR_LANGS": "en", "OCR_INVERT": "0"},
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
print("ALL DONE", flush=True)
