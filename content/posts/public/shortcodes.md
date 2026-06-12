---
title: "Все шорткоды"
description: "Демонстрация всех доступных шорткодов для Anki, карточек и оформления"
date: 2026-05-14
authors:
  - name: notakeith
    avatar: https://avatars.githubusercontent.com/u/108391756?v=4
    link: https://github.com/notakeith
url: "/shortcodes/"
hideLeftSidebar: true
hideTOC: true
hidePrevNext: true
hideBreadCrumbs: true
---

# Шорткоды проекта

Сборка всех доступных компонентов. Используйте их для создания лекций, конспектов и учебных материалов.

## 1. Anki — скачивание колод

Главный шорткод для встраивания карточек Anki. Поддерживает 4 типа ссылок.

{{< anki-download
  lecture="/files/lecture-01.apkg"
  course="/files/full-course.apkg"
  easy="/files/basic-deck.apkg"
  hard="/files/advanced-deck.apkg"
>}}

**Параметры:**
- `lecture` — ссылка на колоду текущей лекции
- `course` — ссылка на общую колоду курса
- `easy` — базовый уровень
- `hard` — продвинутый уровень

## 2. Callout (цветные блоки)

```md
{{</* callout type="info" title="Заметка" */>}}
Текст внутри информационного блока.
{{</* /callout */>}}
```

{{< callout type="info" title="Заметка" >}}
Это информационный блок. Используется для важных дополнений.
{{< /callout >}}

{{< callout type="warning" title="Внимание" >}}
Блок с предупреждением. Здесь стоит быть осторожнее.
{{< /callout >}}

{{< callout type="danger" title="Ошибка" >}}
Критическая информация или распространённая ошибка.
{{< /callout >}}

{{< callout type="success" title="Готово" >}}
Успешное выполнение или результат.
{{< /callout >}}

## 3. Карточки (Card / Cards)

**Одиночная карточка:**
```md
{{</* card icon="🧠" title="Термин" */>}}
Описание или определение.
{{</* /card */>}}
```

{{< card icon="📘" title="Интервальное повторение" >}}
Метод запоминания, при котором информация повторяется через увеличивающиеся интервалы времени. Anki — лучший инструмент для этого.
{{< /card >}}

**Сетка карточек (Cards обёртка):**
```md
{{</* cards */>}}
  {{</* card ... */>}}
  {{</* card ... */>}}
{{</* /cards */>}}
```

{{< cards >}}
  {{< card icon="⚡" title="Быстро" >}}
  Загрузка конспектов происходит мгновенно.
  {{< /card >}}
  {{< card icon="🎨" title="Темно" >}}
  Поддержка светлой и тёмной темы.
  {{< /card >}}
  {{< card icon="📱" title="Адаптивно" >}}
  Идеально смотрится на телефонах и планшетах.
  {{< /card >}}
{{< /cards >}}

## 4. Compare (плюсы/минусы)

```md
{{</* compare
  pros="**Плюсы:** Быстро, удобно, бесплатно."
  cons="**Минусы:** Требует дисциплины."
*/>}}
```

{{< compare >}}
+ Быстрая компиляция
+ Строгая типизация
+ Крутой mascot
|||
- Долгое время сборки
- Сложный синтаксис
{{< /compare >}}

## 5. CTA (призыв к действию)

```md
{{</* cta label="Перейти к курсу" href="/courses/" */>}}
🎯 **Начните учиться прямо сейчас**
Бесплатные конспекты и колоды Anki.
{{</* /cta */>}}
```

{{< cta label="Смотреть все шорткоды" href="#список-шорткодов" >}}
✨ **Понравилась подборка?**
Используйте эти шорткоды в своих лекциях.
{{< /cta >}}

## 6. Disclaimer (отказ от ответственности)

С кастомным текстом:
```md
{{</* disclaimer */>}}
Этот текст написан вручную и заменяет стандартный.
{{</* /disclaimer */>}}
```

{{< disclaimer >}}
⚠️ **Тестовый дисклеймер**: Информация актуальна на май 2026 года.
{{< /disclaimer >}}

## 7. Key (клавиши)

```md
{{</* key "Ctrl" */>}} + {{</* key "C" */>}}
```

Нажмите {{< key "Ctrl" >}} + {{< key "C" >}} для копирования.
Сочетание {{< key "Cmd" >}} + {{< key "Shift" >}} + {{< key "3" >}} для скриншота.

## 8. Spoiler (спойлер/ответ)

```md
{{</* spoiler title="Нажми, чтобы увидеть ответ" */>}}
Скрытый текст. 42 — ответ на главный вопрос.
{{</* /spoiler */>}}
```

{{< spoiler title="🧠 Проверь себя" >}}
**Ответ:** Шорткоды упрощают вставку сложных HTML-компонентов в Markdown.
{{< /spoiler >}}

## 9. Stat (статистика)

**Stat-row с вложенными Stat:**
```md
{{</* stat-row */>}}
  {{</* stat num="150+" label="Лекций" */>}}
  {{</* stat num="24/7" label="Доступ" */>}}
  {{</* stat num="100%" label="Бесплатно" */>}}
{{</* /stat-row */>}}
```

{{< stat-row >}}
  {{< stat num="1000+" label="Карточек" >}}
  {{< stat num="20+" label="Колод" >}}
  {{< stat num="5 мин" label="Настройка" >}}
{{< /stat-row >}}

## 10. YouTube (видео)

```md
{{</* youtube id="dQw4w9WgXcQ" */>}}
```

{{< youtube id="dQw4w9WgXcQ" >}}


{{< terminal title="server.log" prompt="$ ./cpp_server">}}
[INFO] Server listening on port 8080...
[WARN] Connection timeout from 192.168.1.1
{{< /terminal >}}

{{< tabs >}}
  {{< tab title="Bad Code ❌" >}}
  ```cpp
  int* p = new int;
  // Утечка памяти, если не сделать delete
  ```
  {{< /tab >}}

  {{< tab title="Good Code ✅" >}}
  ```cpp
  std::unique_ptr<int> p = std::make_unique<int>();
  // Безопасно!
  ```
  {{< /tab >}}
{{< /tabs >}}


{{< filetree name="OS Kernel Build" >}}
📁 src/
 ├── 📄 main.c
 ├── 📄 memory.c
 └── 📁 include/
      └── 📄 memory.h
⚙️ Makefile
{{< /filetree >}}


{{< godbolt src="https://godbolt.org/z/h5PqPPhE3" h="500px" >}}


{{< math-box type="Теорема" title="Коши — Буняковского" >}}
Для любых векторов $x$ и $y$ выполняется неравенство: 
$$(x, y)^2 \le (x, x)(y, y)$$
{{< /math-box >}}

{{< math-box type="Доказательство" >}}
Рассмотрим функцию $f(t) = (tx + y, tx + y) \ge 0$...
{{< /math-box >}}


{{< timeline >}}
  {{< step num="1" title="Инициализация" >}}
  Всем вершинам задаем расстояние $\infty$, а стартовой $0$.
  {{< /step >}}
  {{< step num="2" title="Выбор вершины" >}}
  Достаем из очереди с приоритетом вершину с минимальным весом.
  {{< /step >}}
{{< /timeline >}}


