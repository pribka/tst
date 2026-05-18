# Local Backend And Frontend Interaction

Дата фиксации: 2026-05-10.

Документ описывает текущую локальную связку фронта `connect_front` с Django-бэком `bpms_crm_develop_new`, фактический поток HTTP/Socket.IO и действия, выполненные для запуска.

## Локальная схема

| Компонент | Значение |
|---|---|
| Frontend repo | `C:\Users\user\Desktop\connect_front` |
| Backend repo | `C:\projects\bpms_crm_develop_new` |
| Backend venv | `C:\projects\venv\bpms_crm` |
| Local domain | `d.centersoft.kz` -> `127.0.0.1` |
| Frontend URL | `http://d.centersoft.kz:8080` |
| Backend URL | `http://d.centersoft.kz:8000` |
| Database | PostgreSQL `bpms` on `127.0.0.1:5433`, user `postgres` |
| Node | `16.20.2` |

Фронт в dev-режиме не ходит в API напрямую на `:8000`. В браузере он делает запросы на свой origin:

```text
http://d.centersoft.kz:8080/api/v1/...
```

А `vue.config.js` проксирует `^/api` на `VUE_APP_PROXY_TARGET`:

```text
VUE_APP_API_URL="/api/v1"
VUE_APP_PROXY_TARGET="http://d.centersoft.kz:8000"
```

Итоговый путь:

```text
browser -> Vue dev server :8080 -> proxy /api -> Django :8000 -> /api/v1/...
```

Socket.IO использует отдельные переменные:

```text
VUE_APP_SOCKET_HOST="http://d.centersoft.kz:8000"
VUE_APP_SOCKET_PATH="/socket"
```

## Найденные существующие документы

- `docs/ARCHITECTURE.md` - общая архитектура Vue 2 SPA, server-driven routing, порядок bootstrapping.
- `docs/INTEGRATIONS.md` - REST, Socket.IO, push, CSRF/cookie auth и внешние интеграции.
- `docs/STACK.md` - стек и важные env-переменные.
- `docs/STRUCTURE.md` - структура папок, модулей и связь `pageWidget` с backend routes.

Этот документ дополняет их локальной рабочей процедурой и конкретной связкой `d.centersoft.kz`.

## Что было переключено локально

Frontend `.env.local` настроен на локальный backend:

```text
VUE_APP_API_URL="/api/v1"
VUE_APP_PROXY_TARGET="http://d.centersoft.kz:8000"
VUE_APP_SOCKET_HOST="http://d.centersoft.kz:8000"
VUE_APP_PUSH_API_URL="http://d.centersoft.kz:8000"
VUE_APP_URL ="http://d.centersoft.kz:8000"
VUE_APP_CSRF_NAME="csrftoken"
```

Backend `bkz3/local_settings.py` переопределяет БД ниже по файлу. Рабочее значение:

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'bpms',
        'USER': 'postgres',
        'PASSWORD': 'postgres',
        'HOST': '127.0.0.1',
        'PORT': '5433',
    }
}
```

В конец `local_settings.py` добавлены локальные override'ы:

```python
BACKEND_URL = 'http://d.centersoft.kz:8000'
FRONTEND_URL = 'http://d.centersoft.kz:8080'
ALLOWED_HOSTS = list(set(ALLOWED_HOSTS + ['d.centersoft.kz', '127.0.0.1', 'localhost']))
CORS_ORIGIN_ALLOW_ALL = True
CORS_ALLOWED_ORIGINS = [
    'http://d.centersoft.kz:8080',
    'http://d.centersoft.kz:8000',
    'http://127.0.0.1:8080',
    'http://127.0.0.1:8000',
]
```

## Git sync

Frontend root был принудительно приведен к ветке `origin/dev`.

Папки внутри `src/modules`, у которых есть свои `.git`, также были принудительно обновлены из `origin/dev`. Исключение: `src/modules/News` не имеет `origin/dev`, поэтому модуль оставлен как есть и отмечен как требующий отдельной проверки ветки.

## Backend запуск

Команды запуска из `C:\projects\bpms_crm_develop_new`:

```powershell
C:\projects\venv\bpms_crm\Scripts\python.exe manage.py check
C:\projects\venv\bpms_crm\Scripts\python.exe manage.py migrate --noinput
C:\projects\venv\bpms_crm\Scripts\python.exe manage.py runserver d.centersoft.kz:8000 --noreload
```

Что было выполнено:

- `manage.py check` проходит.
- Миграции применены к `bpms` на `127.0.0.1:5433`.
- Для запуска не хватало `pywebpush`; пакет установлен, transitive-зависимости выровнены до рабочей связки.
- Backend слушает `127.0.0.1:8000`, доступен как `http://d.centersoft.kz:8000`.

