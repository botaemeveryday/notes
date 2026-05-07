#!/bin/bash
# Локальная сборка, идентичная GitHub Pages

# Устанавливаем переменные окружения как в GitHub Actions
export HUGO_VERSION="0.128.0"
export HUGO_ENVIRONMENT="production"
export GITHUB_PAGES=true

# Создаём временную директорию для кэша как в CI

# Очищаем прошлую сборку

# Собираем с теми же параметрами, что и в CI
echo "🔨 Сборка Hugo (production режим)..."
hugo \
  --minify \
  --baseURL "https://botaemeveryday.github.io/notes/" \
  --environment production \

# Проверяем результат как в CI
echo "✅ Проверка сборки..."
if [ -f public/index.html ]; then
    echo "✓ index.html существует"
    if grep -q "<body" public/index.html; then
        echo "✓ index.html содержит <body>"
    else
        echo "❌ index.html пустой!"
        exit 1
    fi
else
    echo "❌ public/index.html не найден!"
    exit 1
fi

# Показываем пути к интересующим файлам
echo ""
echo "📁 Результаты сборки:"
echo "  - Главная: public/index.html"
echo "  - Раздел матстата: public/posts/math-stats/index.html"
echo "  - Лекция 1: public/posts/math-stats/lecture1/index.html"

# Проверяем содержимое _index.md в собранном HTML
echo ""
echo "🔍 Проверяем, отрендерился ли _index.md:"
if [ -f public/posts/math-stats/index.html ]; then
    if grep -q "Конспекты лекций" public/posts/math-stats/index.html; then
        echo "✅ YES! '_index.md' отрендерился на странице раздела"
        echo "   Строка 'Конспекты лекций' найдена"
    else
        echo "❌ NO! '_index.md' НЕ отрендерился"
        echo "   Ищем альтернативно..."
        grep -E "Конспекты|лекций|Лимар" public/posts/math-stats/index.html | head -5
    fi
else
    echo "❌ public/posts/math-stats/index.html не существует!"
fi

echo ""
echo "🚀 Чтобы посмотреть результат:"
echo "   hugo server --environment production"
echo "   или открыть public/posts/math-stats/index.html в браузере"