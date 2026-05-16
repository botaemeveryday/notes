---
title: Лекция 7
description: Лямбды
date: 2025-03-19
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

## Указатели на функцию

Работают для глобальных функций и статических методов классов:

```cpp
return_type (*pointer_name)(arg_type1, arg_type2, ... arg_typen)
```

**Пример:**

```cpp
int* findMax(int* array, size_t size, bool(*compare)(int, int)) {
    int* result = array;
    for (int i = 1; i < size; ++i) {
        if (!compare(*result, *(array + i)))
            result = array + i;
    }
    return result;
}

bool greater(int a, int b) {
    return a > b;
}

int main() {
    int array[] = {1, 4, 5, 3, 10, 9};
    std::cout << *findMax(array, sizeof(array) / sizeof(int), greater);
    return 0;
}
```

С `using` — чище:

```cpp
using TComparer = bool(*)(int, int);

int* findMax(int* array, size_t size, TComparer comparer) {
    int* result = array;
    for (int i = 1; i < size; ++i) {
        if (!comparer(*result, *(array + i)))
            result = array + i;
    }
    return result;
}
```

Через шаблон — ещё чище (и можно передавать функторы, не только функции):

```cpp
template<typename TCompare>
int* findMax(int* array, size_t size, TCompare comparer) {
    int* result = array;
    for (int i = 1; i < size; ++i) {
        if (!comparer(*result, *(array + i)))
            result = array + i;
    }
    return result;
}

int main() {
    int array[] = {1, 4, 5, 3, 10, 9};
    std::cout << *findMax(array, sizeof(array) / sizeof(int), std::greater<int>());
    return 0;
}
```

## Функторы

Функтор, в отличие от функции, **может хранить состояние**.

Примеры стандартных функторов из `<functional>`: `std::less`, `std::equal_to`, `std::plus`, `std::logical_and`, и т.д.

```cpp
class GreaterThen {
public:
    GreaterThen(int limit)
        : limit_(limit)
    {}

    bool operator()(int value) const {
        return value > limit_;
    }

private:
    int limit_;
};

int main() {
    std::vector v = {1, 2, 3, 4, 5, 6, 7};

    auto it = std::find_if(
        v.begin(), v.end(),
        GreaterThen{4}
    );

    if (it != v.end())
        std::cout << *it;

    return 0;
}
```

`mutable` — поле, которое может быть изменено из константных методов.

Проблемы такого функтора:
- Не хочется ради такой мелочи выделять целый класс.
- Есть почти то же самое — `std::greater`.

`std::bind` помогает «зафиксировать» часть аргументов существующего функтора:

```cpp
int main() {
    std::vector v = {1, 2, 3, 4, 5, 6, 7};

    auto it = std::find_if(
        v.begin(), v.end(),
        std::bind(std::greater<int>{}, std::placeholders::_1, 4)
    );

    if (it != v.end())
        std::cout << *it;

    return 0;
}
```

## Промежуточный итог по функторам

- Позволяют параметризовать алгоритмы.
- Отделены от вызывающего кода.
- Использовать стандартные функторы в нестандартных ситуациях затруднительно.

## Lambda

