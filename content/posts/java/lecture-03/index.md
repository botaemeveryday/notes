---
title: Лекция 3
description: Collection Framework и Stream API
weight: 3
tags:
  - Java
  - 4 Семестр
authors:
  - name: notakeith
    avatar: https://avatars.githubusercontent.com/u/108391756?v=4
    link: https://github.com/notakeith
---

# Лекция 3. Collection Framework и Stream API

## Packages — пакеты в Java

Классы в Java объединяются в **пакеты**. Пакеты позволяют логически организовать классы и избежать конфликтов имён. Java имеет встроенные пакеты: `java.lang`, `java.util`, `java.io` и т.д.

Если для класса пакет не определён, он находится в пакете «по умолчанию». Чтобы использовать классы из других пакетов, нужно их подключить через `import`. **Исключение** — `java.lang` (`String`, `Object` и др.) подключается автоматически.

## Java Editions

| Edition | Описание |
|---------|----------|
| **Java SE** | Standard Edition. Стандартная редакция для консольных, GUI, апплет-приложений. |
| **Java EE** | Enterprise Edition. Для распределённых приложений масштаба предприятий. Включает EJB, JPA, Servlets, JMS. |
| **Java ME** | Micro Edition. Для микрокомпьютеров и мобильных платформ. |

Спецификации формируются через [Java Community Process](https://ru.wikipedia.org/wiki/Java_Community_Process).

## Java Collection Framework

**Collection Framework** — иерархия интерфейсов и реализаций, которая является частью JDK и предоставляет «из коробки» большое количество структур данных.

Все коллекции наследуются от интерфейса `java.util.Collection`. Он же наследуется от `Iterable` — поэтому всё, что является коллекцией, может использоваться в циклах `for-each`.

### Иерархия Collection Framework

```
Iterable
  └── Collection
        ├── List
        │     ├── ArrayList
        │     ├── LinkedList
        │     └── Vector → Stack
        ├── Queue
        │     └── Deque
        │           └── ArrayDeque
        └── Set
              ├── HashSet
              └── TreeSet

Map (отдельная иерархия)
  ├── HashMap
  └── TreeMap
```

## List — списки

### ArrayList vs LinkedList

| Характеристика | ArrayList | LinkedList |
|----------------|-----------|------------|
| Основа | Массив | Связанный список (Entry хранит data + next + previous) |
| Тип доступа | Произвольный (Random Access) — по индексу | Последовательный (Sequential) |
| Рост | В 1.5 раза при заполнении | По одной Entry |

> Массив сам по себе не может изменять размер. Когда в `ArrayList` место заканчивается, создаётся новый массив **в 1.5 раза больше** и старые элементы копируются.

### Vector — предшественник ArrayList

`java.util.Vector` отличается от `ArrayList` тем, что методы для работы синхронизированы — один поток работает с коллекцией, остальные ждут.

- Растёт **в 2 раза** (не в 1.5, как ArrayList)
- В JavaDoc прямым текстом рекомендуется использовать `ArrayList`, если потокобезопасность не нужна
- Vector имеет наследника — `java.util.Stack` (LIFO-структура с методами `push`, `pop`, `peek`)

### Потокобезопасность коллекций

- **Synchronized** — потокобезопасные. Только один поток одновременно работает с коллекцией. Гарантируют целостность, но снижают производительность.
- **Non-Synchronized** — не потокобезопасные. Множество потоков могут работать одновременно.

Потокобезопасные версии коллекций лежат в пакете `java.util.concurrent`.

## Queue — очереди

Очередь (`java.util.Queue`) — FIFO-структура (first in — first out).

### Deque — двусторонняя очередь

`java.util.Deque` — двусторонняя очередь, позволяет использовать структуру с обоих концов. Реализация — `ArrayDeque`.

### Блокирующие очереди

- **BlockingQueue** реализуют: `PriorityBlockingQueue`, `SynchronousQueue`, `ArrayBlockingQueue`, `DelayQueue`, `LinkedBlockingQueue`
- **BlockingDeque** реализует: `LinkedBlockingDeque`

Каждая блокирующая очередь предназначена для определённых задач многопоточного программирования.

## Set — множества

Set отличается от очереди и списка большей абстракцией — «мешок с предметами», где порядок не определён.

- Сам интерфейс `Set` не добавляет новых методов к `Collection`, а лишь **уточняет требования** (отсутствие дубликатов)
- Получение элементов — только через `Iterator`
- Основные реализации:
  - **HashSet** — на основе хэш-кода
  - **TreeSet** — на основе дерева

## Map — карты

`java.util.Map` — структура «ключ — значение». Аналог словарей из C#.

### Основные методы

- `keySet()` — возвращает набор ключей (Set, т.к. ключи уникальны)
- `values()` — возвращает коллекцию значений (Collection, т.к. значения могут повторяться)
- `entrySet()` — возвращает набор пар «ключ — значение»

## Сторонние библиотеки коллекций

При необходимости можно создать собственную реализацию или использовать готовые сторонние решения:

- **Google Guava**
- **Apache Commons Collections**

Эти библиотеки выступают как boost для Java-коллекций (аналог Boost для C++).

## Stream API — «LINQ в Java»

Стримы и коллекции **похожи, но разные по назначению:**

- **Коллекции** — для эффективного доступа к одиночным объектам
- **Стримы** — для параллельных и последовательных агрегаций через цепочки методов

### Получение стрима

```java
list.stream()                       // из коллекции
Stream.empty()                      // пустой
Stream.of("1", "2", "3")            // из указанных элементов
```

### Операторы Stream API

**Промежуточные (intermediate, lazy)** — обрабатывают элементы и возвращают новый стрим. Их в цепочке может быть много.

**Терминальные (terminal, eager)** — обрабатывают элементы и завершают работу стрима. В цепочке только один.

### Важные моменты

1. **Обработка не начнётся до вызова терминального оператора.**
2. **Экземпляр стрима нельзя использовать более одного раза** (в отличие от `IEnumerable` в C#).
3. Каждый раз для работы с коллекцией нужно открывать **новый поток**.

### Пример использования

```java
list.stream()
    .filter(x -> x.toString().length() == 3)
    .forEach(System.out::println);

list.stream().forEach(x -> System.out.println(x));
```

### Сравнение с LINQ (C#)

| C# (LINQ) | Java (Stream API) |
|-----------|-------------------|
| `.Where(predicate)` | `.filter(predicate)` |
| `.Select(...)` | `.map(...)` |
| `.SelectMany(...)` | `.flatMap(...)` |
| `Enumerable.Range` | `IntStream.range` |
| `.Take()` | `.limit()` |
| `.Skip()` | `.skip()` |
| `.Distinct()` | `.distinct()` |
| `.OrderBy(...)` | `.sorted(comparator)` |
| `.Count()` | `.count()` |
| `.Aggregate()` | `.reduce()` |
| `.First()` | `.findFirst()` |
| `.Any()` | `.anyMatch()` |
| `.Any()` с отрицанием | `.noneMatch()` |
| `.ToList()` | `.toList()` |
| `String.Join()` | `.joining(delimiter, prefix, suffix)` |
| `.FirstOrDefault(..., 5)` | `.map(...).orElse(5)` |
| `.Single(...)` | `.filter(...).orElseThrow()` |
