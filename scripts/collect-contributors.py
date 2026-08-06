#!/usr/bin/env python3
"""
collect-contributors.py — собирает список контрибьюторов репозитория в данные Hugo.

Запускается на каждом прогоне CI (и локально). Результат:

  data/contributors.json     ← Hugo читает как site.Data.contributors

Просто список людей: ник, имя, аватар, число коммитов, первый/последний коммит.
Без разбивки по курсам и лекциям.

Источники:
  1. git log — работает всегда, даёт число коммитов и даты
  2. GitHub API /repos/{repo}/contributors — добавляет настоящие ники, аватары
     и ссылки (нужен GITHUB_TOKEN; в Actions он есть из коробки)

Требуется полная история: actions/checkout с fetch-depth: 0.

Использование:
  python scripts/collect-contributors.py
  python scripts/collect-contributors.py --out data/contributors.json
  python scripts/collect-contributors.py --no-api    # только git
"""

import argparse
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

RS = "\x01"   # разделитель записей
FS = "\x1f"   # разделитель полей

NOREPLY_RE = re.compile(r"^(?:\d+\+)?([A-Za-z0-9-]+)@users\.noreply\.github\.com$", re.I)

BOT_EMAILS = {
    "actions@github.com",
    "41898282+github-actions[bot]@users.noreply.github.com",
    "noreply@github.com",
}
BOT_NAME_RE = re.compile(r"\[bot\]$|^github-actions", re.I)


# ── git ───────────────────────────────────────────────────────────────────────

def git(*args: str) -> str:
    r = subprocess.run(["git", *args], capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)}: {r.stderr.strip()}")
    return r.stdout


def is_bot(name: str, email: str) -> bool:
    return email.lower() in BOT_EMAILS or bool(BOT_NAME_RE.search(name))


def identity(name: str, email: str) -> tuple[str, str | None]:
    """Возвращает (стабильный id, github-ник или None)."""
    m = NOREPLY_RE.match(email.strip())
    if m:
        return m.group(1).lower(), m.group(1)
    return (email.strip().lower() or name.strip().lower()), None


def collect_people(content_dir: str) -> dict:
    """Один проход по истории. people[id] = {name, login, emails, commits, first_commit, last_commit}."""
    raw = git(
        "log", "--no-merges", "--date-order",
        f"--pretty=format:{RS}%an{FS}%ae{FS}%aI",
        "--", content_dir,
    )

    people: dict[str, dict] = {}

    for chunk in raw.split(RS):
        chunk = chunk.strip("\n")
        if not chunk:
            continue
        parts = chunk.split(FS)
        if len(parts) != 3:
            continue
        name, email, date = parts
        if is_bot(name, email):
            continue

        pid, login = identity(name, email)
        p = people.setdefault(pid, {
            "id": pid, "name": name, "login": login, "emails": set(),
            "commits": 0, "first_commit": date, "last_commit": date,
        })
        p["emails"].add(email)
        p["commits"] += 1
        p["login"] = p["login"] or login
        if date < p["first_commit"]:
            p["first_commit"] = date
        if date > p["last_commit"]:
            p["last_commit"] = date

    for p in people.values():
        p["emails"] = sorted(p["emails"])

    return people


# ── GitHub API ────────────────────────────────────────────────────────────────

def detect_repo() -> str | None:
    repo = os.environ.get("GITHUB_REPOSITORY")
    if repo:
        return repo
    try:
        url = git("remote", "get-url", "origin").strip()
    except RuntimeError:
        return None
    m = re.search(r"github\.com[:/](.+?)(?:\.git)?$", url)
    return m.group(1) if m else None


def fetch_api_contributors(repo: str, token: str | None) -> list[dict]:
    """Ники + аватары из GitHub API. Пустой список, если недоступно."""
    out, page = [], 1
    while page <= 5:
        url = f"https://api.github.com/repos/{repo}/contributors?per_page=100&page={page}"
        req = urllib.request.Request(url, headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "collect-contributors",
            **({"Authorization": f"Bearer {token}"} if token else {}),
        })
        try:
            with urllib.request.urlopen(req, timeout=15) as r:
                batch = json.load(r)
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as e:
            print(f"  [WARN] GitHub API недоступен ({e}) — только git", file=sys.stderr)
            return out
        if not batch:
            break
        out.extend(batch)
        if len(batch) < 100:
            break
        page += 1
    return [c for c in out
            if c.get("type") != "Bot" and not str(c.get("login", "")).endswith("[bot]")]


def merge_api(people: dict, api: list[dict]) -> None:
    """Дописывает аватар/ссылку/точное число коммитов тем, кого нашли по нику."""
    by_login = {p["login"].lower(): p for p in people.values() if p.get("login")}
    for c in api:
        login = c["login"]
        p = by_login.get(login.lower())
        if p is None:
            # Есть в API, но в content/ не коммитил — всё равно добавляем.
            p = people.setdefault(login.lower(), {
                "id": login.lower(), "name": login, "login": login, "emails": [],
                "commits": 0, "first_commit": None, "last_commit": None,
            })
        p["login"] = login
        p["avatar"] = c.get("avatar_url")
        p["url"] = c.get("html_url")
        p["commits_total"] = c.get("contributions")


# ── вывод ─────────────────────────────────────────────────────────────────────

def build_payload(people: dict, repo: str | None, source: str) -> dict:
    ordered = sorted(
        people.values(),
        key=lambda p: (-(p.get("commits_total") or p["commits"]), (p.get("login") or p["name"]).lower()),
    )

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "repo": repo,
        "commit": os.environ.get("GITHUB_SHA"),
        "run_id": os.environ.get("GITHUB_RUN_ID"),
        "source": source,
        "count": len(ordered),
        "logins": [p["login"] for p in ordered if p.get("login")],
        "people": ordered,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="Сбор контрибьюторов в data/contributors.json")
    ap.add_argument("--out", default="data/contributors.json")
    ap.add_argument("--content-dir", default="content/posts")
    ap.add_argument("--no-api", action="store_true", help="Не ходить в GitHub API")
    args = ap.parse_args()

    try:
        people = collect_people(args.content_dir)
    except RuntimeError as e:
        print(f"[ERROR] {e}", file=sys.stderr)
        print("       Нужна полная история: actions/checkout с fetch-depth: 0", file=sys.stderr)
        return 1

    source = "git"
    repo = detect_repo()
    if not args.no_api and repo:
        api = fetch_api_contributors(repo, os.environ.get("GITHUB_TOKEN"))
        if api:
            merge_api(people, api)
            source = "git+github-api"

    payload = build_payload(people, repo, source)

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"[OK] {out}: {payload['count']} контрибьюторов "
          f"({', '.join(payload['logins'][:10]) or '—'}), источник: {source}")
    return 0


if __name__ == "__main__":
    sys.exit(main())