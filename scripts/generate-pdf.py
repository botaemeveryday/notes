#!/usr/bin/env python3
"""
md_to_pdf.py — собирает Obsidian-лекции в PDF.

Итоговый порядок страниц:
    1. Титульная страница  (из cover.tex рядом со скриптом)
    2. Оглавление          (из # заголовков внутри лекций)
    3. Содержание лекций

Редактирование титульника:
    Открой cover.tex рядом со скриптом — это обычный LaTeX.
    Меняй текст внутри, структуру трогать не нужно.

Использование:
    python md_to_pdf.py
    python md_to_pdf.py --input ./docs --output book.pdf
    python md_to_pdf.py --font "PT Serif" --no-toc
"""

import argparse
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import List, Optional

# ── настройки ─────────────────────────────────────────────────────────────────

SCRIPT_DIR = Path(__file__).parent

DEFAULTS = dict(
    input_dir = ".",
    output_pdf = "result.pdf",
    font_main  = "DejaVu Serif",
    font_mono  = "DejaVu Sans Mono",
    font_size  = "11pt",
    margin     = "2.5cm",
    toc        = True,
    toc_depth  = 3,
)

IGNORE_DIRS = {
    ".venv", "venv", "env", "__pycache__", "node_modules",
    ".git", ".idea", ".vscode", "site-packages", "dist-info", "lib",
}

CUT_RE       = re.compile(r"<br\s*/?>", re.IGNORECASE)
CALLOUT_RE   = re.compile(r"^(>\s*)\[!(\w+)\]\s*(.*)", re.MULTILINE)
WIKILINK_RE  = re.compile(r"\[\[([^\]|]+)(?:\|([^\]]+))?\]\]")
HIGHLIGHT_RE = re.compile(r"==(.+?)==")

# ── утилиты ───────────────────────────────────────────────────────────────────

def natural_sort_key(p: Path) -> list:
    return [int(t) if t.isdigit() else t.lower() for t in re.split(r"(\d+)", str(p))]

def should_ignore(path: Path) -> bool:
    return any(part in IGNORE_DIRS for part in path.parts)

def find_md_files(root: Path) -> List[Path]:
    files = [f for f in root.rglob("*.md") if not should_ignore(f)]
    files.sort(key=natural_sort_key)
    return files

def strip_obsidian_header(content: str) -> str:
    m = CUT_RE.search(content)
    return content[m.end():].lstrip("\n") if m else content

def strip_yaml_frontmatter(content: str) -> str:
    if content.startswith("---"):
        end = content.find("\n---", 3)
        if end != -1:
            return content[end + 4:].lstrip("\n")
    return content

def convert_obsidian(content: str) -> str:
    def callout(m):
        prefix, kind, title = m.group(1), m.group(2).upper(), m.group(3).strip()
        return f"{prefix}**{kind}{': ' + title if title else ''}**"
    content = CALLOUT_RE.sub(callout, content)
    content = WIKILINK_RE.sub(lambda m: m.group(2) or m.group(1), content)
    content = HIGHLIGHT_RE.sub(r"**\1**", content)
    return content

# ── титульник ─────────────────────────────────────────────────────────────────

def get_cover_tex(tmp_dir: str) -> str:
    """
    Возвращает путь к cover.tex для --include-before-body.
    Передача через --include-before-body гарантирует что титульник идёт
    ДО оглавления — в отличие от вставки в тело markdown-файла,
    где pandoc всё равно рендерит --toc первым.
    """
    cover_src = SCRIPT_DIR / "cover.tex"
    if cover_src.exists():
        print(f"Титульник: {cover_src}")
        return str(cover_src)

    print(f"cover.tex не найден в {SCRIPT_DIR} — используется заглушка.")
    print("Создай cover.tex рядом со скриптом для своего титульника.")
    fallback = os.path.join(tmp_dir, "cover_fallback.tex")
    with open(fallback, "w", encoding="utf-8") as f:
        f.write(r"""\begin{titlepage}
\begin{center}
\vspace*{4cm}
{\Huge\bfseries Документ}\\[1cm]
{\large Создай cover.tex рядом со скриптом}
\end{center}
\end{titlepage}
""")
    return fallback

# ── сборка тела ───────────────────────────────────────────────────────────────

