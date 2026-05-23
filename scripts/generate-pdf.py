#!/usr/bin/env python3
"""
generate_pdf.py — генерирует PDF-конспекты для всех курсов Hugo-сайта.

Структура Hugo:
  content/posts/<course>/
    _index.md
    lecture-01/index.md
    lecture-02/index.md
    ...

Вывод:
  static/posts/<course>/resources/<course>_gen.pdf

Использование:
  python scripts/generate-pdf.py                    # все курсы
  python scripts/generate-pdf.py math-stats         # конкретный курс
  python scripts/generate-pdf.py --dry-run
  python scripts/generate-pdf.py --font "PT Serif"
"""

import argparse
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

# cache-utils.py должен лежать рядом со скриптом
sys.path.insert(0, str(Path(__file__).parent))
from cache-utils import compute_course_hash, is_cache_valid, write_cache, invalidate_cache

# ── настройки ─────────────────────────────────────────────────────────────────

DEFAULTS = dict(
    content_dir = "content/posts",
    static_dir  = "static/posts",
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

# Регулярки
YAML_FRONTMATTER_RE = re.compile(r"\A---\s*\n.*?\n---\s*\n", re.DOTALL)
CALLOUT_RE          = re.compile(r"^(>\s*)\[!(\w+)\]\s*(.*)", re.MULTILINE)
WIKILINK_RE         = re.compile(r"\[\[([^\]|]+)(?:\|([^\]]+))?\]\]")
HIGHLIGHT_RE        = re.compile(r"==(.+?)==")
# Hugo shortcodes: {{< ... >}} и {{% ... %}}
SHORTCODE_RE        = re.compile(r"\{\{[<%].*?[>%]\}\}", re.DOTALL)
# Obsidian-шапка: строки ДО первого реального заголовка или текста,
# содержащие только кнопки/теги вида <br>, [[...]], #tag
OBSIDIAN_HEADER_RE  = re.compile(r"<br\s*/?>", re.IGNORECASE)


def natural_sort_key(p: Path) -> list:
    return [int(t) if t.isdigit() else t.lower() for t in re.split(r"(\d+)", str(p))]


def strip_yaml_frontmatter(content: str) -> str:
    """Удаляет YAML frontmatter строго в начале файла."""
    return YAML_FRONTMATTER_RE.sub("", content)


def strip_obsidian_header(content: str) -> str:
    """
    Удаляет Obsidian-шапку (строки до первого <br>) только если
    <br> находится в первых 20 строках — чтобы не резать контент лекций,
    в которых нет такой шапки.
    """
    m = OBSIDIAN_HEADER_RE.search(content)
    if m:
        # Считаем, сколько строк до совпадения
        lines_before = content[:m.start()].count("\n")
        if lines_before <= 20:
            return content[m.end():].lstrip("\n")
    return content


def convert_obsidian(content: str) -> str:
    """Приводит Obsidian-синтаксис к стандартному Markdown."""
    def callout(m):
        prefix, kind, title = m.group(1), m.group(2).upper(), m.group(3).strip()
        return f"{prefix}**{kind}{': ' + title if title else ''}**"
    content = CALLOUT_RE.sub(callout, content)
    content = WIKILINK_RE.sub(lambda m: m.group(2) or m.group(1), content)
    content = HIGHLIGHT_RE.sub(r"**\1**", content)
    content = SHORTCODE_RE.sub("", content)
    return content


def read_title_from_md(md_path: Path, fallback: str) -> str:
    """Читает поле title из front matter."""
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
          pdf: false   # отключить PDF для этого курса
          ai: true     # явно включить (или просто не указывать — дефолт true)

    Если поля нет совсем — генерация разрешена (дефолт = True).
    """
    if not index_md.exists():
        return True
    content = index_md.read_text(encoding="utf-8")

    # Ищем блок generate: внутри YAML frontmatter
    fm_match = re.match(r"\A---\s*\n(.*?)\n---\s*\n", content, re.DOTALL)
    if not fm_match:
        return True
    frontmatter = fm_match.group(1)

    # Ищем вложенный ключ: "  pdf: false" или "  pdf: true"
    pattern = re.compile(
        r'^\s{0,8}generate\s*:\s*\n((?:[ \t]+\S[^\n]*\n?)*)',
        re.MULTILINE,
    )
    block_match = pattern.search(frontmatter)
    if not block_match:
        return True  # блока generate нет — всё генерируем

    block = block_match.group(1)
    key_match = re.search(
        rf'^\s+{re.escape(key)}\s*:\s*(true|false|yes|no|1|0)\s*$',
        block,
        re.MULTILINE | re.IGNORECASE,
    )
    if not key_match:
        return True  # ключ не указан — генерируем

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

def build_body_md(course_dir: Path, course_title: str, args, tmp_dir: str) -> str:
    """Собирает все лекции курса в один .md файл для pandoc."""
    lecture_dirs = find_lecture_dirs(course_dir)
    if not lecture_dirs:
        return ""

    md_files = []
    for ldir in lecture_dirs:
        index = ldir / "index.md"
        if index.exists():
            md_files.append(index)

    if not md_files:
        return ""

    print(f"  Лекций: {len(md_files)}")

    fd, tmp = tempfile.mkstemp(suffix=".md", prefix="pdf_body_", dir=tmp_dir, text=True)
    os.close(fd)

    with open(tmp, "w", encoding="utf-8") as out:
        # YAML front matter для pandoc
        out.write("---\n")
        out.write(f'title: "{course_title}"\n')
        out.write(f'fontsize: "{args.font_size}"\n')
        out.write(f'geometry: "margin={args.margin}"\n')
        out.write( 'linestretch: "1.3"\n')
        out.write(f'mainfont: "{args.font_main}"\n')
        out.write(f'sansfont: "{args.font_main}"\n')
        out.write(f'monofont: "{args.font_mono}"\n')
        out.write("---\n\n")

        for md_file in md_files:
            raw = md_file.read_text(encoding="utf-8")
            content = strip_yaml_frontmatter(raw)
            content = strip_obsidian_header(content)
            content = convert_obsidian(content)
            content = content.strip()
            if not content:
                continue
            out.write(content)
            out.write("\n\n\\newpage\n\n")

    return tmp


# ── LaTeX header ──────────────────────────────────────────────────────────────

def write_header_tex(tmp_dir: str) -> str:
    path = os.path.join(tmp_dir, "header.tex")
    with open(path, "w", encoding="utf-8") as f:
        f.write(r"""\usepackage{polyglossia}
\setdefaultlanguage{russian}
\setotherlanguage{english}
\usepackage{microtype}
\usepackage{booktabs}
\usepackage{longtable}
\usepackage{array}
\usepackage{float}
\usepackage{hyperref}
\hypersetup{colorlinks=true, linkcolor=blue, urlcolor=blue, pdfencoding=auto}
""")
    return path


# ── pandoc ────────────────────────────────────────────────────────────────────

def check_pandoc():
    try:
        subprocess.run(["pandoc", "--version"], capture_output=True, check=True)
    except (FileNotFoundError, subprocess.CalledProcessError):
        sys.exit("pandoc не найден: https://pandoc.org/installing.html")


def check_font(name: str) -> bool:
    try:
        r = subprocess.run(["fc-list", ":", "family"], capture_output=True, text=True)
        return name.lower() in r.stdout.lower()
    except FileNotFoundError:
        return True


def run_pandoc(body_md: str, output_pdf: str, args, tmp_dir: str) -> bool:
    """Запускает pandoc. Возвращает True при успехе."""
    if not check_font(args.font_main):
        print(f"  [WARN] Шрифт '{args.font_main}' не найден. Попробуйте: Liberation Serif, FreeSerif")

    header_tex = write_header_tex(tmp_dir)
    toc_flags = ["--toc", f"--toc-depth={args.toc_depth}"] if args.toc else []

    cmd = [
        "pandoc", body_md,
        "-o", output_pdf,
        "--pdf-engine=xelatex",
        "--from=markdown+raw_tex+tex_math_dollars",
        f"--include-in-header={header_tex}",
        "--highlight-style=tango",
    ] + toc_flags

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        lines = result.stderr.splitlines()
        important = [l for l in lines if l.startswith(("!", "Error", "l.", "LaTeX Error"))]
        print("  [ERROR] pandoc/xelatex:")
        print("\n".join(important[:30] if important else lines[-40:]))
        return False

    for w in [l for l in result.stderr.splitlines() if "Warning" in l][:5]:
        print(f"  [WARN] {w}")

    return True


# ── основная логика ───────────────────────────────────────────────────────────

def generate_course_pdf(
    course_slug: str,
    content_base: Path,
    static_base: Path,
    args,
    dry_run: bool,
) -> bool:
    course_dir = content_base / course_slug
    if not course_dir.exists():
        print(f"[ERROR] Директория курса не найдена: {course_dir}")
        return False

    index_md     = course_dir / "_index.md"
    course_title = read_title_from_md(index_md, course_slug)

    out_dir = static_base / course_slug / "resources"
    out_pdf = out_dir / f"{course_slug}_gen.pdf"

    print(f"\n{'='*60}")
    print(f"Курс: {course_title} ({course_slug})")
    print(f"  → {out_pdf}")
    print(f"{'='*60}")

    if not is_generation_enabled(index_md, "pdf"):
        print("  [SKIP] generate.pdf: false в _index.md")
        return True

    course_hash = compute_course_hash(course_dir)

    if dry_run:
        lecture_dirs = find_lecture_dirs(course_dir)
        md_files = [d / "index.md" for d in lecture_dirs if (d / "index.md").exists()]
        cached = is_cache_valid("pdf", course_slug, course_hash)
        status = "кеш актуален, пропустим" if cached else f"{len(md_files)} лекций"
        print(f"  [DRY] {status} → {out_pdf}")
        return True

    if is_cache_valid("pdf", course_slug, course_hash) and out_pdf.exists():
        print("  [CACHE] Контент не изменился, пропускаем")
        return True

    with tempfile.TemporaryDirectory() as tmp_dir:
        body_md = build_body_md(course_dir, course_title, args, tmp_dir)
        if not body_md:
            print("  [SKIP] Нет .md файлов с контентом")
            return True

        out_dir.mkdir(parents=True, exist_ok=True)
        ok = run_pandoc(body_md, str(out_pdf), args, tmp_dir)

    if ok:
        write_cache("pdf", course_slug, course_hash)
        size_kb = out_pdf.stat().st_size / 1024
        print(f"  [OK] {out_pdf} ({size_kb:.0f} KB)")
    else:
        invalidate_cache("pdf", course_slug)
    return ok


# ── CLI ───────────────────────────────────────────────────────────────────────

def parse_args():
    p = argparse.ArgumentParser(
        description="Генерация PDF-конспектов для всех курсов Hugo-сайта.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    p.add_argument("courses", nargs="*",
                   help="Слаги курсов. Без аргументов — все курсы.")
    p.add_argument("--content-dir", default=DEFAULTS["content_dir"], dest="content_dir")
    p.add_argument("--static-dir",  default=DEFAULTS["static_dir"],  dest="static_dir")
    p.add_argument("--font",      default=DEFAULTS["font_main"],  dest="font_main",
                   help="Основной шрифт с кириллицей")
    p.add_argument("--font-mono", default=DEFAULTS["font_mono"],  dest="font_mono")
    p.add_argument("--font-size", default=DEFAULTS["font_size"],  dest="font_size")
    p.add_argument("--margin",    default=DEFAULTS["margin"])
    p.add_argument("--no-toc",    action="store_false", dest="toc")
    p.add_argument("--toc-depth", default=DEFAULTS["toc_depth"], type=int, dest="toc_depth")
    p.add_argument("--dry-run",   action="store_true")
    return p.parse_args()


def main():
    args = parse_args()
    check_pandoc()

    project_root  = Path.cwd()
    content_base  = project_root / args.content_dir
    static_base   = project_root / args.static_dir

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
        ok = generate_course_pdf(slug, content_base, static_base, args, args.dry_run)
        if not ok:
            failed.append(slug)

    print("\nГотово!")
    if failed:
        print(f"[WARN] Не удалось: {', '.join(failed)}")
        sys.exit(1)


if __name__ == "__main__":
    main()