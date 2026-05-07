#!/usr/bin/env python3
"""
merge_md_for_ai.py — объединяет Obsidian-лекции в один MD файл для ИИ.

Особенности:
    - Удаляет YAML frontmatter (--- ... ---) в начале каждого файла
    - Удаляет содержимое ДО первого <br> (шапка Obsidian с кнопками)
    - Удаляет снабжения Obsidian (callouts, wikilinks, ==highlight==)
    - Добавляет разделители между файлами
    - Сохраняет иерархию заголовков

Использование:
    python merge_md_for_ai.py
    python merge_md_for_ai.py --input ./docs --output merged.md
    python merge_md_for_ai.py --no-convert  # без конвертации Obsidian-синтаксиса
"""

import argparse
import re
from pathlib import Path
from typing import List

# ── настройки по умолчанию ────────────────────────────────────────────────────

DEFAULTS = dict(
    input_dir=".",
    output_file="../merged_for_ai.md",
    convert_obsidian=True,
    add_separators=True,
    separator="---",
    verbose=True,
)

IGNORE_DIRS = {
    ".venv", "venv", "env", "__pycache__", "node_modules",
    ".git", ".idea", ".vscode", "site-packages", "dist-info", "lib",
    "assets", "images", "img", "files", "attachments",
}

CUT_RE = re.compile(r"<br\s*/?>", re.IGNORECASE)
YAML_RE = re.compile(r"^---\s*\n(.*?\n)---\s*\n", re.DOTALL | re.MULTILINE)
CALLOUT_RE = re.compile(r"^(>\s*)\[!(\w+)\]\s*(.*)", re.MULTILINE)
WIKILINK_RE = re.compile(r"\[\[([^\]|]+)(?:\|([^\]]+))?\]\]")
HIGHLIGHT_RE = re.compile(r"==(.+?)==")


# ── утилиты ───────────────────────────────────────────────────────────────────

def natural_sort_key(p: Path) -> list:
    """Натуральная сортировка (lecture1, lecture2, ..., lecture10)"""
    return [int(t) if t.isdigit() else t.lower() for t in re.split(r"(\d+)", str(p))]


def should_ignore(path: Path) -> bool:
    """Проверяет, нужно ли игнорировать папку/файл"""
    return any(part in IGNORE_DIRS for part in path.parts)


def find_md_files(root: Path) -> List[Path]:
    """Находит все .md файлы, рекурсивно, с сортировкой"""
    files = [f for f in root.rglob("*.md") if not should_ignore(f)]
    files.sort(key=natural_sort_key)
    return files


def strip_yaml_frontmatter(content: str) -> str:
    """Удаляет YAML frontmatter (--- ... ---) в начале файла"""
    return YAML_RE.sub("", content)


def strip_obsidian_header(content: str) -> str:
    """Удаляет всё до первого <br> — шапку Obsidian с кнопками"""
    m = CUT_RE.search(content)
    return content[m.end():].lstrip("\n") if m else content


def convert_obsidian_syntax(content: str) -> str:
    """Преобразует Obsidian-синтаксис в читаемый текст"""

    # Callouts: > [!NOTE] Title → > NOTE: Title
    def replace_callout(m):
        prefix, kind, title = m.group(1), m.group(2).upper(), m.group(3).strip()
        label = f"{kind}{': ' + title if title else ''}"
        return f"{prefix}{label}"

    content = CALLOUT_RE.sub(replace_callout, content)

    # Wikilinks: [[Page|Alias]] → Alias; [[Page]] → Page
    content = WIKILINK_RE.sub(lambda m: m.group(2) or m.group(1), content)

    # Highlight: ==text== → text (просто убираем маркеры)
    content = HIGHLIGHT_RE.sub(r"\1", content)

    return content


def clean_content(content: str, convert_obsidian: bool) -> str:
    """Полная очистка файла"""
    # 1. Удаляем YAML
    content = strip_yaml_frontmatter(content)

    # 2. Удаляем шапку до <br>
    content = strip_obsidian_header(content)

    # 3. Конвертируем Obsidian-синтаксис (опционально)
    if convert_obsidian:
        content = convert_obsidian_syntax(content)

    # 4. Убираем лишние пустые строки в начале и конце
    content = content.strip()

    return content


def get_file_info(file_path: Path, root_dir: Path) -> dict:
    """Возвращает информацию о файле для комментария"""
    rel_path = file_path.relative_to(root_dir)
    return {
        "name": file_path.stem,
        "path": str(rel_path),
        "parent": str(rel_path.parent) if rel_path.parent != Path(".") else "",
    }


# ── основная функция объединения ─────────────────────────────────────────────

