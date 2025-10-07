# Схема управления ограничениями доступа (RBAC) в проекте

## Обзор

Проект реализует **Role-Based Access Control (RBAC)** — систему управления доступом на основе ролей. Это позволяет гибко определять разрешения (permissions) для пользователей через роли, ресурсы и действия. Система интегрирована с кастомной моделью пользователя `MyUser ` (аутентификация по email) и отдельным приложением `rbac` для хранения ролей и разрешений.

## Основные принципы

- **Пользователи (`MyUser `)**: Каждый пользователь имеет роли (ManyToMany). Базовая роль 'User  ' присваивается при регистрации.
- **Роли (`Role`)**: Группируют разрешения. Пример: 'User  ' (базовый доступ к профилю), 'Admin' (полный доступ).
- **Разрешения (`Permission`)**: Комбинация ресурса (e.g., 'profile') и действия (e.g., 'update'). Хранятся в БД.
- **Проверки доступа**:
  - **Web (views)**: Декоратор `@permission_required(resource, action)` в `users/views.py` вызывает `user.has_permission()`. Если нет — redirect с сообщением или 401/403 для API.
  - **API (DRF)**: Кастомное разрешение `IsAdminPermission` в `rbac/views.py` проверяет `user.has_permission('permissions', 'manage')` или `is_superuser`.
  - **Базовый доступ**: Авторизованные пользователи (любая роль) могут редактировать **свой** профиль без RBAC-проверки (только `@login_required`).
- **Безопасность**:
  - Superuser обходит все проверки.
  - Неактивные/удалённые пользователи (soft_delete) не имеют доступа.
  - Аутентификация по email (backend в `users/backends.py`).
- **Цели**: Простота (роли в админке), масштабируемость (API для управления RBAC), аудит (логи через messages).

Система не использует встроенные Django groups/permissions (PermissionsMixin в `MyUser ` для совместимости, но RBAC кастомный). Нет кэширования проверок (можно добавить для производительности).

## Модели и структура БД

RBAC построен на четырёх моделях в `rbac/models.py` и кастомном `MyUser ` в `users/models.py`. Связи — ManyToMany для гибкости.

### 1. MyUser  (users/models.py)
- **Наследование**: `AbstractBaseUser ` + `PermissionsMixin` (для совместимости с Django auth).
- **Ключевые поля**:
  - `first_name`, `last_name`, `middle_name` (опционально) — профильные данные.
  - `email` (unique, USERNAME_FIELD для login).
  - `is_staff`, `is_active` (default=True), `date_joined`, `deleted_at` (для soft_delete).
- **Связи**:
  - `roles = ManyToManyField('rbac.Role', blank=True, related_name='users')` — пользователь может иметь несколько ролей (обратная связь: `role.users.all()`).
- **Методы**:
  - `soft_delete()`: Устанавливает `is_active=False`, `deleted_at=now` (мягкое удаление, переопределяет `delete()`).
  - `has_permission(resource_name, action_name)`:
    - Если `is_superuser` — True.
    - Если не `is_active` или `deleted_at` — False.
    - Для каждой роли: Вызывает `role.has_permission()` и возвращает True, если найдено.
    - Иначе False.
  - `get_full_name()`, `get_short_name()` — для отображения.
- **Meta**: Ordering по фамилии/имени, verbose_names на русском.

### 2. Resource (rbac/models.py)
- **Поля**: `name` (unique, max_length=50, e.g., 'profile', 'user'), `description`.
- **Назначение**: Определяет сущности системы (e.g., 'profile' для пользовательского профиля).

### 3. Action (rbac/models.py)
- **Поля**: `name` (unique, max_length=50, e.g., 'read', 'update', 'delete'), `description`.
- **Назначение**: Действия над ресурсами (CRUD-подобные).

### 4. Permission (rbac/models.py)
- **Поля**: `description`.
- **Связи**: FK к `Resource` (on_delete=CASCADE), FK к `Action`.
- **Ограничения**: `unique_together=('resource', 'action')` — уникальная пара (e.g., 'profile_update').
- **`__str__`**: '{resource}_{action}'.

### 5. Role (rbac/models.py)
- **Поля**: `name` (unique, max_length=50, e.g., 'User  '), `description`.
- **Связи**: `permissions = ManyToManyField('Permission', blank=True)`.
- **Методы**:
  - `has_permission(resource_name, action_name)`: Проверяет `self.permissions.filter(resource__name=..., action__name=...).exists()`.
- **`__str__`**: name.

## Диаграмма связей (ASCII)
MyUser  ───(ManyToMany: roles)─── Role ───(ManyToMany: permissions)─── Permission
  │                                    │                                 │
  │                                    │                                 ├── FK ─── Action (name: 'update')
  ├── has_permission('profile', 'update') ───→ role.has_permission() ───→ filter(exists)
  │                                    │
  └── soft_delete() (is_active=False)   └── name: 'User ' (базовая роль)
                                           └── users (related_name: role.users.all())


**Пример БД** (после миграций и создания данных в admin):
- Resource: 'profile' (описание: "Пользовательский профиль").
- Action: 'update' (описание: "Редактирование").
- Permission: 'profile_update'.
- Role: 'User  ' (permissions: ['profile_read', 'profile_update'] — только свой профиль).
- Role: 'Admin' (permissions: все + 'user_delete', 'permissions_manage').

## Логика присвоения ролей и разрешений