def build_body_md(input_dir: Path, args) -> str:
    """
    Собирает только ТЕЛО документа (лекции) в один .md файл.
    Титульник идёт отдельно через --include-before-body.
    YAML frontmatter здесь задаёт шрифты и геометрию.
    """
    md_files = find_md_files(input_dir)
    if not md_files:
        sys.exit("Не найдено ни одного .md файла.")

    print(f"Найдено файлов: {len(md_files)}")
    for f in md_files:
        print(f"    * {f.relative_to(input_dir)}")

    fd, tmp = tempfile.mkstemp(suffix=".md", prefix="md2pdf_", text=True)
    os.close(fd)

    with open(tmp, "w", encoding="utf-8") as out:
        out.write("---\n")
        out.write(f'fontsize: "{args.font_size}"\n')
        out.write(f'geometry: "margin={args.margin}"\n')
        out.write( 'linestretch: "1.3"\n')
        out.write(f'mainfont: "{args.font_main}"\n')
        out.write(f'sansfont: "{args.font_main}"\n')
        out.write(f'monofont: "{args.font_mono}"\n')
        out.write("---\n\n")

        for md_file in md_files:
            rel = md_file.relative_to(input_dir)
            print(f"  -> {rel}")
            raw = md_file.read_text(encoding="utf-8")
            content = strip_obsidian_header(raw)
            content = strip_yaml_frontmatter(content)
            content = convert_obsidian(content)
            if not content.strip():
                continue
            out.write(content.strip())
            out.write("\n\n")

    return tmp

# ── LaTeX header (polyglossia) ────────────────────────────────────────────────

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

def run_pandoc(body_md: str, cover_tex: str, output: str, args, tmp_dir: str):
    if not check_font(args.font_main):
        print(f"Шрифт '{args.font_main}' не найден. Попробуйте: Liberation Serif, FreeSerif, PT Serif")

    header_tex = write_header_tex(tmp_dir)

    toc_flags = ["--toc", f"--toc-depth={args.toc_depth}"] if args.toc else []

    cmd = [
        "pandoc", body_md,
        "-o", output,
        "--pdf-engine=xelatex",
        "--from=markdown+raw_tex+tex_math_dollars",
        f"--include-in-header={header_tex}",
        f"--include-before-body={cover_tex}",
        "--highlight-style=tango",
    ] + toc_flags

    print("\nЗапускаю pandoc + xelatex...")
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        lines = result.stderr.splitlines()
        important = [l for l in lines if l.startswith(("!", "Error", "l.", "LaTeX Error"))]
        print("Ошибка:\n" + "\n".join(important[:40] if important else lines[-60:]))
        print("\n-- Первые 80 строк тела MD (диагностика) --")
        with open(body_md, encoding="utf-8") as f:
            for i, line in enumerate(f):
                if i >= 80:
                    break
                print(f"{i+1:3}: {line}", end="")
        sys.exit(1)

    for w in [l for l in result.stderr.splitlines() if "Warning" in l][:10]:
        print(f"   Warning: {w}")

# ── CLI ───────────────────────────────────────────────────────────────────────

def parse_args():
    p = argparse.ArgumentParser(
        description="Obsidian Markdown -> PDF (XeLaTeX, русский).",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    p.add_argument("--input",     default=DEFAULTS["input_dir"],  dest="input_dir")
    p.add_argument("--output",    default=DEFAULTS["output_pdf"], dest="output_pdf")
    p.add_argument("--font",      default=DEFAULTS["font_main"],  dest="font_main",
                   help="Основной шрифт с кириллицей")
    p.add_argument("--font-mono", default=DEFAULTS["font_mono"],  dest="font_mono")
    p.add_argument("--font-size", default=DEFAULTS["font_size"],  dest="font_size")
    p.add_argument("--margin",    default=DEFAULTS["margin"])
    p.add_argument("--no-toc",    action="store_false", dest="toc")
    p.add_argument("--toc-depth", default=DEFAULTS["toc_depth"],  type=int, dest="toc_depth")
    return p.parse_args()

# ── main ──────────────────────────────────────────────────────────────────────

def main():
    args = parse_args()
    check_pandoc()

    input_dir  = Path(args.input_dir).resolve()
    output_pdf = str(Path(args.output_pdf).resolve())

    if not input_dir.is_dir():
        sys.exit(f"Папка не найдена: {input_dir}")

    body_md = build_body_md(input_dir, args)
    try:
        with tempfile.TemporaryDirectory() as tmp_dir:
            cover_tex = get_cover_tex(tmp_dir)
            run_pandoc(body_md, cover_tex, output_pdf, args, tmp_dir)
    finally:
        if os.path.exists(body_md):
            os.unlink(body_md)

    print(f"\nГотово: {output_pdf}")

if __name__ == "__main__":
    main()