Логи локального запуска:

```text
C:\projects\bpms_crm_develop_new\.codex_runtime\backend.out.log
C:\projects\bpms_crm_develop_new\.codex_runtime\backend.err.log
```

## Frontend запуск

Проект требует Node 16. При Node 20 сборка падает на Webpack 4/OpenSSL (`ERR_OSSL_EVP_UNSUPPORTED`).

Рабочий запуск:

```powershell
$nodeDir = "$env:APPDATA\nvm\v16.20.2"
$env:PATH = "$nodeDir;$env:PATH"
npm run dev4gb
```

`npm run dev4gb` запускает:

```text
cross-env NODE_ENV=dev VUE_APP_BUILD_TYPE=dev node --max-old-space-size=4096 node_modules/@vue/cli-service/bin/vue-cli-service.js serve --host d.centersoft.kz --port 8080
```

Логи локального запуска:

```text
C:\Users\user\Desktop\connect_front\.codex_runtime\frontend.out.log
C:\Users\user\Desktop\connect_front\.codex_runtime\frontend.err.log
```

Фактический запуск 2026-05-10:

- Node: `v16.20.2`
- npm: `8.19.4`
- frontend dev-server: `http://d.centersoft.kz:8080/`
- HTML root `/` отдается со статусом `200`.
- Браузер открыт на `http://d.centersoft.kz:8080/`.

Замечание по сборке: dev-server поднялся, но в логах есть lint diagnostic из Calendar locale declaration files:

```text
src/modules/Calendar/lang/locales/kk.d.ts
src/modules/Calendar/lang/locales/ru.d.ts
Parsing error: Missing semicolon.
```

Это приходит через `eslint-loader` при lazy context `src/modules/Calendar/lang/locales`. Сборку это не остановило, но паттерн стоит поправить отдельно: либо исключить `*.d.ts` из JS eslint-loader, либо убрать declaration files из runtime lazy import-контекста.

## Auth flow

Фронт уже использует `login2`, то есть endpoint без reCAPTCHA:

```text
src/store/modules/user/actions.js
login -> POST /users/login2/
```

С учетом `VUE_APP_API_URL="/api/v1"` фактический браузерный URL:

```text
POST http://d.centersoft.kz:8080/api/v1/users/login2/
```

Через dev-server proxy запрос уходит на backend:

```text
POST http://d.centersoft.kz:8000/api/v1/users/login2/
```

Backend route:

```text
bkz3/urls.py          -> path('api/v1/users/', include('users.urls'))
users/urls.py         -> router.register(r'', CustomUserViewSet)
users/views.py        -> @action(url_path="login2")
users/serializers.py  -> LoginCustomUserSerializerNoCaptcha
```

Auth - session/cookie based:

- axios instance: `src/config/axios.js`
- `withCredentials = true`
- CSRF cookie name: `VUE_APP_CSRF_NAME`, сейчас `csrftoken`
- XSRF header: `X-CSRFToken`
- cookies: `sessionid`, `csrftoken`
- при `401` фронт делает `user/logout` и `location.reload()`
- при `503` axios автоматически повторяет запрос через 200 ms

Пользователь для локальной работы:

```text
pribka@mail.ru
```

Пароль был сброшен локально для запуска, но намеренно не фиксируется в документации.

Проверка через frontend proxy:

| Request через `:8080` | Status | Notes |
|---|---:|---|
| `GET /api/v1/app_info/entry/` | 200 | публичная entry config |
| `POST /api/v1/users/login2/` | 200 | вход под `pribka@mail.ru` |
| `GET /api/v1/users/info/` | 200 | session auth работает |
| `GET /api/v1/app_info/check_front_cache/` | 200 | возвращает cache uid |
| `GET /api/v1/app_info/global/` | 200 | global UI config |
| `GET /api/v1/app_info/routes/?ver=alt` | 200 | server-driven routes |

После `login2` cookies выставляются на домен `d.centersoft.kz`:

```text
csrftoken
sessionid
```

