#!/usr/bin/env python3
"""
generate-covers.py — generate OG/Twitter cover images for Hugo lecture site.

Walks content/posts/<course>/<lecture>/index.md and reads frontmatter,
also reads content/posts/<course>/_index.md for the course accent color.
Produces 1200x630 PNG covers into static/covers/<course>/<lecture>.png
(plus static/covers/<course>/index.png for the course landing).

Hugo serves anything in static/ from site root, so the public URL will be
/covers/<course>/<lecture>.png — perfect for og:image / twitter:image meta tags.

USAGE:
    python scripts/generate-covers.py               # generate everything (cached)
    python scripts/generate-covers.py --force       # regenerate all
    python scripts/generate-covers.py --only operation-systems/lecture-01
    python scripts/generate-covers.py --dry-run     # show what would be generated
    python scripts/generate-covers.py --preview operation-systems/lecture-01
        # generate one cover into ./preview-out/ without touching static/

REQUIREMENTS:
    pip install Pillow pyyaml requests

EXIT CODES:
    0 — success
    1 — fatal error (missing dirs, broken yaml, etc.)
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

try:
    import yaml
except ImportError:
    sys.exit("Need PyYAML: pip install pyyaml")

try:
    from PIL import Image, ImageDraw, ImageFont, ImageFilter
except ImportError:
    sys.exit("Need Pillow: pip install Pillow")


# --- paths ---------------------------------------------------------------

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent              # repo root (scripts/ sits in root)
CONTENT_DIR = PROJECT_ROOT / "content" / "posts"
STATIC_OUT = PROJECT_ROOT / "static" / "covers"
CACHE_DIR = PROJECT_ROOT / ".cache" / "covers"
FONT_CACHE = PROJECT_ROOT / ".cache" / "fonts"


# --- design constants ----------------------------------------------------

W, H = 1200, 630
BG = "#0d0e12"
FG = "#f5f5f7"
DIM = "#c8c8d0"
META_DIM = "#9a9aa3"

# Accent palette by index (matches a typical Hugo theme convention 1..8).
# If your theme uses different colors, tweak this map.
ACCENT_COLORS = {
    1: "#e85d75",
    2: "#f5a623",
    3: "#f8d57e",
    4: "#7ed957",
    5: "#5b8def",
    6: "#9b6dff",
    7: "#ff6dc4",
    8: "#4ecdc4",
}
DEFAULT_ACCENT = 5

# Inter has great cyrillic coverage. We grab static TTFs from Google Fonts'
# GitHub repo (most reliable mirror). Multiple sources per font for resilience.
FONTS = {
    "regular": ("Inter-Regular.ttf", [
        "https://github.com/google/fonts/raw/main/ofl/inter/Inter%5Bopsz%2Cwght%5D.ttf",
        "https://github.com/rsms/inter/raw/master/docs/font-files/Inter-Regular.ttf",
    ]),
    "bold": ("Inter-Bold.ttf", [
        # Bold variant — we'll use the same variable file but render bold via the font.
        # If you prefer a separate static Bold TTF, use the rsms mirror.
        "https://github.com/rsms/inter/raw/master/docs/font-files/Inter-Bold.ttf",
    ]),
    "mono": ("JetBrainsMono-Bold.ttf", [
        "https://github.com/JetBrains/JetBrainsMono/raw/master/fonts/ttf/JetBrainsMono-Bold.ttf",
        "https://github.com/google/fonts/raw/main/ofl/jetbrainsmono/JetBrainsMono%5Bwght%5D.ttf",
    ]),
}

# Fallback fonts shipped with most Linux distros, used if download fails.
FALLBACK_FONTS = {
    "regular": "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "bold": "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "mono": "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf",
}


# --- frontmatter ---------------------------------------------------------

FM_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)


def read_frontmatter(path: Path) -> Optional[dict]:
    """Parse YAML frontmatter. Returns:
      - dict (possibly empty) if parsed successfully
      - None if no frontmatter block was found at all
      - raises ValueError if frontmatter exists but YAML is broken
    """
    # `utf-8-sig` transparently strips a BOM (\ufeff) if present.
    text = path.read_text(encoding="utf-8-sig")
    # Also tolerate stray leading whitespace/blank lines before the opening ---.
    text = text.lstrip()
    m = FM_RE.match(text)
    if not m:
        return None
    try:
        return yaml.safe_load(m.group(1)) or {}
    except yaml.YAMLError as e:
        raise ValueError(f"broken YAML in {path}: {e}") from e


# --- font loading --------------------------------------------------------

def ensure_fonts() -> dict[str, str]:
    """Download Inter + JetBrainsMono if missing, return paths.

    Tries multiple URLs per font, falls back to system DejaVu if all fail.
    """
    FONT_CACHE.mkdir(parents=True, exist_ok=True)
    paths: dict[str, str] = {}
    for key, (fname, urls) in FONTS.items():
        target = FONT_CACHE / fname
        if target.exists() and target.stat().st_size > 1000:
            paths[key] = str(target)
            continue

        import urllib.request
        got = False
        for url in urls:
            try:
                print(f"  downloading {fname} from {url.split('/')[2]} ...")
                req = urllib.request.Request(url, headers={"User-Agent": "covers/1.0"})
                with urllib.request.urlopen(req, timeout=20) as r:
                    data = r.read()
                if len(data) < 1000:
                    raise RuntimeError(f"suspiciously small file ({len(data)} bytes)")
                target.write_bytes(data)
                got = True
                break
            except Exception as e:
                print(f"    failed: {e}", file=sys.stderr)
                continue

        if got:
            paths[key] = str(target)
        else:
            fb = FALLBACK_FONTS[key]
            if not Path(fb).exists():
                sys.exit(
                    f"No font available for '{key}' (downloads failed and fallback "
                    f"missing: {fb}). Install fonts-dejavu or place a TTF at {target}."
                )
            print(f"  !! using fallback {fb} for {key}", file=sys.stderr)
            paths[key] = fb
    return paths


# --- data model ----------------------------------------------------------

@dataclass
class Course:
    slug: str
    title: str
    description: str
    accent: int


@dataclass
class Lecture:
    course_slug: str
    slug: str                 # e.g. "lecture-01"
    number: str               # e.g. "01"
    title: str
    description: str
    path: Path                # path to index.md


def parse_lecture_number(slug: str) -> str:
    """Extract numeric part from slug like 'lecture-01' or 'interpreter-3'."""
    m = re.search(r"(\d+)$", slug)
    if not m:
        return ""
    n = int(m.group(1))
    return f"{n:02d}"


def load_course(course_dir: Path) -> Optional[Course]:
    idx = course_dir / "_index.md"
    if not idx.exists():
        print(f"  skip course {course_dir.name}: no _index.md", file=sys.stderr)
        return None
    try:
        fm = read_frontmatter(idx)
    except ValueError as e:
        print(f"  !! skip course {course_dir.name}: {e}", file=sys.stderr)
        return None
    if fm is None:
        print(
            f"  !! skip course {course_dir.name}: no YAML frontmatter found in "
            f"{idx} (check for BOM, missing ---, or wrong file encoding)",
            file=sys.stderr,
        )
        return None
    if "title" not in fm:
        print(f"  !! skip course {course_dir.name}: no 'title' in frontmatter", file=sys.stderr)
        return None
    return Course(
        slug=course_dir.name,
        title=str(fm.get("title", course_dir.name)),
        description=str(fm.get("description", "")),
        accent=int(fm.get("accent", DEFAULT_ACCENT)),
    )


def load_lectures(course: Course) -> list[Lecture]:
    course_dir = CONTENT_DIR / course.slug
    lectures = []
    for sub in sorted(course_dir.iterdir()):
        if not sub.is_dir():
            continue
        idx = sub / "index.md"
        if not idx.exists():
            continue
        try:
            fm = read_frontmatter(idx)
        except ValueError as e:
            print(f"  !! skip {course.slug}/{sub.name}: {e}", file=sys.stderr)
            continue
        if fm is None:
            print(
                f"  !! skip {course.slug}/{sub.name}: no YAML frontmatter "
                f"(check for BOM or missing ---)",
                file=sys.stderr,
            )
            continue
        if "title" not in fm:
            print(f"  !! skip {course.slug}/{sub.name}: no 'title' in frontmatter", file=sys.stderr)
            continue
        lectures.append(Lecture(
            course_slug=course.slug,
            slug=sub.name,
            number=parse_lecture_number(sub.name),
            title=str(fm.get("title", sub.name)),
            description=str(fm.get("description", "")),
            path=idx,
        ))
    return lectures


# --- drawing -------------------------------------------------------------

def hex_to_rgb(h: str) -> tuple[int, int, int]:
    h = h.lstrip("#")
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))  # type: ignore[return-value]


def font(path: str, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(path, size)


def text_w(draw: ImageDraw.ImageDraw, text: str, fnt: ImageFont.FreeTypeFont) -> int:
    bbox = draw.textbbox((0, 0), text, font=fnt)
    return bbox[2] - bbox[0]


def wrap_text(
    draw: ImageDraw.ImageDraw,
    text: str,
    fnt: ImageFont.FreeTypeFont,
    max_width: int,
    max_lines: int = 2,
) -> list[str]:
    if not text:
        return []
    words = text.split()
    lines: list[str] = []
    cur = ""
    for w in words:
        test = (cur + " " + w).strip()
        if text_w(draw, test, fnt) > max_width and cur:
            lines.append(cur)
            cur = w
            if len(lines) == max_lines:
                # truncate remainder into last line with ellipsis
                last = lines[-1]
                while text_w(draw, last + "…", fnt) > max_width and last:
                    last = last[:-1].rstrip()
                lines[-1] = last + "…"
                return lines
        else:
            cur = test
    if cur and len(lines) < max_lines:
        lines.append(cur)
    return lines


def fit_title(
    draw: ImageDraw.ImageDraw,
    text: str,
    font_path: str,
    max_width: int,
    start_size: int = 120,
    min_size: int = 56,
) -> tuple[ImageFont.FreeTypeFont, list[str]]:
    """Find largest size where title fits in 1 line, else in 2 lines, else truncate.

    Returns (font, lines). Caller draws each line at line height.
    """
    # 1) Try to fit on a single line.
    size = start_size
    while size >= min_size:
        f = font(font_path, size)
        if text_w(draw, text, f) <= max_width:
            return f, [text]
        size -= 4

    # 2) Try 2 lines at progressively smaller sizes.
    size = start_size - 16
    while size >= min_size:
        f = font(font_path, size)
        lines = wrap_text(draw, text, f, max_width, max_lines=2)
        if lines and all(text_w(draw, ln, f) <= max_width for ln in lines):
            return f, lines
        size -= 4

    # 3) Last resort: smallest size with truncation.
    f = font(font_path, min_size)
    lines = wrap_text(draw, text, f, max_width, max_lines=2)
    return f, lines or [text]


def make_gradient(accent: str) -> Image.Image:
    """Create the variant-B gradient: dark base, radial-ish blend toward bottom-right."""
    ar, ag, ab = hex_to_rgb(accent)
    br, bg, bb = hex_to_rgb(BG)

    # Build a small image then upscale — fast and smooth.
    small_w, small_h = 240, 126
    g = Image.new("RGB", (small_w, small_h), BG)
    px = g.load()
    diag = math.sqrt(2)
    for y in range(small_h):
        for x in range(small_w):
            dx = (small_w - x) / small_w
            dy = (small_h - y) / small_h
            d = math.sqrt(dx * dx + dy * dy) / diag
            t = max(0.0, 1.0 - d) * 0.38     # 38% accent blend at corner
            r = int(br * (1 - t) + ar * t)
            gg = int(bg * (1 - t) + ag * t)
            b = int(bb * (1 - t) + ab * t)
            px[x, y] = (r, gg, b)
    return g.resize((W, H), Image.BICUBIC).filter(ImageFilter.GaussianBlur(2))


def render_cover(
    title: str,
    description: str,
    subject: str,
    lecture_num: str,
    accent_idx: int,
    fonts: dict[str, str],
    out_path: Path,
) -> None:
    accent = ACCENT_COLORS.get(accent_idx, ACCENT_COLORS[DEFAULT_ACCENT])
    img = make_gradient(accent)
    draw = ImageDraw.Draw(img)

    PAD_X = 80
    HEADER_Y = 80
    FOOTER_Y = H - 90       # baseline-ish for footer text
    CONTENT_TOP = 180       # top of the title/description block
    CONTENT_BOTTOM = H - 130  # leave space above footer

    # --- header row -----------------------------------------------------
    if lecture_num:
        f_num = font(fonts["mono"], 28)
        draw.text((PAD_X, HEADER_Y), f"L.{lecture_num}", fill=accent, font=f_num)

    if subject:
        f_subj = font(fonts["bold"], 24)
        sw = text_w(draw, subject, f_subj)
        sx = W - PAD_X - sw
        draw.text((sx, HEADER_Y + 6), subject, fill=FG, font=f_subj)
        draw.rectangle([(sx, HEADER_Y + 42), (sx + sw, HEADER_Y + 45)], fill=accent)

    # --- title (with optional wrap) -------------------------------------
    max_title_w = W - 2 * PAD_X
    f_title, title_lines = fit_title(draw, title, fonts["bold"], max_title_w)

    # measure block height
    line_h_title = int(f_title.size * 1.05)
    title_block_h = line_h_title * len(title_lines)

    f_desc = font(fonts["regular"], 34)
    desc_lines = wrap_text(draw, description, f_desc, max_title_w, max_lines=2)
    line_h_desc = int(f_desc.size * 1.4)
    desc_block_h = line_h_desc * len(desc_lines)
    gap_between = 30 if desc_lines else 0

    total_h = title_block_h + gap_between + desc_block_h
    avail_h = CONTENT_BOTTOM - CONTENT_TOP
    start_y = CONTENT_TOP + max(0, (avail_h - total_h) // 2)

    y = start_y
    for ln in title_lines:
        draw.text((PAD_X, y), ln, fill=FG, font=f_title)
        y += line_h_title
    y += gap_between
    for ln in desc_lines:
        draw.text((PAD_X, y), ln, fill=DIM, font=f_desc)
        y += line_h_desc

    # --- footer ---------------------------------------------------------
    f_brand = font(fonts["bold"], 32)
    f_sub = font(fonts["regular"], 22)
    brand_text = "botaemeveryday"
    sub_text = "/ by notakeith"
    bw = text_w(draw, brand_text, f_brand)
    draw.text((PAD_X, FOOTER_Y), brand_text, fill=FG, font=f_brand)
    # vertically align sub_text with brand baseline-ish
    draw.text((PAD_X + bw + 20, FOOTER_Y + 10), sub_text, fill=accent, font=f_sub)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(out_path, format="PNG", optimize=True)


# --- caching -------------------------------------------------------------

def cache_key(payload: dict) -> str:
    """Stable hash of (title, desc, subject, num, accent, design_version)."""
    blob = json.dumps(payload, ensure_ascii=False, sort_keys=True).encode()
    return hashlib.sha256(blob).hexdigest()[:16]


DESIGN_VERSION = "B-1"   # bump this when you tweak render_cover to force a rebuild


def needs_regen(payload: dict, marker_path: Path, out_path: Path) -> bool:
    if not out_path.exists():
        return True
    if not marker_path.exists():
        return True
    return marker_path.read_text().strip() != cache_key(payload)


def write_marker(payload: dict, marker_path: Path) -> None:
    marker_path.parent.mkdir(parents=True, exist_ok=True)
    marker_path.write_text(cache_key(payload))


# --- main ----------------------------------------------------------------

def main() -> int:
    ap = argparse.ArgumentParser(description="Generate OG cover images for lectures.")
    ap.add_argument("--force", action="store_true", help="regenerate even if cached")
    ap.add_argument("--dry-run", action="store_true", help="don't write files, just list")
    ap.add_argument("--only", help="restrict to one path: '<course>' or '<course>/<lecture>'")
    ap.add_argument(
        "--preview",
        help="generate a single cover into ./preview-out/ for local inspection",
    )
    args = ap.parse_args()

    if not CONTENT_DIR.exists():
        print(f"!! content dir not found: {CONTENT_DIR}", file=sys.stderr)
        return 1

    fonts = ensure_fonts()

    courses: list[Course] = []
    for d in sorted(CONTENT_DIR.iterdir()):
        if d.is_dir() and not d.name.startswith("_") and d.name != "public":
            c = load_course(d)
            if c:
                courses.append(c)

    if not courses:
        print("!! no courses found (need _index.md in content/posts/<course>/)", file=sys.stderr)
        return 1

    # --preview is a one-off path: just render and dump to preview-out/, exit.
    if args.preview:
        return run_preview(args.preview, courses, fonts)

    only_course, only_lecture = None, None
    if args.only:
        parts = args.only.split("/", 1)
        only_course = parts[0]
        only_lecture = parts[1] if len(parts) > 1 else None

    total, regenerated, skipped = 0, 0, 0

    for course in courses:
        if only_course and course.slug != only_course:
            continue

        # 1. Course landing cover (acts as default share image for the course page).
        landing_payload = {
            "kind": "course",
            "title": course.title,
            "description": course.description,
            "subject": course.title,
            "number": "",
            "accent": course.accent,
            "design": DESIGN_VERSION,
        }
        landing_out = STATIC_OUT / course.slug / "index.png"
        landing_marker = CACHE_DIR / course.slug / "index.txt"

        if not only_lecture:  # skip landing if user filtered to a specific lecture
            total += 1
            if args.force or needs_regen(landing_payload, landing_marker, landing_out):
                print(f"  render  {landing_out.relative_to(PROJECT_ROOT)}")
                if not args.dry_run:
                    render_cover(
                        title=course.title,
                        description=course.description,
                        subject="",          # would duplicate the title
                        lecture_num="",
                        accent_idx=course.accent,
                        fonts=fonts,
                        out_path=landing_out,
                    )
                    write_marker(landing_payload, landing_marker)
                regenerated += 1
            else:
                skipped += 1

        # 2. Each lecture cover.
        for lec in load_lectures(course):
            if only_lecture and lec.slug != only_lecture:
                continue
            total += 1
            payload = {
                "kind": "lecture",
                "title": lec.title,
                "description": lec.description,
                "subject": course.title,
                "number": lec.number,
                "accent": course.accent,
                "design": DESIGN_VERSION,
            }
            out = STATIC_OUT / course.slug / f"{lec.slug}.png"
            marker = CACHE_DIR / course.slug / f"{lec.slug}.txt"

            if args.force or needs_regen(payload, marker, out):
                print(f"  render  {out.relative_to(PROJECT_ROOT)}")
                if not args.dry_run:
                    render_cover(
                        title=lec.title,
                        description=lec.description,
                        subject=course.title,
                        lecture_num=lec.number,
                        accent_idx=course.accent,
                        fonts=fonts,
                        out_path=out,
                    )
                    write_marker(payload, marker)
                regenerated += 1
            else:
                skipped += 1

    print(f"\n{total} covers · {regenerated} (re)generated · {skipped} cached"
          + ("  [dry-run]" if args.dry_run else ""))
    return 0


def run_preview(target: str, courses: list[Course], fonts: dict[str, str]) -> int:
    parts = target.split("/", 1)
    if len(parts) != 2:
        print("!! --preview expects '<course>/<lecture>'", file=sys.stderr)
        return 1
    cslug, lslug = parts
    course = next((c for c in courses if c.slug == cslug), None)
    if not course:
        print(f"!! course not found: {cslug}", file=sys.stderr)
        return 1
    lec = next((l for l in load_lectures(course) if l.slug == lslug), None)
    if not lec:
        print(f"!! lecture not found: {target}", file=sys.stderr)
        return 1

    out_dir = PROJECT_ROOT / "preview-out"
    out_dir.mkdir(exist_ok=True)
    out = out_dir / f"{cslug}__{lslug}.png"
    render_cover(
        title=lec.title,
        description=lec.description,
        subject=course.title,
        lecture_num=lec.number,
        accent_idx=course.accent,
        fonts=fonts,
        out_path=out,
    )
    print(f"preview: {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())