def merge_markdown_files(
        input_dir: Path,
        output_file: Path,
        convert_obsidian: bool = True,
        add_separators: bool = True,
        separator: str = "---",
        add_metadata_comments: bool = True,
        verbose: bool = True,
) -> None:
    """
    Объединяет все .md файлы в один.

    Args:
        input_dir: Папка с исходными .md файлами
        output_file: Выходной файл
        convert_obsidian: Преобразовывать ли Obsidian-синтаксис
        add_separators: Добавлять ли разделители между файлами
        separator: Строка-разделитель
        add_metadata_comments: Добавлять ли комментарии с путём к файлу
        verbose: Показывать ли прогресс
    """
    md_files = find_md_files(input_dir)

    if not md_files:
        print(f"❌  Не найдено .md файлов в {input_dir}")
        return

    if verbose:
        print(f"📂  Найдено файлов: {len(md_files)}")
        for f in md_files:
            print(f"    • {f.relative_to(input_dir)}")

    with open(output_file, "w", encoding="utf-8") as out:
        out.write(f"# Объединённый контекст\n\n")
        out.write(f"**Источник:** {input_dir}\n")
        out.write(f"**Количество файлов:** {len(md_files)}\n")
        out.write(f"**Обработка:** убраны YAML, шапки Obsidian")
        if convert_obsidian:
            out.write(", конвертирован Obsidian-синтаксис\n\n")
        else:
            out.write("\n\n")

        for i, md_file in enumerate(md_files, 1):
            try:
                raw = md_file.read_text(encoding="utf-8")
                content = clean_content(raw, convert_obsidian)

                if not content:
                    if verbose:
                        print(f"  ⚠️  {md_file.relative_to(input_dir)} — пустой после очистки")
                    continue

                if add_metadata_comments:
                    info = get_file_info(md_file, input_dir)
                    out.write(f"\n<!-- ============================================ -->\n")
                    out.write(f"<!-- Файл: {info['path']} -->\n")
                    if info['parent']:
                        out.write(f"<!-- Папка: {info['parent']} -->\n")
                    out.write(f"<!-- ============================================ -->\n\n")

                out.write(content)

                if add_separators and i < len(md_files):
                    out.write(f"\n\n{separator}\n\n")

                if verbose:
                    print(f"  ✓ {md_file.relative_to(input_dir)}")

            except Exception as e:
                print(f"  ❌ Ошибка при обработке {md_file}: {e}")

    if verbose:
        output_size = output_file.stat().st_size
        size_kb = output_size / 1024
        size_mb = size_kb / 1024

        if size_mb >= 1:
            size_str = f"{size_mb:.2f} MB"
        else:
            size_str = f"{size_kb:.1f} KB"

        print(f"\n✅  Готово: {output_file}")
        print(f"   Размер: {size_str}")
        print(f"   Файлов обработано: {len(md_files)}")


# ── CLI ───────────────────────────────────────────────────────────────────────

def parse_args():
    parser = argparse.ArgumentParser(
        description="Объединяет все .md файлы из папки в один файл для контекста ИИ",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--input", "-i",
        default=DEFAULTS["input_dir"],
        dest="input_dir",
        help="Папка с .md файлами"
    )
    parser.add_argument(
        "--output", "-o",
        default=DEFAULTS["output_file"],
        dest="output_file",
        help="Выходной файл (объединённый)"
    )
    parser.add_argument(
        "--no-convert",
        action="store_false",
        dest="convert_obsidian",
        help="НЕ конвертировать Obsidian-синтаксис (оставить [[wikilinks]] и ==highlight==)"
    )
    parser.add_argument(
        "--no-separators",
        action="store_false",
        dest="add_separators",
        help="Не добавлять разделители между файлами"
    )
    parser.add_argument(
        "--no-metadata",
        action="store_false",
        dest="add_metadata",
        help="Не добавлять комментарии с путём к файлу"
    )
    parser.add_argument(
        "--quiet", "-q",
        action="store_true",
        dest="quiet",
        help="Минимум вывода"
    )

    return parser.parse_args()


def main():
    args = parse_args()

    input_dir = Path(args.input_dir).resolve()
    output_file = Path(args.output_file).resolve()

    if not input_dir.is_dir():
        print(f"❌  Папка не найдена: {input_dir}")
        return

    merge_markdown_files(
        input_dir=input_dir,
        output_file=output_file,
        convert_obsidian=args.convert_obsidian,
        add_separators=args.add_separators,
        separator="---",
        add_metadata_comments=args.add_metadata,
        verbose=not args.quiet,
    )


if __name__ == "__main__":
    main()