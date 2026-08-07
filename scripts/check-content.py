#!/usr/bin/env python3
"""
check-content.py — проверяет конспекты по схеме из archetypes/.

Схема не зашита в скрипт: она читается из архетипов, тех самых, по которым
`hugo new` создаёт файлы. Правило одно — правишь архетип, проверка меняется
вместе с ним, разъехаться они не могут.

    python scripts/check-content.py
    python scripts/check-content.py --strict     # предупреждения тоже валят
    python scripts/check-content.py --md         # отчёт списком задач

Аннотации в архетипе (комментарий в конце строки):

    title: ""      # required                 обязательное поле
    date: ...      # required-any: порядок    хотя бы одно из группы
    accent: 1      # recommended  int: 1..6   без него живём, но лучше с ним
    teacher: ""    # recommended-with: semester  спрашиваем, только если задан semester
    noteType: ...  # enum: human, ai, ai-pro  допустимые значения
    semester: 0    # int                      число (можно диапазон 1..6)

Что определяется по структуре папки:

    есть _index.md              → курс, вложенные папки с index.md → лекции
    нет _index.md, плоские .md  → отдельные страницы (posts/public и т.п.)

Поля, которых нет ни в одном архетипе, дают предупреждение — так ловятся
опечатки вроде noteype или decsription.

Зависимости: PyYAML.
"""

import argparse
import re
import sys
from collections import defaultdict
from datetime import date, datetime
from pathlib import Path

try:
    import yaml
except ImportError:
    print("[ERROR] нужен PyYAML: pip install pyyaml", file=sys.stderr)
    raise SystemExit(2)

FM_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n?", re.S)
KEY_RE = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*)\s*:(.*)$")
KEBAB_RE = re.compile(r"^[a-z0-9]+(?:[-_][a-z0-9]+)*$")
RANGE_RE = re.compile(r"int(?::\s*(\d+)\.\.(\d+))?")

ARCHETYPES = {"lecture": "default.md", "course": "course.md", "page": "page.md"}

LENIENT_DIRS = {"public"}

HUGO_FIELDS = {"draft", "aliases", "slug", "url", "layout", "type", "lastmod",
               "keywords", "summary", "params", "series", "categories",
               "outputs", "sitemap", "expiryDate", "publishDate"}


# ── схема из архетипов ────────────────────────────────────────────────────────

class Schema:
    def __init__(self, path: Path):
        self.path = path
        self.fields: dict[str, dict] = {}
        self.any_groups: dict[str, list[str]] = defaultdict(list)
        self._parse(path)

    def _parse(self, path: Path) -> None:
        text = path.read_text(encoding="utf-8")
        m = FM_RE.match(text)
        body = m.group(1) if m else text

        for line in body.splitlines():
            if not line.strip() or line.startswith("#") or line[0].isspace():
                continue
            km = KEY_RE.match(line)
            if not km:
                continue
            key, rest = km.group(1), km.group(2)
            note = rest.split("#", 1)[1].strip() if "#" in rest else ""
            spec: dict = {"required": False, "recommended": False,
                          "recommended_with": None, "enum": None, "int": None}

            if re.search(r"\brequired\b(?!-)", note):
                spec["required"] = True

            rw = re.search(r"recommended-with:\s*([A-Za-z_][A-Za-z0-9_]*)", note)
            if rw:
                spec["recommended"] = True
                spec["recommended_with"] = rw.group(1)
            elif re.search(r"\brecommended\b(?!-)", note):
                spec["recommended"] = True

            g = re.search(r"required-any:\s*(.+)$", note)
            if g:
                self.any_groups[g.group(1).strip()].append(key)

            e = re.search(r"enum:\s*([^#]+)", note)
            if e:
                spec["enum"] = [v.strip() for v in e.group(1).split(",") if v.strip()]

            i = RANGE_RE.search(note)
            if i:
                spec["int"] = (int(i.group(1)), int(i.group(2))) if i.group(1) else (None, None)

            self.fields[key] = spec


