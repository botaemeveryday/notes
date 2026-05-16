---
title: Лекция 12
description: Keycloak
weight: 12
tags:
  - Java
  - 4 Семестр
authors:
  - name: notakeith
    avatar: https://avatars.githubusercontent.com/u/108391756?v=4
    link: https://github.com/notakeith
---


# Лекция 12. Современная аутентификация и авторизация: Keycloak

## План лекции

1. **Keycloak** — что это и зачем
2. **OAuth 2.0 и OpenID Connect** — теория, JWT
3. **Интеграция со Spring Boot** — `oauth2Login` vs `oauth2ResourceServer`
4. **Магия AutoConfiguration** — какие бины создаются автоматически
5. **Практика и лучшие практики** — реальные репозитории и шпаргалка

## Что такое Keycloak

**Keycloak** — open-source решение для управления идентификацией и доступом (**IAM** — Identity and Access Management), поддерживаемое Red Hat. Берёт на себя весь комплекс задач по аутентификации, оставляя вашему приложению только авторизацию.

### Ключевые возможности

| Возможность | Описание |
|-------------|----------|
| **SSO и Sign-Out** | Бесшовный переход между приложениями без повторного ввода пароля |
| **Identity Brokering** | Аутентификация через Google, GitHub, LDAP, Active Directory |
| **Открытые стандарты** | OpenID Connect, OAuth 2.0, SAML 2.0 — всё из коробки |
| **2FA и Login Flows** | Двухфакторная аутентификация, кастомизация тем и гибкие потоки |

## Быстрый старт с Docker

```yaml
services:
  keycloak:
    container_name: keycloak.openid-provider
    image: quay.io/keycloak/keycloak:26.0
    command:
      - start-dev
      - --import-realm        # Импортируем готовый realm при старте
    ports:
      - 8080:8080
    volumes:
      - ./keycloak/:/opt/keycloak/data/import/
    environment:
      KEYCLOAK_ADMIN: admin
      KEYCLOAK_ADMIN_PASSWORD: ${KEYCLOAK_ADMIN_PASSWORD}
```

> **Совет:** Флаг `--import-realm` позволяет версионировать конфигурацию безопасности вместе с кодом — Realm-файл хранится в Git наравне с исходниками.

## Realm — изолированный домен безопасности

**Realm** — изолированный домен безопасности внутри Keycloak. Это контейнер верхнего уровня, инкапсулирующий уникальный набор пользователей, клиентов, ролей и конфигураций.

> **Аналогия:** Keycloak — многоквартирный дом. Каждый Realm — отдельная квартира со своим замком, жильцами и правилами.

### Ключевые свойства Realm

| Свойство | Описание |
|----------|----------|
| **Изоляция** | Пользователи и настройки одного Realm недоступны в другом. Можно разделить dev и prod |
| **Управление** | Realm управляет пользователями, их учётными данными, ролями и группами |
| **Наследование** | Мастер-администратор может создавать несколько Realms и управлять ими из единой точки |

## Сущности Realm: Клиенты (Clients)

**Client** — приложение или сервис, взаимодействующий с Keycloak для аутентификации и авторизации. Каждый клиент имеет уникальный **Client ID** и тип доступа.

### Типы клиентов

| Тип | Описание | Поток |
|-----|----------|-------|
| **Confidential** | Серверные приложения (бэкенд), могут безопасно хранить client-secret. Пример: Spring Boot API | Authorization Code Flow |
| **Public** | Клиентские приложения (SPA, мобильные), не могут безопасно хранить секреты | Authorization Code Flow with PKCE |

**Создание клиента:** `Clients` → `Create client` → указать Client ID → выбрать тип → `Save`.

## Сущности Realm: Пользователи и Роли

### 👤 Users (Пользователи)

Учётная запись конечного пользователя, аутентифицирующегося в системе.

1. `Users` → `Add user`
2. Заполнить Username, Email, First/Last Name
3. Вкладка `Credentials` → задать пароль, отключить флаг Temporary

