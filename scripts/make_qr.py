#!/usr/bin/env python3
"""Portfolio QR code, two ways (run once, or when the URL changes):

    python scripts/make_qr.py
      -> assets/portfolio-qr.svg   animated terminal card for the README (STATIC=1 to freeze)
      -> assets/portfolio-qr.png   print-ready 1640px QR for your resume / ID card / slides

Error correction H (30%) leaves room for the >_ logo in the middle. Both outputs are
decoded with OpenCV before saving, so a broken code never gets written.
"""
import os
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw

URL = os.environ.get("PORTFOLIO_URL", "https://jsm-portfolio-jsm.surge.sh")
NAME, ROLE = "Jagannath Mishra", "AI/ML Practitioner"
ROOT = Path(__file__).resolve().parent.parent
SVG_OUT = ROOT / "assets" / "portfolio-qr.svg"
PNG_OUT = ROOT / "assets" / "portfolio-qr.png"
STATIC = os.environ.get("STATIC") == "1"

INKQ, EYE, PAPER, ACCENT = "#0d1117", "#0b7fc0", "#f6f8fa", "#36bcf7"
BG, BORDER, BARBG, INK, DIM, GREEN = "#0d1117", "#30363d", "#161b22", "#c9d1d9", "#8b949e", "#3fb950"
FONT = "ui-monospace,SFMono-Regular,Menlo,Consolas,'Liberation Mono','DejaVu Sans Mono',monospace"
W, H, BAR = 840, 290, 30


def qr_matrix(url):
    params = cv2.QRCodeEncoder_Params()
    params.correction_level = cv2.QRCodeEncoder_CORRECT_LEVEL_H
    dark = cv2.QRCodeEncoder.create(params).encode(url) < 128
    ys, xs = np.where(dark)
    dark = dark[ys.min(): ys.max() + 1, xs.min(): xs.max() + 1]
    px = int(np.argmin(dark[0])) // 7 or 1  # finder pattern is 7 modules wide
    return dark[::px, ::px]


def zones(n):
    finders = [(0, 0), (0, n - 7), (n - 7, 0)]
    logo = 7 if n >= 29 else 5
    start = (n - logo) // 2
    return finders, (start, logo)


def is_reserved(r, c, n):
    finders, (s, logo) = zones(n)
    in_finder = any(fr <= r < fr + 7 and fc <= c < fc + 7 for fr, fc in finders)
    return in_finder or (s <= r < s + logo and s <= c < s + logo)


def verify(img_gray, label):
    found = {cv2.QRCodeDetector().detectAndDecode(img_gray)[0], cv2.QRCodeDetectorAruco().detectAndDecode(img_gray)[0]}
    text = URL if URL in found else next(iter(found))
    if text != URL:
        raise SystemExit(f"{label}: decoded {text!r}, expected {URL!r} - not saving")
    print(f"{label}: scans OK -> {text}")


