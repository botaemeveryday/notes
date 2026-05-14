---
title: Концепты
date: 2025-05-14
cover: images/cover.png
tags:
  - 2 семестр
  - Основы программирования
nolastmod: true
draft: false
description: Лекция 15
authors:
  - name: notakeith
    avatar: https://avatars.githubusercontent.com/u/108391756?v=4
    link: https://github.com/notakeith
  - name: salt-caramel
    avatar: https://avatars.githubusercontent.com/u/180561221?v=4
    link: https://github.com/salt-caramel
---

> До концептов ограничения на шаблонные параметры выражались через `enable_if`, `conjunction`, `is_integral`, `void_t` и подобные трюки SFINAE. Concepts — это официальный, читаемый способ делать то же самое.

## Зачем нужны Concepts

Concepts позволяют задавать **ограничения на шаблонные параметры** — то есть указывать, каким требованиям должен удовлетворять тип, чтобы шаблон инстанцировался.

Преимущества перед альтернативами:
- **Проще, чем `enable_if`** — не нужно городить SFINAE-конструкции
- **Лучше, чем `if constexpr`** — `if constexpr` работает внутри тела функции и не влияет на разрешение перегрузок; концепты участвуют в overload resolution
- **Понятные ошибки компиляции** — компилятор сразу говорит, какое требование не выполнено
- **Неявный SFINAE** — если концепт не выполнен, перегрузка просто не рассматривается

---

## Синтаксис `requires`

Ключевое слово `requires` пишется перед телом функции и задаёт условие для выбора перегрузки:

```cpp
// Перегрузка для указателей
template<typename T>
requires std::is_pointer_v<T>
void print(const T& value) {
    std::cout << *value << std::endl;
}

// Перегрузка для всех остальных типов
template<typename T>
void print(const T& value) {
    std::cout << value << std::endl;
}
```

---

## Объявление концепта

`concept` — это именованное требование к типам, которое можно переиспользовать:

```cpp
template<typename T, typename U>
concept Addable = requires(T a, U b) {
    a + b; // тип должен поддерживать operator+
};

template<typename T, typename U>
requires Addable<T, U>
auto add(const T& a, const U& b) {
    return a + b;
}

int main() {
    add(1, 2);       // OK
    add(Foo{}, Foo{}); // OK, если Foo поддерживает operator+
}
```

### Способы использования концепта

```cpp
// 1. В requires-clause перед телом функции
template<typename T, typename U>
requires Addable<T, U>
auto add(const T& a, const U& b);

// 2. Прямо в списке шаблонных параметров
template<typename T, Addable<T> U>
auto add(const T& a, const U& b);

// 3. Сокращённый синтаксис с auto (без явного шаблона)
auto add(const Addable auto& a, const auto& b);
```

---

## Виды требований внутри `requires`-выражения

### 1. Simple requirement (простое требование)
Просто выражение, которое должно быть синтаксически корректным. Возвращаемое значение не проверяется.

```cpp
template<typename... Args>
concept Addable = requires(Args... args) {
    (args + ...); // simple requirement: operator+ должен существовать
};
```

### 2. Nested requirement (вложенное требование)
`requires`-выражение внутри `requires`-блока — позволяет добавить булево условие:

```cpp
template<class T, typename... TArgs>
constexpr bool are_all_same = std::conjunction_v<std::is_same<T, TArgs>...>;

template<typename... Args>
concept Addable = requires(Args... args) {
    (args + ...);                      // simple
    requires sizeof...(Args) > 1;      // nested: аргументов должно быть больше одного
    requires are_all_same<Args...>;    // nested: все типы должны совпадать
};
```

### 3. Compound requirement (составное требование)
Проверяет не только корректность выражения, но и тип результата и/или `noexcept`:

```cpp
// Вспомогательный алиас для получения типа первого аргумента пакета
template<typename First, typename...>
struct first_arg { using type = First; };

template<typename... Ts>
using first_arg_t = typename first_arg<Ts...>::type;

template<typename... Args>
concept Addable = requires(Args... args) {
    (args + ...);                       // simple
    requires sizeof...(Args) > 1;       // nested
    requires are_all_same<Args...>;     // nested
    // compound: выражение не бросает исключений,
    // и результат имеет тип первого аргумента
    { (args + ...) } noexcept -> std::same_as<first_arg_t<Args...>>;
};
```

### 4. Type requirement (требование к типу)
Проверяет, что вложенный тип существует:

```cpp
template<typename T>
concept HasValueType = requires {
    typename T::value_type; // тип T должен иметь вложенный тип value_type
};
```

> В примере с `Addable` выше type requirement явно не используется, но синтаксис именно такой: `typename SomeType;` внутри `requires`-блока.

---

## Полный пример с вариативным шаблоном

```cpp
template<typename... Args>
requires Addable<Args...>
auto add(Args&&... args) {
    return (args + ...);
}

int main() {
    add(1, 2, 3, 4);     // OK
    add(Foo{}, Foo{});   // OK, если Foo удовлетворяет Addable
}
```

---

## Область применения

- Выбор перегрузки функции в зависимости от свойств типа
- Ограничение шаблонных классов/функций с читаемыми ошибками
- Замена громоздких SFINAE-конструкций на выразительные именованные требования