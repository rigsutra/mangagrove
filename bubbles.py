"""Find white speech bubbles per page and OCR each one separately.

usage: python bubbles.py "raw_en/Vol. 1 Ch. 1"  ->  out/<chapter>/bubbles.json + annotated/*.jpg
"""
import json, sys, pathlib
import cv2, numpy as np, easyocr

def find_bubbles(im):
    g = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)
    h, w = g.shape
    white = (g > 225).astype(np.uint8) * 255
    white = cv2.morphologyEx(white, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
    cs, _ = cv2.findContours(white, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    out = []
    for c in cs:
        x, y, bw, bh = cv2.boundingRect(c)
        if bw * bh < 2500 or bw * bh > 0.55 * w * h or bw < 40 or bh < 25:
            continue
        m = np.zeros(g.shape, np.uint8)
        cv2.drawContours(m, [c], -1, 255, -1)
        inside = m > 0
        dark = (g < 120) & inside
        if dark.sum() < 60 or dark.sum() / inside.sum() > 0.35:
            continue
        out.append({"box": [x, y, x + bw, y + bh], "mask_c": c})
    out.sort(key=lambda b: (b["box"][1] // 120, -b["box"][0]))  # panel rows top->bottom, right->left
    return out

if __name__ == "__main__":
    ch = pathlib.Path(sys.argv[1])
    reader = easyocr.Reader(["en"], gpu=False, verbose=False)
    dest = pathlib.Path("out") / ch.name
    (dest / "annotated").mkdir(parents=True, exist_ok=True)
    res = {}
    for img in sorted(ch.glob("*.jpg")):
        im = cv2.imread(str(img))
        ann = im.copy()
        res[img.name] = []
        for n, b in enumerate(find_bubbles(im)):
            x0, y0, x1, y1 = b["box"]
            crop = cv2.resize(im[y0:y1, x0:x1], None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
            lines = reader.readtext(crop, detail=0, paragraph=True)
            text = " ".join(lines).strip()
            if len(text) < 2:
                continue
            res[img.name].append({"id": n, "box": b["box"], "ocr": text})
            cv2.rectangle(ann, (x0, y0), (x1, y1), (0, 0, 255), 2)
            cv2.putText(ann, str(n), (x0 + 4, y0 + 22), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
        cv2.imwrite(str(dest / "annotated" / img.name), ann)
        print(img.name, len(res[img.name]), flush=True)
    (dest / "bubbles.json").write_text(json.dumps(res, ensure_ascii=False, indent=1))
