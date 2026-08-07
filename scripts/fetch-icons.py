#!/usr/bin/env python3
"""
fetch-icons.py — складывает используемые иконки в assets/icons.

Зачем: <ion-icon> — это веб-компонент, который тянет с CDN свой рантайм,
а потом на КАЖДУЮ иконку делает отдельный запрос за её SVG. Десяток
иконок в шапке = десяток запросов и мигание до гидрации.

После этого скрипта иконки лежат в репозитории и вставляются инлайном
партиалом layouts/partials/ui/icon.html — ноль запросов, ноль JS.

Запускать руками и коммитить результат (в CI сеть тогда не нужна):

    python scripts/fetch-icons.py
    python scripts/fetch-icons.py --check     # только показать, чего не хватает

Имена собираются из:
  • layouts/**  — <ion-icon name="x"> и partial "ui/icon.html" (dict "name" "x")
  • content/**  — icon: x во front matter (закреплённые ссылки, callout'ы)
  • EXTRA ниже  — то, что подставляется динамически и в тексте не встречается
"""

import argparse
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

VERSION = "7.4.0"
CDN = "https://cdn.jsdelivr.net/npm/ionicons@{v}/dist/svg/{name}.svg"

# Иконки, которые выбираются в рантайме и по шаблонам не находятся.
EXTRA = [
    "information-circle-outline",
    "alert-circle-outline",
    "checkmark-circle-outline",
    "close-circle-outline",
    "bulb-outline",
    "sparkles",
    "sparkles-outline",
    "create-outline",
    "chevron-forward",
    "chevron-down",
    "close",
    "checkmark-circle",
    "person-outline",
    "people-outline",
]

ION_RE = re.compile(r'<ion-icon[^>]*\bname="([a-z0-9-]+)"', re.I)
PARTIAL_RE = re.compile(r'"ui/icon\.html"\s*\(dict\s*"name"\s*"([a-z0-9-]+)"')
FRONTMATTER_ICON_RE = re.compile(r'^\s*icon:\s*"?([a-z0-9-]+)"?\s*$', re.M)


def collect(root: Path) -> set[str]:
    names: set[str] = set(EXTRA)

    layouts = root / "layouts"
    if layouts.is_dir():
        for f in layouts.rglob("*.html"):
            text = f.read_text(encoding="utf-8", errors="ignore")
            names |= set(ION_RE.findall(text))
            names |= set(PARTIAL_RE.findall(text))

    content = root / "content"
    if content.is_dir():
        for f in content.rglob("*.md"):
            head = f.read_text(encoding="utf-8", errors="ignore")[:2000]
            names |= set(FRONTMATTER_ICON_RE.findall(head))

    return {n for n in names if n and not n.startswith("{{")}


def download(name: str, dest: Path) -> bool:
    url = CDN.format(v=VERSION, name=name)
    req = urllib.request.Request(url, headers={"User-Agent": "fetch-icons"})
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            body = r.read().decode("utf-8")
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as e:
        print(f"  [WARN] {name}: {e}", file=sys.stderr)
        return False

    if "<svg" not in body:
        print(f"  [WARN] {name}: это не SVG", file=sys.stderr)
        return False

    dest.write_text(body.strip() + "\n", encoding="utf-8")
    return True


def main() -> int:
    ap = argparse.ArgumentParser(description="Скачать используемые иконки в assets/icons")
    ap.add_argument("--out", default="assets/icons")
    ap.add_argument("--root", default=".")
    ap.add_argument("--check", action="store_true", help="Ничего не качать, только отчёт")
    ap.add_argument("--force", action="store_true", help="Перекачать даже существующие")
    args = ap.parse_args()

    root = Path(args.root)
    out = root / args.out
    out.mkdir(parents=True, exist_ok=True)

    names = sorted(collect(root))
    missing = [n for n in names if args.force or not (out / f"{n}.svg").exists()]

    print(f"[i] используется иконок: {len(names)}, не хватает: {len(missing)}")

    if args.check:
        for n in missing:
            print(f"    - {n}")
        return 1 if missing else 0

    ok = 0
    for n in missing:
        if download(n, out / f"{n}.svg"):
            ok += 1

    # Лишнее не удаляем автоматически — только показываем.
    have = {p.stem for p in out.glob("*.svg")}
    extra = sorted(have - set(names))
    if extra:
        print(f"[i] в {out} лежат неиспользуемые: {', '.join(extra)}")

    print(f"[OK] скачано {ok} из {len(missing)} → {out}")
    return 0 if ok == len(missing) else 1


if __name__ == "__main__":
    sys.exit(main())