### 🎭 Roles (Роли)

Именованный набор прав (**RBAC** — Role-Based Access Control). Keycloak поддерживает два типа ролей:

| Тип ролей | Описание |
|-----------|----------|
| **Realm Roles** | Глобальные роли, доступные всем клиентам в Realm. Подходят для `admin`, `user`, `manager` |
| **Client Roles** | Роли, специфичные для конкретного клиента. Когда разрешения уникальны для одного приложения |

### Назначение ролей и экспорт Realm

**Назначение роли:**
1. `Users` → выбрать пользователя
2. Вкладка `Role mapping` → `Assign role`
3. Выбрать нужные Realm- или Client-роли → `Assign`

**Экспорт Realm:**
1. `Realm Settings` → `Action` → `Partial Export` → JSON-файл
2. Сохранить JSON в репозиторий
3. Импорт: Docker `--import-realm` + смонтированная директория

## OAuth 2.0 и OpenID Connect

**OAuth 2.0** — протокол **авторизации**. Позволяет приложению получить доступ к ресурсам пользователя без передачи пароля.

**OIDC** (OpenID Connect) — слой **аутентификации** поверх OAuth 2.0, добавляющий **ID Token** — ответ на вопрос «кто этот пользователь?».

### Роли в архитектуре OAuth 2.0 / OIDC

| Роль | Кто это | Что делает |
|------|---------|------------|
| **Authorization Server** | Keycloak | Выдаёт токены после успешной аутентификации |
| **Resource Server** | Spring Boot API | Принимает и проверяет Access Token |
| **Access Token** | JWT | Доступ к защищённым эндпоинтам API |
| **ID Token** | JWT | Данные о пользователе (OIDC-специфичный) |
| **Refresh Token** | Долгоживущий токен | Обновление Access Token без участия пользователя |

## JWT — JSON Web Token

**JWT** (RFC 7519) — открытый стандарт, компактный и самодостаточный способ безопасной передачи информации между сторонами в виде JSON-объекта.

### Три ключевых свойства

1. **Компактный** — передаётся в URL, POST-параметрах или HTTP-заголовке
2. **Самодостаточный** — содержит всю информацию о пользователе и его правах
3. **Подписанный** — подпись гарантирует целостность данных

### Формат токена

JWT состоит из **трёх частей**, разделённых точками:

```
xxxxx.yyyyy.zzzzz
Header.Payload.Signature
```

Каждая часть кодируется в Base64Url. Итоговый токен передаётся в заголовке:

```
Authorization: Bearer eyJhbGci...
```

### Структура JWT

| Часть | Содержимое |
|-------|------------|
| **Header** | `typ: "JWT"`, алгоритм подписи `alg: "RS256"`. Кодируется в Base64Url |
| **Payload (Claims)** | Зарегистрированные (`iss`, `exp`, `sub`) и кастомные (`realm_access.roles`, `resource_access`). Кодируется в Base64Url |
| **Signature** | `HMAC(Base64Url(header) + "." + Base64Url(payload), privateKey)`. Проверяет целостность и подлинность |

### JWT Claims в Keycloak

Keycloak добавляет специфические claims, на которых строится авторизация в Spring Security:

**realm_access — Realm Roles:**

```json
{
  "realm_access": {
    "roles": ["user", "admin"]
  }
}
```

**resource_access — Client Roles:**

```json
{
  "resource_access": {
    "my-backend-api": {
      "roles": ["client_user"]
    }
  }
}
```

> **Важно:** Именно эти claims являются основой для авторизации в Spring Security. Без кастомного конвертера Spring «не увидит» роли в JWT от Keycloak.

## Преимущества Stateless JWT-подхода

| Преимущество | Описание |
|--------------|----------|
| **Горизонтальное масштабирование** | Любой экземпляр сервера обработает запрос — состояние не хранится на сервере |
| **Упрощение архитектуры** | Отпадает необходимость в Spring Session |
| **Универсальный токен** | Один JWT используется для доступа к нескольким микросервисам одновременно |

