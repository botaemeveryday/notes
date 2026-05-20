#!/usr/bin/env python3
"""
merge-md-for-ai.py — объединяет лекции курса в один MD файл для ИИ.

Структура Hugo:
  content/posts/<course>/
    _index.md
    lecture-01/index.md
    lecture-02/index.md
    ...

Вывод:
  static/posts/<course>/resources/<course>_merged.md

Использование:
  python scripts/merge-md-for-ai.py                    # все курсы
  python scripts/merge-md-for-ai.py math-stats         # конкретный курс
  python scripts/merge-md-for-ai.py --no-convert
  python scripts/merge-md-for-ai.py --dry-run
"""

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from cache_utils import compute_course_hash, is_cache_valid, write_cache, invalidate_cache

# ── настройки ─────────────────────────────────────────────────────────────────

DEFAULTS = dict(
    content_dir     = "content/posts",
    static_dir      = "static/posts",
    convert_obsidian = True,
    add_separators   = True,
    separator        = "---",
    verbose          = True,
)

IGNORE_DIRS = {
    ".venv", "venv", "env", "__pycache__", "node_modules",
    ".git", ".idea", ".vscode", "site-packages", "dist-info", "lib",
    "images", "img", "attachments", "resources",
}

# Регулярки
YAML_FRONTMATTER_RE = re.compile(r"\A---\s*\n.*?\n---\s*\n", re.DOTALL)
CALLOUT_RE          = re.compile(r"^(>\s*)\[!(\w+)\]\s*(.*)", re.MULTILINE)
WIKILINK_RE         = re.compile(r"\[\[([^\]|]+)(?:\|([^\]]+))?\]\]")
HIGHLIGHT_RE        = re.compile(r"==(.+?)==")
# Hugo shortcodes
SHORTCODE_RE        = re.compile(r"\{\{[<%].*?[>%]\}\}", re.DOTALL)
# Obsidian-шапка
OBSIDIAN_HEADER_RE  = re.compile(r"<br\s*/?>", re.IGNORECASE)


# ── утилиты ───────────────────────────────────────────────────────────────────

def natural_sort_key(p: Path) -> list:
    return [int(t) if t.isdigit() else t.lower() for t in re.split(r"(\d+)", str(p))]


def read_title_from_md(md_path: Path, fallback: str) -> str:
    if not md_path.exists():
        return fallback
    content = md_path.read_text(encoding="utf-8")
    m = re.search(r'^title\s*[:=]\s*["\']?(.+?)["\']?\s*$', content, re.MULTILINE)
    return m.group(1).strip() if m else fallback


def is_generation_enabled(index_md: Path, key: str) -> bool:
    """
    Читает блок generate: из front matter _index.md и возвращает,
    нужно ли генерировать артефакт с данным ключом.

    Пример _index.md:
        generate:
          pdf: false
          ai: false

    Если поля нет совсем — генерация разрешена (дефолт = True).
    """
    if not index_md.exists():
        return True
    content = index_md.read_text(encoding="utf-8")

    fm_match = re.match(r"\A---\s*\n(.*?)\n---\s*\n", content, re.DOTALL)
    if not fm_match:
        return True
    frontmatter = fm_match.group(1)

    pattern = re.compile(
        r'^\s{0,8}generate\s*:\s*\n((?:[ \t]+\S[^\n]*\n?)*)',
        re.MULTILINE,
    )
    block_match = pattern.search(frontmatter)
    if not block_match:
        return True

    block = block_match.group(1)
    key_match = re.search(
        rf'^\s+{re.escape(key)}\s*:\s*(true|false|yes|no|1|0)\s*$',
        block,
        re.MULTILINE | re.IGNORECASE,
    )
    if not key_match:
        return True

    return key_match.group(1).lower() not in ("false", "no", "0")