# ── проверка ─────────────────────────────────────────────────────────────────

class Report:
    def __init__(self) -> None:
        self.errors: list[tuple[Path, str]] = []
        self.warnings: list[tuple[Path, str]] = []

    def err(self, path: Path, msg: str) -> None:
        self.errors.append((path, msg))

    def warn(self, path: Path, msg: str) -> None:
        self.warnings.append((path, msg))


def front_matter(path: Path, rep: Report) -> dict | None:
    text = path.read_text(encoding="utf-8", errors="replace")
    m = FM_RE.match(text)
    if not m:
        rep.err(path, "нет YAML front matter в начале файла")
        return None
    try:
        data = yaml.safe_load(m.group(1)) or {}
    except yaml.YAMLError as e:
        rep.err(path, f"не парсится YAML: {e}")
        return None
    if not isinstance(data, dict):
        rep.err(path, "front matter должен быть словарём")
        return None
    return data


def is_empty(value) -> bool:
    if value is None:
        return True
    if isinstance(value, bool):
        return False
    return isinstance(value, (str, list, dict)) and len(value) == 0


def check_against(path: Path, fm: dict, schema: Schema, rep: Report,
                  strict_fields: bool = True) -> None:
    """strict_fields=False — только настоящие ошибки, без придирок к полям."""
    for key, spec in schema.fields.items():
        value = fm.get(key)

        if spec["required"] and is_empty(value):
            rep.err(path, f"нет обязательного поля {key}")
            continue
        if spec["recommended"] and is_empty(value) and strict_fields:
            partner = spec["recommended_with"]
            if not partner or not is_empty(fm.get(partner)):
                rep.warn(path, f"не заполнено {key} — стоит указать")
        if is_empty(value):
            continue

        if spec["enum"] and str(value) not in spec["enum"]:
            rep.err(path, f"{key}: ожидается {', '.join(spec['enum'])}, получено {value!r}")

        if spec["int"] is not None:
            if isinstance(value, bool) or not isinstance(value, int):
                rep.err(path, f"{key}: должно быть числом, а не {value!r}")
            else:
                lo, hi = spec["int"]
                if lo is not None and not lo <= value <= hi:
                    rep.err(path, f"{key}: ожидается {lo}..{hi}, получено {value}")

    for group, keys in schema.any_groups.items():
        if all(is_empty(fm.get(k)) for k in keys):
            rep.err(path, f"нужно хотя бы одно из полей: {', '.join(keys)} — {group}")

    if strict_fields:
        known = {k.lower() for k in set(schema.fields) | HUGO_FIELDS}
        for key in fm:
            if key.lower() not in known:
                rep.warn(path, f"поле {key} не описано в archetypes/{schema.path.name} — опечатка?")

    raw = fm.get("date")
    if isinstance(raw, str):
        try:
            datetime.fromisoformat(raw.replace("Z", "+00:00"))
        except ValueError:
            rep.err(path, f"date не разбирается: {raw!r}")
    elif raw is not None and not isinstance(raw, (date, datetime)):
        rep.err(path, f"date не разбирается: {raw!r}")


def check_subjects(variants_by_subject: dict, rep: Report) -> None:
    """Варианты одного предмета должны выглядеть как один предмет."""
    for subject, variants in variants_by_subject.items():
        if len(variants) < 2:
            continue
        titles = {str(fm.get("title")) for _, fm in variants}
        if len(titles) > 1:
            rep.err(variants[0][0], f"subject: {subject} — разные title: {sorted(titles)}")
        accents = {fm.get("accent") for _, fm in variants}
        if len(accents) > 1:
            rep.err(variants[0][0], f"subject: {subject} — разный accent: {sorted(map(str, accents))}")
        for path, fm in variants:
            if is_empty(fm.get("teacher")):
                rep.err(path, f"subject: {subject} — вариантов несколько, нужен teacher")
            if fm.get("weight") in (None, 0):
                rep.warn(path, "нет weight — порядок преподавателей будет произвольным")


