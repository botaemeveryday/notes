---
title: Лекция 1
description: Специализация шаблонов. Умные указатели
date: 2025-02-05
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

## Идиома RAII

**RAII (Resource Acquisition Is Initialization)** — идиома, при которой ресурс (память, файл, сокет, мьютекс) захватывается в конструкторе и освобождается в деструкторе. Это гарантирует, что ресурс будет освобождён при любом выходе из области видимости — нормальном завершении, `return` посередине функции, или раскрутке стека при исключении.

**Проблема без RAII:** код может закончить работу до того, как вызовется `delete` — например, из-за раннего `return` или исключения. Память утечёт.

```cpp
// Плохо: если return сработает раньше delete — утечка
void func() {
    int* ptri = new int(5);
    return;
    /* ... */
    delete ptri;  // никогда не выполнится
}
```

**Решение** — обернуть указатель в класс, который сам управляет временем жизни ресурса:

```cpp
// Используя идиому RAII
class AutoPtr {
public:
    AutoPtr(int value)
        : value_(new int(value))  // в списке инициализации можно вызывать new
    {}

    ~AutoPtr() {
        delete value_;
    }

    int operator*() {
        return *value_;
    }
private:
    int* value_;
};

void func() {
    AutoPtr ptr(5);
    return;  // деструктор сам освободит память
}
```

## Конструктор копирования и оператор присваивания

- Чтобы поддерживать цепочки присваиваний (`a = b = c`), оператор `=` должен возвращать `*this` по ссылке.
- Дефолтный конструктор копирования просто скопирует указатель — а потом деструктор каждого из двух объектов попытается освободить **одну и ту же память**. Это **double-free** → undefined behavior.
- Поэтому конструктор копирования должен **сам выделять новую память** и копировать в неё значение.

```cpp
AutoPtr(const AutoPtr& other)
    : value_(new T(*(other.value_)))
{}

AutoPtr& operator=(const AutoPtr& other) {
    if (&other == this) {        // защита от самоприсваивания
        return *this;
    }
    delete value_;                // освобождаем старое
    value_ = new T(*(other.value_));  // копируем новое
    return *this;
}
```

Если же указатель не сам создаёт объект, а ему **передают владение** уже существующим указателем — есть три стратегии копирования.

---

## Стратегия 1. «Передаю владение ресурсом» — `std::auto_ptr` (устарел)

Передаём значение, а у источника обнуляем — теперь владелец только один. Это стандарт C++98, `std::auto_ptr`. **Был удалён в C++17** из-за коварства: владение могло «незаметно» утечь, например при копировании внутрь контейнера.

```cpp
AutoPtr(AutoPtr& other) {
    value_ = other.value_;
    other.value_ = nullptr;   // отбираем владение
}

AutoPtr& operator=(AutoPtr& other) {
    if (&other == this) {
        return *this;
    }
    value_ = other.value_;
    other.value_ = nullptr;
    return *this;
}
```

Пример коварства:

```cpp
int main() {
    auto_ptr<Boo> b{new Boo()};
    std::vector<auto_ptr<Boo>> boos(1);

    boos[0] = b;          // владение незаметно ушло из b в boos[0]
    boos[0]->func();
    auto_ptr<Boo> a = boos[0];   // и теперь — из boos[0] в a
    a->func();

    // b->func();         // Segmentation fault — b больше ничем не владеет
    // boos[0]->func();   // Segmentation fault — boos[0] тоже пуст

    return 0;
}
```

---

## Стратегия 2. «Ресурс мой, никому не отдам» — `std::unique_ptr`

Просто запрещаем копирование. Один объект — один владелец. Передача владения возможна только явно через `std::move` (об этом позже).

```cpp
AutoPtr(const AutoPtr& other) = delete;
AutoPtr& operator=(const AutoPtr& other) = delete;
```

У `std::unique_ptr` есть второй шаблонный параметр — **`Deleter`** (функтор). По умолчанию это `delete`, но можно передать свой, чтобы освобождать не только память. Например, файл закрывается через `fclose`:

```cpp
template<typename T, typename DeletePtr>
class AutoPtr {
public:
    AutoPtr(T* value) : value_(value) {}
    ~AutoPtr() {
        if (value_) {
            DeletePtr deleter;
            deleter(value_);
        }
    }
    /* ... */
private:
    T* value_;
};

struct FileDeleter {
    void operator()(FILE* f) const { fclose(f); }
};

int main() {
    FILE* file = fopen("in.txt", "r");
    AutoPtr<FILE, FileDeleter> fPtr(file);
    // fclose будет вызван автоматически в деструкторе
}
```

Также у `unique_ptr` есть метод `release()` — отдаёт сырой указатель и снимает с себя ответственность за его освобождение.

---

## Стратегия 3. «Делим ресурс» — `std::shared_ptr`

Несколько объектов могут совместно владеть одним ресурсом. Ресурс освобождается, **когда уничтожается последний владелец**.

**Как работает:** хранится указатель на счётчик владельцев (reference count). Копирование увеличивает счётчик, деструктор уменьшает. При счётчике 0 — ресурс освобождается.

> **Совет:** сначала тянись к `unique_ptr`, и только если действительно нужно разделять владение — к `shared_ptr`. Он немного дороже (атомарный счётчик, дополнительная аллокация).

### Проблема циклических ссылок

```cpp
struct A;
struct B {
    B()  { std::cout << "B\n";  }
    ~B() { std::cout << "~B\n"; }
    std::shared_ptr<A> ptr;
};
struct A {
    A()  { std::cout << "A\n";  }
    ~A() { std::cout << "~A\n"; }
    std::shared_ptr<B> ptr;
};

void func() {
    std::shared_ptr<A> a{new A()};
    std::shared_ptr<B> b{new B()};
    a->ptr = b;
    b->ptr = a;

    std::cout << a.use_count() << " " << a->ptr.use_count() << std::endl;
    std::cout << b.use_count() << " " << b->ptr.use_count() << std::endl;
    // выйдя из функции, локальные a и b уйдут — но ресурсы НЕ освободятся:
    // a держит b, b держит a → счётчики так и останутся равными 1
}

int main() {
    func();
}
```

### Решение: `std::weak_ptr`

`weak_ptr` **не владеет** объектом напрямую (не увеличивает счётчик), но знает о его существовании. Чтобы получить доступ — вызывают `lock()`: если объект ещё жив, вернётся `shared_ptr`; если умер — пустой `shared_ptr`.

```cpp
struct A;
struct B {
    B()  { std::cout << "B\n";  }
    ~B() { std::cout << "~B\n"; }
    std::weak_ptr<A> ptr;    // заменили shared_ptr на weak_ptr
};
struct A {
    A()  { std::cout << "A\n";  }
    ~A() { std::cout << "~A\n"; }
    std::weak_ptr<B> ptr;    // и здесь тоже
};

void func() {
    std::shared_ptr<A> a{new A()};
    std::shared_ptr<B> b{new B()};
    a->ptr = b;
    b->ptr = a;
    // теперь циклической shared-зависимости нет — деструкторы вызовутся
}
```