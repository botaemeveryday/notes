---
title: Metaprogramming
date: 2025-05-07
cover: images/cover.png
tags:
  - 2 семестр
  - Основы программирования
nolastmod: true
draft: false
description: Лекция 14
---

### Метапрограммирование (продолжение)
### is_same (naive)
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
отличает одинаковые `Т`, имеет шаблон для одинаковых `Т` тру, а во всех других случаях false

если убрать `::value` и забыть о треугольных скобочках, то шаблон почти превращается в шаблон 

мы пишем структуру, которая создаёт метафункцию

любую функцию можно попробовать переписать на метафункцию

### identity
в прошлый раз писали `identity` 

вот обычная функция
```cpp
template<typename T>
T&& identity(T&& value) {
	return std::forward<T>(value);
}

int main() {
	int x = identity(239);
}
```

вот переписали круто на метафункцию ура
теперь она вычисляется в компайл тайме
```cpp
template<typename T, T Value>
	struct value_identity {
	static constexpr T value = Value;
};

int main() {
	int x = value_identity<int, 239>::value;
}
```
ограничения:
- нужно знать данные на момент компиляции
- только литеральные типы

грустно что нужно `int` указывать, а давайте по приколу напишем auto
```cpp
template<auto Value>
struct value_identity {
	static constexpr auto value = Value;
};

int main() {
	static_assert(value_identity<239>::value == 239);
}
```


метафункции можно написать и с помощью вариативных шаблонов
```cpp
template<auto... Value>
struct sum {
	static constexpr auto value = (Value + ...);
};

int main() {
	static_assert(sum<1,2,3,4,5>::value == 15);
}
```

функции ранее в качестве результата возвращали какое-то конкретное значение 

в отличие от обычных функций, метафункции не обязаны возвращать указанные типы , она может вернуть в качестве результата даже просто сам тип

два типа метафункций
1) могут возвращать типы
2) могут возвращать значения
```cpp
struct Boo {};

int main() {
	static_assert(
	std::is_same<
		std::type_identity<Boo>::type
		Boo
	>::value
);

}
```

хотим избавится от `::`, а давайте воспользуемся юсингом

договорённость такая: если имеем метафункцию, для неё можно написать класс `подчеркушка t` или `подчеркушка v`, которые возвращают тип и значение соответственно
```cpp
template< class T, class U >
constexpr bool is_same_v = is_same<T, U>::value;

template <typename T>
using type_identity_t = typename std::type_identity<T>::type;

int main() {
	static_assert(
		std::is_same_v<std:: type_identity_t<Boo>, Boo>
	);
}
```

### integral_constant

принимает `T` и принимает `value`

объединяет обе идеи, которые писали ранее: возвращает и тип и значение
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
    

template< bool B >
using bool_constant = integral_constant<bool, B>;

using true_type = integral_constant<bool, true>;
using false_type = integral_constant<bool, false>;
```

интегральная потому что вместо `value` можем подставить только интегральный тип

> интегральный тип это **целочисленный тип**

и теперь эта гениальная вещь позволяет делать метафункции проще и лаконичнее 
```cpp
template<class T, class U>
struct is_same : std::false_type {};

template<class T>
struct is_same<T, T> : std::true_type {};
```

### type_traits
[<type_traits>](https://en.cppreference.com/w/cpp/header/type_traits)
Содержит набор метафункция для работы с типами
- Primary type categories
- Composite type categories
- Type properties
- Supported operations
- Type relationships
- Const-volatility specifiers
- etc

давайте скопируем их наработки:

пишем “является ли тип указателем”
```cpp
template<class T>
struct is_pointer : std::false_type {};

template<class T>
struct is_pointer<T*> : std::true_type {};

template<class T>
struct is_pointer<T* const> : std::true_type {};

template<class T>
struct is_pointer<T* volatile> : std::true_type {};

template<class T>
struct is_pointer<T* const volatile> : std::true_type {};

