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
---

conjuction and is_integral в презенташке
void_t
### concepts
- позволяют задавать ограничения для шаблонных (слайдик)

```cpp
template<typename T>
requires std::is_pointer_v<T>
void print(const T& value) {
	std::cout << *value << std::endl;
}

template<typename T>
void print(const T& value) {
	std::cout << value << std::endl;
}
```

- requires
	пишем перед функцией (requires std::is_pointer_v< T >) и будет выбираться такая перегрзка только при это м условии
- Намного проще, чем enable_if
- Лучше, чем if constexpr, потому что в ифик можно не положишь

```cpp
template<typename T, typename U>
concept Addable = requires(T a, U b) {
	a + b;
};

template<typename T, typename U>
requires Addable<T,U>
auto add(const T& a, const U& b) {
	return a + b;
}

int main() {
	add(1, 2);
	add(Foo{}, Foo{});
}
```


- Основная мощь концептов - требования к типам
- concept - расписывается требование к типам
	- к примеру требование к суммированию типов
	- просто дают более понятную ошибку компиляции
	- но и делают sfinae
	- можно использовать в шаблоне template< typename T, Addable< T > U> - превратится в requires
	- можно написать перед фигурными скобочками concept
	- можно вообще шаблоны не испоьзовать, а decltype и auto

# Requirements
- **simple**
	- один require
- **type**
- **compound** 
	- когда ещё и требует какое-то определённое возвращаемое значение, требование к noexcept
- **nested**
	- несколько requires

```cpp
template<typename... Args>
concept Addable = requires(Args... args) {
	(args + ...); // simple requirement
};

template<typename... Args>
requires Addable<Args...>
auto add(Args&&... args) {
	return (args + ...);
}

int main() {
	add(Foo{}, Foo{});
	add(1,2,3,4);
}
```

### nested requirements
```cpp
template<class T, typename... TArgs>
constexpr bool are_all_same = std::disjunction_v<std::is_same<T, TArgs>...>;

template<typename... Args>
concept Addable = requires(Args... args) {
	(args + ...); // simple requirement
	requires sizeof...(Args) > 1;
	requires are_all_same<Args...>;
};
```

### compound requirements
```cpp
template<typename... Ts>
using first_arg_t = first_arg<Ts...>::type;

template<typename... Args>
concept Addable = requires(Args... args) {
	(args + ...); // simple requirement
	requires sizeof...(Args) > 1;
	requires are_all_same<Args...>;
	{(args + ...)} noexcept -> std::same_as<first_arg_t<Args...>>;
};
```

### type requirements
```cpp
template<typename... Ts>
using first_arg_t = first_arg<Ts...>::type;

template<typename... Args>
concept Addable = requires(Args... args) {
	(args + ...); // simple requirement
	requires sizeof...(Args) > 1;
	requires are_all_same<Args...>;
	{(args + ...)} noexcept -> std::same_as<first_arg_t<Args...>>;
};
```


Область применения:
- Выбор того или иного в зависимости от требований