def main() -> int:
    ap = argparse.ArgumentParser(description="Проверка конспектов по archetypes/")
    ap.add_argument("--root", default="content/posts")
    ap.add_argument("--archetypes", default="archetypes")
    ap.add_argument("--strict", action="store_true", help="Предупреждения тоже валят")
    ap.add_argument("--md", action="store_true", help="Отчёт списком задач для issue")
    ap.add_argument("--lenient", nargs="*", default=sorted(LENIENT_DIRS),
                    metavar="DIR", help="Разделы, где проверяются только ошибки")
    args = ap.parse_args()

    arch_dir = Path(args.archetypes)
    schemas: dict[str, Schema] = {}
    for kind, filename in ARCHETYPES.items():
        p = arch_dir / filename
        if not p.exists():
            print(f"[ERROR] нет {p} — схему брать неоткуда", file=sys.stderr)
            return 2
        schemas[kind] = Schema(p)

    root = Path(args.root)
    if not root.is_dir():
        print(f"[ERROR] нет каталога {root}", file=sys.stderr)
        return 2

    rep = Report()
    lenient = set(args.lenient or [])
    subjects: dict[str, list] = defaultdict(list)
    courses = lectures = pages = 0

    for d in sorted(p for p in root.iterdir() if p.is_dir()):
        index = d / "_index.md"
        has_lectures = any((sub / "index.md").exists() for sub in d.iterdir() if sub.is_dir())

        if not index.exists():
            if has_lectures and d.name not in lenient:
                rep.err(d, "есть лекции, но нет _index.md — курс не появится на главной")
            strict = d.name not in lenient
            for md in sorted(d.rglob("*.md")):
                pages += 1
                fm = front_matter(md, rep)
                if fm is not None:
                    check_against(md, fm, schemas["page"], rep, strict_fields=strict)
            continue

        courses += 1
        fm = front_matter(index, rep)
        if fm is not None:
            check_against(index, fm, schemas["course"], rep)
            if not is_empty(fm.get("subject")):
                subjects[str(fm["subject"])].append((index, fm))

        if not KEBAB_RE.match(d.name):
            rep.warn(d, "имя папки курса не в kebab-case")

        for sub in sorted(p for p in d.iterdir() if p.is_dir()):
            md = sub / "index.md"
            if not md.exists():
                continue
            lectures += 1
            lfm = front_matter(md, rep)
            if lfm is not None:
                check_against(md, lfm, schemas["lecture"], rep)
            if not KEBAB_RE.match(sub.name):
                rep.warn(sub, "имя папки лекции не в kebab-case")

        for md in sorted(d.glob("*.md")):
            if md.name == "_index.md":
                continue
            lectures += 1
            lfm = front_matter(md, rep)
            if lfm is not None:
                check_against(md, lfm, schemas["lecture"], rep)

    check_subjects(subjects, rep)

    if args.md:
        by_file: dict[Path, list[str]] = defaultdict(list)
        for p, m in rep.errors:
            by_file[p].append(f"**{m}**")
        for p, m in rep.warnings:
            by_file[p].append(m)
        print("## Что привести в порядок\n")
        for p in sorted(by_file, key=str):
            print(f"- [ ] `{p}`")
            for m in by_file[p]:
                print(f"  - {m}")
        print(f"\nОшибок: {len(rep.errors)}, предупреждений: {len(rep.warnings)}.")
    else:
        for p, m in rep.warnings:
            print(f"[WARN]  {p}: {m}")
        for p, m in rep.errors:
            print(f"[ERROR] {p}: {m}", file=sys.stderr)
        print(f"\n[i] курсов: {courses}, лекций: {lectures}, страниц: {pages}, "
              f"ошибок: {len(rep.errors)}, предупреждений: {len(rep.warnings)}")

    if rep.errors:
        return 1
    if args.strict and rep.warnings:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())