def find_lecture_dirs(course_dir: Path) -> list[Path]:
    """Находит все подпапки лекций (любой префикс + число)."""
    dirs = [
        d for d in course_dir.iterdir()
        if d.is_dir() and re.search(r"\d+", d.name) and d.name not in IGNORE_DIRS
    ]
    dirs.sort(key=natural_sort_key)
    return dirs


def discover_courses(content_base: Path) -> list[str]:
    """Находит все курсы — подпапки с _index.md и хотя бы одной лекцией."""
    courses = []
    for d in sorted(content_base.iterdir()):
        if not d.is_dir():
            continue
        has_index    = (d / "_index.md").exists()
        has_lectures = any(
            re.search(r"\d+", sub.name)
            for sub in d.iterdir()
            if sub.is_dir() and sub.name not in IGNORE_DIRS
        )
        if has_index and has_lectures:
            courses.append(d.name)
    return courses


def strip_yaml_frontmatter(content: str) -> str:
    """Удаляет YAML frontmatter строго в начале файла."""
    return YAML_FRONTMATTER_RE.sub("", content)


def strip_obsidian_header(content: str) -> str:
    """
    Удаляет Obsidian-шапку (контент до <br>) только если
    <br> встречается в первых 20 строках файла.
    """
    m = OBSIDIAN_HEADER_RE.search(content)
    if m:
        lines_before = content[:m.start()].count("\n")
        if lines_before <= 20:
            return content[m.end():].lstrip("\n")
    return content


def convert_obsidian_syntax(content: str) -> str:
    def replace_callout(m):
        prefix, kind, title = m.group(1), m.group(2).upper(), m.group(3).strip()
        label = f"{kind}{': ' + title if title else ''}"
        return f"{prefix}{label}"

    content = CALLOUT_RE.sub(replace_callout, content)
    content = WIKILINK_RE.sub(lambda m: m.group(2) or m.group(1), content)
    content = HIGHLIGHT_RE.sub(r"\1", content)
    content = SHORTCODE_RE.sub("", content)
    return content


def clean_content(content: str, convert_obsidian: bool) -> str:
    content = strip_yaml_frontmatter(content)
    content = strip_obsidian_header(content)
    if convert_obsidian:
        content = convert_obsidian_syntax(content)
    return content.strip()


# ── основная логика ───────────────────────────────────────────────────────────