## Startup request flow

Основная последовательность на фронте находится в `src/main.js`:

```text
mainAppInit()
  -> store.dispatch('user/getUserInfo')
  -> asyncInitLang
  -> store.dispatch('getCacheUID')
  -> store.dispatch('configInit')
  -> store.dispatch('navigation/routeInit')
  -> setupRouter()
  -> new Vue()
```

Ключевые HTTP-запросы:

| Шаг | Frontend call | Backend endpoint | Назначение |
|---|---|---|---|
| Проверка сессии | `GET /users/info/` | `/api/v1/users/info/` | текущий пользователь, профиль, permissions |
| Auth config | `GET /app_info/entry/` | `/api/v1/app_info/entry/` | настройки экрана входа/регистрации |
| Cache UID | `GET /app_info/check_front_cache/` | `/api/v1/app_info/check_front_cache/` | uid фронтового кеша |
| Global config | `GET /app_info/global/` | `/api/v1/app_info/global/` | глобальные настройки UI |
| Routes | `GET /app_info/routes/?ver=alt` | `/api/v1/app_info/routes/?ver=alt` | server-driven меню/роуты |
| Profile sync | `PUT /users/update_profile/` | `/api/v1/users/update_profile/` | автосинхронизация timezone, если включена |
| Logout | `GET /users/logout/` | `/api/v1/users/logout/` | завершение session auth |

Backend route logic:

- `common/views.py::AppInfoViewSet.get_entry` - публичные настройки entry screen.
- `common/views.py::AppInfoViewSet.check_front_cache` - uid кеша.
- `common/views.py::AppInfoViewSet.get_global` - authenticated global config.
- `common/views.py::AppInfoViewSet.get_routes` - authenticated routes; `ver=alt` идет через `common.utils.get_alt_routes(request)`.
- `users/views.py::CustomUserViewSet.get_info` - данные текущей сессии.
- `users/views.py::CustomUserViewSet.login2` - вход без reCAPTCHA.

## Server-driven routes pattern

Backend отдает список маршрутов через:

```text
GET /api/v1/app_info/routes/?ver=alt
```

Frontend затем собирает Vue Router на лету. Значение `pageWidget` из backend response должно совпадать с файлом в:

```text
src/views/Dashboard/PageWidgets/{pageWidget}.vue
```

Feature modules живут в:

```text
src/modules/
```

И подключаются через webpack alias:

```text
@apps -> src/modules
```

## Task Filtering Pattern

Список задач использует тот же общий механизм фильтров, что и остальные табличные страницы. Главное правило: выбранные фильтры обычно не передаются в каждом `GET /tasks/task/list/`; они сохраняются на бэке в разрезе `page_name`, а список потом передает `page_name`, `task_type`, пагинацию и сортировку.

Frontend flow:

```text
PageTask/Tasks.vue
  -> taskList from @apps/vue2TaskComponent
  -> TaskTablePage.vue
  -> UniversalTable.vue
  -> GET /api/v1/tasks/task/list/
```

Filter UI flow:

```text
PageFilter
  -> GET  /api/v1/app_info/active_filters/?model=tasks.TaskModel&page_name=<page_name>
  -> POST /api/v1/app_info/chosen_filters/
```

Task table data flow:

```text
GET /api/v1/tasks/task/list/?page=1&page_size=15&page_name=<page_name>&task_type=<task_type>
```

`task_type` - это прямой scope списка, а не сохраненный фильтр:

| Frontend source | Value |
|---|---|
| `src/views/Dashboard/PageWidgets/PageTask.vue` | `taskType = getRouteInfo.task_type || "task"` |
| `src/views/Dashboard/PageWidgets/Tasks.vue` | `taskType = getRouteInfo.task_type || "task,stage"` |
| `TaskTablePage.vue::getDataEndpoint` | `/tasks/task/list/?task_type=${taskType}` |
| `PageTask.vue::page_name` | `page_list_${taskType}_task.TaskModel` |

`page_name` - namespace для пользовательского состояния фильтра. Если переиспользовать `page_name`, переиспользуются те же сохраненные filters, search и ordering. Если нужен независимый список задач, нужен отдельный `page_name`.

Backend flow:

