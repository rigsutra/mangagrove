"""Make annotated page pairs + a bubble list for a chapter so a translator can read boxes by id.
usage: python scripts/annotate_chapter.py "raw_en/<title>/<chapter>"
-> out/<title>/<chapter>/pairs/NN.jpg  and  out/<title>/<chapter>/bubbles.txt"""
import json, pathlib, sys
import cv2, numpy as np
ch = pathlib.Path(sys.argv[1])
par = "" if ch.parent.name in ("raw_en", "raw", ".", "") else ch.parent.name
dest = pathlib.Path("out") / par / ch.name
ocr = json.load(open(dest / "ocr.json"))
names = sorted(ocr)
(dest / "pairs").mkdir(exist_ok=True)
def ann(n):
    im = cv2.imread(str(ch / n))
    for b in ocr[n]:
        x0, y0, x1, y1 = b["box"]; cv2.rectangle(im, (x0, y0), (x1, y1), (0, 0, 255), 2)
        cv2.putText(im, str(b["id"]), (x0, max(y0 - 3, 14)), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2)
    return im
for i in range(0, len(names), 2):
    ims = [ann(n) for n in names[i:i + 2]]; h = max(x.shape[0] for x in ims)
    ims = [cv2.copyMakeBorder(x, 0, h - x.shape[0], 0, 0, cv2.BORDER_CONSTANT, value=(255, 255, 255)) for x in ims]
    cv2.imwrite(str(dest / "pairs" / f"{i:02d}.jpg"), np.hstack(ims), [cv2.IMWRITE_JPEG_QUALITY, 85])
lines = []
for n in names:
    lines.append(f"## {n}")
    lines += [f"  {b['id']}: {b['zh']}" for b in ocr[n]]
(dest / "bubbles.txt").write_text("\n".join(lines))
print(dest, len(names), "pages,", sum(map(len, ocr.values())), "boxes")
