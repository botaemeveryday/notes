#!/usr/bin/env python3
"""
generate-pdf.py — генерирует PDF-конспекты для курсов Hugo-сайта.

Один курс = один PDF: сквозное оглавление, сквозная нумерация страниц.
Кешируется целиком по хешу всех .md курса + настроек рендера.

Структура Hugo:
  content/posts/<course>/
    _index.md
    lecture-01/index.md
    lecture-02/index.md

Вывод:
  static/posts/<course>/resources/<course>_gen.pdf

Отключить генерацию для курса — в его _index.md:
  generate:
    pdf: false

Зависимости: pandoc + tectonic (или другой --pdf-engine)

Использование:
  python scripts/generate-pdf.py                    # все курсы
  python scripts/generate-pdf.py math-stats         # конкретный курс
  python scripts/generate-pdf.py --dry-run
  python scripts/generate-pdf.py --force            # игнорировать кеш
  python scripts/generate-pdf.py --font "PT Serif"
"""

import argparse
import concurrent.futures
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from cache_utils import (
    compute_course_hash,
    invalidate_cache,
    is_cache_valid,
    salt_hash,
    write_cache,
)

# ── настройки ─────────────────────────────────────────────────────────────────

# Бампни, когда меняешь HEADER_TEX / структуру документа — форсит пересборку.
RENDER_VERSION = "2"

DEFAULTS = dict(
    content_dir = "content/posts",
    static_dir  = "static/posts",
    pdf_engine  = "tectonic",
    font_main   = "DejaVu Serif",
    font_mono   = "DejaVu Sans Mono",
    font_size   = "11pt",
    margin      = "2.5cm",
    toc         = True,
    toc_depth   = 3,
)

IGNORE_DIRS = {
    ".venv", "venv", "env", "__pycache__", "node_modules",
    ".git", ".idea", ".vscode", "site-packages", "dist-info", "lib",
    "images", "img", "attachments", "resources",
}

YAML_FRONTMATTER_RE = re.compile(r"\A---\s*\n.*?\n---\s*\n", re.DOTALL)
CALLOUT_RE          = re.compile(r"^(>\s*)\[!(\w+)\]\s*(.*)", re.MULTILINE)
WIKILINK_RE         = re.compile(r"\[\[([^\]|]+)(?:\|([^\]]+))?\]\]")
HIGHLIGHT_RE        = re.compile(r"==(.+?)==")
SHORTCODE_RE        = re.compile(r"\{\{[<%].*?[>%]\}\}", re.DOTALL)
OBSIDIAN_HEADER_RE  = re.compile(r"<br\s*/?>", re.IGNORECASE)

HEADER_TEX = r"""\usepackage{polyglossia}
\setdefaultlanguage{russian}
\setotherlanguage{english}
\usepackage{microtype}
\usepackage{booktabs}
\usepackage{longtable}
\usepackage{array}
\usepackage{float}
\usepackage{hyperref}
\hypersetup{colorlinks=true, linkcolor=blue, urlcolor=blue, pdfencoding=auto}
"""


# ── текстовые утилиты ─────────────────────────────────────────────────────────

def natural_sort_key(p: Path) -> list:
    return [int(t) if t.isdigit() else t.lower() for t in re.split(r"(\d+)", str(p))]


def strip_yaml_frontmatter(content: str) -> str:
    return YAML_FRONTMATTER_RE.sub("", content)


def strip_obsidian_header(content: str) -> str:
    """Удаляет Obsidian-шапку (до первого <br>), если она в первых 20 строках."""
    m = OBSIDIAN_HEADER_RE.search(content)
    if m and content[:m.start()].count("\n") <= 20:
        return content[m.end():].lstrip("\n")
    return content


def convert_obsidian(content: str) -> str:
    def callout(m):
        prefix, kind, title = m.group(1), m.group(2).upper(), m.group(3).strip()
        return f"{prefix}**{kind}{': ' + title if title else ''}**"
    content = CALLOUT_RE.sub(callout, content)
    content = WIKILINK_RE.sub(lambda m: m.group(2) or m.group(1), content)
    content = HIGHLIGHT_RE.sub(r"**\1**", content)
    content = SHORTCODE_RE.sub("", content)
    return content


def read_title_from_md(md_path: Path, fallback: str) -> str:
    if not md_path.exists():
        return fallback
    content = md_path.read_text(encoding="utf-8")
    m = re.search(r'^title\s*[:=]\s*["\']?(.+?)["\']?\s*$', content, re.MULTILINE)
    return m.group(1).strip() if m else fallback


def yaml_escape(s: str) -> str:
    return s.replace("\\", "\\\\").replace('"', '\\"')