[Замыкание](https://en.wikipedia.org/wiki/Closure_(computer_programming)) — позволяет создавать неименованные функторы с захватом переменных из текущей области видимости.

**Синтаксис:**
```
[capture] (params) attrs -> return { body }
```
- `(params)` — optional;
- `attrs` — optional (например, `mutable`, `noexcept`);
- `-> return` — optional (тип возвращаемого значения; помогает компилятору и читающему код).

```cpp
int main() {
    std::vector v = {1, 2, 3, 4, 5, 6, 7};

    auto it = std::find_if(
        v.begin(), v.end(),
        [](int value) { return value > 4; }
    );
    if (it != v.end())
        std::cout << *it;

    return 0;
}
```

**Более читаемо** — синтаксический сахар над функтором.

```cpp
// всё это корректно
int x = 1;
[]{};
[](int i) { return i + 1; };
[](int i) -> float { return i + 1; };
[x](int i) { return x + i; };
[](int i) noexcept { return i + 1; };
[&x](int i) mutable { ++x; return i + x; };
```

Компилятор за нас создаёт функциональный объект — у каждой лямбды свой уникальный тип:

![](images/ea94972b631029e66b37b483d90e59dd.png)

Если написать **две идентичные** лямбды — это всё равно будут два **разных типа**:

![](images/df657ac7f07c6b9d788f2e4876801e1f.png)

---

## Проблемы функторов

- Реализация далеко от места вызова.
- Много текста.
- Часто функтор используется один раз *(самостоятельно писать редко приходится — обычно хватает стандартных)*.

> Начиная с C++11 вместо собственных функторов используют **лямбда-функции**.

## Преимущества лямбд

- Не нужно отдельно писать функционал — прямо в месте использования.
- Не нужно искать реализацию.
- Более элегантный синтаксис, чем у функтора.
- **Захват переменных** из локальной области видимости.

## Захват переменных (capture)

- `[x, y]` — by value
- `[=]` — все используемые в теле — by value, у которых automatic storage duration
- `[&x, &y]` — by reference
- `[&]` — все используемые — by reference (с automatic storage)
- `[this]` — захват `this`-указателя (доступ к полям без копии — `field` обращается к полю объекта)
- `[*this]` — захват **копии текущего объекта** (C++17)

**Example 1: Capture by Value and by Reference**

```cpp
int main() {
    int x = 1;
    int y = 2;

    auto f = [x, &y](int v) { return v + x + y; };
}
```

**Example 2: Capture `*this` by Value (C++17)**

```cpp
struct Foo {
    int field = 0;
};

int func(int i) {
    auto f = [*this](int value) { return field + value; };
    return f(i);
}
```

**Example 3: Capture `this` by Value (Pointer)**

```cpp
struct Foo {
    int field = 0;
};

int func(int i) {
    auto f = [this](int value) { return field + value; };
    return f(i);
}
```

## `mutable` лямбда

- Явно разрешает менять переменную, **захваченную по значению**.
- Захваченная **по ссылке** — меняется и снаружи (как и в обычной функции).
- Захваченная **по значению с `mutable`** — внутри лямбды состояние сохраняется между вызовами, но снаружи переменная не меняется.

> Если написать «сырую» лямбду и сразу её вызвать `[]{ ... }();` — она вызовется один раз на месте.

## Условный выбор объекта-функции

Если нужно в зависимости от условия использовать разные функциональные объекты — это раньше было больно (вызов дефолтного конструктора, потом присваивание; вопросы константности; дефолтного конструктора может вообще не быть). Варианты:
- **Указатель на функцию** — но тогда сами объекты живут на куче, а не на стеке.
- **Лямбда** — инициализируем переменную лямбдой, возвращающей нужный объект.

Изначально лямбды задумывались как упрощённый способ объявления функторов для передачи; сейчас их используют **просто на месте** для красоты.

> Чтобы отказаться от вызова через `()`, можно использовать `std::invoke(f, args...)` — чисто ради эстетики.

## Лямбды и наследование

Если сделать структуру, наследующую от двух функторов, и подключить их `operator()` через `using` — компилятор сможет различать вызовы по типу аргумента (или ругаться при конфликте). По сути функциональный объект = двум функциональным объектам сразу.

Как это упростить:
1. Сделать отдельную фабричную функцию для красивого создания такого объекта.
2. Передавать в эту функцию лямбды вместо функторов.

Раньше похожее делали через `std::bind`, но с появлением лямбд он по большей части не нужен — в лямбду можно вложить другую лямбду.

## Generic lambda (C++14)

Вместо типов аргументов можно ставить `auto` — при инстанциации компилятор сам подберёт тип и создаст шаблонный функтор:

```cpp
auto f = [](auto x, auto y) { return x + y; };
```

## Рекурсивная лямбда

Рекурсия прямо в месте использования. Поскольку лямбда не знает своего имени, есть два классических способа:

```cpp
// (а) Через std::function — лямбда знает себя по имени переменной
std::function<int(int)> fact = [&](int n) {
    return n <= 1 ? 1 : n * fact(n - 1);
};

// (б) Через "Y-комбинатор" — передаём саму себя как аргумент
auto fact = [](auto self, int n) -> int {
    return n <= 1 ? 1 : n * self(self, n - 1);
};
fact(fact, 5);
```

## Function pointer ↔ Lambda

Лямбды **без захвата** обратно совместимы с указателями на функцию — они конвертируются в обычный указатель на функцию. Лямбды с захватом — нет (у них есть состояние).