## Миграция от сессий к JWT

### Старый код (Stateful)

```java
@Bean
public SecurityFilterChain filterChain(HttpSecurity http) throws Exception {
    http
        .sessionManagement(session -> session
            .sessionCreationPolicy(SessionCreationPolicy.IF_REQUIRED))
        .formLogin(Customizer.withDefaults())
        .authorizeHttpRequests(auth -> auth.anyRequest().authenticated());
    return http.build();
}
```

### Новый код (Stateless JWT)

```java
@Bean
public SecurityFilterChain filterChain(HttpSecurity http) throws Exception {
    http
        .sessionManagement(session -> session
            .sessionCreationPolicy(SessionCreationPolicy.STATELESS))  // ①
        .csrf(csrf -> csrf.disable())                                  // ②
        .authorizeHttpRequests(auth -> auth
            .requestMatchers("/api/public/**").permitAll()
            .anyRequest().authenticated())
        .oauth2ResourceServer(oauth2 ->
            oauth2.jwt(Customizer.withDefaults()));                    // ③
    return http.build();
}
```

### Три ключевых изменения

1. **STATELESS** — `SessionCreationPolicy.STATELESS` полностью отключает создание HTTP-сессий. Каждый запрос аутентифицируется заново по токену.
2. **`csrf().disable()`** — для stateless API защита от CSRF не требуется: браузер не отправляет cookies с токеном автоматически.
3. **`oauth2ResourceServer().jwt()`** — настраиваем Spring на приём и проверку JWT. Spring Boot автоматически создаст `JwtDecoder` на основе `issuer-uri`.

## Два подхода интеграции Spring Boot + Keycloak

| Характеристика | `oauth2Login` (Stateful) | `oauth2ResourceServer` (Stateless) |
|----------------|--------------------------|-------------------------------------|
| **Назначение** | Серверные веб-приложения с UI (MVC, Thymeleaf) | REST API, микросервисы |
| **Состояние** | Есть (HTTP-сессии) | Нет (Bearer-токен в каждом запросе) |
| **Защита от CSRF** | Требуется | Не требуется |
| **Тип объекта аутентификации** | `OAuth2AuthenticationToken` | `JwtAuthenticationToken` |
| **Масштабирование** | Нужна репликация сессий (Redis) | Легко, stateless |
| **Аутентификация** | Редирект на страницу логина | Bearer-токен в заголовке |

> ⚠️ **Правило:** Никогда не смешивайте `oauth2Login` и `oauth2ResourceServer` в одном `SecurityFilterChain`!

## Настройка Stateless-клиента

### application.yml

Минимальная конфигурация — **одна строка**:

```yaml
spring:
  security:
    oauth2:
      resourceserver:
        jwt:
          issuer-uri: http://localhost:8080/realms/baeldung-keycloak
```

Указав `issuer-uri`, Spring Boot **автоматически:**

1. Запросит конфигурацию OIDC-провайдера
2. Получит публичные ключи (JWKS)
3. Создаст `JwtDecoder` — без единой строки Java-кода

### SecurityFilterChain: настройка доступа

```java
@Bean
public SecurityFilterChain filterChain(HttpSecurity http) throws Exception {
    http
        .authorizeHttpRequests(auth -> auth
            .requestMatchers("/api/public/**").permitAll()      // открыто всем
            .requestMatchers("/api/admin/**").hasRole("ADMIN")  // только ADMIN
            .anyRequest().authenticated())                       // остальное — авторизованным
        .oauth2ResourceServer(oauth2 ->
            oauth2.jwt(Customizer.withDefaults()));
    return http.build();
}
```

> **Важно:** Метод `.hasRole("ADMIN")` автоматически ищет `ROLE_ADMIN` в `GrantedAuthorities`. Необходим кастомный конвертер!

## JwtAuthenticationConverter — извлечение ролей из JWT

