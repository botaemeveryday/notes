---
title: Лекция 14
description: Метапрограммирование
date: 2025-05-07
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

## `is_same` (наивно)

```cpp
template<typename T, typename U>
struct is_same {
    static constexpr bool value = false;
};

template<typename T>
struct is_same<T, T> {
    static constexpr bool value = true;
};

int main() {
    static_assert(is_same<int, int>::value);
    static_assert(!is_same<int, float>::value);
    static_assert(!is_same<int, int&>::value);
    static_assert(!is_same<const int, int>::value);
}
```

Отличает одинаковые `T`: имеет специализацию для одинаковых типов (`true`), во всех других случаях — `false`.

> Если убрать `::value` и забыть про треугольные скобочки — шаблон почти превращается в обычную функцию.
>
> По сути мы пишем структуру, которая создаёт **метафункцию**. Любую функцию можно попробовать переписать на метафункцию.

## `identity`

В прошлый раз писали `identity` — обычная функция:

```cpp
template<typename T>
T&& identity(T&& value) {
    return std::forward<T>(value);
}

int main() {
    int x = identity(239);
}
```

Переписываем на метафункцию — теперь вычисляется в compile-time:

```cpp
template<typename T, T Value>
struct value_identity {
    static constexpr T value = Value;
};

int main() {
    int x = value_identity<int, 239>::value;
}
```

**Ограничения:**
- Нужно знать данные на момент компиляции.
- Только литеральные типы.

Грустно, что нужно указывать `int`. Используем `auto`:

```cpp
template<auto Value>
struct value_identity {
    static constexpr auto value = Value;
};

int main() {
    static_assert(value_identity<239>::value == 239);
}
```

Метафункции прекрасно работают с вариативными шаблонами:

```cpp
template<auto... Value>
struct sum {
    static constexpr auto value = (Value + ...);
};

int main() {
    static_assert(sum<1, 2, 3, 4, 5>::value == 15);
}
```

Обычная функция возвращает конкретное значение. **Метафункция** может вернуть и значение, и даже сам тип.

**Два типа метафункций:**
1. Возвращающие типы.
2. Возвращающие значения.

```cpp
struct Boo {};

int main() {
    static_assert(
        std::is_same<
            std::type_identity<Boo>::type,
            Boo
        >::value
    );
}
```

Хотим избавиться от `::`. Договорённость такая: если есть метафункция, для неё пишут алиас `что-то_t` (если возвращает тип) или `что-то_v` (если значение):

```cpp
template<class T, class U>
constexpr bool is_same_v = is_same<T, U>::value;

template<typename T>
using type_identity_t = typename std::type_identity<T>::type;

int main() {
    static_assert(
        std::is_same_v<std::type_identity_t<Boo>, Boo>
    );
}
```

## `integral_constant`

Принимает `T` и значение. Объединяет обе идеи: возвращает и тип, и значение.

```cpp
template<typename T, T Value>
struct integral_constant {
    static constexpr T value = Value;
    using value_type = T;
    using type = integral_constant;
    constexpr operator value_type() const noexcept { return value; }
    constexpr value_type operator()() const noexcept { return value; }
};
```

```cpp
template<bool B>
using bool_constant = integral_constant<bool, B>;

using true_type  = integral_constant<bool, true>;
using false_type = integral_constant<bool, false>;
```

> **Интегральный тип** — это целочисленный тип (`bool`, `char`, `int`, `long`, …). Поэтому константа называется *integral*.

Эта гениальная штука позволяет писать метафункции лаконичнее:

```cpp
template<class T, class U>
struct is_same : std::false_type {};

template<class T>
struct is_same<T, T> : std::true_type {};
```

## `<type_traits>`

