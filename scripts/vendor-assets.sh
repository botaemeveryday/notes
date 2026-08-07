#!/usr/bin/env bash
#
# Выкачивает всё, что раньше приезжало с CDN, в репозиторий.
# Запускается руками и редко; результат коммитится.
#
#   ./scripts/vendor-assets.sh
#
# Кладёт:
#   static/fonts/*.woff2   — Inter 900 и Pangolin (SIL OFL 1.1)
#   static/katex/          — katex.min.css + шрифты формул (MIT)
#   assets/icons/*.svg     — только те иконки, что реально нужны (MIT)

set -euo pipefail
cd "$(dirname "$0")/.."

TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT

fetch() { (cd "$TMP" && npm pack --silent "$1" >/dev/null && tar xzf ./*"${1##*/}"*.tgz && mv package "$2" && rm -f ./*.tgz); }

# ── Шрифты текста ───────────────────────────────────────────────────
echo "→ шрифты"
mkdir -p static/fonts
fetch @fontsource/inter inter
fetch @fontsource/pangolin pangolin

for f in latin latin-ext cyrillic; do
  cp "$TMP/inter/files/inter-$f-900-normal.woff2"       static/fonts/
  cp "$TMP/pangolin/files/pangolin-$f-400-normal.woff2" static/fonts/
done

# ── KaTeX ───────────────────────────────────────────────────────────
echo "→ katex"
rm -rf static/katex && mkdir -p static/katex/fonts
fetch katex katex
cp "$TMP/katex/dist/katex.min.css" static/katex/
cp "$TMP/katex"/dist/fonts/*.woff2 static/katex/fonts/

# ── Иконки ──────────────────────────────────────────────────────────
echo "→ иконки"
fetch ionicons ionicons

EXTRA=(
  information-circle
  bulb
  sparkles
  warning
  alert-circle
)

NAMES=$(
  {
    grep -rhoE '<ion-icon[^>]*name="[a-z0-9-]+"' layouts content 2>/dev/null \
      | grep -oE 'name="[a-z0-9-]+"' | cut -d'"' -f2 || true
    grep -rhoE '\{\{< *icon +"?[a-z0-9-]+' content 2>/dev/null \
      | grep -oE '[a-z0-9-]+$' || true
    grep -rhoE 'partial "ui/icon\.html" "[a-z0-9-]+"' layouts 2>/dev/null \
      | grep -oE '"[a-z0-9-]+"$' | tr -d '"' || true
    grep -rhoE '"name" "[a-z0-9-]+"' layouts 2>/dev/null \
      | grep -oE '"[a-z0-9-]+"$' | tr -d '"' || true
    printf '%s\n' "${EXTRA[@]}"
  } | sort -u
)

if [ -z "$NAMES" ]; then
  echo "  ! не собрано ни одного имени — запущен ли скрипт из корня сайта?" >&2
  exit 1
fi

mkdir -p assets/icons
missing=0
while read -r name; do
  [ -z "$name" ] && continue
  if [ -f "$TMP/ionicons/dist/svg/$name.svg" ]; then
    cp "$TMP/ionicons/dist/svg/$name.svg" "assets/icons/$name.svg"
  else
    echo "  ! нет такой иконки в ionicons: $name" >&2
    missing=$((missing + 1))
  fi
done <<< "$NAMES"

echo
echo "готово:"
echo "  static/fonts   $(ls static/fonts | wc -l | tr -d ' ') файлов"
echo "  static/katex   $(du -sh static/katex | cut -f1)"
echo "  assets/icons   $(ls assets/icons | wc -l | tr -d ' ') иконок"
[ "$missing" -gt 0 ] && echo "  пропущено      $missing (см. выше)"
exit 0