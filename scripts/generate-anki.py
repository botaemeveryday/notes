#!/usr/bin/env python3
r"""
generate_anki.py — генерация Anki-колод (.apkg) для курсов Hugo-сайта.

Структура Hugo (пример):
  content/posts/<course>/
    _index.md                  ← метаданные курса (title)
    lecture1/
      index.md                 ← метаданные лекции (title)
      resources/
        lecture1.csv           ← карточки: Front, Back
    ...

Вывод (static/):
  static/posts/<course>/
    resources/
      <course>.apkg            ← общая колода с подколодами по лекциям
    lecture1/resources/
      lecture1.apkg            ← колода отдельной лекции
    ...

Зависимости:
  pip install genanki

Использование:
  python scripts/generate_anki.py                    # все курсы
  python scripts/generate_anki.py math-stats         # конкретный курс
  python scripts/generate_anki.py math-stats --dry-run
"""

import argparse
import csv
import hashlib
import os
import re
import sys
from pathlib import Path

# ──────────────────────────────────────────────
# Попытка импорта genanki
# ──────────────────────────────────────────────
try:
    import genanki
except ImportError:
    print("Установите зависимость: pip install genanki")
    sys.exit(1)


# ══════════════════════════════════════════════
# Утилиты
# ══════════════════════════════════════════════

def stable_id(name: str) -> int:
    """Детерминированный числовой ID из строки (для моделей и колод)."""
    h = hashlib.md5(name.encode()).hexdigest()
    return int(h[:8], 16)


def read_title_from_md(md_path: Path, fallback: str) -> str:
    """Читает поле title: из front matter .md файла."""
    if not md_path.exists():
        return fallback
    content = md_path.read_text(encoding="utf-8")
    m = re.search(r"^title\s*[:=]\s*[\"']?(.+?)[\"']?\s*$", content, re.MULTILINE)
    return m.group(1).strip() if m else fallback


def read_csv_cards(csv_path: Path) -> list[tuple[str, str]]:
    """Читает CSV/TSV с колонками Front / Back."""
    if not csv_path.exists():
        print(f"  [WARN] CSV не найден: {csv_path}")
        return []

    with csv_path.open(encoding="utf-8", newline="") as f:
        first_line = f.readline()
        delimiter = '\t' if '\t' in first_line else ','

    cards = []
    with csv_path.open(encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f, delimiter=delimiter)
        for row in reader:
            front = row.get("Front", "").strip()
            back = row.get("Back", "").strip()
            if front:
                cards.append((front, back))
    return cards


# ══════════════════════════════════════════════
# Построение модели Anki (с поддержкой LaTeX)
# ══════════════════════════════════════════════

def make_model(model_name: str) -> genanki.Model:
    r"""
    Модель с двумя полями и поддержкой:
      • Markdown-bold (**текст**) — через CSS
      • LaTeX-формул (\( ... \) и \[ ... \]) — Anki рендерит нативно
    """
    model_id = stable_id(f"model::{model_name}")
    return genanki.Model(
        model_id,
        model_name,
        fields=[
            {"name": "Front"},
            {"name": "Back"},
        ],
        templates=[
            {
                "name": "Card 1",
                "qfmt": "{{Front}}",
                "afmt": "{{FrontSide}}<hr id='answer'>{{Back}}",
            },
        ],
        css="""
.card {
  font-family: "Segoe UI", Arial, sans-serif;
  font-size: 16px;
  text-align: left;
  color: #1a1a1a;
  background: #fff;
  padding: 16px;
  line-height: 1.6;
}
strong, b { color: #2c5282; }
code { background: #edf2f7; padding: 2px 4px; border-radius: 4px; font-size: 0.9em; }
hr { border: none; border-top: 1px solid #e2e8f0; margin: 12px 0; }
""",
    )


# ══════════════════════════════════════════════
# Основная логика
# ══════════════════════════════════════════════

def find_lecture_dirs(course_content_dir: Path) -> list[Path]:
    """Возвращает отсортированный список директорий lecture*."""
    dirs = sorted(
        [d for d in course_content_dir.iterdir()
         if d.is_dir() and re.match(r"lecture-\d+$", d.name)],
        key=lambda d: int(re.search(r"\d+", d.name).group()),
    )
    return dirs


def find_lecture_csv(lecture_dir: Path) -> Path | None:
    """Ищет CSV в resources/ внутри директории лекции."""
    resources = lecture_dir / "resources"
    if not resources.exists():
        return None
    for f in resources.iterdir():
        if f.suffix.lower() == ".csv":
            return f
    return None


