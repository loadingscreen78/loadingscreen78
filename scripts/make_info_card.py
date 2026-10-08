#!/usr/bin/env python3
"""Neofetch-style info card -> assets/info-card.svg  (STATIC=1 for a frozen frame).

Edit ROWS below when your story changes; the contribution graph already covers the numbers.
"""
import os
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "assets" / "info-card.svg"
STATIC = os.environ.get("STATIC") == "1"

USER, HOST = "jagannath", "loadingscreen78"
ROWS = [
    ("OS", "Engineering Student"),
    ("Role", "AI/ML Practitioner · Deep Learning"),
    ("Now", "building Safend"),
    ("Learning", "Machine Learning"),
    ("ML", "PyTorch · TensorFlow · Keras · scikit-learn"),
    ("Data", "Pandas · NumPy · Matplotlib"),
    ("Langs", "Python · C · C++ · Java · Go · TypeScript"),
    ("Web", "React · FastAPI · Flask · Express · Streamlit"),
    ("DB", "MySQL · MariaDB · DynamoDB"),
    ("Tools", "Jenkins · Unreal Engine · Canva"),
    ("Pinned", "Disease-Prediction-based-on-Symptoms"),
    ("Badges", "Pull Shark · YOLO · Quickdraw"),
    ("Fun fact", "all AI can code, but all humans can't"),
    ("Contact", "jagannathmishra540@gmail.com"),
]

W, H = 490, 430
BAR, X, KEYW, LINE = 30, 22, 92, 21.5
BG, BORDER, BARBG = "#0d1117", "#30363d", "#161b22"
INK, DIM, ACCENT = "#c9d1d9", "#8b949e", "#36bcf7"
FONT = "ui-monospace,SFMono-Regular,Menlo,Consolas,'Liberation Mono','DejaVu Sans Mono',monospace"
BLOCKS = ["#484f58", "#ff7b72", "#3fb950", "#d29922", "#58a6ff", "#bc8cff", "#36bcf7", "#c9d1d9"]

CSS = """
.l{opacity:0;animation:in .45s cubic-bezier(.2,.7,.2,1) forwards}
@keyframes in{from{opacity:0;transform:translateX(-8px)}to{opacity:1;transform:translateX(0)}}
"""


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
    lines, n = [], 0

    def add(inner, y):
        nonlocal n
        attrs = "" if STATIC else f' class="l" style="animation-delay:{0.3 + n * 0.11:.2f}s"'
        lines.append(f"<g{attrs}>{inner.format(y=y)}</g>")
        n += 1

    y = BAR + 32
    add(
        f'<text x="{X}" y="{{y}}" font-size="15" font-weight="700">'
        f'<tspan fill="{ACCENT}">{USER}</tspan><tspan fill="{INK}">@</tspan>'
        f'<tspan fill="{ACCENT}">{HOST}</tspan></text>',
        y,
    )
    y += 12
    add(f'<line x1="{X}" y1="{{y}}" x2="{X + 236}" y2="{{y}}" stroke="{BORDER}" stroke-dasharray="5 3"/>', y)
    y += 24
    for key, value in ROWS:
        add(
            f'<text x="{X}" y="{{y}}" font-size="12.5"><tspan fill="{ACCENT}" font-weight="700">{escape(key)}</tspan>'
            f'<tspan x="{X + KEYW}" fill="{INK}">{escape(value)}</tspan></text>',
            y,
        )
        y += LINE
    y += 4
    blocks = "".join(
        f'<rect x="{X + i * 26}" y="{{y}}" width="22" height="13" rx="2" fill="{c}"/>' for i, c in enumerate(BLOCKS)
    )
    add(blocks, y)

    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" font-family="{FONT}">'
        f"<title>neofetch-style card for {USER}@{HOST}</title>"
        f"{'' if STATIC else f'<style>{CSS}</style>'}{window('neofetch')}{''.join(lines)}</svg>"
    )
    OUT.write_text(svg, encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)} ({len(svg) // 1024} KB)")


if __name__ == "__main__":
    main()
