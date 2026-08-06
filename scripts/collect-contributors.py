#!/usr/bin/env python3
"""
collect-contributors.py — собирает контрибьюторов репозитория в данные Hugo.

Запускается на каждом прогоне CI (и локально). Результат:

  data/contributors.json     ← Hugo читает как site.Data.contributors

Что внутри:
  • people   — все контрибьюторы: ник, имя, аватар, число коммитов, первый/последний
  • courses  — кто и сколько коммитил в каждый курс, вплоть до конкретной лекции

Источники:
  1. GitHub API /repos/{repo}/contributors — даёт настоящие ники и аватары
     (нужен GITHUB_TOKEN; в Actions он есть из коробки)
  2. git log — работает всегда, даёт привязку к курсам/лекциям и даты

Требуется полная история: actions/checkout с fetch-depth: 0.

Использование:
  python scripts/collect-contributors.py
  python scripts/collect-contributors.py --out data/contributors.json
  python scripts/collect-contributors.py --no-api          # только git
  python scripts/collect-contributors.py --history         # + снапшот в .cache/
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


def parse_git_log(content_dir: str) -> tuple[dict, dict]:
    """
    Один проход по истории. Возвращает (people, courses).

    people[id]  = {name, login, emails, commits, first_commit, last_commit}
    courses[c]  = {contributors: {id: {commits, last_commit}},
                   lectures: {lec: {id: commits}}}
    """
    raw = git(
        "log", "--no-merges", "--date-order",
        f"--pretty=format:{RS}%H{FS}%an{FS}%ae{FS}%aI",
        "--name-only", "--", content_dir,
    )

    people: dict[str, dict] = {}
    courses: dict[str, dict] = {}
    base = Path(content_dir)

    for chunk in raw.split(RS):
        chunk = chunk.strip("\n")
        if not chunk:
            continue
        head, _, files_blob = chunk.partition("\n")
        parts = head.split(FS)
        if len(parts) != 4:
            continue
        _sha, name, email, date = parts
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

        touched_courses: set[str] = set()
        touched_lectures: set[tuple[str, str]] = set()
        for f in files_blob.splitlines():
            f = f.strip()
            if not f:
                continue
            try:
                rel = Path(f).relative_to(base).parts
            except ValueError:
                continue
            if not rel:
                continue
            touched_courses.add(rel[0])
            if len(rel) >= 2 and not rel[1].startswith("_") and "." not in rel[1]:
                touched_lectures.add((rel[0], rel[1]))

        for c in touched_courses:
            entry = courses.setdefault(c, {"contributors": {}, "lectures": {}})
            cc = entry["contributors"].setdefault(pid, {"commits": 0, "last_commit": date})
            cc["commits"] += 1
            if date > cc["last_commit"]:
                cc["last_commit"] = date

        for c, lec in touched_lectures:
            lecs = courses[c]["lectures"].setdefault(lec, {})
            lecs[pid] = lecs.get(pid, 0) + 1

    for p in people.values():
        p["emails"] = sorted(p["emails"])

    return people, courses


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

def build_payload(people: dict, courses: dict, repo: str | None, source: str) -> dict:
    ordered = sorted(
        people.values(),
        key=lambda p: (-(p.get("commits_total") or p["commits"]), (p.get("login") or p["name"]).lower()),
    )

    def rank(d: dict, key="commits"):
        return [
            {"id": pid, **vals}
            for pid, vals in sorted(d.items(), key=lambda kv: -_num(kv[1], key))
        ]

    def _num(v, key):
        return v[key] if isinstance(v, dict) else v

    courses_out = {}
    for slug, data in sorted(courses.items()):
        courses_out[slug] = {
            "contributors": rank(data["contributors"]),
            "lectures": {
                lec: [{"id": pid, "commits": n}
                      for pid, n in sorted(who.items(), key=lambda kv: -kv[1])]
                for lec, who in sorted(data["lectures"].items())
            },
        }

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "repo": repo,
        "commit": os.environ.get("GITHUB_SHA"),
        "run_id": os.environ.get("GITHUB_RUN_ID"),
        "source": source,
        "count": len(ordered),
        "logins": [p["login"] for p in ordered if p.get("login")],
        "people": ordered,
        "courses": courses_out,
    }


def append_history(payload: dict, path: Path) -> None:
    """Снапшот прогона в .cache — переживает между запусками через кеш Actions."""
    path.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps({
        "at": payload["generated_at"],
        "run_id": payload["run_id"],
        "commit": payload["commit"],
        "count": payload["count"],
        "logins": payload["logins"],
    }, ensure_ascii=False)
    with path.open("a", encoding="utf-8") as f:
        f.write(line + "\n")


def main() -> int:
    ap = argparse.ArgumentParser(description="Сбор контрибьюторов в data/contributors.json")
    ap.add_argument("--out", default="data/contributors.json")
    ap.add_argument("--content-dir", default="content/posts")
    ap.add_argument("--no-api", action="store_true", help="Не ходить в GitHub API")
    ap.add_argument("--history", action="store_true",
                    help="Дописать снапшот в .cache/contributors/history.jsonl")
    args = ap.parse_args()

    try:
        people, courses = parse_git_log(args.content_dir)
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

    payload = build_payload(people, courses, repo, source)

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    if args.history:
        append_history(payload, Path(".cache/contributors/history.jsonl"))

    print(f"[OK] {out}: {payload['count']} контрибьюторов "
          f"({', '.join(payload['logins'][:10]) or '—'}), источник: {source}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