По умолчанию Spring Security не знает, где в JWT от Keycloak лежат роли. Нужен кастомный конвертер:

```java
@Bean
public JwtAuthenticationConverter jwtAuthenticationConverter() {
    JwtGrantedAuthoritiesConverter grantedAuthoritiesConverter =
        new JwtGrantedAuthoritiesConverter();
    // Префикс, который Spring Security ожидает для hasRole()
    grantedAuthoritiesConverter.setAuthorityPrefix("ROLE_");
    // Путь к ролям в JWT-структуре Keycloak
    grantedAuthoritiesConverter.setAuthoritiesClaimName("realm_access.roles");

    JwtAuthenticationConverter jwtAuthenticationConverter =
        new JwtAuthenticationConverter();
    jwtAuthenticationConverter.setJwtGrantedAuthoritiesConverter(grantedAuthoritiesConverter);
    return jwtAuthenticationConverter;
}
```

Регистрация в SecurityFilterChain:

```java
.oauth2ResourceServer(oauth2 ->
    oauth2.jwt(jwt ->
        jwt.jwtAuthenticationConverter(jwtAuthenticationConverter())))
```

## Получение данных пользователя в контроллере

### Способ 1: @AuthenticationPrincipal (предпочтительно)

```java
@GetMapping("/api/user")
public Map getUserInfo(@AuthenticationPrincipal Jwt jwt) {
    return Map.of(
        "username", jwt.getClaimAsString("preferred_username"),
        "email", jwt.getClaimAsString("email"),
        "roles", jwt.getClaimAsStringList("realm_access.roles")
    );
}
```

### Способ 2: SecurityContextHolder

Используется вне контроллера — в сервисах и компонентах, где нет доступа к параметрам запроса.

```java
Authentication auth = SecurityContextHolder.getContext().getAuthentication();
Jwt jwt = (Jwt) auth.getPrincipal();
String username = jwt.getClaimAsString("preferred_username");
```

## Как Spring проверяет подпись JWT: JWKS

Для верификации каждого входящего токена бэкенду нужны публичные ключи Keycloak. Spring Boot получает их **автоматически и кэширует**:

1. **Конфигурация** — Spring читает `issuer-uri` из `application.yml`
2. **Discovery** — `GET /.well-known/openid-configuration`
3. **Извлечение** — берёт `jwks_uri` из JSON-ответа
4. **Загрузка** — скачивает JWKS с certs endpoint

> Keycloak периодически ротирует ключи. Spring Boot автоматически обновляет кэш при получении JWT с неизвестным `kid` (Key ID), обеспечивая бесперебойную работу.

## Stateful-клиент: oauth2Login

Если бэкенд рендерит страницы (Thymeleaf, JSP) и управляет сессиями — используйте `oauth2Login`. Spring Security полностью берёт на себя редирект и обработку callback.

### SecurityFilterChain

```java
@Bean
public SecurityFilterChain filterChain(HttpSecurity http) throws Exception {
    http
        .authorizeHttpRequests(auth -> auth
            .requestMatchers("/public/**").permitAll()
            .anyRequest().authenticated())
        .oauth2Login(oauth2 -> oauth2.defaultSuccessUrl("/home", true))
        .logout(logout -> logout
            .logoutSuccessHandler(oidcLogoutSuccessHandler()));
    return http.build();
}
```

### application.yml

```yaml
spring:
  security:
    oauth2:
      client:
        registration:
          keycloak:
            client-id: ${KC_CLIENT_ID}
            client-secret: ${KC_SECRET}
            authorization-grant-type: authorization_code
            scope: openid, profile, email
        provider:
          keycloak:
            issuer-uri: ${KC_ISSUER_URI}
            user-name-attribute: preferred_username
```

### Важные нюансы oauth2Login

- **RP-Initiated Logout** — используйте `OidcClientInitiatedLogoutSuccessHandler` для корректного выхода. Без него пользователь останется залогиненным в Keycloak.
- **Back-Channel Logout** — Keycloak может инициировать logout на всех клиентах. Зарегистрируйте специальный URL — приложение получит POST от Keycloak.
- **User Info и OAuth2UserService** — для получения дополнительной информации настройте `OAuth2UserService` или `OidcUserService`.

