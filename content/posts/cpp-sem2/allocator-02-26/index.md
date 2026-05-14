---
title: Allocator
date: 2025-02-26
cover: images/cover.png
tags:
  - 2 семестр
  - Основы программирования
nolastmod: true
draft: false
description: Лекция 4
authors:
  - name: notakeith
    avatar: https://avatars.githubusercontent.com/u/108391756?v=4
    link: https://github.com/notakeith
  - name: salt-caramel
    avatar: https://avatars.githubusercontent.com/u/180561221?v=4
    link: https://github.com/salt-caramel
---

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

**Зачем вообще всё это?** — https://habr.com/ru/articles/274827/  
**Доп. инфа** — https://habr.com/ru/articles/505632/

### Allocator

— это **класс, который отвечает за абстрагирование выделения и освобождения памяти для различных объектов**. Он предоставляет механизм для выделения и конструирования объектов, а также для их освобождения и уничтожения.

У аллокатора есть 2 ключевых метода:
- выделить память под `n` элементов типа `T`
- освободить память по указателю, который был ранее выдан

Часто может возникать потребность написать свой аллокатор (например, чтобы для `std::list` выделять память сразу под ноду):
- если на каждую вставку вызывать `malloc`, то это неоптимально: приходится обращаться к системе, брать память, маппить её на виртуальную таблицу
- долго и неудобно «таскать» с собой кэш процессора на разные участки памяти
- Выводы:
    - нужно аллоцировать память не каждый раз при вставке. То есть единожды выделить большой блок, а потом раздавать из него куски
    - если выделить память на стеке, обращение к ней будет быстрее
    - пример: выделить массив памяти, а потом возвращать первый свободный элемент (указатель на свободное место сдвигается; при выходе за пределы массива — ошибка)

`rebind` объясняет компилятору, как, имея аллокатор типа `T`, получить аллокатор типа `U`. Это нужно, потому что внутри реализации одного контейнера может потребоваться аллокатор для другого типа.

---

### StackAllocator

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
        // Например, std::list<int> внутри хранит не int, а Node<int> (значение + два указателя),
        // поэтому контейнер через rebind запрашивает аллокатор именно под Node<int>.
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

**Аллокатор** — абстракция, которая знает про тип `T` и умеет: по умолчанию выдавать память под `n` элементов этого типа и освобождать её обратно.

> **Как это грубо говоря работает:**  
> «У меня есть указатель на `n` элементов типа `T` — верни мне память»

По сути мы передаём ответственность за управление памятью другой сущности.

Есть `std::list`. Когда происходит вставка, лист знает, что он двусвязный: нужно взять где-то память под ноду (значение + два указателя `prev`/`next`). Именно аллокатор эту память возвращает — ответственность не лежит на самом листе.

Аллокатор по умолчанию (`std::allocator`) для произвольного типа `T` делает `malloc` при выделении и `free` при освобождении — примерно как `CSimpleAllocator` выше.

В `std::vector` есть `capacity` и `size` — вектор также использует аллокатор для управления своим внутренним буфером.

---

- **Адаптеры контейнеров** — адаптируют существующие контейнеры под другие интерфейсы:
    - стек (`std::stack`)
    - очередь (`std::queue`)
    - приоритетная очередь (`std::priority_queue`)
- **Адаптеры итераторов** — отдельный вид итераторов со специальным поведением. Упрощают работу с контейнерами и очень полезны в стандартных алгоритмах. Умеют делать итераторы из других объектов. ([доп. информация](https://pvs-studio.ru/ru/blog/terms/6561/))
    - `back_insert_iterator` — удовлетворяет требованиям выходного итератора; вставляет в конец
    - `front_insert_iterator` — вставляет в начало
    - `insert_iterator` — вставляет в произвольную позицию
- **Потоковые итераторы** — часто бывает, что поток содержит однотипные элементы. В таких случаях потоковые итераторы позволяют работать с потоком как с контейнером и применять к нему стандартные алгоритмы.
- **Tag Dispatch Idiom** — техника, при которой создаются пустые теги-типы, чтобы компилятор выбирал нужную перегрузку функции в зависимости от переданного тега. Это позволяет специализировать поведение алгоритма под конкретную категорию итератора без `if`-веток в рантайме.

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

- **`iterator_traits`** — позволяет алгоритмам узнать свойства переданного итератора (категорию, тип элемента, тип разности) и использовать наиболее эффективную реализацию для каждой категории.
