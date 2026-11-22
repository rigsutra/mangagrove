"""OCR a chapter folder -> out/<chapter>/ocr.json (grouped text blocks with boxes)."""
import json, sys, os, pathlib
def outdir(ch):
    """out/<chapter> for raw_en/<chapter>, out/<title>/<chapter> for raw_en/<title>/<chapter>"""
    import pathlib as _p
    ch=_p.Path(ch); par='' if ch.parent.name in ('raw_en','raw','.','') else ch.parent.name
    return _p.Path('out')/par/ch.name

import cv2, easyocr

MAX_W, MAX_H = int(os.environ.get("OCR_MAXW", "480")), int(os.environ.get("OCR_MAXH", "420"))  # original-page px

def group(dets, gap=int(os.environ.get("OCR_GAP", "22"))):
    """Merge OCR lines that sit close together (same bubble / caption)."""
    boxes = [{"b": [min(p[0] for p in d[0]), min(p[1] for p in d[0]),
                    max(p[0] for p in d[0]), max(p[1] for p in d[0])],
              "t": [d[1]], "c": d[2]} for d in dets
              if d[2] > 0.0 and not (d[0][0][1] > 1085 and d[0][0][0] > 600)]  # keep weak hits; skip site logo
    merged = True
    while merged:
        merged = False
        for i in range(len(boxes)):
            for j in range(i + 1, len(boxes)):
                a, b = boxes[i]["b"], boxes[j]["b"]
                if a[0] - gap < b[2] and b[0] - gap < a[2] and a[1] - gap < b[3] and b[1] - gap < a[3]:
                    # cap merged size so art/SFX hits can't chain separate bubbles into one panel-sized box
                    if max(a[2], b[2]) - min(a[0], b[0]) > MAX_W or max(a[3], b[3]) - min(a[1], b[1]) > MAX_H:
                        continue
                    boxes[i] ={"b": [min(a[0], b[0]), min(a[1], b[1]), max(a[2], b[2]), max(a[3], b[3])],
                                "t": boxes[i]["t"] + boxes[j]["t"], "c": min(boxes[i]["c"], boxes[j]["c"])}
                    del boxes[j]; merged = True; break
            if merged: break
    boxes.sort(key=lambda x: (x["b"][1] // 80, -x["b"][0]))  # top->bottom, right->left
    return [{"id": n, "box": [int(v) for v in x["b"]], "zh": "".join(x["t"]), "conf": round(float(x["c"]), 2)}
            for n, x in enumerate(boxes)]

if __name__ == "__main__":
    ch = pathlib.Path(sys.argv[1])
    reader = easyocr.Reader(os.environ.get("OCR_LANGS", "ch_sim,en").split(","), gpu=False)
    out = {}
    for img in sorted(p for p in ch.iterdir() if p.suffix.lower() in {'.jpg', '.jpeg', '.png', '.webp'}):
        im = cv2.imread(str(img))
        S = float(os.environ.get("OCR_SCALE", "1"))
        if S != 1:  # enhance first: upscale + mild sharpen so tiny text becomes detectable
            big = cv2.resize(im, None, fx=S, fy=S, interpolation=cv2.INTER_CUBIC)
            im = cv2.addWeighted(big, 1.6, cv2.GaussianBlur(big, (0, 0), 2), -0.6, 0)
        dets = reader.readtext(im, paragraph=False, text_threshold=0.5, low_text=0.25, link_threshold=0.3, min_size=6, mag_ratio=1.0)
        def bb(d): return [min(p[0] for p in d[0]), min(p[1] for p in d[0]), max(p[0] for p in d[0]), max(p[1] for p in d[0])]
        def hit(a, b): return a[0] < b[2] and b[0] < a[2] and a[1] < b[3] and b[1] < a[3]
        have = [bb(d) for d in dets]
        # white-on-black text (captions in dark gutters): OCR the inverted page too
        if os.environ.get("OCR_INVERT", "1") == "1": dets += [d for d in reader.readtext(255 - im, paragraph=False) if not any(hit(bb(d), h) for h in have)]
        if S != 1:  # back to original page coordinates
            dets = [([[p[0] / S, p[1] / S] for p in d[0]], d[1], d[2]) for d in dets]
        out[img.name] = group(dets)
        print(img.name, len(out[img.name]), flush=True)
    dest = outdir(ch)
    dest.mkdir(parents=True, exist_ok=True)
    (dest / "ocr.json").write_text(json.dumps(out, ensure_ascii=False, indent=1))