## Когда что использовать

### ✅ oauth2ResourceServer (Stateless)

- Разрабатываете REST API или микросервис
- Бэкенд не управляет сессиями
- Планируете горизонтальное масштабирование
- Клиент — SPA, мобильное приложение или другой сервис

👉 **Выбор по умолчанию для большинства современных бэкенд-сервисов**

### ✅ oauth2Login (Stateful)

- Разрабатываете веб-приложение с серверным рендерингом (MVC)
- Нужны сессии на сервере
- Хотите, чтобы Spring полностью управлял процессом логина/логаута
- Нет нужды в масштабировании без состояния

## Ошибка: смешивание двух подходов

### ❌ Так делать нельзя

```java
@Bean
public SecurityFilterChain filterChain(HttpSecurity http) throws Exception {
    http
        .oauth2Login(Customizer.withDefaults())
        .oauth2ResourceServer(oauth2 ->
            oauth2.jwt(Customizer.withDefaults()));
    return http.build();
}
```

**Почему нельзя?** Один компонент использует сессии, другой — stateless JWT. Они **конфликтуют** в обработке аутентификации.

### ✅ Правильное решение

Создайте **два отдельных бина** `SecurityFilterChain`, разграничив их по URL с помощью `securityMatcher`:

```java
@Bean
@Order(1)
public SecurityFilterChain uiChain(HttpSecurity http) throws Exception {
    http.securityMatcher("/ui/**").oauth2Login(...);
    return http.build();
}

@Bean
@Order(2)
public SecurityFilterChain apiChain(HttpSecurity http) throws Exception {
    http.securityMatcher("/api/**").oauth2ResourceServer(...);
    return http.build();
}
```

## AutoConfiguration в Spring Boot

### Какие стартеры нужны

| Стартер | Назначение |
|---------|------------|
| **`spring-boot-starter-oauth2-resource-server`** | Для REST API. Поддержка JWT и Opaque токенов, библиотека Nimbus JOSE+JWT |
| **`spring-boot-starter-oauth2-client`** | Для серверных веб-приложений. Authorization Code Flow и управление сессиями |
| **`spring-boot-starter-security`** | Базовый стартер, обязателен в обоих случаях |

> ⚠️ Устаревший **Keycloak Adapter больше не используется** — только стандартные стартеры Spring Security OAuth2.

### Бины oauth2-resource-server

Когда обнаружены стартер и `issuer-uri`, Spring Boot создаёт три ключевых бина:

1. **JwtDecoder** — реализация `NimbusJwtDecoder`. Декодирует и верифицирует подпись, проверяет `exp`, `nbf`, `iss`.
2. **JwtAuthenticationConverter** — стандартный извлекает `scope`. Почти всегда нужно переопределять для маппинга ролей Keycloak.
3. **BearerTokenAuthenticationFilter** — перехватывает запрос, извлекает токен из `Authorization: Bearer ...`, делегирует проверку `JwtDecoder` и `JwtAuthenticationProvider`.

### Бины oauth2-client (Stateful)

1. **ClientRegistrationRepository** — хранилище конфигураций OAuth2-клиентов из `application.yml`
2. **OAuth2AuthorizedClientService** — управляет токенами доступа. По умолчанию — in-memory
3. **OAuth2AuthorizationRequestRedirectFilter** — перенаправляет на страницу логина Keycloak
4. **OAuth2LoginAuthenticationFilter** — обрабатывает callback после успешного логина

## NimbusJwtDecoder: цепочка проверок

1. Получает публичный ключ (JWK) из кэша или JWKS-эндпоинта Keycloak
2. Проверяет подпись с помощью публичного ключа
3. Проверяет `exp` (не просрочен) и `nbf` (already valid)
4. Проверяет, что `iss` совпадает с `issuer-uri`
5. Возвращает объект `Jwt` или бросает исключение

