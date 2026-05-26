# Computer Science Notes

[![Hugo](https://img.shields.io/badge/Hugo-FF4088?style=flat-square&logo=hugo&logoColor=white)](https://gohugo.io/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=flat-square)](LICENSE)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg?style=flat-square)](CONTRIBUTING.md)

Открытая база конспектов по дисциплинам computer science: лекции, переводы, разборы. Сайт собирается на Hugo и публикуется через GitHub Pages.

**→ [botaemeveryday.github.io/notes](https://botaemeveryday.github.io/notes/)**

## Содержание

База регулярно пополняется. Текущий состав:

### Учебные курсы

| Дисциплина | Преподаватель |
|---|---|
| [Математическая статистика](https://botaemeveryday.github.io/notes/posts/math-stats/) | Лимар И. А. |
| [Операционные системы](https://botaemeveryday.github.io/notes/posts/operation-systems/) | Маятин А. В. |
| [Базы данных](https://botaemeveryday.github.io/notes/posts/databases/) | Мацнев Н. И. |
| [Технологии программирования на Java](https://botaemeveryday.github.io/notes/posts/java/) | Макаревич Р. Д. |
| [C++ (семестр 1)](https://botaemeveryday.github.io/notes/posts/cpp-sem1/) | Хвастунов А. П. |
| [C++ (семестр 2)](https://botaemeveryday.github.io/notes/posts/cpp-sem2/) | Хвастунов А. П. |

### Дополнительные материалы

- [Let's Build A Simple Interpreter](https://botaemeveryday.github.io/notes/posts/interpreter/) — перевод серии статей Руслана Спивака по построению интерпретатора.

## Как принять участие

Проект открыт для правок и дополнений. Pull request'ы приветствуются в любом объёме — от исправления опечатки до публикации собственных конспектов по новому курсу.

Сценарии участия:

- **Опечатка или неточность** — откройте issue или сразу PR с правкой.
- **Дополнение существующего конспекта** — отредактируйте соответствующий `index.md` в `content/posts/<курс>/<лекция>/`.
- **Новая лекция в рамках существующего курса** — добавьте директорию по образцу соседних лекций.
- **Новый курс** — создайте директорию в `content/posts/` с файлом `_index.md` и лекциями внутри. Перед публикацией ознакомьтесь с правилами оформления.

Все требования к структуре файлов, front matter и шорткодам описаны в **[CONTRIBUTING.md](CONTRIBUTING.md)**.

## Структура репозитория

```
content/posts/      # конспекты, сгруппированные по дисциплинам
layouts/            # шаблоны Hugo
  ├── _default/     # базовые шаблоны (list, single, baseof)
  ├── partials/     # переиспользуемые блоки (header, footer, post)
  └── shortcodes/   # callout, card, compare, spoiler, key и др.
```

## Локальная разработка

Требования: Hugo (extended), Node.js, npm.

```bash
git clone https://github.com/botaemeveryday/notes.git
cd notes

npm install        # зависимости Tailwind
npm run build        # сборка стилей
hugo server -D     # локальный сервер на http://localhost:1313/
```

Флаг `-D` включает рендеринг черновиков (`draft: true` в front matter).

## Лицензия

Распространяется под лицензией MIT. См. [LICENSE.md](LICENSE.md).
