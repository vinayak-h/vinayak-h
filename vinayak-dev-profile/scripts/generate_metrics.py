#!/usr/bin/env python3
"""Generate a compact SVG using the GitHub public REST API."""
import json, os, urllib.request
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from xml.sax.saxutils import escape

USER = "vinayak-h"
OUT = Path("assets/github-metrics.svg")

def get_json(url):
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "vinayak-profile-metrics",
    }
    token = os.getenv("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=20) as response:
        return json.load(response)

def label(x, y, value, size=13, fill="#A1A1AA", weight="400"):
    return (f'<text x="{x}" y="{y}" fill="{fill}" font-size="{size}" '
            f'font-weight="{weight}" font-family="Inter,Segoe UI,Arial,sans-serif">'
            f'{escape(str(value))}</text>')

def main():
    user = get_json(f"https://api.github.com/users/{USER}")
    repos, page = [], 1
    while page <= 10:
        batch = get_json(f"https://api.github.com/users/{USER}/repos?type=owner&sort=updated&per_page=100&page={page}")
        if not batch:
            break
        repos.extend(r for r in batch if not r.get("fork", False))
        if len(batch) < 100:
            break
        page += 1
    stars = sum(int(r.get("stargazers_count", 0)) for r in repos)
    forks = sum(int(r.get("forks_count", 0)) for r in repos)
    langs = Counter(r["language"] for r in repos if r.get("language"))
    top = ", ".join(f"{name} ({count})" for name, count in langs.most_common(4)) or "No language metadata yet"
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    parts = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="1000" height="190" viewBox="0 0 1000 190">',
        '<rect width="100%" height="100%" rx="12" fill="#0B0B0C" stroke="#303036"/>',
        label(28, 34, "PUBLIC GITHUB SNAPSHOT", 12, "#A1A1AA", "600")
    ]
    values = [
        ("PUBLIC REPOSITORIES", user.get("public_repos", 0)),
        ("FOLLOWERS", user.get("followers", 0)),
        ("STARS EARNED", stars),
        ("FORKS", forks)
    ]
    for x, (title, value) in zip([28, 275, 522, 769], values):
        parts += [label(x, 88, value, 30, "#F4F4F5", "650"), label(x, 111, title, 10, "#A1A1AA", "600")]
    parts += [
        '<line x1="28" y1="132" x2="972" y2="132" stroke="#303036"/>',
        label(28, 157, "LANGUAGES BY REPOSITORY METADATA", 10, "#A1A1AA", "600"),
        label(28, 179, top, 13, "#D4D4D8"),
        label(972, 179, f"Updated {stamp}", 10, "#71717A"),
        "</svg>"
    ]
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(parts), encoding="utf-8")
    print(f"Wrote {OUT}; scanned {len(repos)} non-fork repositories.")

if __name__ == "__main__":
    main()