template <typename T>
inline constexpr bool is_pointer_v = is_pointer< T>::value;
```

проблема в том что `const`, `volatile` мешает обычному TAD с `T*` нужны специализации с указанием этих модификаторов

если на 2 переменные, тогда нужно будет очень много перегрузок (комбинаторика)

т.е. хотим избавиться от обилия перегрузок

просто напишем метафункцию которая снимает const
```cpp
template<typename T>
struct remove_const {
	using type = T
}
template<typename T>
struct remove_const<const T> {
	using type = T
}
```

такой же фокус с volatile
```cpp
template<typename T>
struct remove_volatile {
	using type = T
}
template<typename T>
struct remove_volatile<volatile T> {
	using type = T
}
```

а давайте объединим 
```cpp
template<typename T>
using remove_cv = remove_volatile<typename remove_const<T>::type>::type
```

перепишем `is_pointer` с `remove_cv`
```cpp
template <typename T>
inline constexpr bool is_pointer_v = is_pointer<remove_cv<T>>::value;
```

Александр Павлович сказал это not so good, ведь нельзя пользоваться просто `is_pointer`, поэтому будем писать иначе. Перепишем полностью `is_pointer`
```cpp
template<typename T>
struct is_pointer_innter : std::false_type{};

template<typename T>
struct is_pointer_innter<T*> : std::true_type{};

template<typename T>
struct is_ponter : is_pointer_inner<remove_cv<T>>{};
```

### SFINAE
- *"Substitution Failure Is Not An Error"* (неудавшаяся подстановка — не ошибка)
- Если для перегрузки функции невозможно вывести параметры шаблона *(type deduction)* и инстанциировть функцию, то это не приводит к ошибки компиляции. Такая перегрузка опускается *(ill-formed)*
- SFINAE работает только с перегрузками функций
- SFINAE рассматривает только заголовки функция
- SFINAE отбрасывает только шаблонные функции
- За счета SFINAE можно создавать условия, когда перегрузка будет отбрасываеться *(well-formed)*

- T::* - указатель на член структуры/класса

- Хотим сделать функцию, которая будет по-разному работать для пользовательских типов и всех остальных
- Делаем шаблонную функцию с вызовом Т::* , будет использоваться для пользовательских типов
- Делаем шаблонную перегрузку функции для ..., которая будет выбираться для всех типов, кроме классов и структур
- Ошибки компиляции не будет, выберет то, что нужно

- Если мы не вызываем функцию, то её можно не определять, а только объявлять
- decltype не вызывает функцию, чисто на сигнатуру смотрит

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
	print(1,1);
}
```

перейдем к примеру посложнее
```cpp
struct Boo{};

int maint() {
using IntBooMemberPtr = int Boo::*;
using IntBooMemberPtr = int int::*;
}
```

P.S. `int Boo::*` это указатель на член класса `Boo` типа `int`

сделаем функцию void
```cpp
template<typename T>
void foo(int T::*) {
	std::cout << "foo(int T::*)\n"
}

template<typename T>
void foo(...) {
	std::cout << "foo(...)\n"
}
```

обладая знаниями, полученными ранее, можем сделать так:
```cpp
template <typename T>
std::true_type can_have_member_ptr(int T::*);

template <typename T>
std::false_type can_have_member_ptr(...);

int main() {
	static_assert(decltype(can_have_member_ptr<Boo>(nullptr)){});
	static_assert(!decltype(can_have_member_ptr<int>(nullptr)){});
}
```


напишем метафункцию, которая позволит определить класс ли это
```cpp
template<typename T>
std::true_type check_class(int T::*);

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

### std::enable_if
- если в шаблон передать false, то она по типу ничего не возвращает, соответственно она просто не скомпилируется и выберется другая функция
- если в шаболне true, то из неё можно получить тип
- в чём фокус?
- теперь можем класть в аргумент шаблона метафункции
- засчёт этой функции явно показываем, что теперь может быть ill_formed;
- тоже самое можно писать просто за счёт if constexpr
- Что лучше sfinae или if constexpr - вкусовщина

```cpp
template <bool, class T = void>
struct enable_if {};

template <class T>
struct enable_if<true, T> {
	using type = T;
};

template <bool B, class T = void>
using enable_if_t = typename enable_if<B, T>::type;
```

```cpp hl:13-14
template<typename T>
void print(const T& value, std::enable_if_t<std::is_pointer_v<T>, void*> = nullptr) {
	std::cout << *value << std::endl;
}

template<typename T>
void print(const T& value, std::enable_if_t<!std::is_pointer_v<T>, void*> = nullptr) {
	std::cout << value << std::endl;
}

int main() {
	int i = 1;
	print(i);
	print(&i);
}
```



#### Metaprogramming+variadic
- Вариативные шаблоны
- можем узнать, являются ли все типы интегральными
- дз - написать свою конъюкцию