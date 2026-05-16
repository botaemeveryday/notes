---
title: Лекция 8
description: Spring MVC
weight: 8
tags:
  - Java
  - 4 Семестр
authors:
  - name: notakeith
    avatar: https://avatars.githubusercontent.com/u/108391756?v=4
    link: https://github.com/notakeith
---

# Лекция 8. Spring MVC

## Что такое Spring MVC

**Spring MVC** — модуль, обеспечивающий архитектуру паттерна **Model — View — Controller** при помощи слабосвязанных готовых компонентов.

Паттерн MVC разделяет аспекты приложения и обеспечивает свободную связь между ними:

| Компонент | Назначение |
|-----------|------------|
| **Model** (Модель) | Инкапсулирует данные приложения. Обычно — POJO («Plain Old Java Objects» или бины) |
| **View** (Отображение) | Отвечает за отображение данных Модели, обычно генерируя HTML |
| **Controller** (Контроллер) | Обрабатывает запрос пользователя, создаёт Модель и передаёт её в View |

## DispatcherServlet — сердце Spring MVC

Spring MVC построен вокруг центрального сервлета — **DispatcherServlet**, который:

- Распределяет запросы по контроллерам
- Полностью интегрирован в Spring IoC-контейнер
- Имеет доступ ко всем возможностям Spring

### Базовый алгоритм работы DispatcherServlet

1. Получает HTTP-запрос
2. Обращается к **HandlerMapping** для определения, какой контроллер вызвать
3. Отправляет запрос в нужный контроллер
4. Контроллер вызывает соответствующий метод (на основе GET/POST), формирует Модель и возвращает имя View
5. **ViewResolver** определяет, какой View использовать на основе полученного имени
6. После создания View, DispatcherServlet отправляет данные Модели в виде атрибутов в View, который отображается в браузере

## Аннотация @Controller

`DispatcherServlet` отправляет запрос **контроллерам**. Аннотация **`@Controller`** указывает, что класс является контроллером. **`@RequestMapping`** связывает класс или метод с URL.

## Специальные бины Spring MVC

`DispatcherServlet` делегирует специальные компоненты для обработки запросов:

| Бин | Назначение |
|-----|------------|
| **HandlerMapping** | Сопоставляет запрос с обработчиком (handler-объектом) и списком интерсепторов |
| **HandlerAdapter** | Помогает DispatcherServlet вызвать обработчик независимо от того, как он реализован |
| **HandlerExceptionResolver** | Стратегия разрешения исключений: сопоставление с обработчиками, представлениями ошибок |
| **ViewResolver** | Преобразует логические имена View в фактические View |
| **LocaleResolver / LocaleContextResolver** | Определяет «локаль» клиента и часовой пояс для интернационализированных представлений |
| **ThemeResolver** | Определяет темы веб-приложения |
| **MultipartResolver** | Абстракция для разбора multipart-запросов (загрузка файлов) |
| **FlashMapManager** | Хранит и извлекает «входную» и «выходную» FlashMap для передачи атрибутов между запросами (через redirect) |

### Реализации HandlerMapping

Основные реализации:

- **RequestMappingHandlerMapping** — поддерживает аннотированные методы `@RequestMapping`
- **SimpleUrlHandlerMapping** — поддерживает явную регистрацию шаблонов пути URI к обработчикам
- **BeanNameUrlHandlerMapping**

### Реализации HandlerAdapter

- **HttpRequestHandlerAdapter** — поддерживает классы, реализующие `HttpRequestHandler`
- **SimpleControllerHandlerAdapter** — поддерживает классы, реализующие `Controller`
- **RequestMappingHandlerAdapter** — поддерживает контроллеры с `@RequestMapping`

## Полный путь HTTP-запроса в Spring MVC

### Шаг 1. Поиск обработчика

После получения HTTP-запроса `DispatcherServlet` перебирает доступные `HandlerMapping`. Один из них определит, какой метод какого контроллера должен быть вызван.

- HandlerMapping по `HttpServletRequest` находит **handler-объект** (например, `HandlerMethod`)
- Каждый HandlerMapping может иметь несколько реализаций `HandlerInterceptor` — для кастомизации пред- и пост-обработки запроса
- Список `HandlerInterceptor` + handler-объект → формируют `HandlerExecutionChain`

### Шаг 2. Выбор HandlerAdapter

Для выбранного обработчика определяется соответствующий `HandlerAdapter`.

### Шаг 3. Предобработка (preHandle)

Вызывается `applyPreHandle` на `HandlerExecutionChain`:

- Если вернул `true` — все интерсепторы выполнили предобработку, переходим к основному обработчику
- Если вернул `false` — один из интерсепторов взял обработку ответа на себя

### Шаг 4. Вызов handle

HandlerAdapter извлекается из `HandlerExecutionChain`. Через метод `handle` принимаются объекты запроса и ответа, а также метод-обработчик.

### Шаг 5. Возврат ModelAndView

Метод-обработчик возвращает в `DispatcherServlet` объект **ModelAndView**. Через `ViewResolver` определяется, какой View использовать.

**Для REST-контроллеров:**

- Вместо `ModelAndView` возвращается `null`
- `ViewResolver` не используется
- Ответ полностью содержится в теле `HttpServletResponse`
- Контроллер аннотируется `@RestController` или методы — `@ResponseBody`

### Шаг 6. Постобработка (postHandle)

Перед завершением вызывается `applyPostHandle` для постобработки с помощью интерсепторов.

### Шаг 7. Обработка исключений

Если в процессе обработки выбрасывается исключение, обрабатывается через одну из реализаций `HandlerExceptionResolver`:

- **ExceptionHandlerExceptionResolver** — обрабатывает исключения из методов с `@ExceptionHandler`
- **ResponseStatusExceptionResolver** — отображает исключения с `@ResponseStatus` в HTTP-статусы
- **DefaultHandlerExceptionResolver** — отображает стандартные исключения Spring MVC в HTTP-статусы

### Шаг 8. Рендеринг View

Для классических контроллеров — `DispatcherServlet` отправляет данные в виде атрибутов в View, который записывается в `HttpServletResponse`. Для REST — данная логика не вызывается, ответ уже в `HttpServletResponse`.

## HttpMessageConverter

Когда HTTP-запрос приходит с заголовком `Accept`, Spring MVC перебирает доступные `HttpMessageConverter`, пока не найдёт того, кто сможет конвертировать из POJO в указанный тип `Accept`.

**HttpMessageConverter работает в обоих направлениях:**

- Тела входящих запросов конвертируются в Java-объекты
- Java-объекты конвертируются в тела HTTP-ответов

Spring Boot определяет довольно обширный набор реализаций `HttpMessageConverter`. Можно добавлять собственные реализации или переопределять существующие.