def is_generation_enabled(index_md: Path, key: str) -> bool:
    """
    Читает блок generate: из front matter _index.md.

        generate:
          pdf: false   # отключить PDF для этого курса
          ai: true

    Если блока или ключа нет — генерация разрешена.
    """
    if not index_md.exists():
        return True
    content = index_md.read_text(encoding="utf-8")

    fm_match = re.match(r"\A---\s*\n(.*?)\n---\s*\n", content, re.DOTALL)
    if not fm_match:
        return True

    block_match = re.search(
        r'^\s{0,8}generate\s*:\s*\n((?:[ \t]+\S[^\n]*\n?)*)',
        fm_match.group(1), re.MULTILINE,
    )
    if not block_match:
        return True

    key_match = re.search(
        rf'^\s+{re.escape(key)}\s*:\s*(true|false|yes|no|1|0)\s*$',
        block_match.group(1), re.MULTILINE | re.IGNORECASE,
    )
    if not key_match:
        return True
    return key_match.group(1).lower() not in ("false", "no", "0")


def find_lecture_dirs(course_dir: Path) -> list[Path]:
    dirs = [
        d for d in course_dir.iterdir()
        if d.is_dir() and re.search(r"\d+", d.name) and d.name not in IGNORE_DIRS
    ]
    dirs.sort(key=natural_sort_key)
    return dirs


def discover_courses(content_base: Path) -> list[str]:
    courses = []
    for d in sorted(content_base.iterdir()):
        if not d.is_dir():
            continue
        has_index = (d / "_index.md").exists()
        has_lectures = any(
            re.search(r"\d+", sub.name)
            for sub in d.iterdir()
            if sub.is_dir() and sub.name not in IGNORE_DIRS
        )
        if has_index and has_lectures:
            courses.append(d.name)
    return courses


# ── сборка тела ───────────────────────────────────────────────────────────────

def build_body_md(course_dir: Path, course_title: str, args, tmp_dir: str) -> str | None:
    """Собирает все лекции курса в один .md для pandoc."""
    md_files = [
        d / "index.md" for d in find_lecture_dirs(course_dir)
        if (d / "index.md").exists()
    ]
    if not md_files:
        return None

    print(f"  Лекций: {len(md_files)}")

    fd, tmp = tempfile.mkstemp(suffix=".md", prefix="pdf_body_", dir=tmp_dir, text=True)
    os.close(fd)

    written = 0
    with open(tmp, "w", encoding="utf-8") as out:
        out.write("---\n")
        out.write(f'title: "{yaml_escape(course_title)}"\n')
        out.write(f'fontsize: "{args.font_size}"\n')
        out.write(f'geometry: "margin={args.margin}"\n')
        out.write('linestretch: "1.3"\n')
        out.write(f'mainfont: "{yaml_escape(args.font_main)}"\n')
        out.write(f'sansfont: "{yaml_escape(args.font_main)}"\n')
        out.write(f'monofont: "{yaml_escape(args.font_mono)}"\n')
        out.write("---\n\n")

        for md_file in md_files:
            raw = md_file.read_text(encoding="utf-8")
            content = convert_obsidian(
                strip_obsidian_header(strip_yaml_frontmatter(raw))
            ).strip()
            if not content:
                print(f"  [WARN] {md_file.parent.name} — пусто после очистки")
                continue
            out.write(content)
            out.write("\n\n\\newpage\n\n")
            written += 1

    return tmp if written else None


# ── pandoc ────────────────────────────────────────────────────────────────────

def render_settings(args) -> dict:
    """Всё, что влияет на внешний вид PDF — входит в хеш курса."""
    return {
        "version":   RENDER_VERSION,
        "engine":    args.pdf_engine,
        "font_main": args.font_main,
        "font_mono": args.font_mono,
        "font_size": args.font_size,
        "margin":    args.margin,
        "toc":       args.toc,
        "toc_depth": args.toc_depth,
        "header":    HEADER_TEX,
    }


def check_tools(engine: str) -> None:
    for tool in ("pandoc", engine):
        try:
            subprocess.run([tool, "--version"], capture_output=True, check=True)
        except (FileNotFoundError, subprocess.CalledProcessError):
            sys.exit(f"{tool} не найден в PATH")


def check_font(name: str) -> bool:
    try:
        r = subprocess.run(["fc-list", ":", "family"], capture_output=True, text=True)
        return name.lower() in r.stdout.lower()
    except FileNotFoundError:
        return True


def write_header_tex(tmp_dir: str) -> str:
    path = os.path.join(tmp_dir, "header.tex")
    with open(path, "w", encoding="utf-8") as f:
        f.write(HEADER_TEX)
    return path


def run_pandoc(body_md: str, output_pdf: str, args, tmp_dir: str, label: str = "") -> bool:
    header_tex = write_header_tex(tmp_dir)
    toc_flags = ["--toc", f"--toc-depth={args.toc_depth}"] if args.toc else []

    cmd = [
        "pandoc", body_md,
        "-o", output_pdf,
        f"--pdf-engine={args.pdf_engine}",
        "--from=markdown+raw_tex+tex_math_dollars",
        f"--include-in-header={header_tex}",
        "--highlight-style=tango",
    ] + toc_flags

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        lines = result.stderr.splitlines()
        important = [l for l in lines if l.startswith(("!", "Error", "l.", "LaTeX Error"))]
        print(f"  [ERROR] pandoc/{args.pdf_engine} {label}:")
        print("\n".join(important[:30] if important else lines[-40:]))
        return False

    for w in [l for l in result.stderr.splitlines() if "Warning" in l][:5]:
        print(f"  [WARN] {w}")

    return True


