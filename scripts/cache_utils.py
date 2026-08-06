"""
cache_utils.py — утилиты кеширования для скриптов генерации.

Логика:
  - Считаем SHA-256 от входных данных артефакта (+ настроек рендера)
  - Хеш кладём в .cache/<artifact>/<course>.hash
  - При следующем запуске сравниваем: совпал — пропускаем

Структура .cache/:
  .cache/
    pdf/
      cpp-sem1.hash
      math-stats.hash
    ai/
      cpp-sem1.hash
    anki/
      math-stats.hash
    covers/          ← маркеры generate-covers.py
    fonts/           ← скачанные TTF
"""

import hashlib
import json
import re
from pathlib import Path


CACHE_DIR = Path(".cache")

TITLE_RE = re.compile(r'^title\s*[:=]\s*["\']?(.+?)["\']?\s*$', re.MULTILINE)


def _cache_file(artifact: str, course_slug: str) -> Path:
    return CACHE_DIR / artifact / f"{course_slug}.hash"


# ── низкоуровневое ────────────────────────────────────────────────────────────

def salt_hash(payload: dict) -> str:
    """
    Стабильный хеш от словаря настроек рендера (шрифт, поля, версия шаблона).
    Подмешивается в хеш курса: поменял оформление — всё пересобралось.
    """
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, ensure_ascii=False).encode()
    ).hexdigest()


def hash_files(files: list[Path], base: Path | None = None, extra: str = "") -> str:
    """
    SHA-256 от содержимого файлов (отсортированных по пути) + произвольной строки.
    Путь тоже хешируется, чтобы переименование детектировалось.
    """
    h = hashlib.sha256()
    h.update(extra.encode())
    for f in sorted(files, key=str):
        if not f.exists():
            continue
        name = str(f.relative_to(base)) if base else str(f)
        h.update(name.encode())
        h.update(f.read_bytes())
    return h.hexdigest()


# ── специализированное ────────────────────────────────────────────────────────

def compute_course_hash(
    course_dir: Path,
    extra_files: list[Path] | None = None,
    salt: str = "",
) -> str:
    """SHA-256 от всех .md курса + дополнительных файлов + настроек рендера."""
    files = list(course_dir.rglob("*.md"))
    if extra_files:
        files += list(extra_files)
    return hash_files(files, base=course_dir, extra=salt)


def compute_anki_hash(course_dir: Path, csv_files: list[Path]) -> str:
    """
    Хеш для Anki: только CSV-карточки + строки title: из .md (имена колод).

    Тексты лекций сюда намеренно не входят — правка абзаца в конспекте
    не должна пересобирать колоды.
    """
    h = hashlib.sha256()
    for f in sorted(csv_files, key=str):
        if not f.exists():
            continue
        h.update(str(f.relative_to(course_dir)).encode())
        h.update(f.read_bytes())
    for md in sorted(course_dir.rglob("*.md"), key=str):
        m = TITLE_RE.search(md.read_text(encoding="utf-8"))
        h.update(str(md.relative_to(course_dir)).encode())
        h.update((m.group(1).strip() if m else "").encode())
    return h.hexdigest()


# ── чтение/запись кеша ────────────────────────────────────────────────────────

def is_cache_valid(artifact: str, course_slug: str, current_hash: str) -> bool:
    """Возвращает True, если кеш актуален (хеш совпадает)."""
    cf = _cache_file(artifact, course_slug)
    if not cf.exists():
        return False
    return cf.read_text().strip() == current_hash


def write_cache(artifact: str, course_slug: str, current_hash: str) -> None:
    """Сохраняет хеш в кеш после успешной генерации."""
    cf = _cache_file(artifact, course_slug)
    cf.parent.mkdir(parents=True, exist_ok=True)
    cf.write_text(current_hash)


def invalidate_cache(artifact: str, course_slug: str) -> None:
    """Принудительно инвалидирует кеш (напр. при ошибке генерации)."""
    cf = _cache_file(artifact, course_slug)
    if cf.exists():
        cf.unlink()