def merge_course(
    course_slug: str,
    content_base: Path,
    static_base: Path,
    convert_obsidian: bool = True,
    add_separators: bool = True,
    separator: str = "---",
    verbose: bool = True,
    dry_run: bool = False,
) -> bool:
    course_dir = content_base / course_slug
    if not course_dir.exists():
        print(f"[ERROR] Директория курса не найдена: {course_dir}")
        return False

    index_md     = course_dir / "_index.md"
    course_title = read_title_from_md(index_md, course_slug)

    out_dir  = static_base / course_slug / "resources"
    out_file = out_dir / f"{course_slug}_merged.md"

    print(f"\n{'='*60}")
    print(f"Курс: {course_title} ({course_slug})")
    print(f"  → {out_file}")
    print(f"{'='*60}")

    if not is_generation_enabled(index_md, "ai"):
        print("  [SKIP] generate.ai: false в _index.md")
        return True

    course_hash = compute_course_hash(course_dir)

    lecture_dirs = find_lecture_dirs(course_dir)
    md_files = [d / "index.md" for d in lecture_dirs if (d / "index.md").exists()]

    if not md_files:
        print("  [SKIP] Нет index.md файлов")
        return True

    if verbose:
        for f in md_files:
            print(f"    • {f.relative_to(course_dir)}")

    if dry_run:
        cached = is_cache_valid("ai", course_slug, course_hash)
        status = "кеш актуален, пропустим" if cached else f"{len(md_files)} лекций"
        print(f"  [DRY] {status} → {out_file}")
        return True

    if is_cache_valid("ai", course_slug, course_hash) and out_file.exists():
        print("  [CACHE] Контент не изменился, пропускаем")
        return True

    out_dir.mkdir(parents=True, exist_ok=True)

    processed = 0
    try:
        with open(out_file, "w", encoding="utf-8") as out:
            out.write(f"# {course_title}\n\n")
            out.write(f"**Курс:** {course_slug}  \n")
            out.write(f"**Лекций:** {len(md_files)}  \n")
            out.write(f"**Обработка:** убраны YAML, Hugo shortcodes")
            if convert_obsidian:
                out.write(", конвертирован Obsidian-синтаксис")
            out.write("\n\n")

            for i, md_file in enumerate(md_files, 1):
                try:
                    raw     = md_file.read_text(encoding="utf-8")
                    content = clean_content(raw, convert_obsidian)

                    if not content:
                        if verbose:
                            print(f"  [WARN] {md_file.relative_to(course_dir)} — пустой после очистки")
                        continue

                    ldir      = md_file.parent
                    lec_title = read_title_from_md(md_file, ldir.name)
                    out.write(f"\n<!-- ============================================ -->\n")
                    out.write(f"<!-- Лекция: {ldir.name} | {lec_title} -->\n")
                    out.write(f"<!-- ============================================ -->\n\n")

                    out.write(content)

                    if add_separators and i < len(md_files):
                        out.write(f"\n\n{separator}\n\n")

                    processed += 1
                    if verbose:
                        print(f"  ✓ {md_file.relative_to(course_dir)}")

                except Exception as e:
                    print(f"  [ERROR] {md_file}: {e}")

    except Exception as e:
        print(f"  [ERROR] Запись файла: {e}")
        invalidate_cache("ai", course_slug)
        return False

    write_cache("ai", course_slug, course_hash)
    size_kb = out_file.stat().st_size / 1024
    size_str = f"{size_kb / 1024:.2f} MB" if size_kb >= 1024 else f"{size_kb:.1f} KB"
    print(f"  [OK] {out_file} ({size_str}, {processed} лекций)")
    return True


# ── CLI ───────────────────────────────────────────────────────────────────────

def parse_args():
    p = argparse.ArgumentParser(
        description="Объединяет лекции курсов Hugo в MD-файлы для ИИ.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    p.add_argument("courses", nargs="*",
                   help="Слаги курсов. Без аргументов — все курсы.")
    p.add_argument("--content-dir",   default=DEFAULTS["content_dir"],  dest="content_dir")
    p.add_argument("--static-dir",    default=DEFAULTS["static_dir"],   dest="static_dir")
    p.add_argument("--no-convert",    action="store_false", dest="convert_obsidian",
                   help="Не конвертировать Obsidian-синтаксис")
    p.add_argument("--no-separators", action="store_false", dest="add_separators")
    p.add_argument("--quiet", "-q",   action="store_true", dest="quiet")
    p.add_argument("--dry-run",       action="store_true")
    return p.parse_args()


def main():
    args = parse_args()

    project_root = Path.cwd()
    content_base = project_root / args.content_dir
    static_base  = project_root / args.static_dir

    if not content_base.exists():
        sys.exit(f"[ERROR] content dir не найден: {content_base}")

    courses = args.courses if args.courses else discover_courses(content_base)
    if not courses:
        sys.exit("[ERROR] Курсы не найдены")

    print(f"Проект:  {project_root}")
    print(f"Content: {content_base}")
    print(f"Static:  {static_base}")
    print(f"Курсы:   {', '.join(courses)}")
    if args.dry_run:
        print("** DRY RUN — файлы не создаются **")

    failed = []
    for slug in courses:
        ok = merge_course(
            course_slug      = slug,
            content_base     = content_base,
            static_base      = static_base,
            convert_obsidian = args.convert_obsidian,
            add_separators   = args.add_separators,
            separator        = "---",
            verbose          = not args.quiet,
            dry_run          = args.dry_run,
        )
        if not ok:
            failed.append(slug)

    print("\nГотово!")
    if failed:
        print(f"[WARN] Не удалось: {', '.join(failed)}")
        sys.exit(1)


if __name__ == "__main__":
    main()