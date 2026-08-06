#!/usr/bin/env python3
"""Build ASU's GitHub stats card from the API, instead of borrowing one.

The public github-readme-stats instance is regularly rate limited into 503s,
which leaves a broken image sitting in the profile. This asks GitHub for the
numbers directly and renders them with the same palette as the banner, so the
card is ours: never down, always on theme.

Needs a token, because contribution counts are only exposed over GraphQL:

    GitHub Actions   secrets.GITHUB_TOKEN is passed in automatically
    locally          GITHUB_TOKEN=ghp_xxx python scripts/generate_stats.py

Out:  assets/stats/dark.svg
      assets/stats/light.svg
"""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from theme import PAL, FONT, esc, reveal, gradient_defs, window_chrome  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "assets" / "stats"

LOGIN = os.environ.get("GH_LOGIN", "asuzey")
API = "https://api.github.com/graphql"

W, H = 920, 344
PANEL = (26, 26, W - 52, H - 52)
TOP_LANGS = 6

QUERY = """
query($login: String!) {
  user(login: $login) {
    followers { totalCount }
    repositories(first: 100, ownerAffiliations: OWNER, isFork: false,
                 orderBy: {field: STARGAZERS, direction: DESC}) {
      totalCount
      nodes {
        stargazerCount
        languages(first: 10, orderBy: {field: SIZE, direction: DESC}) {
          edges { size node { name color } }
        }
      }
    }
    contributionsCollection {
      totalCommitContributions
      totalPullRequestContributions
      totalIssueContributions
      restrictedContributionsCount
      contributionCalendar {
        totalContributions
        weeks { contributionDays { date contributionCount } }
      }
    }
  }
}
"""


# -------------------------------------------------------------------- data ---

def fetch() -> dict:
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        raise SystemExit(
            "GITHUB_TOKEN is not set. GitHub only exposes contribution counts "
            "over the authenticated GraphQL API.\n"
            "  locally:  GITHUB_TOKEN=<a token with public access> "
            "python scripts/generate_stats.py"
        )

    body = json.dumps({"query": QUERY, "variables": {"login": LOGIN}}).encode()
    request = urllib.request.Request(API, data=body, method="POST", headers={
        "Authorization": f"bearer {token}",
        "Content-Type": "application/json",
        "User-Agent": f"{LOGIN}-profile-card",
    })
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            payload = json.load(response)
    except urllib.error.HTTPError as err:
        raise SystemExit(f"GitHub API returned {err.code}: {err.read()[:300]!r}")

    if "errors" in payload:
        raise SystemExit(f"GitHub API error: {payload['errors']}")
    return payload["data"]["user"]


def streaks(weeks: list[dict]) -> tuple[int, int]:
    """Current and longest run of consecutive days with at least one contribution."""
    days = [(day["date"], day["contributionCount"])
            for week in weeks for day in week["contributionDays"]]
    days.sort()

    longest = run = 0
    for _, count in days:
        run = run + 1 if count else 0
        longest = max(longest, run)

    # Today may simply not have happened yet, so an empty today does not break
    # a streak -- only an empty yesterday does.
    today = date.today().isoformat()
    yesterday = (date.today() - timedelta(days=1)).isoformat()
    counts = dict(days)
    if counts.get(today, 0) == 0 and counts.get(yesterday, 0) == 0:
        return 0, longest

    current = 0
    for iso, count in reversed(days):
        if iso > today:
            continue
        if count == 0:
            if iso == today:
                continue          # skip an empty today, then stop at the first gap
            break
        current += 1
    return current, longest


