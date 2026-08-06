#!/usr/bin/env python3
"""Rewrite the recent-activity list in README.md from GitHub's events feed.

The off-the-shelf action this replaces only knew how to describe issues, pull
requests and releases -- it had no serializer for PushEvent at all, so pushes
and commits could never appear no matter how it was configured.

This walks the public events feed itself, so pushes are first-class, and
consecutive pushes to the same repository are grouped the way GitHub's own
feed groups them.

A token is optional: it only lifts the rate limit from 60 to 5000 an hour.

Run:  python scripts/update_activity.py
Out:  the block between <!--START_SECTION:activity--> and
      <!--END_SECTION:activity--> in README.md
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "README.md"

LOGIN = os.environ.get("GH_LOGIN", "asuzey")
MAX_LINES = int(os.environ.get("MAX_LINES", "6"))

START = "<!--START_SECTION:activity-->"
END = "<!--END_SECTION:activity-->"


def fetch_events() -> list[dict]:
    url = f"https://api.github.com/users/{LOGIN}/events/public?per_page=100"
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": f"{LOGIN}-profile-activity",
    }
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"

    try:
        with urllib.request.urlopen(
            urllib.request.Request(url, headers=headers), timeout=30
        ) as response:
            return json.load(response)
    except urllib.error.HTTPError as err:
        raise SystemExit(f"GitHub API returned {err.code}: {err.read()[:200]!r}")


def repo_link(name: str) -> str:
    return f"[{name}](https://github.com/{name})"


def describe(event: dict, extra_commits: int = 0) -> str | None:
    """One markdown line for an event, or None for the kinds we skip."""
    kind = event["type"]
    repo = event["repo"]["name"]
    payload = event.get("payload", {})

    if kind == "PushEvent":
        count = payload.get("size", 0) + extra_commits
        branch = payload.get("ref", "").rsplit("/", 1)[-1]
        plural = "commit" if count == 1 else "commits"
        where = f" on `{branch}`" if branch and branch not in ("main", "master") else ""
        return f"&#11014;&#65039; Pushed {count} {plural} to {repo_link(repo)}{where}"

    if kind == "CreateEvent":
        ref_type = payload.get("ref_type")
        if ref_type == "repository":
            return f"&#10024; Created {repo_link(repo)}"
        if ref_type in ("branch", "tag"):
            return f"&#127793; Created {ref_type} `{payload.get('ref')}` in {repo_link(repo)}"
        return None

    if kind == "IssuesEvent":
        issue = payload.get("issue", {})
        action = payload.get("action", "updated")
        emoji = {"opened": "&#10071;", "closed": "&#128274;",
                 "reopened": "&#128275;"}.get(action, "&#8505;&#65039;")
        return (f"{emoji} {action.capitalize()} issue "
                f"[#{issue.get('number')}]({issue.get('html_url')}) in {repo_link(repo)}")

    if kind == "PullRequestEvent":
        pull = payload.get("pull_request", {})
        action = payload.get("action", "updated")
        if action == "closed" and pull.get("merged"):
            action, emoji = "merged", "&#127881;"
        else:
            emoji = {"opened": "&#128170;", "closed": "&#10060;",
                     "reopened": "&#128275;"}.get(action, "&#8505;&#65039;")
        return (f"{emoji} {action.capitalize()} pull request "
                f"[#{pull.get('number')}]({pull.get('html_url')}) in {repo_link(repo)}")

    if kind == "IssueCommentEvent":
        issue = payload.get("issue", {})
        comment = payload.get("comment", {})
        return (f"&#128172; Commented on [#{issue.get('number')}]"
                f"({comment.get('html_url')}) in {repo_link(repo)}")

    if kind == "ReleaseEvent":
        release = payload.get("release", {})
        label = release.get("name") or release.get("tag_name")
        return (f"&#128640; Released [{label}]({release.get('html_url')}) "
                f"in {repo_link(repo)}")

    if kind == "PublicEvent":
        return f"&#128275; Made {repo_link(repo)} public"

    if kind == "ForkEvent":
        return f"&#127860; Forked {repo_link(repo)}"

    if kind == "WatchEvent":
        return f"&#11088; Starred {repo_link(repo)}"

    return None


def build_lines(events: list[dict]) -> list[str]:
    """Group consecutive pushes to one repo, then describe the first MAX_LINES."""
    merged: list[tuple[dict, int]] = []
    for event in events:
        if merged:
            previous, extra = merged[-1]
            same_repo_push = (
                event["type"] == "PushEvent"
                and previous["type"] == "PushEvent"
                and event["repo"]["name"] == previous["repo"]["name"]
            )
            if same_repo_push:
                merged[-1] = (previous, extra + event.get("payload", {}).get("size", 0))
                continue
        merged.append((event, 0))

    lines = []
    for event, extra in merged:
        line = describe(event, extra)
        if line:
            lines.append(f"{len(lines) + 1}. {line}")
        if len(lines) == MAX_LINES:
            break
    return lines


def main() -> None:
    text = README.read_text(encoding="utf-8")
    if START not in text or END not in text:
        raise SystemExit(f"README.md is missing the {START} / {END} markers")

    lines = build_lines(fetch_events())
    body = "\n".join(lines) if lines else "_Nothing public yet -- check back soon._"

    head, rest = text.split(START, 1)
    _, tail = rest.split(END, 1)
    updated = f"{head}{START}\n{body}\n{END}{tail}"

    if updated == text:
        print("activity unchanged")
        return

    README.write_text(updated, encoding="utf-8")
    print(f"activity updated ({len(lines)} entries)")


if __name__ == "__main__":
    main()
