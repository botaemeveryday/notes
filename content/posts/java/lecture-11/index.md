---
title: Лекция 11
description: Spring Security
weight: 11
tags:
  - Java
  - 4 Семестр
authors:
  - name: notakeith
    avatar: https://avatars.githubusercontent.com/u/108391756?v=4
    link: https://github.com/notakeith
---

# Лекция 11. Spring Security

## Что такое Spring Security

**Spring Security** — Java/Java EE фреймворк, предоставляющий механизмы построения систем **аутентификации и авторизации**, а также другие возможности обеспечения безопасности для корпоративных приложений на Spring Framework.

## Архитектура: цепочка фильтров

Spring Security использует паттерн **«Цепочка обязанностей» (Chain of Responsibility)**. При выполнении HTTP-запроса происходит **поэтапная обработка фильтрами**, которые производят валидацию запроса.

## Основные фильтры Spring Security

### WebAsyncManagerIntegrationFilter

Интегрирует `SecurityContext` с `WebAsyncManager`, который ответственен за асинхронные запросы.

### SecurityContextPersistenceFilter

- Ищет `SecurityContext` в сессии
- Заполняет `SecurityContextHolder`, если находит
- По умолчанию используется `ThreadLocalSecurityContextHolderStrategy`, хранящий `SecurityContext` в `ThreadLocal`-переменной

### HeaderWriterFilter

Просто добавляет заголовки в response.

### LogoutFilter

Проверяет совпадает ли URL с паттерном (`/logout` POST по умолчанию) и запускает процедуру логаута:

1. Удаляется CSRF-токен
2. Завершается сессия
3. Чистится `SecurityContextHolder`

### BasicAuthenticationFilter

- Проверяет, есть ли заголовок `Authorization: Basic ...`
- Если находит — извлекает логин/пароль и передаёт их в `AuthenticationManager`

### RequestCacheAwareFilter

Восстанавливает оригинальный запрос пользователя после логина:

1. Пользователь заходит на защищённый URL
2. Его перекидывает на страницу логина
3. После успешной авторизации — возвращает на исходную страницу

Внутри проверяет, есть ли сохранённый запрос, и подменяет им текущий. Запрос сохраняется в сессии.

### AnonymousAuthenticationFilter

Если к моменту выполнения этого фильтра `SecurityContextHolder` пуст (т.е. аутентификации не произошло), фильтр заполняет его **анонимной аутентификацией** — `AnonymousAuthenticationToken` с ролью `ROLE_ANONYMOUS`.

Это гарантирует, что в `SecurityContextHolder` всегда будет объект — можно не бояться `NullPointerException` и более гибко настраивать доступ для неавторизованных пользователей.

### SessionManagementFilter

На этом этапе производятся действия, связанные с сессией:

- Смена идентификатора сессии
- Ограничение количества одновременных сессий
- Сохранение `SecurityContext` в `securityContextRepository`

В обычном случае:

1. `HttpSessionSecurityContextRepository` сохраняет `SecurityContext` в сессию
2. Вызывается `sessionAuthenticationStrategy.onAuthentication`
3. По умолчанию включена защита от **session fixation attack** — после аутентификации меняется ID сессии
4. Если был передан CSRF-токен — генерируется новый

### ExceptionTranslationFilter

К этому моменту `SecurityContext` должен содержать анонимную или нормальную аутентификацию. Этот фильтр прокидывает запрос/ответ по filter chain и обрабатывает возможные ошибки авторизации.

### FilterSecurityInterceptor

На **последнем этапе** происходит **авторизация** на основе URL запроса.

- Наследуется от `AbstractSecurityInterceptor`
- Решает, имеет ли текущий пользователь доступ к URL
- Существует другая реализация — `MethodSecurityInterceptor` — для допуска к методам (при использовании `@Secured` / `@PreAuthorize`)
- Внутри вызывается `AccessDecisionManager`
- Несколько стратегий принятия решения, по умолчанию: **AffirmativeBased**

## AuthenticationManager

**AuthenticationManager** — интерфейс, который принимает `Authentication` и возвращает `Authentication`. Это центральная точка процесса аутентификации.

Типичная реализация `Authentication` — **`UsernamePasswordAuthenticationToken`**.

## ProviderManager

**ProviderManager** — стандартная реализация `AuthenticationManager`. Содержит список `AuthenticationProvider`.

## AuthenticationProvider

Когда мы передаём объект `Authentication` в `ProviderManager`, он:

1. **Перебирает** существующие `AuthenticationProvider`-ы
2. **Проверяет**, поддерживает ли `AuthenticationProvider` эту имплементацию `Authentication`
3. Внутри `AuthenticationProvider.authenticate` мы приводим переданный `Authentication` к нужной реализации
4. Извлекаем credentials
5. **Если аутентификация не удалась** — выбрасываем исключение
6. **ProviderManager** ловит исключение и пробует следующий провайдер
7. Если **ни один** провайдер не вернул успешную аутентификацию — ProviderManager пробрасывает последнее пойманное исключение

После успешной аутентификации `BasicAuthenticationFilter` сохраняет полученный `Authentication`:

```java
SecurityContextHolder.getContext().setAuthentication(authResult);
```

Если выбрасывается `AuthenticationException` — контекст сбрасывается, вызывается `AuthenticationEntryPoint`.

---