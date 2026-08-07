#!/usr/bin/env python3
"""
migrate-icons.py — заменяет <ion-icon> на partial "ui/icon.html".

    python scripts/migrate-icons.py --dry     # посмотреть, что изменится
    python scripts/migrate-icons.py           # переписать файлы

Что делает:

    <ion-icon name="calendar-outline"></ion-icon>
    → {{ partial "ui/icon.html" (dict "name" "calendar-outline") }}

    <ion-icon name="{{ $icon }}" class="text-lg opacity-60"></ion-icon>
    → {{ partial "ui/icon.html" (dict "name" $icon "class" "text-lg opacity-60") }}

Динамические имена (из front matter) шаблон найдёт только если такой SVG
лежит в assets/icons — добавь их в EXTRA внутри fetch-icons.py.

После прогона: убедиться, что <ion-icon> не осталось, и убрать подключение
ionicons из layouts/partials/core/scripts.html.
"""

import argparse
import re
import sys
from pathlib import Path

TAG_RE = re.compile(r"<ion-icon\b([^>]*?)\s*(?:/>|>\s*</ion-icon>)", re.S)
ATTR_RE = re.compile(r'([a-zA-Z:-]+)="([^"]*)"')
EXPR_RE = re.compile(r"^\{\{-?\s*(.*?)\s*-?\}\}$", re.S)


def as_hugo_value(raw: str) -> str:
    """`{{ $icon }}` → `$icon`, обычная строка → `"строка"`."""
    m = EXPR_RE.match(raw.strip())
    if m:
        return m.group(1)
    return '"%s"' % raw.replace('"', '\\"')


def convert(match: re.Match) -> str:
    attrs = dict(ATTR_RE.findall(match.group(1)))
    name = attrs.pop("name", "")
    cls = attrs.pop("class", "")
    label = attrs.pop("aria-label", "")

    parts = ['"name" %s' % as_hugo_value(name)]
    if cls:
        parts.append('"class" %s' % as_hugo_value(cls))
    if label:
        parts.append('"label" %s' % as_hugo_value(label))

    return '{{ partial "ui/icon.html" (dict %s) }}' % " ".join(parts)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default="layouts")
    ap.add_argument("--dry", action="store_true")
    args = ap.parse_args()

    total = 0
    touched = 0

    for f in Path(args.root).rglob("*.html"):
        text = f.read_text(encoding="utf-8")
        new, n = TAG_RE.subn(convert, text)
        if not n:
            continue
        total += n
        touched += 1
        if args.dry:
            print(f"--- {f} ({n})")
            for line in new.splitlines():
                if "ui/icon.html" in line:
                    print("    " + line.strip())
        else:
            f.write_text(new, encoding="utf-8")

    print(f"[{'DRY' if args.dry else 'OK'}] {total} иконок в {touched} файлах")

    left = [str(f) for f in Path(args.root).rglob("*.html")
            if "<ion-icon" in f.read_text(encoding="utf-8")]
    if left:
        print("[WARN] остались <ion-icon>: " + ", ".join(left), file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
