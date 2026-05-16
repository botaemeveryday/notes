---
title: Лекция 5
description: Работа с базами данных (JDBC и JPA)
weight: 5
tags:
  - Java
  - 4 Семестр
authors:
  - name: notakeith
    avatar: https://avatars.githubusercontent.com/u/108391756?v=4
    link: https://github.com/notakeith
---

# Лекция 5. Работа с базами данных (JDBC и JPA)

## Архитектура Java EE приложений

Java EE приложения разделены по функциональному принципу на изолированные модули. Обычно делятся на **три уровня** (как у Фаулера):

1. **Клиентский уровень**
2. **Промежуточный уровень (BLL)** — Business Logic Layer
3. **Уровень доступа к данным (DAL)**

### Технологии уровня доступа к данным

- **JDBC** — Java Database Connectivity API
- **JPA** — Java Persistence API
- **Java EE Connector Architecture**
- **JTA** — Java Transaction API

## JDBC — Java Database Connectivity

**Низкоуровневое API** для доступа к данным в хранилищах. Типичное использование — написание SQL-запросов к конкретной базе.

### JDBC Driver Manager

Java-приложение общается с БД через **JDBC Driver** — набор классов, реализующих JDBC API для конкретной СУБД.

Драйвер выбирается через **DriverManager**. Можно использовать In-Memory-DB, NoSQL-DB или базу, встроенную в Android-приложение — Java-разработчика эти нюансы не касаются, DriverManager сам выберет подходящий драйвер.

### Connection String

Для подключения протокола JDBC API:

```
jdbc:mysql://localhost:3306/db_scheme
```

- `mysql` — протокол работы с сервером
- `localhost` — имя хоста в сети
- `3306` — порт
- `db_scheme` — имя схемы (БД)

### Установка JDBC Driver

Драйвер для конкретной БД нужно установить через систему сборки:

```xml
<dependency>
    <groupId>mysql</groupId>
    <artifactId>mysql-connector-java</artifactId>
    <version>8.0.29</version>
</dependency>
```

### Statements

SQL-запросы делятся на две группы:

| Группа | Операторы | Метод |
|--------|-----------|-------|
| **Получение данных** | `SELECT` | `executeQuery()` — возвращает `ResultSet` |
| **Изменение данных** | `INSERT`, `UPDATE`, `DELETE` | `executeUpdate()` — возвращает число изменённых строк |

### Callable Statements

**CallableStatement** используется для вызова хранимых процедур в БД. Хранимая процедура похожа на функцию класса, но находится в базе данных. Тяжёлые операции с БД могут выиграть в производительности при выполнении в том же пространстве памяти, что и сервер БД.

### DataSource и ConnectionPoolDataSource

Интерфейсы из пакета `javax.sql`, реализуемые поставщиками JDBC-классов.

**Основное назначение:** предоставить возможность получения соединения с БД **абстрагируясь от местоположения сервера СУБД и типа драйвера**.

Объекты `DataSource` используются для получения **физического соединения** с БД и являются **альтернативой DriverManager** — нет необходимости регистрировать драйвер. Достаточно установить параметры соединения и вызвать `getConnection()`.

## JTA — Java Transaction API

**API для определения и управления транзакциями**, включая распределённые транзакции, а также транзакции, затрагивающие множество хранилищ данных.

## JPA — Java Persistence API

**JPA** — спецификация Java EE и Java SE, описывающая систему управления **сохранением Java-объектов в таблицы реляционных БД**. Гораздо более высокоуровневое API по сравнению с JDBC — скрывает всю его сложность.

### JDO vs JPA

**JDO** (Java Data Objects) — более общая спецификация ORM для любых баз и хранилищ. **JPA** можно рассматривать как часть JDO, специализированную на реляционных базах.

### Hibernate

**Hibernate** — самая популярная open-source реализация JPA (де-факто стандарт). JPA только описывает правила и API, а Hibernate реализует эти описания. Hibernate имеет дополнительные возможности, не описанные в JPA (и не переносимые на другие реализации).

## JPA Entity

**Entity** — это легковесный хранимый объект бизнес-логики (persistent domain object). Основная программная сущность — entity-класс. Может использовать дополнительные вспомогательные классы.

### Жизненный цикл Entity

У Entity четыре статуса:

1. **new** — объект создан, ещё нет сгенерированных первичных ключей, не сохранён в БД
2. **managed** — объект создан, управляется JPA, имеет первичные ключи
3. **detached** — объект был создан, но не управляется (или больше не управляется) JPA
4. **removed** — объект создан, управляется JPA, но будет удалён после коммита транзакции

## JPA EntityManager

**EntityManager** — главный интерфейс для работы с JPA. Описывает API для всех основных операций.

### Группы операций EntityManager

**1. Операции над Entity:**

- `persist` — сохранение нового объекта
- `merge` — слияние с существующим
- `remove` — удаление
- `refresh` — обновление из БД
- `detach` — отсоединение от управления
- `lock` — блокировка

**2. Получение данных:**

- `find` — поиск по ключу
- `createQuery`, `createNamedQuery`, `createNativeQuery` — создание запросов
- `contains` — проверка наличия
- `createNamedStoredProcedureQuery`, `createStoredProcedureQuery` — вызов процедур

**3. Получение других сущностей JPA:**

- `getTransaction` — транзакция
- `getEntityManagerFactory` — фабрика
- `getCriteriaBuilder` — построитель критериев
- `getMetamodel` — метамодель
- `getDelegate` — делегат

**4. Работа с EntityGraph:**

- `createEntityGraph`, `getEntityGraph`

**5. Общие операции:**

- `close`, `isOpen`, `getProperties`, `setProperty`, `clear`