# ---------- print PNG ----------
def make_png(m, mod=40, quiet=4):
    n = len(m)
    ss = 2  # supersample for smooth corners
    u = mod * ss
    size = (n + 2 * quiet) * u
    im = Image.new("RGB", (size, size), PAPER)
    d = ImageDraw.Draw(im)
    o = quiet * u
    for r in range(n):
        for c in range(n):
            if m[r][c] and not is_reserved(r, c, n):
                x, y = o + c * u, o + r * u
                g = u * 0.04
                d.rounded_rectangle((x + g, y + g, x + u - g - 1, y + u - g - 1), radius=u * 0.25, fill=INKQ)
    finders, (s, logo) = zones(n)
    for fr, fc in finders:
        x, y = o + fc * u, o + fr * u
        d.rounded_rectangle((x, y, x + 7 * u - 1, y + 7 * u - 1), radius=u * 0.5, outline=INKQ, width=u)
        d.rounded_rectangle((x + 2 * u, y + 2 * u, x + 5 * u - 1, y + 5 * u - 1), radius=u * 0.3, fill=EYE)
    x, y = o + s * u, o + s * u
    inset = u * 0.35
    d.rounded_rectangle((x + inset, y + inset, x + logo * u - inset, y + logo * u - inset), radius=u * 1.4, fill=INKQ)
    cx, cy, k = x + logo * u / 2, y + logo * u / 2, u * 0.95
    d.line([(cx - 1.6 * k, cy - 1.1 * k), (cx - 0.4 * k, cy), (cx - 1.6 * k, cy + 1.1 * k)],
           fill=ACCENT, width=int(u * 0.55), joint="curve")
    d.rounded_rectangle((cx + 0.1 * k, cy + 0.85 * k, cx + 1.7 * k, cy + 1.3 * k), radius=u * 0.2, fill=ACCENT)
    im = im.resize((size // ss, size // ss), Image.LANCZOS)
    gray = cv2.cvtColor(np.asarray(im), cv2.COLOR_RGB2GRAY)
    for scale in (1.0, 0.5, 0.25, 0.12):  # also check it survives being printed small
        verify(cv2.resize(gray, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA), f"png @{scale:g}x")
    im.save(PNG_OUT, optimize=True)
    print(f"wrote {PNG_OUT.relative_to(ROOT)} ({im.width}px)")


# ---------- animated README card ----------
def make_svg(m, tile=230, quiet=3):
    n = len(m)
    ms = tile / (n + 2 * quiet)
    tx, ty = 28, BAR + 15
    groups = {}
    for r in range(n):
        for c in range(n):
            if m[r][c] and not is_reserved(r, c, n):
                groups.setdefault(r + c, []).append(
                    f'<rect x="{c + 0.04}" y="{r + 0.04}" width="0.92" height="0.92" rx="0.25"/>')
    anim = (lambda delay, cls="q": "" if STATIC else f' class="{cls}" style="animation-delay:{delay:.2f}s"')
    mods = "".join(f"<g{anim(0.25 + k * 0.016)}>{''.join(v)}</g>" for k, v in sorted(groups.items()))
    finders, (s, logo) = zones(n)
    eyes = "".join(
        f'<rect x="{fc + 0.5}" y="{fr + 0.5}" width="6" height="6" rx="0.2" fill="none" stroke="{INKQ}" stroke-width="1"/>'
        f'<rect x="{fc + 2}" y="{fr + 2}" width="3" height="3" rx="0.3" fill="{EYE}"/>'
        for fr, fc in finders
    )
    cx = cy = s + logo / 2
    logo_svg = (
        f'<rect x="{s + 0.35}" y="{s + 0.35}" width="{logo - 0.7}" height="{logo - 0.7}" rx="1.4" fill="{INKQ}"/>'
        f'<path d="M{cx - 1.52} {cy - 1.05}L{cx - 0.38} {cy}L{cx - 1.52} {cy + 1.05}" fill="none" stroke="{ACCENT}" '
        f'stroke-width="0.55" stroke-linecap="round" stroke-linejoin="round"/>'
        f'<rect x="{cx + 0.1}" y="{cy + 0.8}" width="1.5" height="0.45" rx="0.2" fill="{ACCENT}"/>'
    )
    scan = "" if STATIC else (
        f'<rect x="{tx}" y="{ty}" width="{tile}" height="10" fill="url(#scan)" opacity="0">'
        f'<animate attributeName="y" from="{ty - 10}" to="{ty + tile}" begin="1.45s" dur="1.1s" fill="freeze"/>'
        f'<set attributeName="opacity" to="1" begin="1.45s"/><set attributeName="opacity" to="0" begin="2.55s"/></rect>'
    )
    x = tx + tile + 34
    lines = [
        (82, f'<tspan fill="{GREEN}">jagannath@github</tspan><tspan fill="{DIM}"> ~ $ </tspan>'
             f'<tspan fill="{INK}">open portfolio</tspan>', 12, ""),
        (124, URL.split("://", 1)[1].rstrip("/"), 24, f' fill="{ACCENT}" font-weight="700"'),
        (156, f"{NAME} · {ROLE}", 14, f' fill="{INK}"'),
        (180, "projects · experiments · contact", 12, f' fill="{DIM}"'),
        (226, "&gt; point your phone camera at the code", 12, f' fill="{INK}"'),
        (248, "&gt; or click anywhere on this card", 12, f' fill="{DIM}"'),
    ]
    text = "".join(
        f'<text x="{x}" y="{y}" font-size="{fs}"{attrs}{anim(1.0 + i * 0.16, "t")}>{body}</text>'
        for i, (y, body, fs, attrs) in enumerate(lines)
    )
    dots = "".join(f'<circle cx="{18 + i * 16}" cy="15" r="5" fill="{c}"/>'
                   for i, c in enumerate(("#ff5f56", "#ffbd2e", "#27c93f")))
    css = "" if STATIC else (
        "<style>.q{opacity:0;animation:pop .35s ease-out forwards}"
        ".t{opacity:0;animation:in .45s cubic-bezier(.2,.7,.2,1) forwards}"
        "@keyframes pop{to{opacity:1}}"
        "@keyframes in{from{opacity:0;transform:translateX(-8px)}to{opacity:1;transform:translateX(0)}}</style>"
    )
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" font-family="{FONT}">'
        f"<title>Scan to open {NAME}'s portfolio: {URL}</title>{css}"
        f'<defs><linearGradient id="scan" x1="0" y1="0" x2="0" y2="1">'
        f'<stop offset="0" stop-color="{ACCENT}" stop-opacity="0"/><stop offset=".8" stop-color="{ACCENT}" stop-opacity=".55"/>'
        f'<stop offset="1" stop-color="{ACCENT}" stop-opacity="0"/></linearGradient></defs>'
        f'<rect x="0.5" y="0.5" width="{W - 1}" height="{H - 1}" rx="10" fill="{BG}" stroke="{BORDER}"/>'
        f'<path d="M0.5 {BAR}V10.5a10 10 0 0 1 10-10h{W - 21}a10 10 0 0 1 10 10V{BAR}Z" fill="{BARBG}"/>'
        f'<line x1="0.5" y1="{BAR}" x2="{W - 0.5}" y2="{BAR}" stroke="{BORDER}"/>{dots}'
        f'<text x="{W / 2}" y="19" text-anchor="middle" fill="{DIM}" font-size="11">~/portfolio — qr</text>'
        f'<rect x="{tx}" y="{ty}" width="{tile}" height="{tile}" rx="12" fill="{PAPER}"/>'
        f'<g transform="translate({tx + quiet * ms:.3f} {ty + quiet * ms:.3f}) scale({ms:.4f})">'
        f'<g fill="{INKQ}">{mods}</g><g{anim(0.15)}>{eyes}</g><g{anim(1.2)}>{logo_svg}</g></g>'
        f"{scan}{text}</svg>"
    )
    SVG_OUT.write_text(svg, encoding="utf-8")
    print(f"wrote {SVG_OUT.relative_to(ROOT)} ({len(svg) // 1024} KB)")


if __name__ == "__main__":
    mat = qr_matrix(URL)
    print(f"QR {len(mat)}x{len(mat)} modules, error correction H, url {URL}")
    make_png(mat)
    make_svg(mat)