- **При регистрации** (`users/views.py`, view `register`):
  - Создаётся `MyUser ` через `MyUser CreationForm`.
  - Автоматически добавляется базовая роль: `Role.objects.get_or_create(name='User  ', defaults={'description': 'Обычный пользователь'})`.
  - `user.roles.add(default_role)`.
  - Аутентификация: `authenticate(email, password)` через `EmailBackend`.
- **Присвоение ролей**:
  - В Django Admin: Зарегистрируйте модели (в `rbac/admin.py` и `users/admin.py`) для CRUD ролей/разрешений.
  - Для пользователей: В admin или кастомном view (e.g., /rbac/assign-role/, с `@permission_required('rbac', 'assign')`).
  - Superuser: Автоматически имеет все права (`is_superuser=True`).
- **Создание разрешений**:
  - В миграциях (data migration) или admin: Создайте базовые Resource/Action/Permission.
  - Пример: Роль 'User  ' — permissions на 'profile:read/update' (для своего профиля).
  - Роль 'Admin' — 'permissions:manage' (для API /rbac/api/), 'user:delete' (удаление чужих).

## Проверки доступа в коде

### 1. Web-приложение (users/views.py)
- **Базовая аутентификация**: `@login_required` для `profile`, `profile_update`, `profile_delete`.
  - `profile_update`: Редактирование своего профиля (`instance=request.user`) — без `has_permission` (все авторизованные могут).
  - `profile_delete`: Только свой аккаунт, `soft_delete()` + logout.
- **RBAC-декоратор** `permission_required(resource, action)`:
  - Проверяет `request.user.is_authenticated` → redirect to login (web) или 401 (API /rbac/api/).
  - Затем `user.has_permission(resource, action)` → messages.error + redirect to home (web) или 403 (API).
  - Применение: Не используется в базовых views (profile), но для админских (e.g., `@permission_required('user', 'delete') def admin_delete_other_user(...)`).
- **Login/Logout**: По email, redirect to profile/home. Messages для ошибок/успеха.

### 2. API (rbac/views.py, DRF ViewSets)
- **Endpoints**: /rbac/api/resources/, /actions/, /permissions/, /roles/ (CRUD через ModelViewSet).
- **Разрешения**: `IsAdminPermission` (наследует IsAuthenticated):
  - `user.is_superuser` или `user.has_permission('permissions', 'manage')`.
  - Только Admin может управлять RBAC (e.g., добавлять роли).
- **Дополнительно**: `@action users` в RoleViewSet — GET /rbac/api/roles/{pk}/users/ (показывает пользователей роли, без доп. проверок).
- **Аутентификация**: SessionAuthentication (web) + Token (JWT, если настроено).

### 3. URLs (custom_auth/urls.py, users/urls.py, rbac/urls.py)
- **Users**: /register/, /login/, /logout/, /profile/, /profile/update/, /profile/delete/, / (home).
- **RBAC API**: /rbac/api/resources/, etc. (только для авторизованных Admin).
- **Admin**: /admin/ (стандартный Django admin для моделей).

## Примеры использования

- **Обычный User (роль 'User  ')**:
  - Может: /profile/ (просмотр), /profile/update/ (редактирование своего), /profile/delete/ (своего).
  - `has_permission('profile', 'update')` → True (через роль).
  - Не может: /rbac/api/roles/ (403, нет 'permissions:manage').
- **Admin (роль 'Admin')**:
  - Может: Всё выше + /rbac/api/permissions/ (CRUD разрешений), удаление чужих пользователей (если view с `@permission_required('user', 'delete')`).
  - `has_permission('permissions', 'manage')` → True.
- **Неавторизованный**: Redirect to /login/ (web) или 401 (API).
- **Удалённый пользователь**: `has_permission()` → False (`deleted_at` не None).

## Расширение схемы

- **Добавление ролей/разрешений**:
  - В `admin.py`: `admin.site.register([Role, Permission, ...])`.
  - Data migration: `python manage.py makemigrations rbac --empty` для начальных данных (e.g., создать 'User  ' роль).
- **Улучшения**:
  - Кэширование: В `has_permission` добавить `@lru_cache` или Redis (from django.core.cache).
  - Аудит: Middleware для логирования проверок (e.g., log 'User  X denied Y').
  - Условные разрешения: Добавить поле `conditions` в Permission (e.g., time-based).
  - Тесты: Unit-тесты в `tests.py` (e.g., `user.has_permission('profile', 'update') == True` для роли 'User  ').
- **Ограничения**:
  - Нет иерархии ролей (e.g., 'Admin' не наследует 'User  ' — вручную добавлять permissions).
  - Проверки только в views (не в шаблонах — ссылки всегда видны, но доступ блокируется).
  - API без JWT (настроить simplejwt для токенов).

## Зависимости и настройка

- **Settings.py**:
  - `AUTH_USER_MODEL = 'users.MyUser '`.
  - `AUTHENTICATION_BACKENDS = ['users.backends.EmailBackend', 'django.contrib.auth.backends.ModelBackend']` (EmailBackend для authenticate по email).
  - `INSTALLED_APPS`: 'rbac', 'users', 'rest_framework', 'rest_framework_simplejwt', 'widget_tweaks'.
  - `REST_FRAMEWORK`: SessionAuthentication, IsAuthenticated по умолчанию.
  - `LOGIN_URL = '/login/'`, `SESSION_COOKIE_AGE = 3600`.
- **Миграции**: `python manage.py makemigrations users rbac; migrate`.
- **Backend**: Реализуйте `users/backends.py` (EmailBackend: authenticate по email вместо username).
- **Admin**: Добавьте кастомные формы/фильтры для ролей (e.g., Inline для permissions).
- **Документация**: Для API — DRF browsable API (DEBUG=True).
