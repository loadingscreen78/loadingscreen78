#!/usr/bin/env python3
"""Prep a portrait photo for ASCII conversion (run once per photo).

    python scripts/prep_photo.py assets/source-photo.jpg

1. Cut the subject out of the background (rembg if installed, else OpenCV GrabCut).
2. Boost local contrast with CLAHE so a flatly-lit face gets real highlights/shadows.
3. Crop to the subject and save assets/source-prepped.png as gray + alpha.
"""
import sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "assets" / "source-prepped.png"


def cutout_rembg(rgb):
    from rembg import remove  # optional dependency
    rgba = np.asarray(remove(Image.fromarray(rgb)))
    return rgba[..., 3].astype(np.float32) / 255.0


def cutout_grabcut(rgb):
    h, w = rgb.shape[:2]
    mask = np.zeros((h, w), np.uint8)
    rect = (int(w * 0.03), int(h * 0.02), int(w * 0.94), h - int(h * 0.02) - 1)
    bgd, fgd = np.zeros((1, 65), np.float64), np.zeros((1, 65), np.float64)
    cv2.grabCut(cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR), mask, rect, bgd, fgd, 8, cv2.GC_INIT_WITH_RECT)
    fg = np.where((mask == cv2.GC_FGD) | (mask == cv2.GC_PR_FGD), 255, 0).astype(np.uint8)
    # keep the largest blob (the person), close small gaps, fill holes
    n, labels, stats, _ = cv2.connectedComponentsWithStats(fg, 8)
    if n > 1:
        biggest = 1 + int(np.argmax(stats[1:, cv2.CC_STAT_AREA]))
        fg = np.where(labels == biggest, 255, 0).astype(np.uint8)
    fg = cv2.morphologyEx(fg, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9)))
    contours, _ = cv2.findContours(fg, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    fg = cv2.drawContours(np.zeros_like(fg), contours, -1, 255, cv2.FILLED)
    return cv2.GaussianBlur(fg.astype(np.float32) / 255.0, (0, 0), 1.2)


def main(path):
    im = ImageOps.exif_transpose(Image.open(path)).convert("RGB")
    if max(im.size) > 1200:
        im.thumbnail((1200, 1200), Image.LANCZOS)
    rgb = np.asarray(im)

    try:
        alpha = cutout_rembg(rgb)
        print("background removed with rembg")
    except Exception as exc:  # rembg missing or model download blocked
        print(f"rembg unavailable ({exc.__class__.__name__}); using GrabCut")
        alpha = cutout_grabcut(rgb)

    gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
    # neutralise the background first, or CLAHE "equalises" dark hair against dark foliage
    fill = int(np.median(gray[alpha > 0.5]))
    gray = np.where(alpha > 0.5, gray, fill).astype(np.uint8)
    gray = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(6, 6)).apply(gray)

    # crop to the subject with a little breathing room
    ys, xs = np.where(alpha > 0.5)
    pad = int(0.03 * max(gray.shape))
    y0, y1 = max(ys.min() - pad, 0), min(ys.max() + pad, gray.shape[0])
    x0, x1 = max(xs.min() - pad, 0), min(xs.max() + pad, gray.shape[1])
    gray, alpha = gray[y0:y1, x0:x1], alpha[y0:y1, x0:x1]

    la = np.dstack([gray, (alpha * 255).astype(np.uint8)])
    OUT.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(la, "LA").save(OUT)
    print(f"wrote {OUT.relative_to(ROOT)} ({la.shape[1]}x{la.shape[0]})")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else ROOT / "assets" / "source-photo.jpg")