def summarise(user: dict) -> dict:
    repos = user["repositories"]["nodes"]
    contrib = user["contributionsCollection"]
    calendar = contrib["contributionCalendar"]

    sizes: dict[str, int] = {}
    colors: dict[str, str] = {}
    for repo in repos:
        for edge in repo["languages"]["edges"]:
            name = edge["node"]["name"]
            sizes[name] = sizes.get(name, 0) + edge["size"]
            if edge["node"]["color"]:
                colors[name] = edge["node"]["color"]

    ranked = sorted(sizes.items(), key=lambda kv: kv[1], reverse=True)[:TOP_LANGS]
    total_bytes = sum(size for _, size in ranked) or 1
    languages = [(name, size / total_bytes, colors.get(name)) for name, size in ranked]

    current, longest = streaks(calendar["weeks"])

    return {
        "contributions": calendar["totalContributions"]
                         + contrib["restrictedContributionsCount"],
        "commits": contrib["totalCommitContributions"],
        "prs": contrib["totalPullRequestContributions"],
        "issues": contrib["totalIssueContributions"],
        "stars": sum(repo["stargazerCount"] for repo in repos),
        "repos": user["repositories"]["totalCount"],
        "followers": user["followers"]["totalCount"],
        "current_streak": current,
        "longest_streak": longest,
        "languages": languages,
    }


# ------------------------------------------------------------------ render ---

def defs(p: dict, mode: str) -> str:
    x, y, w, h = PANEL
    return ('<defs>' + gradient_defs(p, mode) +
            f'<clipPath id="panelClip"><rect x="{x}" y="{y}" width="{w}" '
            f'height="{h}" rx="18"/></clipPath></defs>')


def background(p: dict) -> str:
    return "".join([
        f'<rect width="{W}" height="{H}" rx="24" fill="{p["bg"]}"/>',
        f'<rect width="{W}" height="{H}" rx="24" fill="url(#dots)"/>',
        '<circle cx="200" cy="120" r="260" fill="url(#glowB)">'
        '<animateTransform attributeName="transform" type="translate" '
        'values="0 0;28 20;0 0" dur="16s" repeatCount="indefinite"/></circle>',
        '<circle cx="760" cy="300" r="280" fill="url(#glowA)">'
        '<animateTransform attributeName="transform" type="translate" '
        'values="0 0;-24 -16;0 0" dur="19s" repeatCount="indefinite"/></circle>',
        f'<rect x="1.5" y="1.5" width="{W-3}" height="{H-3}" rx="23" fill="none" '
        f'stroke="{p["border"]}" stroke-width="1.5"/>',
        f'<rect x="1.5" y="1.5" width="{W-3}" height="{H-3}" rx="23" fill="none" '
        f'stroke="url(#shimmer)" stroke-width="1.5" opacity=".75"/>',
    ])


def num(value: int | str) -> str:
    """Group thousands, but let the placeholder card's dashes through untouched."""
    return f"{value:,}" if isinstance(value, int) else str(value)