### Кастомизация JwtDecoder

```java
@Bean
public JwtDecoder jwtDecoder() {
    NimbusJwtDecoder decoder = NimbusJwtDecoder.withJwkSetUri(jwksUri).build();
    decoder.setJwtValidator(
        new DelegatingOAuth2TokenValidator<>(
            JwtValidators.createDefaultWithIssuer(issuer),
            new CustomBlacklistValidator()
        )
    );
    return decoder;
}
```

## Полная конфигурация: oauth2ResourceServer

### application.yml

```yaml
spring:
  security:
    oauth2:
      resourceserver:
        jwt:
          issuer-uri: http://localhost:8080/realms/baeldung-keycloak
```

### SecurityConfig.java

```java
@Configuration
@EnableWebSecurity
public class SecurityConfig {

    @Bean
    public SecurityFilterChain filterChain(HttpSecurity http) throws Exception {
        http
            .sessionManagement(s -> s.sessionCreationPolicy(STATELESS))
            .csrf(AbstractHttpConfigurer::disable)
            .authorizeHttpRequests(auth -> auth
                .requestMatchers("/api/public/**").permitAll()
                .anyRequest().authenticated())
            .oauth2ResourceServer(oauth2 -> oauth2
                .jwt(jwt -> jwt.jwtAuthenticationConverter(jwtAuthenticationConverter())));
        return http.build();
    }

    @Bean
    public JwtAuthenticationConverter jwtAuthenticationConverter() {
        JwtGrantedAuthoritiesConverter conv = new JwtGrantedAuthoritiesConverter();
        conv.setAuthorityPrefix("ROLE_");
        conv.setAuthoritiesClaimName("realm_access.roles");

        JwtAuthenticationConverter converter = new JwtAuthenticationConverter();
        converter.setJwtGrantedAuthoritiesConverter(conv);
        return converter;
    }
}
```

> Это **полный минимум** для production-ready Resource Server с поддержкой Realm Roles из Keycloak.

## Лучшие практики и частые ошибки

### ✅ Делайте так

- Всегда указывайте `issuer-uri` — это источник правды для автоконфигурации
- Используйте `preferred_username` как `user-name-attribute`
- Храните секреты в переменных окружения или Vault (HashiCorp, AWS Secrets Manager)
- Версионируйте Realm-конфигурацию в Git через `--import-realm`

### ❌ Не делайте так

- Не используйте устаревший Keycloak Adapter — только стандартный Spring Security OAuth2
- Не смешивайте `oauth2Login` и `oauth2ResourceServer` в одном `SecurityFilterChain`
- Не забывайте про префикс `ROLE_`: `.hasRole("ADMIN")` ищет `ROLE_ADMIN`
- Не используйте `.hasAuthority("ROLE_ADMIN")` и `.hasRole("ADMIN")` вперемешку без понимания разницы

## Cheat Sheet

| Тема | Главное |
|------|---------|
| **Keycloak иерархия** | `Realm` → `Client` → `Users` → `Roles`. Экспортируйте Realm в JSON и храните в Git |
| **OAuth2 / OIDC** | Keycloak = Authorization Server, выдаёт Access Token (JWT). Spring Boot API = Resource Server, проверяет токен |
| **JWT структура** | `Header.Payload.Signature`. Роли Keycloak в `realm_access.roles`. Используйте кастомный `JwtAuthenticationConverter` |
| **Stateless vs Stateful** | `oauth2ResourceServer` + STATELESS для REST API. `oauth2Login` + сессии для MVC. Не смешивать! |
| **Ключевые бины** | `JwtDecoder` (подпись и claims), `JwtAuthenticationConverter` (маппит роли), `BearerTokenAuthenticationFilter` (перехватывает запросы) |
| **Минимальный старт** | Стартер `spring-boot-starter-oauth2-resource-server` + одна строка `issuer-uri` + кастомный конвертер ролей |