[Заголовок `<type_traits>`](https://en.cppreference.com/w/cpp/header/type_traits) содержит набор метафункций для работы с типами:
- Primary type categories (`is_integral`, `is_pointer`, …)
- Composite type categories (`is_arithmetic`, `is_object`, …)
- Type properties (`is_const`, `is_signed`, …)
- Supported operations (`is_constructible`, `is_assignable`, …)
- Type relationships (`is_same`, `is_base_of`, …)
- Const-volatility specifiers (`remove_const`, `add_volatile`, …)
- и др.

### Свой `is_pointer`

```cpp
template<class T> struct is_pointer                    : std::false_type {};
template<class T> struct is_pointer<T*>                : std::true_type  {};
template<class T> struct is_pointer<T* const>          : std::true_type  {};
template<class T> struct is_pointer<T* volatile>       : std::true_type  {};
template<class T> struct is_pointer<T* const volatile> : std::true_type  {};

template<typename T>
inline constexpr bool is_pointer_v = is_pointer<T>::value;
```

Проблема: `const`, `volatile` мешают обычному TAD по `T*` — нужны отдельные специализации. На двух квалификаторах уже четыре комбинации, на трёх было бы восемь — комбинаторика.

Хотим **избавиться от обилия перегрузок**. Напишем метафункцию, снимающую `const`:

```cpp
template<typename T>
struct remove_const {
    using type = T;
};
template<typename T>
struct remove_const<const T> {
    using type = T;
};
```

Аналогично для `volatile`:

```cpp
template<typename T>
struct remove_volatile {
    using type = T;
};
template<typename T>
struct remove_volatile<volatile T> {
    using type = T;
};
```

Объединяем:

```cpp
template<typename T>
using remove_cv_t = typename remove_volatile<typename remove_const<T>::type>::type;
```

Переписываем `is_pointer` через `remove_cv`:

```cpp
template<typename T>
inline constexpr bool is_pointer_v = is_pointer<remove_cv_t<T>>::value;
```

Александр Павлович сказал: *not so good* — ведь нельзя пользоваться просто `is_pointer<T>` (без `_v`). Перепишем полностью:

```cpp
template<typename T>
struct is_pointer_inner : std::false_type {};

template<typename T>
struct is_pointer_inner<T*> : std::true_type {};

template<typename T>
struct is_pointer : is_pointer_inner<remove_cv_t<T>> {};
```

## SFINAE

- **«Substitution Failure Is Not An Error»** (неудавшаяся подстановка — не ошибка).
- Если для перегрузки функции невозможно вывести шаблонные параметры (type deduction) и инстанцировать функцию, **это не ошибка компиляции**. Такая перегрузка просто опускается (ill-formed) — а компилятор пробует остальные.
- SFINAE работает только с перегрузками функций.
- SFINAE смотрит только на **заголовок** функции (сигнатуру), а не на тело.
- SFINAE отбрасывает только **шаблонные** функции.
- За счёт SFINAE можно создавать условия, при которых перегрузка отбрасывается, оставляя только подходящие (well-formed).

### Полезная конструкция: `T::*` (указатель на член класса)

Хотим функцию, по-разному работающую для пользовательских типов и всех остальных.
- Шаблонная функция с параметром `int T::*` — будет валидна только для классов/структур (для `int` или `double` такого члена быть не может).
- Шаблонная перегрузка с `...` — для всех остальных типов.

Ошибки компиляции не будет — выберется подходящая.

> Если функцию не вызывать — её можно только объявить, не определяя.
> `decltype` не вызывает функцию — смотрит только на сигнатуру.

```cpp
void print(...) {
    std::cout << "No implementation\n";
}

void print(int i) {
    std::cout << "int value " << i << std::endl;
}

int main() {
    print(1);
    print("Hello world");
    print(1, 1);
}
```

Усложняем:

```cpp
struct Boo {};

int main() {
    using IntBooMemberPtr = int Boo::*;      // OK
    using IntIntMemberPtr = int int::*;       // ERROR — int не класс
}
```

> `int Boo::*` — указатель на член класса `Boo` типа `int`.

Делаем void-функции:

```cpp
template<typename T>
void foo(int T::*) {
    std::cout << "foo(int T::*)\n";
}

template<typename T>
void foo(...) {
    std::cout << "foo(...)\n";
}
```

Используем для определения, является ли тип классом:

```cpp
template<typename T>
std::true_type  can_have_member_ptr(int T::*);

template<typename T>
std::false_type can_have_member_ptr(...);

int main() {
    static_assert(decltype(can_have_member_ptr<Boo>(nullptr)){});
    static_assert(!decltype(can_have_member_ptr<int>(nullptr)){});
}
```

Метафункция `is_class`:

```cpp
template<typename T>
std::true_type  check_class(int T::*);

template<typename T>
std::false_type check_class(...);

template<typename T>
struct is_class : decltype(check_class<T>(nullptr)) {};

template<typename T>
constexpr bool is_class_v = is_class<T>::value;

int main() {
    static_assert(is_class_v<Boo>);
    static_assert(!is_class_v<int>);
}
```

## `std::enable_if`

- Если в шаблон передать `false` — внутри нет `::type`, попытка использовать `enable_if_t<false>` приведёт к **ошибке подстановки** → перегрузка отбрасывается (SFINAE), компилируется другая.
- Если `true` — `::type` есть, всё хорошо.

В чём фокус: теперь можно класть в `enable_if` метафункцию (например, `is_pointer_v<T>`) и явно показывать компилятору, какие перегрузки разрешены, а какие — нет.

```cpp
template<bool, class T = void>
struct enable_if {};

template<class T>
struct enable_if<true, T> {
    using type = T;
};

template<bool B, class T = void>
using enable_if_t = typename enable_if<B, T>::type;
```

```cpp
template<typename T>
void print(const T& value,
           std::enable_if_t<std::is_pointer_v<T>, void*> = nullptr) {
    std::cout << *value << std::endl;
}

template<typename T>
void print(const T& value,
           std::enable_if_t<!std::is_pointer_v<T>, void*> = nullptr) {
    std::cout << value << std::endl;
}

int main() {
    int i = 1;
    print(i);
    print(&i);
}
```

> То же самое можно сделать через `if constexpr` (внутри одной функции). Что лучше — SFINAE или `if constexpr` — дело вкуса; `if constexpr` обычно читабельнее, но не позволяет различать **перегрузки**, только ветви внутри одной функции.

## Metaprogramming + variadic

С вариативными шаблонами можно, например, проверить, что **все** типы интегральные:

```cpp
template<typename... Ts>
constexpr bool all_integral = (std::is_integral_v<Ts> && ...);
```

> Домашнее задание — написать свою `conjunction`.