"""Translate a chapter's speech bubbles with a vision model through OpenRouter.

usage:
  python scripts/translate_openrouter.py "raw_en/<title>/<chapter>" --rights rights/<title>.json [--lang hinglish] [--dry-run]

Needs OPENROUTER_API_KEY (environment or a local .env file, never committed).
Optional: OPENROUTER_MODEL (default google/gemini-2.5-flash; any vision-capable model on OpenRouter).
LOCAL MODEL: set LLM_BASE_URL (e.g. http://localhost:11434/v1 for Ollama, http://localhost:1234/v1 for LM Studio)
and LLM_MODEL; no key needed. Add --no-image to send OCR text only (works with text-only models).

Reads  out/<title>/<chapter>/ocr.json (from ocr.py) and the original pages.
Writes tr/<title>/<chapter>.json  in the format render.py expects. Resumable: finished pages are skipped.

RIGHTS GATE: refuses to run unless --rights points to a JSON file with an open licence
(see RIGHTS.md): {"license": {"name": "CC BY 4.0", "url": ..., "holder": ..., "source": ..., "verified": ...}}
"""
import argparse, base64, json, os, pathlib, re, sys, time
import cv2, requests

OPEN_LICENSES = ["CC0", "CC BY 4.0", "CC BY-SA 4.0", "Public Domain"]   # keep in sync with site/src/lib/url.ts
LANG_NAME = {"hinglish": "casual Hinglish (Hindi written in Latin/English letters, as young Indians chat)",
             "hi": "natural Hindi in Devanagari script", "en": "natural English"}


def load_env():
    f = pathlib.Path(__file__).resolve().parent.parent / ".env"
    if f.exists():
        for line in f.read_text().splitlines():
            if "=" in line and not line.strip().startswith("#"):
                k, v = line.split("=", 1); os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


def check_rights(path):
    try:
        lic = json.load(open(path))["license"]
    except Exception:
        sys.exit(f"Rights check failed: cannot read a 'license' block from {path}. See RIGHTS.md.")
    need = ["name", "url", "holder", "source", "verified"]
    if any(not lic.get(k) for k in need) or lic["name"] not in OPEN_LICENSES:
        sys.exit(f"Rights check failed: license must have {need} and name in {OPEN_LICENSES}. See RIGHTS.md.")
    return lic


def page_image_b64(ch, name, ocr_boxes):
    im = cv2.imread(str(ch / name))
    for b in ocr_boxes:  # draw ids so the model can map text to boxes
        x0, y0, x1, y1 = b["box"]
        cv2.rectangle(im, (x0, y0), (x1, y1), (0, 0, 255), 2)
        cv2.putText(im, str(b["id"]), (x0, max(y0 - 3, 14)), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2)
    ok, buf = cv2.imencode(".jpg", im, [cv2.IMWRITE_JPEG_QUALITY, 85])
    return base64.b64encode(buf).decode()


def build_messages(lang, glossary, recent, boxes, b64):  # b64=None -> text only
    rules = (f"Translate comic speech bubbles into {LANG_NAME.get(lang, lang)}. Rules: keep names, places, technique and "
             "rank terms in English exactly as in the source; keep each line about as short as the original (it must fit the same bubble); "
             "keep tone; fix OCR mistakes by reading the image; skip sound effects, big art lettering, titles, watermarks and junk boxes. "
             'Reply with ONLY a JSON object {"<box id>": "<translation>"}; merge a sentence split across boxes by using a key like "6+7".')
    text = (f"Glossary so far: {json.dumps(glossary, ensure_ascii=False)}\n"
            f"Previous lines (for continuity): {json.dumps(recent, ensure_ascii=False)}\n"
            "OCR boxes (noisy):\n" + "\n".join(f"{b['id']}: {b['zh']}" for b in boxes))
    if b64 is None:
        return [{"role": "system", "content": rules}, {"role": "user", "content": text}]
    return [{"role": "system", "content": rules},
            {"role": "user", "content": [{"type": "text", "text": text},
                                         {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}}]}]


def call(messages, model, key, api, tries=4):
    for i in range(tries):
        r = requests.post(api, headers={"Authorization": f"Bearer {key or 'none'}", "Content-Type": "application/json",
                                        "X-Title": "mangagrove"}, json={"model": model, "messages": messages, "temperature": 0.3}, timeout=180)
        if r.status_code == 200:
            d = r.json()
            return d["choices"][0]["message"]["content"], d.get("usage", {})
        if r.status_code in (429, 500, 502, 503):
            time.sleep(2 ** (i + 1)); continue
        sys.exit(f"LLM server error {r.status_code}: {r.text[:300]}")
    sys.exit("The model server kept failing; try again later (progress is saved).")


def parse_json(s):
    m = re.search(r"\{.*\}", s, re.S)
    return json.loads(m.group(0)) if m else {}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("chapter"); ap.add_argument("--rights", required=True)
    ap.add_argument("--lang", default="hinglish"); ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--no-image", action="store_true", help="send OCR text only (no page image)")
    a = ap.parse_args()
    check_rights(a.rights)
    load_env()
    base = os.environ.get("LLM_BASE_URL", "https://openrouter.ai/api/v1").rstrip("/")
    api, local = base + "/chat/completions", ("localhost" in base or "127.0.0.1" in base)
    key = os.environ.get("OPENROUTER_API_KEY")
    model = os.environ.get("LLM_MODEL") or os.environ.get("OPENROUTER_MODEL", "google/gemini-2.5-flash")
    if not key and not local and not a.dry_run:
        sys.exit("Set OPENROUTER_API_KEY in your environment or in a .env file (see .env.example).")
    ch = pathlib.Path(a.chapter)
    par = "" if ch.parent.name in ("raw_en", "raw", ".", "") else ch.parent.name
    ocr = json.load(open(pathlib.Path("out") / par / ch.name / "ocr.json"))
    dest = pathlib.Path("tr") / par / f"{ch.name}.json"; dest.parent.mkdir(parents=True, exist_ok=True)
    result = json.load(open(dest)) if dest.exists() else {}
    gl_file = dest.parent / "glossary.json"; glossary = json.load(open(gl_file)) if gl_file.exists() else {}
    recent, tokens = [], 0
    for name in sorted(ocr):
        boxes = [b for b in ocr[name] if len(b["zh"].strip()) > 1]
        if name in result or not boxes:
            continue
        msgs = build_messages(a.lang, glossary, recent[-8:], boxes, None if a.no_image else page_image_b64(ch, name, boxes))
        if a.dry_run:
            print(f"[dry run] {name}: {len(boxes)} boxes, request ~{len(json.dumps(msgs)) // 1024} KB, model {model}"); return
        out, usage = call(msgs, model, key, api)
        tokens += usage.get("total_tokens", 0)
        try:
            page = parse_json(out)
        except Exception:
            print(f"  {name}: could not parse reply, skipped"); continue
        result[name] = {str(k): v for k, v in page.items() if isinstance(v, str) and v.strip()}
        recent += list(result[name].values())
        json.dump(result, open(dest, "w"), ensure_ascii=False, indent=1)   # save after every page
        print(f"  {name}: {len(result[name])} translated", flush=True)
    print(f"done -> {dest}  (tokens used: {tokens})")


if __name__ == "__main__":
    main()