def tiles(p: dict, data: dict) -> str:
    cells = [
        ("contributions", num(data["contributions"]), "past year"),
        ("current streak", num(data["current_streak"]), "days in a row"),
        ("longest streak", num(data["longest_streak"]), "days"),
        ("commits", num(data["commits"]), "past year"),
        ("stars earned", num(data["stars"]), f"across {num(data['repos'])} repos"),
        ("followers", num(data["followers"]), "people"),
    ]
    s = []
    for i, (label, value, note) in enumerate(cells):
        x = 62 + (i % 3) * 146
        y = 112 + (i // 3) * 108
        begin = 0.4 + i * 0.12
        s.append(reveal(f'<text x="{x}" y="{y - 26}" font-size="11" letter-spacing="1.4" '
                        f'fill="{p["dim"]}">{esc(label.upper())}</text>', begin))
        s.append(reveal(f'<text x="{x}" y="{y + 12}" font-size="32" font-weight="700" '
                        f'fill="url(#acc)">{esc(value)}</text>', begin + 0.1))
        s.append(reveal(f'<text x="{x}" y="{y + 34}" font-size="11" '
                        f'fill="{p["muted"]}">{esc(note)}</text>', begin + 0.18))
    return "".join(s)


def languages(p: dict, data: dict) -> str:
    left, bar_w = 520, 342
    s = [reveal(f'<text x="{left}" y="86" font-size="11" letter-spacing="1.4" '
                f'fill="{p["dim"]}">TOP LANGUAGES</text>', 0.4)]

    # One stacked bar, each slice widening into place once on load.
    offset = 0.0
    for i, (name, share, color) in enumerate(data["languages"]):
        width = share * bar_w
        fill = color or (p["g1"], p["g2"], p["g3"])[i % 3]
        radius = ' rx="5"' if i == 0 or i == len(data["languages"]) - 1 else ""
        s.append(
            f'<rect x="{left + offset:.1f}" y="98" width="0" height="10"{radius} '
            f'fill="{fill}"><animate attributeName="width" values="0;{width:.1f}" '
            f'dur=".7s" begin="{0.7 + i * 0.09:.2f}s" fill="freeze" '
            f'calcMode="spline" keyTimes="0;1" keySplines="0.3 0 0.2 1"/></rect>'
        )
        offset += width

    y = 142
    for i, (name, share, color) in enumerate(data["languages"]):
        fill = color or (p["g1"], p["g2"], p["g3"])[i % 3]
        begin = 1.0 + i * 0.1
        s.append(reveal(
            f'<text x="{left + 16}" y="{y + 4}" font-size="13" fill="{p["text"]}">'
            f'{esc(name)}</text>', begin))
        if not data.get("placeholder"):
            s.append(reveal(
                f'<text x="{left + bar_w}" y="{y + 4}" font-size="13" text-anchor="end" '
                f'fill="{p["muted"]}">{share * 100:.1f}%</text>', begin))
        s.append(
            f'<circle cx="{left + 4}" cy="{y}" r="4" fill="{fill}" opacity="0">'
            f'<animate attributeName="opacity" values="0;1" dur=".4s" '
            f'begin="{begin}s" fill="freeze"/></circle>'
        )
        y += 26
    return "".join(s)


def build(mode: str, data: dict) -> str:
    p = PAL[mode]
    x, y, w, h = PANEL
    stamp = date.today().isoformat()
    return "".join([
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="100%" '
        f'role="img" aria-label="GitHub statistics for {LOGIN}" font-family="{FONT}">',
        defs(p, mode),
        background(p),
        window_chrome(p, x, y, w, h, f"asu@webcore: ~/stats"),
        f'<line x1="494" y1="72" x2="494" y2="{y + h - 26}" stroke="{p["border"]}" '
        f'stroke-width="1"/>',
        tiles(p, data),
        languages(p, data),
        f'<text x="{x + w - 22}" y="{y + h - 16}" font-size="10" text-anchor="end" '
        f'fill="{p["dim"]}">updated {stamp}</text>',
        f'<g clip-path="url(#panelClip)"><rect x="{x}" y="{y}" width="{w}" height="20" '
        f'fill="{p["scan"]}"><animateTransform attributeName="transform" '
        f'type="translate" values="0 -40;0 {h + 10};0 -40" dur="12s" '
        f'repeatCount="indefinite"/></rect></g>',
        '</svg>',
    ])


def placeholder() -> dict:
    """A card with no numbers in it yet.

    Committed once so the README never points at a missing file; the scheduled
    job overwrites it with real figures on its first run.
    """
    return {
        "contributions": "-", "commits": "-", "stars": "-", "repos": "-",
        "followers": "-", "current_streak": "-", "longest_streak": "-",
        "prs": "-", "issues": "-", "placeholder": True,
        "languages": [("waiting for the first run", 1.0, None)],
    }


def main() -> None:
    if "--placeholder" in sys.argv:
        data = placeholder()
        print("rendering the placeholder card (no API call)")
    else:
        data = summarise(fetch())

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for mode in ("dark", "light"):
        target = OUT_DIR / f"{mode}.svg"
        target.write_text(build(mode, data), encoding="utf-8")
        print(f"wrote {target.relative_to(ROOT)} ({target.stat().st_size / 1024:.1f} KB)")
    print(f"  {data['contributions']} contributions, {data['current_streak']}d streak, "
          f"{data['stars']} stars, {len(data['languages'])} languages")


if __name__ == "__main__":
    main()
