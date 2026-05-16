---
title: Лекция 10
description: Spring Data JPA
weight: 10
tags:
  - Java
  - 4 Семестр
authors:
  - name: notakeith
    avatar: https://avatars.githubusercontent.com/u/108391756?v=4
    link: https://github.com/notakeith
---

# Лекция 10. Spring Data JPA

## Что такое Spring Data

**Spring Data** — дополнительный удобный механизм для взаимодействия с сущностями БД, их организации в репозитории, извлечения и изменения данных. В некоторых случаях достаточно объявить **интерфейс с методом без реализации** — Spring сгенерирует её сам.

## Spring Repository

Основное понятие в Spring Data — **репозиторий**. Это интерфейсы, использующие JPA Entity для взаимодействия с базой.

### Базовый интерфейс — CrudRepository

```java
public interface CrudRepository<T, ID extends Serializable>
    extends Repository<T, ID>
```

Обеспечивает основные **CRUD-операции:**

| Буква | Операция |
|-------|----------|
| **C** | Create — создание |
| **R** | Read — чтение |
| **U** | Update — обновление |
| **D** | Delete — удаление |

### Другие абстракции репозиториев

- **PagingAndSortingRepository** — добавляет пагинацию и сортировку
- **JpaRepository** — JPA-специфичный, добавляет flush и batch-операции

### Расширение базового интерфейса

Если предоставленных методов достаточно — расширяете базовый интерфейс для своей сущности и добавляете свои методы запросов.

## Spring Data и сканирование сущностей

Традиционно сущности JPA задаются в `persistence.xml`. **В Spring Boot этот файл не требуется** — используется **Entity Scanning**. По умолчанию поиск выполняется во всех пакетах ниже основного конфигурационного класса (с `@EnableAutoConfiguration` или `@SpringBootApplication`).

## Подключение Spring Data JPA

Через стартер:

```groovy
implementation 'org.springframework.boot:spring-boot-starter-data-jpa'
```

### Application properties

DataSource по умолчанию использует H2 — встроенную in-memory БД:

```properties
spring.datasource.url=jdbc:h2:mem:db;DB_CLOSE_DELAY=-1
spring.datasource.username=sa
spring.datasource.password=sa
```

### Включение Spring Data

```java
@Configuration
@EnableJpaRepositories(basePackages = "org.example.data")
class JpaConfig {}
```

## Naming Conventions для методов репозитория

Spring Data JPA генерирует SQL-запросы **на основе имён методов**. Например:

- `findByNameAndAge(String name, int age)` — `SELECT ... WHERE name = ? AND age = ?`
- `findByLastNameOrderByFirstNameAsc(String lastName)` — `SELECT ... WHERE last_name = ? ORDER BY first_name ASC`

Полная документация: [Spring Data JPA Query Methods](https://docs.spring.io/spring-data/jpa/reference/jpa/query-methods.html)

## Аннотация @Query

Если name conventions не подходят — можно явно указать запрос через `@Query`.

```java
@Query("SELECT u FROM User u WHERE u.email = ?1")
User findByEmail(String email);
```

Также поддерживаются native SQL-запросы.

## Явная реализация репозиториев

Если нужно явно реализовать репозитории — это тоже возможно.

> **По умолчанию Spring Data будет «генерировать» реализацию только тех методов, которые не переопределены в классах с постфиксом `Impl`.**

То есть, если есть интерфейс `UserRepository` — создаём класс `UserRepositoryImpl`, и Spring Data будет использовать его реализации для пересекающихся методов.

## Что делать с DAO-слоем?

Spring Data JPA менеджит большую часть рутины:

- Генерирует SQL-запросы
- Производит маппинг
- Управляет транзакциями (JTA)
- … и многое другое

> Старые явные реализации DAO как будто бы и не нужны…

## Полезные инструменты

**JPA-Buddy plugin** для IntelliJ IDEA — упрощает создание Entity, репозиториев и других классов. Но не все фичи доступны в бесплатной версии.

Полезные ссылки для изучения:

- [Baeldung: Spring Data](https://www.baeldung.com/spring-data)
- [Baeldung: Persistence with Spring](https://www.baeldung.com/persistence-with-spring-series)

---
