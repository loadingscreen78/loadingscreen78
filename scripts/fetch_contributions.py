#!/usr/bin/env python3
"""Fetch your public contribution calendar (no token) -> data/contributions.json

GitHub serves the calendar as public HTML at https://github.com/users/<user>/contributions,
the same fragment the profile page uses. We parse the day cells + their tooltips and
derive a few stats. On any failure we exit non-zero and leave the old data untouched.
"""
import datetime as dt
import json
import os
import re
import sys
from collections import defaultdict
from pathlib import Path

import requests
from bs4 import BeautifulSoup

USERNAME = os.environ.get("GH_USERNAME", "loadingscreen78")
ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "contributions.json"
COUNT_RE = re.compile(r"^\s*(No|[\d,]+)\s+contributions?\b", re.I)


def fetch_html(user):
    resp = requests.get(
        f"https://github.com/users/{user}/contributions",
        headers={"User-Agent": "Mozilla/5.0 (profile-art; +https://github.com/%s)" % user,
                 "X-Requested-With": "XMLHttpRequest"},
        timeout=30,
    )
    resp.raise_for_status()
    return resp.text


def parse(html):
    soup = BeautifulSoup(html, "html.parser")
    tips = {t["for"]: t.get_text(" ", strip=True) for t in soup.find_all("tool-tip") if t.get("for")}
    days = []
    for td in soup.select("td.ContributionCalendar-day[data-date]"):
        text = tips.get(td.get("id"), "") or td.get_text(" ", strip=True)
        m = COUNT_RE.match(text)
        if m:
            count = 0 if m.group(1).lower() == "no" else int(m.group(1).replace(",", ""))
        elif td.get("data-count", "").isdigit():
            count = int(td["data-count"])
        else:
            raise ValueError(f"could not read a count for {td['data-date']!r}: {text!r}")
        days.append({"date": td["data-date"], "count": count, "level": int(td.get("data-level") or 0)})
    if not days:
        raise ValueError("no contribution cells found - GitHub's markup may have changed")
    days.sort(key=lambda d: d["date"])

    total = None
    head = soup.find(id="js-contribution-activity-description") or soup.find(
        string=re.compile(r"contributions?\s+in the last year", re.I))
    if head is not None:
        m = re.search(r"([\d,]+)\s+contributions?", head.get_text(" ") if hasattr(head, "get_text") else str(head))
        total = int(m.group(1).replace(",", "")) if m else None
    return days, total


def stats(days, total=None):
    dates = [dt.date.fromisoformat(d["date"]) for d in days]
    counts = [d["count"] for d in days]

    longest, run, run_start, best_span = 0, 0, None, (None, None)
    for day, c in zip(dates, counts):
        if c > 0:
            run_start = day if run == 0 else run_start
            run += 1
            if run > longest:
                longest, best_span = run, (run_start, day)
        else:
            run = 0

    current, i = 0, len(counts) - 1
    if i >= 0 and counts[i] == 0:  # today not done yet: the streak can still be alive
        i -= 1
    while i >= 0 and counts[i] > 0:
        current, i = current + 1, i - 1

    months = defaultdict(int)
    for d in days:
        months[d["date"][:7]] += d["count"]
    best = max(days, key=lambda d: d["count"])
    busiest = max(months.items(), key=lambda kv: kv[1])
    return {
        "total": total if total is not None else sum(counts),
        "active_days": sum(c > 0 for c in counts),
        "current_streak": current,
        "longest_streak": longest,
        "longest_streak_span": [s.isoformat() if s else None for s in best_span],
        "best_day": {"date": best["date"], "count": best["count"]},
        "busiest_month": {"month": busiest[0], "count": busiest[1]},
        "monthly": dict(sorted(months.items())),
    }


def build_payload(user, days, total=None):
    return {
        "user": user,
        "generated_at": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat(),
        "range": [days[0]["date"], days[-1]["date"]],
        "stats": stats(days, total),
        "days": days,
    }


def main():
    try:
        days, total = parse(fetch_html(USERNAME))
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)
    payload = build_payload(USERNAME, days, total)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=1) + "\n", encoding="utf-8")
    s = payload["stats"]
    print(f"{USERNAME}: {s['total']} contributions, {s['active_days']} active days, "
          f"longest streak {s['longest_streak']}, current {s['current_streak']}")


if __name__ == "__main__":
    main()