def generate_lecture_deck(
    lecture_dir: Path,
    course_name: str,
    course_title: str,
    model: genanki.Model,
    static_base: Path,
    dry_run: bool,
) -> tuple[genanki.Deck | None, str]:
    """
    Генерирует .apkg для одной лекции.
    Возвращает (deck_object, lecture_title) — deck нужен для общей колоды.
    """
    lnum = re.search(r"\d+", lecture_dir.name).group()
    lecture_title_fallback = f"Лекция {lnum}"

    md_path = lecture_dir / "index.md"
    lecture_title = read_title_from_md(md_path, lecture_title_fallback)

    csv_path = find_lecture_csv(lecture_dir)
    if csv_path is None:
        print(f"  [SKIP] {lecture_dir.name}: CSV не найден")
        return None, lecture_title

    cards = read_csv_cards(csv_path)
    if not cards:
        print(f"  [SKIP] {lecture_dir.name}: карточки пусты")
        return None, lecture_title

    # Имя колоды: "Курс::Лекция N"
    deck_name = f"{course_title}::{lecture_title}"
    deck = genanki.Deck(stable_id(deck_name), deck_name)

    for front, back in cards:
        note = genanki.Note(
            model=model,
            fields=[front, back],
            guid=genanki.guid_for(deck_name, front),
        )
        deck.add_note(note)

    # Сохраняем отдельный .apkg
    out_dir = static_base / course_name / lecture_dir.name / "resources"
    apkg_path = out_dir / f"{lecture_dir.name}.apkg"

    if not dry_run:
        out_dir.mkdir(parents=True, exist_ok=True)
        genanki.Package(deck).write_to_file(str(apkg_path))
        print(f"  [OK]   {lecture_dir.name}: {len(cards)} карточек → {apkg_path}")
    else:
        print(f"  [DRY]  {lecture_dir.name}: {len(cards)} карточек → {apkg_path}")

    return deck, lecture_title


def generate_course(
    course_slug: str,
    content_base: Path,
    static_base: Path,
    dry_run: bool,
) -> None:
    """Генерирует колоды для всего курса."""
    course_dir = content_base / course_slug
    if not course_dir.exists():
        print(f"[ERROR] Директория курса не найдена: {course_dir}")
        return

    index_md = course_dir / "_index.md"
    course_title = read_title_from_md(index_md, course_slug)
    print(f"\n{'='*60}")
    print(f"Курс: {course_title} ({course_slug})")
    print(f"{'='*60}")

    model = make_model(f"Model::{course_slug}")
    lecture_dirs = find_lecture_dirs(course_dir)

    if not lecture_dirs:
        print("  [WARN] Директории лекций не найдены")
        return

    all_decks: list[genanki.Deck] = []

    for ldir in lecture_dirs:
        deck, _ = generate_lecture_deck(
            lecture_dir=ldir,
            course_name=course_slug,
            course_title=course_title,
            model=model,
            static_base=static_base,
            dry_run=dry_run,
        )
        if deck is not None:
            all_decks.append(deck)

    if not all_decks:
        print("  [WARN] Нет колод для общего .apkg")
        return

    # Общая колода (корневая)
    master_deck_name = course_title
    master_deck = genanki.Deck(stable_id(master_deck_name), master_deck_name)

    # В Anki иерархия строится через "::" в имени.
    # Все карточки уже добавлены в sub-decks с именем "Курс::Лекция N",
    # поэтому пакуем все колоды вместе — Anki покажет дерево.
    package = genanki.Package([master_deck] + all_decks)

    out_dir = static_base / course_slug / "resources"
    apkg_path = out_dir / f"{course_slug}.apkg"

    if not dry_run:
        out_dir.mkdir(parents=True, exist_ok=True)
        package.write_to_file(str(apkg_path))
        print(f"\n[MASTER] {len(all_decks)} колод → {apkg_path}")
    else:
        print(f"\n[DRY MASTER] {len(all_decks)} колод → {apkg_path}")


def discover_courses(content_base: Path) -> list[str]:
    """Находит все курсы (подпапки с _index.md и хотя бы одной lecture*)."""
    courses = []
    for d in sorted(content_base.iterdir()):
        if not d.is_dir():
            continue
        has_index = (d / "_index.md").exists()
        has_lectures = any(
            re.match(r"lecture-\d+$", sub.name)
            for sub in d.iterdir()
            if sub.is_dir()
        )
        if has_index and has_lectures:
            courses.append(d.name)
    return courses


# ══════════════════════════════════════════════
# CLI
# ══════════════════════════════════════════════

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Генерация Anki-колод (.apkg) из CSV-карточек Hugo-курсов.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "courses",
        nargs="*",
        help="Слаги курсов (например: math-stats). Без аргументов — все курсы.",
    )
    parser.add_argument(
        "--content-dir",
        default="content/posts",
        help="Базовый путь к контенту Hugo (по умолчанию: content/posts)",
    )
    parser.add_argument(
        "--static-dir",
        default="static/posts",
        help="Базовый путь к static Hugo (по умолчанию: static/posts)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Показать, что будет сделано, без создания файлов",
    )
    args = parser.parse_args()

    # Корень проекта — директория, откуда запускается скрипт
    # (предполагается: python scripts/generate_anki.py из корня Hugo-проекта)
    project_root = Path.cwd()
    content_base = project_root / args.content_dir
    static_base = project_root / args.static_dir

    if not content_base.exists():
        print(f"[ERROR] content dir не найден: {content_base}")
        sys.exit(1)

    courses = args.courses if args.courses else discover_courses(content_base)

    if not courses:
        print("[ERROR] Курсы не найдены")
        sys.exit(1)

    print(f"Проект: {project_root}")
    print(f"Content: {content_base}")
    print(f"Static:  {static_base}")
    print(f"Курсы:   {', '.join(courses)}")
    if args.dry_run:
        print("** DRY RUN — файлы не создаются **")

    for slug in courses:
        generate_course(
            course_slug=slug,
            content_base=content_base,
            static_base=static_base,
            dry_run=args.dry_run,
        )

    print("\nГотово!")


if __name__ == "__main__":
    main()