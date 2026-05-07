from PIL import Image, ImageDraw, ImageFont, ImageOps
import textwrap
import os
import re
from pathlib import Path


def parse_markdown_frontmatter(file_path):
    """Парсит фронт-маттер из markdown файла"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        match = re.search(r'^---\n(.*?)\n---', content, re.DOTALL)
        if not match:
            return {}

        frontmatter = match.group(1)
        result = {}

        lines = frontmatter.split('\n')
        for line in lines:
            if ':' in line:
                key, value = line.split(':', 1)
                key = key.strip()
                value = value.strip()
                value = value.strip('"\'')
                result[key] = value

        return result
    except Exception as e:
        print(f"  ⚠️ Ошибка парсинга {file_path}: {e}")
        return {}


def generate_subject_card(
        title,
        semester="1 семестр",
        subject=None,
        output_path="cover.png",
        width=1200,
        height=600,
        theme="light",
        font_size=60,
        shadow=True,
        rounded_corners=True,
):
    """Генерирует карточку (без изменений)"""

    if theme == "light":
        bg_color = "#f6f8fa"
        text_color = "#24292f"
        secondary_color = "#57606a"
    else:
        bg_color = "#0d1117"
        text_color = "#f0f6fc"
        secondary_color = "#8b949e"

    image = Image.new("RGB", (width, height), bg_color)
    draw = ImageDraw.Draw(image)

    try:
        font_title = ImageFont.truetype("fonts/TTInterfaces-Bold.ttf", font_size)
        font_secondary = ImageFont.truetype("fonts/TTInterfaces-Regular.ttf", font_size // 2)
    except IOError:
        font_title = ImageFont.load_default()
        font_secondary = ImageFont.load_default()
        print("  ⚠️ Используются стандартные шрифты")

    avg_char_width = font_size * 0.55
    max_chars_per_line = int(width / avg_char_width)
    wrapped_title = textwrap.fill(title, width=max_chars_per_line)

    title_bbox = draw.textbbox((0, 0), wrapped_title, font=font_title)
    title_width = title_bbox[2] - title_bbox[0]
    title_height = title_bbox[3] - title_bbox[1]
    title_x = (width - title_width) / 2
    title_y = (height - title_height) / 2 - 30

    if shadow:
        shadow_color = "#00000022" if theme == "light" else "#00000088"
        draw.text((title_x + 3, title_y + 3), wrapped_title, font=font_title, fill=shadow_color)

    draw.text((title_x, title_y), wrapped_title, font=font_title, fill=text_color)

    if subject:
        secondary_text = f"{semester} • {subject}"
    else:
        secondary_text = f"{semester}"

    secondary_bbox = draw.textbbox((0, 0), secondary_text, font=font_secondary)
    secondary_width = secondary_bbox[2] - secondary_bbox[0]
    secondary_x = (width - secondary_width) / 2
    secondary_y = title_y + title_height + 30

    draw.text((secondary_x, secondary_y), secondary_text, font=font_secondary, fill=secondary_color)

    if rounded_corners:
        radius = 30
        mask = Image.new("L", (width, height), 0)
        mask_draw = ImageDraw.Draw(mask)
        mask_draw.rounded_rectangle((0, 0, width, height), radius, fill=255)
        image = ImageOps.fit(image, mask.size, centering=(0.5, 0.5))
        image.putalpha(mask)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    image.save(output_path, "PNG", quality=95)
    print(f"  ✅ Сохранено: {output_path}")


def scan_and_generate(content_path="../content/posts"):
    """Сканирует папки и генерирует обложки"""

    posts_dir = Path(content_path)

    if not posts_dir.exists():
        print(f"❌ Папка не найдена: {posts_dir}")
        return

    print(f"🔍 Сканируем {posts_dir}...\n")

    generated_count = 0

    for section_path in posts_dir.iterdir():
        if not section_path.is_dir():
            continue

        if section_path.name.startswith('.'):
            continue

        print(f"📁 Обработка: {section_path.name}")

        index_md = section_path / "_index.md"
        if index_md.exists():
            data = parse_markdown_frontmatter(index_md)
            title = data.get('title', section_path.name)
            semester = data.get('semester', '')

            if semester:
                semester_text = f"{semester} семестр"
            else:
                semester_text = "Без семестра"

            output_file = section_path / "cover.png"

            generate_subject_card(
                title=title,
                semester=semester_text,
                subject=None,
                output_path=str(output_file),
                theme="light",
                shadow=False,
                rounded_corners=False,
                font_size=90
            )
            generated_count += 1

        for lecture_path in section_path.iterdir():
            if not lecture_path.is_dir():
                continue

            lecture_index = lecture_path / "index.md"
            if lecture_index.exists():
                data = parse_markdown_frontmatter(lecture_index)
                title = data.get('title', lecture_path.name)
                semester = data.get('semester', '')
                subject = data.get('subject', '')


                if subject:
                    semester_text = f"{subject}"
                else:
                    semester_text = ""

                output_file = lecture_path / "cover.png"

                generate_subject_card(
                    title=title,
                    semester=semester_text,
                    subject=subject if subject else None,
                    output_path=str(output_file),
                    theme="light",
                    shadow=False,
                    rounded_corners=False,
                    font_size=60
                )
                generated_count += 1

        print()

    print(f"✨ Всего сгенерировано обложек: {generated_count}")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        scan_and_generate(sys.argv[1])
    else:
        scan_and_generate("./content/posts")