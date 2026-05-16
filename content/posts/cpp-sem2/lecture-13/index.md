---
title: Лекция 13
description: Метапрограммирование
date: 2025-04-30
tags:
  - 2 семестр
  - Основы программирования
authors:
  - name: notakeith
    avatar: https://avatars.githubusercontent.com/u/108391756?v=4
    link: https://github.com/notakeith
  - name: salt-caramel
    avatar: https://avatars.githubusercontent.com/u/180561221?v=4
    link: https://github.com/salt-caramel
---

## Compile-time evaluation

- Шаблон работает как приём аргументов.
- Экономим на времени в рантайме.
- Все данные для вычисления должны быть известны до компиляции.

## Template Specialization

В зависимости от **порядка функций**, специализация шаблона может относиться к разным функциям. Например:
- Если у нас сначала шаблон по `T*`, а потом специализация для `int*` — выбирается `int*` (более специфичная).
- Если же сначала специализировать `T` как `int*`, а потом написать функцию для `T*` — выбирается более общий вариант, как более «удачный».

### Пишем свой `is_same`

```cpp
template<typename T, typename U>
struct is_same {
    static constexpr bool value = false;
};

template<typename T>
struct is_same<T, T> {
    static constexpr bool value = true;
};
```

По дефолту — `false`. Специализация для одинаковых типов — `true`.

### Пишем `identity`

Фокус: в шаблоне принимаем тип `T`, а потом значение `T value` — внутри структуры лежит это же значение. Можно сделать инкремент — внутри хранить `T value + 1`.

Если положить в шаблон сразу `auto` — не надо указывать тип:

```cpp
template<auto Value>
struct identity {
    static constexpr auto value = Value;
};
```

А если сделать снаружи `constexpr` переменную, которая держит `value` от структуры — не нужно писать `::value`.

### Метафункции, возвращающие типы

- Просто пишем `using` внутри структуры.
- Возвращается тип — а значит, его можно положить в другой шаблон.

```cpp
template<typename T>
struct type_identity {
    using type = T;
};
```