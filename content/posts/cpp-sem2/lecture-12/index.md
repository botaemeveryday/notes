---
title: Лекция 12
description: Templates (еще глубже!)
date: 2025-04-23
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

## Дописываем `tuple` — Getter

Делаем шаблонную рекурсию, чтобы получить тип `N`-го элемента:

```cpp
template<size_t N, typename Head, typename... Tail>
struct Getter<N, Head, Tail...> {
    using value_type = typename Getter<N - 1, Tail...>::value_type;
};

template<typename Head, typename... Tail>
struct Getter<0, Head, Tail...> {
    using value_type = Head;
};
```

- В шаблоне лежит индекс элемента из `tuple`.
- На каждом шаге специализация откусывает один элемент.
- Отдельная специализация для индекса 0 — конец рекурсии: возвращаем тип `Head`.

Получение значения: когда доходим до 0 — возвращаем `value` текущего уровня.

### TAD vs CTAD

Перечислять все типы `tuple` при вызове геттера — громоздко. Хочется, чтобы компилятор сам вывел типы.
- **CTAD** (Class Template Argument Deduction) не подходит, потому что для него нужен конструктор.
- **TAD** (Template Argument Deduction) — работает для функций:

```cpp
template<size_t N, typename... Ts>
auto& get(tuple<Ts...>& t) {
    return Getter<N, Ts...>::get(t);
}
```

Здесь компилятор сам выведет `Ts...` из аргумента-тюпла.

### `make_tuple`

Функция, которая сама выводит все типы:

```cpp
template<typename... Ts>
auto make_tuple(Ts... ts) {
    return tuple<Ts...>(ts...);
}
```

### Подсказки для вывода типов конструктора

Например, `std::vector` можно конструировать из пары итераторов. Чтобы CTAD заработал, в стандартной библиотеке прописаны **deduction guides** — подсказки компилятору о том, какие шаблонные аргументы вывести при конструировании.

## Overload pattern

Класс, наследующийся от нескольких лямбд, и подтягивающий их `operator()` через `using`. За счёт того, что лямбды принимают разные типы — выбирается нужная перегрузка.

```cpp
template<class... Ts>
struct overloaded : Ts... { using Ts::operator()...; };
template<class... Ts>
overloaded(Ts...) -> overloaded<Ts...>;   // deduction guide
```

Используется со `std::variant` / `std::visit`.

## `std::variant`

- **Строго типизированный union** (хранит одно из значений перечисленных типов).
- Решает главную проблему `union` — не нужно вручную помнить, какой тип сейчас лежит.

**Типичное использование:**
- Конструктор сам определяет, какой тип кладётся.
- Типы не приводятся друг к другу.
- В `std::get<T>(v)` указываем тип, который мы ожидаем достать; если там лежит другой тип — `std::bad_variant_access`.
- Если в варианте лежит `int(11)`, достать как `long` не выйдет (никакого автоматического каста).

## `std::visit`

Мёрджим overload pattern и `std::variant`. Вызываем `std::visit(overloaded{...}, variant)` — будет вызвана та функция (лямбда), которая принимает текущий хранимый тип:

```cpp
std::variant<int, std::string, double> v = 42;

std::visit(overloaded{
    [](int i)              { std::cout << "int: " << i; },
    [](const std::string& s){ std::cout << "string: " << s; },
    [](double d)           { std::cout << "double: " << d; }
}, v);
```

## Variadic CRTP

Обычный CRTP — derived наследует от `Base<Derived>`. Variadic CRTP — наследование сразу от нескольких базовых шаблонов:

```cpp
template<typename Derived, template<typename> class... Mixins>
struct CRTPBase : Mixins<Derived>... {
    // ...
};
```

Из-за того, что базы тоже шаблонные, при перечислении их в списке нужно указывать, что аргументы шаблонные (через `template<typename> class`).

## Метапрограммирование (введение)

**Compile-time evaluation:**
- Шаблон работает как «приём аргументов» на этапе компиляции.
- Экономим время в рантайме.
- Все данные для вычисления должны быть известны до компиляции.

### `constexpr`

- Позволяет функции или переменной быть вычисленной в **compile-time**.
- Если можно посчитать в compile-time — посчитается там; иначе — в рантайме.
- **`constexpr` переменная:**
    - Литеральный тип.
    - Инициализация через константное выражение (явно, `constexpr`-функция и т.д.).
- **`constexpr` функция:**
    - Возвращает литеральный тип.
    - Содержит переменные литеральных типов.
    - Не виртуальная.
    - Без исключений (в C++11; позже ограничения смягчили).

> Теперь достаточно просто написать `constexpr`, а не городить трюки с `enum` (как делали раньше для compile-time констант в шаблонах).
