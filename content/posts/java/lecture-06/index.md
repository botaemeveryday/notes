---
title: Лекция 6
description: Spring Framework
weight: 6
tags:
  - Java
  - 4 Семестр
authors:
  - name: notakeith
    avatar: https://avatars.githubusercontent.com/u/108391756?v=4
    link: https://github.com/notakeith
---

# Лекция 6. Spring Framework

## Что такое Spring Framework

**Spring Framework** — open-source фреймворк (платформа) для языков семейства JVM:

- Java
- Kotlin
- Groovy
- Scala
- C# (форк)

### Spring и Java EE

Spring является **альтернативой Java EE (Jakarta EE)** и по сути его расширением:

- Spring совместим с Java EE (но не обратное)
- Имеет множество расширений (MVC, Data и т.п.)
- Активно поддерживается сообществом

## Inversion of Control (IoC) — инверсия управления

**IoC-контейнер** — центральная часть фреймворка. Предоставляет средства конфигурирования и управления Java-объектами с помощью **рефлексии**.

IoC-контейнер отвечает за:

- Управление **жизненным циклом** объекта
- Создание объектов
- Вызов методов инициализации
- Связывание объектов между собой

Объекты, создаваемые контейнером, называются **бинами (Beans)**.

### Два способа реализации IoC

1. **Поиск зависимостей (Dependency Lookup)** — вызывающий объект запрашивает у контейнера экземпляр объекта с определённым именем или типом
2. **Внедрение зависимостей (Dependency Injection)** — контейнер передаёт экземпляры объектов другим объектам по их имени

### Способы внедрения зависимостей

- **Через конструктор** (Constructor Injection)
- **Через set-метод** (Setter Injection)
- **Через свойства** (Field Injection)

## Spring изнутри: жизненный цикл бина

### 1. Парсинг конфигурации и создание BeanDefinition

Существует три способа конфигурации Spring:

| Способ | Класс контекста |
|--------|-----------------|
| **XML-конфигурация** | `ClassPathXmlApplicationContext("context.xml")` |
| **Аннотации со сканированием пакета** | `AnnotationConfigApplicationContext("package.name")` |
| **JavaConfig** (через `@Configuration`) | `AnnotationConfigApplicationContext(JavaConfig.class)` |

### XML-конфигурация

Использует класс `XmlBeanDefinitionReader`, реализующий интерфейс `BeanDefinitionReader`. Каждый элемент XML обрабатывается, и если он является бином — создаётся `BeanDefinition`. Все `BeanDefinition` помещаются в `Map`, хранящийся в `DefaultListableBeanFactory`.

### Конфигурация через аннотации и JavaConfig

Используется класс `AnnotationConfigApplicationContext`. Внутри два важных поля:

- **ClassPathBeanDefinitionScanner** — сканирует указанный пакет на наличие классов с аннотацией `@Component`. Найденные классы парсируются, для них создаются `BeanDefinition`.
- **AnnotatedBeanDefinitionReader** — работает в несколько этапов:
  1. Регистрирует все `@Configuration` для дальнейшего парсинга
  2. Регистрирует специальный `BeanFactoryPostProcessor` (а именно `BeanDefinitionRegistryPostProcessor`), который парсит JavaConfig через `ConfigurationClassParser` и создаёт `BeanDefinition`

### 2. Настройка созданных BeanDefinition

После первого этапа `BeanDefinition` хранятся в `Map`. Архитектура Spring позволяет повлиять на бины **ещё до их фактического создания** — у нас есть доступ к метаданным класса.

Для этого существует интерфейс **`BeanFactoryPostProcessor`**. Реализовав его, мы получаем доступ к созданным `BeanDefinition` и можем их изменять.

Метод `postProcessBeanFactory` принимает `ConfigurableListableBeanFactory`. Через `getBeanDefinitionNames` можем получить все имена, а затем по конкретному имени — конкретный `BeanDefinition` для обработки метаданных.

### 3. FactoryBean

**FactoryBean** — generic-интерфейс, которому можно делегировать процесс создания бинов определённого типа. Был особенно нужен в эпоху XML-конфигурации, когда требовался механизм управления процессом создания бинов.

### 4. Создание экземпляров бинов

На этом этапе Spring создаёт сами экземпляры бинов согласно `BeanDefinition`.

### 5. Настройка созданных бинов через BeanPostProcessor

Интерфейс **`BeanPostProcessor`** позволяет вклиниться в процесс настройки бинов **до того, как они попадут в контейнер**. Содержит два метода:

- `postProcessBeforeInitialization` — вызывается **до** init-метода
- `postProcessAfterInitialization` — вызывается **после** init-метода

> **Важно:** на этом этапе экземпляр бина уже создан и идёт его донастройка. Если хотите сделать прокси над объектом — делайте это в `postProcessAfterInitialization`.

## Scope бинов

Spring поддерживает несколько scope для бинов:

- **`SCOPE_SINGLETON`** — инициализация **один раз** на этапе поднятия контекста (по умолчанию)
- **`SCOPE_PROTOTYPE`** — инициализация **каждый раз** по запросу

(Также существуют request, session, application и websocket для веб-приложений.)
