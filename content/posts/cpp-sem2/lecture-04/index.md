---
title: Лекция 4
description: Аллокаторы
date: 2025-02-26
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

**Зачем вообще всё это?** — https://habr.com/ru/articles/274827/
**Доп. инфа** — https://habr.com/ru/articles/505632/

## Allocator

— это **класс, который абстрагирует выделение и освобождение памяти** для различных объектов. Предоставляет механизм для выделения и конструирования объектов, а также их освобождения и уничтожения.

Два ключевых метода аллокатора:
- выделить память под `n` элементов типа `T`
- освободить память по указателю, который был ранее выдан

**Зачем писать свой аллокатор?**
Например, для `std::list` хочется выделять память сразу под несколько нод:
- Если на каждую вставку вызывать `malloc` — это неоптимально: обращение к ОС, маппинг страниц на виртуальную память.
- Долго и неудобно «таскать» с собой кэш процессора между разными участками памяти (плохая локальность).

**Выводы:**
- Аллоцировать не каждый раз при вставке, а **сразу большим куском**, а потом раздавать его «по чуть-чуть».
- Если выделить память на стеке — обращение к ней быстрее (горячий кэш, нет системного вызова).
- Простейшая реализация: выделить массив; возвращать первый свободный элемент, сдвигая указатель; при выходе за пределы массива — ошибка.

```cpp
template <typename T>
class CSimpleAllocator {
public:
    pointer allocate(size_type size) {
        pointer result = static_cast<pointer>(malloc(size * sizeof(T)));
        if (result == nullptr) {
            // error
        }
        std::cout << "Allocate count: " << size << " elements. Pointer: " << result << std::endl;
        return result;
    }
    void deallocate(pointer p, size_type n) {
        std::cout << "Deallocate pointer: " << p << std::endl;
        free(p);
    }
};
```

## `rebind`

Объясняет компилятору, как, имея аллокатор для типа `T`, получить аллокатор для типа `U`. Это нужно, потому что **внутри реализации контейнера часто требуется аллокатор для другого типа**, чем тот, который виден снаружи.

Классический пример: `std::list<int>` снаружи кажется, что хранит `int`, но внутри он хранит **ноды** — структуры вида `{ T value; Node* prev; Node* next; }`. Поэтому контейнер через `rebind` запрашивает у переданного `Allocator<int>` соответствующий `Allocator<Node<int>>`.

## StackAllocator

Простая идея: вместо `malloc` использовать заранее выделенный массив; раздавать память «накатом», сдвигая внутренний указатель. `deallocate` ничего не делает — освобождать что-то посередине нельзя, вся память живёт до уничтожения самого аллокатора.

```cpp
#include <iostream>
#include <vector>

template<typename T, size_t SIZE>
class CStackAllocator {
public:
    typedef size_t    size_type;
    typedef ptrdiff_t difference_type;
    typedef T*        pointer;
    typedef const T*  const_pointer;
    typedef T&        reference;
    typedef const T&  const_reference;
    typedef T         value_type;

    template<typename U>
    struct rebind {
        typedef CStackAllocator<U, SIZE> other;
        // Важно: rebind должен давать аллокатор для типа U, а не T.
        // Например, std::list<int> внутри хранит не int, а Node<int>
        // (значение + два указателя), поэтому контейнер через rebind
        // запрашивает аллокатор именно под Node<int>.
    };

    pointer allocate(size_type n) {
        pointer result = buffer_ + size_;
        std::cout << "Allocate " << result << "  " << n << std::endl;
        size_ += n;
        return result;
    }

    void deallocate(pointer p, size_type n) {
        std::cout << "Deallocate " << p << " " << n << std::endl;
        // Реального освобождения нет — память стековая, живёт до уничтожения аллокатора
    }

private:
    T      buffer_[SIZE];
    size_t size_ = 0;
};

int main() {
    CStackAllocator<int, 100> al;
    std::vector<int, CStackAllocator<int, 100>> v;
    for (int i = 0; i < 10; ++i)
        v.push_back(i);
}
```

> **Грубая идея:** «У меня есть массив на `SIZE` элементов типа `T` — выдавай мне куски из него».

По сути, мы передаём ответственность за управление памятью **другой сущности** (аллокатору). Контейнер не должен знать, откуда берётся память.

Так, например, работает `std::list`: при вставке он понимает, что нужна нода (`value + prev + next`), и просит у аллокатора память под неё. Сам список не аллоцирует.

Аллокатор по умолчанию (`std::allocator`) для произвольного `T` делает `::operator new` (по сути `malloc`) при выделении и `::operator delete` (по сути `free`) при освобождении — как `CSimpleAllocator` выше.

`std::vector` использует аллокатор для своего внутреннего буфера, где живут `size` элементов в пределах `capacity`.

## Адаптеры

- **Адаптеры контейнеров** — оборачивают существующие контейнеры в другой интерфейс:
    - `std::stack`
    - `std::queue`
    - `std::priority_queue`
- **Адаптеры итераторов** — отдельный вид итераторов со специальным поведением. Упрощают работу с контейнерами в стандартных алгоритмах ([доп. информация](https://pvs-studio.ru/ru/blog/terms/6561/)):
    - `back_insert_iterator` — output-итератор; вставляет в конец
    - `front_insert_iterator` — вставляет в начало
    - `insert_iterator` — вставляет в заданную позицию
- **Потоковые итераторы** — позволяют работать с потоком (`std::cin`, `std::cout` и т.д.) как с контейнером и применять к нему стандартные алгоритмы.

## Tag Dispatch Idiom

Техника, при которой создаются **пустые теги-типы**, чтобы компилятор выбирал нужную перегрузку функции по переданному тегу. Это позволяет специализировать поведение алгоритма под конкретную категорию итератора (или другую характеристику) **без `if`-веток в рантайме**.

```cpp
template<typename T>
void func_dispatch(const T& value, const tag_1&) {
    std::cout << "tag1\n";
}

template<typename T>
void func_dispatch(const T& value, const tag_2&) {
    std::cout << "tag2\n";
}

template<typename T>
void evaluate(const T& value) {
    func_dispatch(value, typename my_traits<T>::tag());
}
```

```cpp
struct tag_1 {};
struct tag_2 {};
struct tag_3 : public tag_2 {};

struct TypeA {};
struct TypeB {};
struct TypeC {};

template<typename T>
struct my_traits {
    typedef tag_1 tag;
};

template<> struct my_traits<TypeB> {
    typedef tag_2 tag;
};

template<> struct my_traits<TypeC> {
    typedef tag_3 tag;
};
```

## `iterator_traits`

Позволяет алгоритмам узнать свойства переданного итератора (категорию, тип элемента, тип разности) и выбрать наиболее эффективную реализацию для каждой категории. Например, `std::distance` для random-access — `O(1)` (вычитание), а для остальных — `O(n)` (счёт в цикле).