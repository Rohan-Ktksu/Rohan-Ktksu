#!/usr/bin/env python3
"""Refresh the profile's public GitHub activity card using GitHub Search API.

The counts represent public, searchable items and are *not* the same as GitHub's
contribution calendar, which has different attribution and visibility rules.
"""
import html
import json
import os
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

OWNER = os.getenv("GITHUB_REPOSITORY_OWNER", "Rohan-Ktksu")
TOKEN = os.getenv("GH_TOKEN")
DESTINATION = Path("assets/github-activity.svg")


def count(kind: str, query: str) -> int:
    url = "https://api.github.com/search/" + kind + "?" + urlencode(
        {"q": query, "per_page": 1}
    )
    headers = {
        "User-Agent": "profile-readme-activity-tracker",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if TOKEN:
        headers["Authorization"] = "Bearer " + TOKEN
    with urlopen(Request(url, headers=headers), timeout=30) as response:
        payload = json.load(response)
    if payload.get("incomplete_results"):
        raise RuntimeError(f"GitHub reports incomplete results for {query}")
    value = payload.get("total_count")
    if not isinstance(value, int):
        raise RuntimeError(f"Missing count for {query}")
    return value


def build_svg(commits: int, prs: int, issues: int) -> str:
    items = [
        ("PUBLIC COMMITS", commits, "#A9BCEB"),
        ("PULL REQUESTS", prs, "#8FCFC6"),
        ("ISSUES OPENED", issues, "#D3AFDF"),
    ]
    parts = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="900" height="152" '
        'viewBox="0 0 900 152" role="img" '
        f'aria-label="{commits} public commits, {prs} pull requests, {issues} issues opened">',
        '<rect width="900" height="152" rx="16" fill="#0D1117"/>',
    ]
    for index, (label, value, accent) in enumerate(items):
        x = 7 + index * 300
        parts += [
            f'<rect x="{x}" y="7" width="286" height="138" rx="14" '
            'fill="#151E2B" stroke="#344459"/>',
            f'<rect x="{x + 20}" y="26" width="4" height="27" rx="2" fill="{accent}"/>',
            f'<text x="{x + 35}" y="46" fill="#BACADB" font-size="15" '
            'font-family="Arial,sans-serif" font-weight="700" letter-spacing="1">'
            f'{html.escape(label)}</text>',
            f'<text x="{x + 20}" y="112" fill="{accent}" font-size="44" '
            f'font-family="Arial,sans-serif" font-weight="700">{value:,}</text>',
        ]
    parts.append("</svg>")
    return "\n".join(parts) + "\n"


def main() -> None:
    # A search failure exits before changing the old, valid card.
    try:
        commits = count("commits", f"author:{OWNER}")
        prs = count("issues", f"is:pr author:{OWNER}")
        issues = count("issues", f"is:issue author:{OWNER}")
    except (HTTPError, URLError, OSError, RuntimeError, ValueError) as exc:
        raise SystemExit(f"Activity refresh failed (old card unchanged): {exc}")
    svg = build_svg(commits, prs, issues)
    if not DESTINATION.exists() or DESTINATION.read_text(encoding="utf-8") != svg:
        DESTINATION.parent.mkdir(parents=True, exist_ok=True)
        DESTINATION.write_text(svg, encoding="utf-8")
    print(f"Public activity: {commits:,} commits; {prs:,} PRs; {issues:,} issues")


if __name__ == "__main__":
    main()
