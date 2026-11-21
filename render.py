"""Erase OCR'd text and draw translated text.

usage: python render.py "raw_en/Vol. 1 Ch. 1" tr/ch1_hinglish.json [scale]
  tr value: "text"  |  {"text": ..., "box": [x0,y0,x1,y1]}   key: "7" or "6+7" (merge boxes)
  -> out/<chapter>/translated/<page>.jpg   (scale 2 = sharpened 2x output)
"""
import json, sys, pathlib
def outdir(ch):
    """out/<chapter> for raw_en/<chapter>, out/<title>/<chapter> for raw_en/<title>/<chapter>"""
    import pathlib as _p
    ch=_p.Path(ch); par='' if ch.parent.name in ('raw_en','raw','.','') else ch.parent.name
    return _p.Path('out')/par/ch.name

import cv2, numpy as np
from PIL import Image, ImageDraw, ImageFont

FONT = "/System/Library/Fonts/Supplemental/Comic Sans MS Bold.ttf"

def ring_stats(im, box, pad):
    h, w = im.shape[:2]
    x0, y0, x1, y1 = box
    x0, y0, x1, y1 = max(x0 - pad, 0), max(y0 - pad, 0), min(x1 + pad, w), min(y1 + pad, h)
    m = np.zeros((h, w), np.uint8)
    cv2.rectangle(m, (x0, y0), (x1 - 1, y1 - 1), 255, -1)
    inner = m.copy(); cv2.rectangle(inner, (x0 + 3, y0 + 3), (x1 - 4, y1 - 4), 0, -1)
    px = im[inner > 0].reshape(-1, 3)
    return (x0, y0, x1, y1), np.median(px, axis=0), px.std(axis=0).max(), (px.mean(axis=1) > 215).mean()

def wrap(draw, text, font, maxw):
    lines, cur = [], ""
    for word in text.split():
        t = (cur + " " + word).strip()
        if draw.textlength(t, font=font) <= maxw or not cur:
            cur = t
        else:
            lines.append(cur); cur = word
    return lines + [cur]

def fit(draw, text, box, S, smallest=8):
    bw, bh = box[2] - box[0] - 6 * S, box[3] - box[1] - 6 * S
    for size in range(int(26 * S), int(smallest * S) - 1, -1):
        font = ImageFont.truetype(FONT, size)
        lines = wrap(draw, text, font, bw)
        lh = size * 1.18
        if len(lines) * lh <= bh and all(draw.textlength(l, font=font) <= bw for l in lines):
            return font, lines, lh
    return None

def art_erase(im, box):
    """caption over artwork: inpaint only the lettering pixels (very light or very dark) inside the box"""
    x0, y0, x1, y1 = box
    g = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)
    m = np.zeros(g.shape, np.uint8)
    reg = g[y0:y1, x0:x1]
    m[y0:y1, x0:x1] = ((reg > 215) | (reg < 55)).astype(np.uint8) * 255
    m = cv2.dilate(m, np.ones((5, 5), np.uint8))
    return cv2.inpaint(im, m, 4, cv2.INPAINT_TELEA)

if __name__ == "__main__":
    ch, tr = pathlib.Path(sys.argv[1]), json.load(open(sys.argv[2]))
    S = int(sys.argv[3]) if len(sys.argv) > 3 else 1
    ocr = json.load(open(outdir(ch) / "ocr.json"))
    dest = outdir(ch) / "translated"; dest.mkdir(parents=True, exist_ok=True)
    skipped, art = [], []
    for img in sorted(ch.glob("*.jpg")):
        im = cv2.imread(str(img))
        enh = outdir(ch) / "enhanced" / (img.stem + ".png")
        if enh.exists():  # AI-enhanced page from enhance.py
            S = round(cv2.imread(str(enh)).shape[1] / im.shape[1])
            im = cv2.imread(str(enh))
        elif S > 1:  # fallback: cubic upscale + mild sharpen
            big = cv2.resize(im, None, fx=S, fy=S, interpolation=cv2.INTER_CUBIC)
            im = cv2.addWeighted(big, 1.5, cv2.GaussianBlur(big, (0, 0), 1.5 * S), -0.5, 0)
        boxes = {str(b["id"]): b["box"] for b in ocr[img.name]}
        flat, arts = [], []
        for key, val in tr.get(img.name, {}).items():
            text, manual = (val, None) if isinstance(val, str) else (val["text"], val.get("box"))
            if manual: box = manual
            else:
                bs = [boxes[k] for k in key.split("+")]
                box = [min(b[0] for b in bs), min(b[1] for b in bs), max(b[2] for b in bs), max(b[3] for b in bs)]
            box = [int(v * S) for v in box]
            best = None
            for pad in (14, 10, 6, 3):
                area, col, std, white = ring_stats(im, box, pad * S)
                if std < 18 or (std < 45 and white > 0.8): best = (area, col); break
            if best is None:
                area, col, std, white = ring_stats(im, box, 3 * S)
                if white > 0.8: best = (area, col)
            if best: flat.append((best[0], best[1], text))
            else: arts.append((box, text)); art.append((img.name, key, text[:30]))
        for area, col, _ in flat:
            cv2.rectangle(im, (area[0], area[1]), (area[2] - 1, area[3] - 1), tuple(int(c) for c in col), -1)
        for box, _ in arts:
            im = art_erase(im, box)
        pil = Image.fromarray(cv2.cvtColor(im, cv2.COLOR_BGR2RGB)); d = ImageDraw.Draw(pil)
        for area, col, text in flat:
            r = fit(d, text, area, S, smallest=7)
            if r is None: skipped.append((img.name, "overflow", text[:30])); continue
            font, lines, lh = r
            ink = (0, 0, 0) if col.mean() > 110 else (255, 255, 255)
            y = (area[1] + area[3]) / 2 - len(lines) * lh / 2
            for l in lines:
                d.text(((area[0] + area[2]) / 2 - d.textlength(l, font=font) / 2, y), l, font=font, fill=ink)
                y += lh
        for box, text in arts:  # outlined text so it reads on any art
            r = fit(d, text, [box[0] - 10 * S, box[1] - 6 * S, box[2] + 10 * S, box[3] + 6 * S], S, smallest=7)
            if r is None: skipped.append((img.name, "overflow-art", text[:30])); continue
            font, lines, lh = r
            y = (box[1] + box[3]) / 2 - len(lines) * lh / 2
            for l in lines:
                d.text(((box[0] + box[2]) / 2 - d.textlength(l, font=font) / 2, y), l, font=font,
                       fill=(255, 255, 255), stroke_width=max(2, S + 1), stroke_fill=(0, 0, 0))
                y += lh
        pil.save(dest / img.name, quality=93)
    print("art-mode captions:", len(art), "| skipped:", len(skipped)); [print(" ", s) for s in skipped]