```text
bkz3/urls.py
  -> /api/v1/tasks/
  -> bpms.tasks.apiurls
  -> task/list/
  -> bpms.tasks.apiviews.ListTaskView
  -> bpms.tasks.utils.get_task_queryset()
  -> common.utils.get_filter_queryset()
  -> common.models.FiltersStore(author, model, page_name)
  -> bpms.tasks.utils.filter_by_permissions()
  -> order/paginate/serialize
```

Сохраненный payload лежит в `FiltersStore.filters`:

```text
values      -> active field filters
filterTags  -> UI tags/chips for selected filters
search      -> common search input
ordering    -> selected ordering fields
others      -> page-specific extra state
```

`common.utils.get_filter_queryset()` применяет:

1. Прямой GET-параметр `filters`, если он есть. Это JSON для контекстных одноразовых фильтров.
2. Сохраненные `FiltersStore.values` для `(request.user.profile, model.get_label(), page_name)`.
3. Сохраненный или прямой `search`.
4. Сохраненный `ordering`.

Для задач `bpms.tasks.utils.get_task_queryset()` дополнительно накладывает task-specific параметры:

```text
parent
dead_line_after / dead_line_before / dead_line_is_null / only_no_dead_line
only_participant
im_executor
is_overdue
is_risk
status
task_type
exclude
or_project / or_workgroup
```

После этого `filter_by_permissions()` ограничивает queryset задачами, видимыми пользователю: owner, operator, visors, cooperators, supervisor permissions, director permissions, project/workgroup membership и связанные chat/share cases.

Итоговое правило:

```text
route/list scope + saved page filters + direct query filters + permissions
```

Live check под `pribka@mail.ru` от 2026-05-10:

| Request | Result |
|---|---|
| `POST /api/v1/users/login2/` | `200`, cookies `csrftoken`, `sessionid` |
| `GET /api/v1/app_info/active_filters/?model=tasks.TaskModel&page_name=page_list_task_task.TaskModel` | `200`, saved `search="контракт"`, `ordering=["-counter"]` |
| `GET /api/v1/tasks/task/list/?page=1&page_size=5&page_name=page_list_task_task.TaskModel&task_type=task` | `200`, `count=5`; сохраненный search сузил список |
| `GET /api/v1/tasks/task/list/?page=1&page_size=5&page_name=page_list_task,stage_task.TaskModel&task_type=task,stage` | `200`, `count=10788`; это другой `page_name`, поэтому search от `page_list_task_task.TaskModel` не применился |

Практические правила:

1. Для новой страницы задач `page_name` выбирать осознанно: он управляет сохраненными фильтрами и настройками таблицы.
2. Жесткий контекст страницы передавать query params (`task_type`, `parent`, `status`, project/workgroup params), а не пользовательским saved filter.
3. `PageFilter model="tasks.TaskModel"` подключать там, где пользователь должен сохранять и переиспользовать фильтр.
4. Если список внезапно пустой, сначала проверить `active_filters` для точного `page_name`, а уже потом дебажить `/tasks/task/list/`.
5. Для независимого вида задач нужен новый `page_name`; для намеренно общего фильтра - тот же `page_name`.

## Browser login trace 2026-05-10

Trace was captured from a real visible Chrome session against:

```text
http://d.centersoft.kz:8080/
```

Credentials used locally:

```text
login: pribka@mail.ru
password: reset locally in the local database
```

Final browser state:

```text
URL: http://d.centersoft.kz:8080/dashboard
title: Рабочий стол | Gos24.Connect
cookies: csrftoken, sessionid
```

The UI login form sends:

```text
POST /api/v1/users/login2/ -> 200
GET  /api/v1/users/info/   -> 200
```

Important backend fix found during this trace:

```text
users/views.py::CustomUserViewSet.get_info
```

Before the fix, `GET /api/v1/users/info/` always deleted `sessionid` and `csrftoken` in the response. The frontend then immediately made authenticated follow-up requests as anonymous and returned to `/user/login`. The local fix preserves cookies for the normal browser flow and deletes them only for the `withsecret=true` flow.

One local profile setting was also changed directly through ORM `.update()` to avoid a noisy Elasticsearch side effect during automatic timezone sync:

```text
profile.timezone = Asia/Qyzylorda
profile.timezone_auto_detect = False
```

Observed successful API calls after login:

