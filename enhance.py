"""AI-upscale pages (Real-ESRGAN anime 6B) -> out/<chapter>/enhanced/<page>.png at OUT_SCALE x original.
usage: python enhance.py "raw_en/Vol. 1 Ch. 1" [page-glob] """
import sys, pathlib, os
def outdir(ch):
    """out/<chapter> for raw_en/<chapter>, out/<title>/<chapter> for raw_en/<title>/<chapter>"""
    import pathlib as _p
    ch=_p.Path(ch); par='' if ch.parent.name in ('raw_en','raw','.','') else ch.parent.name
    return _p.Path('out')/par/ch.name

import cv2, numpy as np, torch
from spandrel import ModelLoader

OUT_SCALE = float(os.environ.get("OUT_SCALE", "2"))
dev = torch.device("mps" if torch.backends.mps.is_available() else "cpu")
model = ModelLoader().load_from_file("models/RealESRGAN_x4plus_anime_6B.pth").to(dev).eval()

@torch.no_grad()
def up4(img, tile=192, pad=16):
    h, w = img.shape[:2]
    out = np.zeros((h * 4, w * 4, 3), np.float32)
    for y in range(0, h, tile):
        for x in range(0, w, tile):
            y0, x0, y1, x1 = max(y - pad, 0), max(x - pad, 0), min(y + tile + pad, h), min(x + tile + pad, w)
            t = torch.from_numpy(img[y0:y1, x0:x1, ::-1].copy()).permute(2, 0, 1)[None].float().div(255).to(dev)
            r = model(t).clamp(0, 1)[0].permute(1, 2, 0).cpu().numpy()[:, :, ::-1]
            ty0, tx0 = (y - y0) * 4, (x - x0) * 4
            hh, ww = min(tile, h - y) * 4, min(tile, w - x) * 4
            out[y * 4:y * 4 + hh, x * 4:x * 4 + ww] = r[ty0:ty0 + hh, tx0:tx0 + ww]
    return (out * 255).round().astype(np.uint8)

if __name__ == "__main__":
    ch = pathlib.Path(sys.argv[1]); pat = sys.argv[2] if len(sys.argv) > 2 else "*.jpg"
    dest = outdir(ch) / "enhanced"; dest.mkdir(parents=True, exist_ok=True)
    for img in (sorted(p for p in ch.iterdir() if p.suffix.lower() in {'.jpg', '.jpeg', '.png', '.webp'}) if pat == "*.jpg" else sorted(ch.glob(pat))):
        im = cv2.imread(str(img))
        big = up4(im)
        if OUT_SCALE != 4:
            big = cv2.resize(big, (int(im.shape[1] * OUT_SCALE), int(im.shape[0] * OUT_SCALE)), interpolation=cv2.INTER_AREA)
        cv2.imwrite(str(dest / (img.stem + ".png")), big)
        print(img.name, big.shape[1], "x", big.shape[0], flush=True)