# ── основная логика ───────────────────────────────────────────────────────────

def generate_course_pdf(course_slug: str, content_base: Path, static_base: Path,
                        args, dry_run: bool) -> bool:
    course_dir = content_base / course_slug
    if not course_dir.exists():
        print(f"[ERROR] Директория курса не найдена: {course_dir}")
        return False

    index_md     = course_dir / "_index.md"
    course_title = read_title_from_md(index_md, course_slug)
    out_pdf      = static_base / course_slug / "resources" / f"{course_slug}_gen.pdf"

    print(f"\n{'='*60}")
    print(f"Курс: {course_title} ({course_slug})")
    print(f"  → {out_pdf}")
    print(f"{'='*60}")

    if not is_generation_enabled(index_md, "pdf"):
        print("  [SKIP] generate.pdf: false в _index.md")
        return True

    salt = salt_hash(render_settings(args))
    course_hash = compute_course_hash(course_dir, salt=salt)

    cached = is_cache_valid("pdf", course_slug, course_hash) and out_pdf.exists()

    if dry_run:
        n = len([d for d in find_lecture_dirs(course_dir) if (d / "index.md").exists()])
        print(f"  [DRY] {'кеш актуален, пропустим' if cached else f'{n} лекций'}")
        return True

    if cached and not args.force:
        print("  [CACHE] Контент не изменился, пропускаем")
        return True

    with tempfile.TemporaryDirectory() as tmp_dir:
        body_md = build_body_md(course_dir, course_title, args, tmp_dir)
        if body_md is None:
            print("  [SKIP] Нет .md файлов с контентом")
            return True

        out_pdf.parent.mkdir(parents=True, exist_ok=True)
        ok = run_pandoc(body_md, str(out_pdf), args, tmp_dir, label=course_slug)

    if ok:
        write_cache("pdf", course_slug, course_hash)
        print(f"  [OK] {out_pdf} ({out_pdf.stat().st_size // 1024} KB)")
    else:
        invalidate_cache("pdf", course_slug)
    return ok


# ── CLI ───────────────────────────────────────────────────────────────────────

def parse_args():
    p = argparse.ArgumentParser(
        description="Генерация PDF-конспектов для курсов Hugo-сайта.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    p.add_argument("courses", nargs="*",
                   help="Слаги курсов. Без аргументов — все курсы.")
    p.add_argument("--content-dir", default=DEFAULTS["content_dir"], dest="content_dir")
    p.add_argument("--static-dir",  default=DEFAULTS["static_dir"],  dest="static_dir")
    p.add_argument("--pdf-engine",  default=DEFAULTS["pdf_engine"],  dest="pdf_engine",
                   help="tectonic / xelatex / lualatex")
    p.add_argument("--font",        default=DEFAULTS["font_main"],   dest="font_main",
                   help="Основной шрифт с кириллицей")
    p.add_argument("--font-mono",   default=DEFAULTS["font_mono"],   dest="font_mono")
    p.add_argument("--font-size",   default=DEFAULTS["font_size"],   dest="font_size")
    p.add_argument("--margin",      default=DEFAULTS["margin"])
    p.add_argument("--no-toc",      action="store_false", dest="toc")
    p.add_argument("--toc-depth",   default=DEFAULTS["toc_depth"], type=int, dest="toc_depth")
    p.add_argument("--jobs", "-j",  type=int, default=min(4, os.cpu_count() or 1),
                   help="Сколько курсов собирать параллельно")
    p.add_argument("--force",       action="store_true", help="Игнорировать кеш")
    p.add_argument("--dry-run",     action="store_true")
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

    if not args.dry_run:
        check_tools(args.pdf_engine)
        if not check_font(args.font_main):
            print(f"[WARN] Шрифт '{args.font_main}' не найден. "
                  f"Попробуйте: Liberation Serif, FreeSerif")

    print(f"Проект:  {project_root}")
    print(f"Content: {content_base}")
    print(f"Static:  {static_base}")
    print(f"Курсы:   {', '.join(courses)}")
    print(f"Движок:  {args.pdf_engine}")
    if args.dry_run:
        print("** DRY RUN — файлы не создаются **")

    def work(slug: str) -> tuple[str, bool]:
        return slug, generate_course_pdf(slug, content_base, static_base, args, args.dry_run)

    # Первый курс — последовательно: на холодном кеше tectonic качает бандл
    # пакетов, параллельный старт даёт гонку за ~/.cache/Tectonic.
    results = [work(courses[0])]
    rest = courses[1:]
    if rest and not args.dry_run:
        jobs = max(1, min(args.jobs, len(rest)))
        with concurrent.futures.ThreadPoolExecutor(max_workers=jobs) as pool:
            results += list(pool.map(work, rest))
    else:
        results += [work(s) for s in rest]

    failed = [slug for slug, ok in results if not ok]

    print("\nГотово!")
    if failed:
        print(f"[WARN] Не удалось: {', '.join(failed)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
