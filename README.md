# Computer Science Notes

[![Hugo](https://img.shields.io/badge/Hugo-FF4088?style=flat-square&logo=hugo&logoColor=white)](https://gohugo.io/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=flat-square)](LICENSE)

# [Сайт: botaemeveryday.github.io/notes](https://botaemeveryday.github.io/notes/)

## Разделы

На данный момент база содержит материалы по следующим дисциплинам:

- **[Математическая статистика](https://botaemeveryday.github.io/notes/posts/math-stats/)** — Лекции Лимара Ивана Александровича
- **[Операционные системы](https://botaemeveryday.github.io/notes/posts/operation-systems/)** — Лекции Маятина Александр Владимирович
- **[Базы Данных](https://botaemeveryday.github.io/notes/posts/databases/)** — Лекции Мацнева Никиты Игоревича
- **[Let's Build A Simple Interpreter](https://botaemeveryday.github.io/notes/posts/interpreter/)** — Перевод серии статей Руслана Спивака по созданию интерпретатора.
- **[C++ (Семестр 2)](https://botaemeveryday.github.io/notes/posts/cpp-sem2/)** — Лекции Хвастунова Александра Павловича

## 🤝 Как контрибьютить

Проект открыт для улучшений! Если вы нашли опечатку, хотите дополнить конспект или добавить новую лекцию или свои конспекты — мы будем рады вашим Pull Requests.

1. Форкните репозиторий.
2. Ознакомьтесь с правилами оформления в **[CONTRIBUTING.md](CONTRIBUTING.md)**.
3. Добавьте свои изменения и создайте PR.

## 🛠 Локальный запуск

Если вы хотите развернуть проект у себя на компьютере для разработки:

```bash
# Клонируем репозиторий
git clone https://github.com/botaemeveryday/notes.git
cd notes

# Устанавливаем зависимости (Tailwind)
npm install

# Собираем стили
npm run css

# Запускаем локальный сервер Hugo
hugo server -D

# Сайт будет доступен по адресу http://localhost:1313/
```