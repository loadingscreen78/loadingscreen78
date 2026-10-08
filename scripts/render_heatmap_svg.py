#!/usr/bin/env python3
"""data/contributions.json -> assets/contrib-heatmap.svg  (STATIC=1 for a frozen frame).

53-week x 7-day grid of rounded boxes that slide in diagonally once, then freeze.
"""
import datetime as dt
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "data" / "contributions.json"
OUT = ROOT / "assets" / "contrib-heatmap.svg"
STATIC = os.environ.get("STATIC") == "1"

PALETTE = ["#161b22", "#0b3048", "#0f527a", "#1a7fb4", "#36bcf7", "#a6e9ff"]  # none -> neon top end
W, H = 840, 222
BAR, CELL, GAP = 30, 11, 3
STEP = CELL + GAP
BG, BORDER, BARBG = "#0d1117", "#30363d", "#161b22"
INK, DIM, ACCENT = "#c9d1d9", "#8b949e", "#36bcf7"
FONT = "ui-monospace,SFMono-Regular,Menlo,Consolas,'Liberation Mono','DejaVu Sans Mono',monospace"

CSS = """
.c{opacity:0;animation:drop .5s cubic-bezier(.2,.7,.2,1) forwards}
.f{opacity:0;animation:fade .6s ease-out forwards}
@keyframes drop{from{opacity:0;transform:translateY(-7px)}to{opacity:1;transform:translateY(0)}}
@keyframes fade{to{opacity:1}}
"""


def levels(counts):
    nz = sorted(c for c in counts if c > 0)
    if not nz:
        return [0] * len(counts)
    q = lambda p: nz[min(len(nz) - 1, int(p * (len(nz) - 1)))]
    cuts = [q(0.25), q(0.5), q(0.75), q(0.92)]
    return [0 if c == 0 else 1 + sum(c > t for t in cuts) for c in counts]


def window(title, right):
    dots = "".join(
        f'<circle cx="{18 + i * 16}" cy="15" r="5" fill="{c}"/>'
        for i, c in enumerate(("#ff5f56", "#ffbd2e", "#27c93f"))
    )
    return (
        f'<rect x="0.5" y="0.5" width="{W - 1}" height="{H - 1}" rx="10" fill="{BG}" stroke="{BORDER}"/>'
        f'<path d="M0.5 {BAR}V10.5a10 10 0 0 1 10-10h{W - 21}a10 10 0 0 1 10 10V{BAR}Z" fill="{BARBG}"/>'
        f'<line x1="0.5" y1="{BAR}" x2="{W - 0.5}" y2="{BAR}" stroke="{BORDER}"/>{dots}'
        f'<text x="{W / 2}" y="19" text-anchor="middle" fill="{DIM}" font-size="11">{title}</text>'
        f'<text x="{W - 16}" y="19" text-anchor="end" fill="{DIM}" font-size="11">{right}</text>'
    )


def fmt_day(iso):
    d = dt.date.fromisoformat(iso)
    return f"{d:%b} {d.day}"


def main():
    data = json.loads(SRC.read_text(encoding="utf-8"))
    days, s = data["days"], data["stats"]
    lv = levels([d["count"] for d in days])
    first = dt.date.fromisoformat(days[0]["date"])
    lead = (first.weekday() + 1) % 7  # Sunday-first rows
    weeks = (lead + len(days) + 6) // 7

    grid_w = weeks * STEP - GAP
    x0 = (W - (grid_w + 30)) / 2 + 30
    y0 = BAR + 34
    parts, months, last_col = [], [], -9
    for i, (d, l) in enumerate(zip(days, lv)):
        col, row = divmod(lead + i, 7)
        date = dt.date.fromisoformat(d["date"])
        if date.day <= 7 and row == 0 or i == 0:
            if col - last_col >= 3:
                months.append(f'<text x="{x0 + col * STEP:.1f}" y="{y0 - 8}">{date:%b}</text>')
                last_col = col
        anim = "" if STATIC else f' class="c" style="animation-delay:{0.15 + col * 0.017 + row * 0.035:.3f}s"'
        tip = f'{d["count"]} contribution{"s" if d["count"] != 1 else ""} on {d["date"]}'
        parts.append(
            f'<rect x="{x0 + col * STEP:.1f}" y="{y0 + row * STEP}" width="{CELL}" height="{CELL}" rx="2.5" '
            f'fill="{PALETTE[l]}"{anim}><title>{tip}</title></rect>'
        )
    labels = "".join(
        f'<text x="{x0 - 8:.1f}" y="{y0 + r * STEP + 9}" text-anchor="end">{name}</text>'
        for r, name in ((1, "Mon"), (3, "Wed"), (5, "Fri"))
    )

    fy = y0 + 7 * STEP + 22
    fade = "" if STATIC else ' class="f" style="animation-delay:1.35s"'
    legend_x = x0 + grid_w - (len(PALETTE) * 14 + 34)
    legend = "".join(
        f'<rect x="{legend_x + 34 + i * 14:.1f}" y="{fy - 10}" width="{CELL}" height="{CELL}" rx="2.5" fill="{c}"/>'
        for i, c in enumerate(PALETTE)
    )
    bm = dt.date.fromisoformat(s["busiest_month"]["month"] + "-01")
    facts = [f'best day {s["best_day"]["count"]} on {fmt_day(s["best_day"]["date"])}',
             f'busiest month {bm:%b %Y}']
    if s["longest_streak"] > 1:
        facts.append(f'longest streak {s["longest_streak"]} days')
    if s["current_streak"] > 0:
        facts.append(f'current streak {s["current_streak"]} day{"s" if s["current_streak"] != 1 else ""}')
    footer = (
        f'<g{fade}>'
        f'<text x="{x0:.1f}" y="{fy}" fill="{INK}" font-size="13" font-weight="700">'
        f'<tspan fill="{ACCENT}">{s["total"]:,}</tspan> contributions in the last year</text>'
        f'<text x="{x0:.1f}" y="{fy + 20}" fill="{DIM}" font-size="11">{"  ·  ".join(facts)}</text>'
        f'<text x="{legend_x:.1f}" y="{fy}" fill="{DIM}" font-size="10">Less</text>{legend}'
        f'<text x="{legend_x + 34 + len(PALETTE) * 14 + 2:.1f}" y="{fy}" fill="{DIM}" font-size="10">More</text>'
        f"</g>"
    )
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" font-family="{FONT}">'
        f"<title>{data['user']} contribution graph</title>"
        f"{'' if STATIC else f'<style>{CSS}</style>'}"
        f'{window("contributions.sh — last 12 months", "@" + data["user"])}'
        f'<g fill="{DIM}" font-size="10">{"".join(months)}{labels}</g>'
        f'{"".join(parts)}{footer}</svg>'
    )
    OUT.write_text(svg, encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)} ({weeks} weeks, {len(svg) // 1024} KB)")


if __name__ == "__main__":
    main()