| Count | Method | Status | Path |
|---:|---|---:|---|
| 3 | GET | 200 | `/api/v1/users/info/` |
| 1 | POST | 200 | `/api/v1/users/login2/` |
| 1 | GET | 200 | `/api/v1/app_info/entry/` |
| 1 | GET | 200 | `/api/v1/app_info/check_front_cache/` |
| 1 | GET | 200 | `/api/v1/app_info/global/` |
| 1 | GET | 200 | `/api/v1/app_info/routes/?ver=alt&view=desktop` |
| 1 | GET | 200 | `/api/v1/app_info/routes/meta/?name=dashboard` |
| 1 | GET | 200 | `/api/v1/app_info/timer/` |
| 1 | GET | 200 | `/api/v1/news/news/list/?page=1&page_size=1&is_banner=true` |
| 1 | GET | 200 | `/api/v1/meetings/calls/active_calls/` |
| 1 | GET | 200 | `/api/v1/notifications/unread_count/` |
| 1 | GET | 200 | `/api/v1/personal_planes/work_plan_show/` |
| 1 | GET | 200 | `/api/v1/widgets/user_desktops/` |
| 1 | GET | 200 | `/api/v1/widgets/user_desktops/729d762a-7882-11ee-b13d-0242ac11000e/?is_desktop=true` |
| 2 | GET | 200 | `/api/v1/calendars/events/top/?start=2026-05-10T00:01:01.000%2B05:00&end=2026-05-10T23:59:59.059%2B05:00` |
| 1 | GET | 200 | `/api/v1/calendars/info/` |
| 1 | GET | 200 | `/api/v1/calendars/events/?start=2026-05-03T00:00:00.000Z&end=2026-05-11T00:00:00.000Z&page_name=c917942c-ffcc-11ef-a323-0242ac11000f` |
| 1 | GET | 200 | `/api/v1/chat/list/?page=1&page_size=15` |
| 1 | GET | 200 | `/api/v1/chat/message/count/` |
| 5 | GET | 200 | `/api/v1/tasks/task/list/?page=1&page_size=15&...&task_type=task` |

Non-fatal network noise observed:

| Type | Details |
|---|---|
| reCAPTCHA | `POST https://www.google.com/recaptcha/api2/clr?...` aborted by Chrome; login still uses `/login2/` and succeeds. |
| Avatars | Several `GET http://d.centersoft.kz:8000/media/avatars/...` requests failed with `net::ERR_BLOCKED_BY_ORB`; dashboard still loaded. |
| Socket.IO | Frontend tries `GET http://d.centersoft.kz:8000/socket/?EIO=4&transport=websocket`; local Django runserver returns `404`. Socket service is not served by this local backend process. |

External hosts seen in the browser session:

```text
http://d.centersoft.kz:8080
http://d.centersoft.kz:8000
https://connect.gos24.kz
https://fonts.googleapis.com
https://fonts.gstatic.com
https://www.google.com
https://www.gstatic.com
```

Raw local trace artifact:

```text
C:\Users\user\Desktop\connect_front\.codex_runtime\browser_probe\network-log.json
```

## Практические паттерны, которых не хватает

1. Локальный runbook.
   Нужен короткий `docs/LOCAL_RUNBOOK.md` или npm/script, который явно запускает Node 16, backend venv, миграции и health checks.

2. Контроль вложенных module repos.
   Нужен список модулей с ожидаемой веткой. Сейчас `src/modules/News` не имеет `origin/dev`, это легко пропустить при массовом обновлении.

3. Env examples.
   Стоит добавить `.env.local.example` без секретов, где отдельно показан режим `d.centersoft.kz -> local backend`.

4. CSRF/CORS compatibility.
   В текущем Django-стиле `CSRF_TRUSTED_ORIGINS` используется без схемы. При апгрейде Django нужно добавить значения со схемой: `http://d.centersoft.kz:8080`, `http://d.centersoft.kz:8000`.

5. Dependency pinning.
   `pywebpush` отсутствовал в venv, а его зависимости конфликтуют со старыми пакетами. Лучше зафиксировать совместимые версии в backend requirements.

6. Management command side effects.
   Во время `manage.py check`, migration и shell-скриптов приложение может выполнять side effects из `ready()`/async tasks. Это лучше изолировать, чтобы maintenance commands не запускали фоновые бизнес-действия.

7. Auth endpoint policy.
   `login2` уже подключен на фронте, но стоит явно зафиксировать в README/dev docs, что для локального и dev-режима используется `login2`, а `login` остается reCAPTCHA-вариантом.
