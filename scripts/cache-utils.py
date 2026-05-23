"""
cache-utils.py — утилиты кеширования для скриптов генерации.

Логика:
  - Считаем SHA-256 от всех входных файлов курса (отсортированных по пути)
  - Хеш кладём в .cache/<artifact>/<course>.hash
  - При следующем запуске сравниваем: совпал — пропускаем

Структура .cache/:
  .cache/
    pdf/
      cpp-sem1.hash
      math-stats.hash
      ...
    ai/
      cpp-sem1.hash
      ...
    anki/
      math-stats.hash
      ...
"""

import hashlib
from pathlib import Path


CACHE_DIR = Path(".cache")


def _cache_file(artifact: str, course_slug: str) -> Path:
    return CACHE_DIR / artifact / f"{course_slug}.hash"


def compute_course_hash(course_dir: Path, extra_files: list[Path] | None = None) -> str:
    """
    Считает SHA-256 от содержимого всех .md файлов курса
    (включая _index.md) + опциональных дополнительных файлов (напр. CSV).

    Файлы сортируются по пути — порядок детерминирован.
    """
    h = hashlib.sha256()

    files = sorted(course_dir.rglob("*.md"), key=lambda p: str(p))
    if extra_files:
        files += sorted(extra_files, key=lambda p: str(p))

    for f in files:
        if f.exists():
            # Хешируем путь + содержимое, чтобы переименование тоже детектировалось
            h.update(str(f.relative_to(course_dir)).encode())
            h.update(f.read_bytes())

    return h.hexdigest()


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