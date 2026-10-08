#!/usr/bin/env python3
"""Turn assets/source-prepped.png into a self-typing, one-color ASCII portrait.

    python scripts/make_ascii_svg.py          # animated -> assets/ascii-portrait.svg
    STATIC=1 python scripts/make_ascii_svg.py # frozen frame for previews

Each row is revealed by a left-to-right clip wipe with a block cursor riding the
edge, staggered top to bottom. It prints once and freezes (SMIL, so GitHub plays it).
"""
import os
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "assets" / "source-prepped.png"
OUT = ROOT / "assets" / "ascii-portrait.svg"
STATIC = os.environ.get("STATIC") == "1"

RAMP = " .`:-=+*cs#%@"  # sparse -> dense; the space is reserved for the background
COLS = 92
FRAME_W = 0.64          # head & shoulders framing: crop width as a share of the cut-out
W, H = 350, 430          # same height as the info card so the two panes line up
BAR, PAD = 30, 15
BG, BORDER, BARBG = "#0d1117", "#30363d", "#161b22"
INK, DIM, ACCENT = "#c9d1d9", "#8b949e", "#36bcf7"
FONT = "ui-monospace,SFMono-Regular,Menlo,Consolas,'Liberation Mono','DejaVu Sans Mono',monospace"


def to_rows():
    la = np.asarray(Image.open(SRC).convert("LA"), dtype=np.float32) / 255.0
    # frame head & shoulders: centre on the head, crop to the pane's aspect ratio
    h, w = la.shape[:2]
    ys, xs = np.where(la[: int(h * 0.25), :, 1] > 0.5)
    cx = int(np.median(xs)) if xs.size else w // 2
    fw = int(w * FRAME_W)
    x0 = min(max(cx - fw // 2, 0), w - fw)
    fh = min(h, int(fw * (H - BAR - 2 * PAD) / (W - 2 * PAD)))
    la = la[:fh, x0:x0 + fw]
    gray, alpha = la[..., 0], la[..., 1]
    h, w = gray.shape
    cw = (W - 2 * PAD) / COLS
    lh = cw * 2.0
    rows = min(round(COLS * (h / w) * (cw / lh)), int((H - BAR - 2 * PAD) / lh))

    def shrink(a, resample):
        img = Image.fromarray((a * 255).astype(np.uint8))
        return np.asarray(img.resize((COLS, rows), resample), np.float32) / 255.0

    g, m = shrink(gray, Image.LANCZOS), shrink(alpha, Image.BILINEAR)
    inside = m >= 0.5
    lo, hi = np.percentile(g[inside], [2, 98])
    g = np.clip((g - lo) / max(hi - lo, 1e-6), 0, 1) ** 0.9
    # positive image on a dark pane: bright -> dense glyph, subject never drops to blank
    idx = np.where(inside, 1 + np.rint(g * (len(RAMP) - 2)).astype(int), 0)
    # non-breaking spaces: renderers may collapse plain spaces and misalign the rows
    return ["".join(RAMP[i] for i in row).replace(" ", "\u00a0") for row in idx], cw, lh


def window(title):
    dots = "".join(
        f'<circle cx="{18 + i * 16}" cy="15" r="5" fill="{c}"/>'
        for i, c in enumerate(("#ff5f56", "#ffbd2e", "#27c93f"))
    )
    return (
        f'<rect x="0.5" y="0.5" width="{W - 1}" height="{H - 1}" rx="10" fill="{BG}" stroke="{BORDER}"/>'
        f'<path d="M0.5 {BAR}V10.5a10 10 0 0 1 10-10h{W - 21}a10 10 0 0 1 10 10V{BAR}Z" fill="{BARBG}"/>'
        f'<line x1="0.5" y1="{BAR}" x2="{W - 0.5}" y2="{BAR}" stroke="{BORDER}"/>{dots}'
        f'<text x="{W / 2}" y="19" text-anchor="middle" fill="{DIM}" font-size="11">{title}</text>'
    )


def main():
    rows, cw, lh = to_rows()
    fs = cw / 0.6
    width = COLS * cw
    y0 = BAR + (H - BAR - len(rows) * lh) / 2
    defs, body = [], []
    t, step, dur = 0.35, 0.05, 0.45
    for i, line in enumerate(rows):
        if not line.replace("\u00a0", "").strip():
            continue
        top = y0 + i * lh
        text = (
            f'<text x="{PAD}" y="{top + lh * 0.78:.2f}" textLength="{width:.2f}" '
            f'lengthAdjust="spacingAndGlyphs"{{clip}}>{line}</text>'
        )
        if STATIC:
            body.append(text.format(clip=""))
            continue
        begin = t + i * step
        defs.append(
            f'<clipPath id="r{i}"><rect x="{PAD}" y="{top:.2f}" width="0" height="{lh + 0.5:.2f}">'
            f'<animate attributeName="width" from="0" to="{width:.2f}" begin="{begin:.2f}s" '
            f'dur="{dur}s" fill="freeze"/></rect></clipPath>'
        )
        body.append(text.format(clip=f' clip-path="url(#r{i})"'))
        body.append(
            f'<rect x="{PAD}" y="{top + 0.6:.2f}" width="{cw:.2f}" height="{lh - 1.2:.2f}" fill="{ACCENT}" opacity="0">'
            f'<animate attributeName="x" from="{PAD}" to="{PAD + width:.2f}" begin="{begin:.2f}s" dur="{dur}s" fill="freeze"/>'
            f'<set attributeName="opacity" to="0.9" begin="{begin:.2f}s"/>'
            f'<set attributeName="opacity" to="0" begin="{begin + dur:.2f}s"/></rect>'
        )
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
        f'xml:space="preserve" font-family="{FONT}">'
        f"<title>ASCII portrait of Jagannath Mishra</title>"
        f'<defs>{"".join(defs)}</defs>{window("~/portrait.txt")}'
        f'<g fill="{INK}" font-size="{fs:.2f}">{"".join(body)}</g></svg>'
    )
    OUT.write_text(svg, encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)} ({COLS}x{len(rows)} chars, {len(svg) // 1024} KB)")


if __name__ == "__main__":
    main()
