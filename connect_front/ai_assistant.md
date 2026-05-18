# AI Assistant: механика взаимодействия фронта с бэкендом

Актуально по состоянию кода в:

- фронт: `C:\Users\user\Desktop\connect_front`
- бэкенд: `C:\projects\bpms_crm_develop_new`

Отдельно вынесен краткий список рисков и точек для рефакторинга:

- `ai_assistant_risks.md`

## Где находится код

### Фронт

- `src/modules/AIAssistant/*` — весь UI ассистента
- `src/layouts/components/Header/mixins.js`
- `src/layouts/components/Mobile/Header/mixins.js`
- `src/config/axios.js`
- `.env.local`

### Бэкенд

- `bpms/chat_ai/*` — основной backend-модуль ассистента
- `users/models.py`
- `users/serializers.py`
- `users/views.py`
- `bkz3/urls.py`

## Короткий вывод

Ассистент работает как обычный REST-чат без SSE/WebSocket/streaming.

Сценарий такой:

1. Фронт открывает drawer по `?ai_chat=true`.
2. Загружает список чатов и берёт первый чат как активный.
3. Загружает сообщения этого чата.
4. При отправке текста фронт сразу локально дорисовывает сообщение пользователя.
5. Затем делает `POST /chat_ai/messages/`.
6. Бэкенд синхронно:
   - сохраняет сообщение пользователя,
   - вызывает LLM для классификации,
   - при необходимости вызывает LLM для парсинга intents,
   - создаёт bot-message,
   - создаёт `IntentModel` для каждого найденного намерения.
7. Фронт получает уже готовый bot-message с вложенными intents и рендерит форму уточнений/кнопки создания объектов.

То есть фронт не ведёт отдельный state-машинный протокол с беком: он просто ждёт один длинный `POST`, который возвращает готовый ответ бота.

## Вход в ассистент

### Показ кнопки

Кнопка ассистента подключается только если у пользователя `use_ai_bot = true`:

- `src/layouts/components/Header/mixins.js:23`
- `src/layouts/components/Mobile/Header/mixins.js:19`
- `users/models.py:416`

### Открытие UI

- Кнопка находится в `src/modules/AIAssistant/AIButton.vue`
- Открытие идёт не через отдельный route, а через query-параметр `ai_chat=true`
- Модуль и drawer лениво подгружаются:
  - `src/modules/AIAssistant/init.vue`
  - `src/modules/AIAssistant/Drawer/index.vue:114`

### Подсказки около кнопки

Состояние подсказок хранится в профиле пользователя:

- поле: `users.models.ProfileModel.chat_ai_tooltip` — `users/models.py:420`
- сериализация в user payload: `users/serializers.py:1240`
- обновление: `PATCH /users/chat_ai_tooltip/` — `users/views.py:742`
- фронтовый вызов: `src/modules/AIAssistant/AIButton.vue:284`

Подсказки отдельны для `task`, `event`, `meeting`, `reports`.

## Базовый API префикс

Во фронте `axios` настроен на `baseURL = process.env.VUE_APP_API_URL`:

- `src/config/axios.js:5`
- `src/config/axios.js:8` — timeout `60000`
- `.env.local:1` — `VUE_APP_API_URL="/api/v1"`

Поэтому фронтовый вызов `'/chat_ai/messages/'` реально уходит на:

- `/api/v1/chat_ai/messages/`

Подключение backend URL:

- `bkz3/urls.py:107`

## Что делает фронт

## 1. Получение чатов

Vuex action:

- `src/modules/AIAssistant/store/actions.js:7`

Запрос:

- `GET /chat_ai/chats/`

Поведение:

- бэкенд возвращает список чатов пользователя
- фронт кладёт список в `chatList`
- активным делает только `data.results[0]`
- сразу инициализирует локальное хранилище сообщений только для этого чата

Вывод: backend поддерживает список чатов, но текущий UI фактически живёт только с первым чатом.

## 2. Получение сообщений

Vuex action:

- `src/modules/AIAssistant/store/actions.js:26`

Запрос:

- `GET /chat_ai/messages/?page=...&page_size=...&chat=<id>`

Рендер/скролл:

- `src/modules/AIAssistant/Drawer/Body.vue`

Особенности:

- backend выдаёт сообщения `order_by('-created_at')`, а paginator затем делает `data.reverse()`
- внутри одной страницы фронт получает порядок от старых к новым
- старые страницы догружаются вверх infinite-scroll’ом
- новые сообщения фронт добавляет вниз локально

Пагинатор:

- `bpms/chat_ai/paginators.py:7`
- `bpms/chat_ai/paginators.py:15`

## 3. Отправка сообщения

Vuex action:

- `src/modules/AIAssistant/store/actions.js:50`

Запрос:

- `POST /chat_ai/messages/`

Payload:

```json
{
  "text": "...",
  "chat": "<activeChat.id>"
}
```

Фактическая механика на фронте:

1. Сразу добавляется optimistic-сообщение пользователя с локальным `uuid`.
2. В store включается `aiLoading = true`.
3. UI показывает индикатор "думает":
   - `src/modules/AIAssistant/Drawer/Body.vue:16`
   - `src/modules/AIAssistant/Drawer/Footer.vue:508`
4. Фронт ждёт один HTTP-ответ.
5. Если ответ пришёл, в список добавляется bot-message.
6. Если запрос упал, фронт добавляет локальное error-message от бота.

Важно: фронт не получает в ответ серверную запись пользовательского сообщения, только bot-message. Поэтому локальное сообщение пользователя в текущей сессии не reconciled с backend-id.

## 4. Быстрые действия и голос

### Быстрые действия

- `src/modules/AIAssistant/Drawer/Footer.vue:142`

Быстрые кнопки просто подставляют готовый текст в input и затем отправляются как обычное сообщение. Отдельного API под них нет.

### Голосовой ввод

- `src/modules/AIAssistant/Drawer/Footer.vue:236`

Используется browser `SpeechRecognition` / `webkitSpeechRecognition`.

Важно:

- аудио на бэкенд не отправляется
- на бэкенд уходит уже распознанный текст
- значит backend ничего не знает про исходную аудиозапись

## 5. Очистка диалога

- фронт: `src/modules/AIAssistant/Drawer/Header.vue:79`
- backend action: `POST /chat_ai/chats/<id>/clear-messages/`

Бэкенд soft-delete’ит:

- все `AIMessageModel` этого чата
- все `IntentModel`, связанные с этими сообщениями

## Что делает бэкенд

## 1. Chats API

`AIChatViewSet`:

- `bpms/chat_ai/views.py:50`

### `GET /api/v1/chat_ai/chats/`

- `bpms/chat_ai/views.py:54`

Логика:

- берёт активные чаты текущего `request.user.profile`
- если чатов нет, создаёт новый автоматически
- возвращает paginated list

### `POST /api/v1/chat_ai/chats/<id>/clear-messages/`

- `bpms/chat_ai/views.py:83`

## 2. Messages API

`AIMessageViewSet`:

- `bpms/chat_ai/views.py:103`

### `GET /api/v1/chat_ai/messages/`

Фильтры:

- `chat`
- `since`

Код:

- `bpms/chat_ai/views.py:107`

### `POST /api/v1/chat_ai/messages/`

Код:

- `bpms/chat_ai/views.py:136`

Логика:

1. Находит чат по `chat_id`.
2. Создаёт user-message со статусом `queued`.
3. Обновляет `chat.last_sent`.
4. Синхронно вызывает `process_message(user_message.id, request)`.
5. Возвращает сериализованный bot-message.

Это ключевая точка: обработка сейчас не async, хотя в коде есть комментарий про `django_q`.

### `GET /api/v1/chat_ai/messages/<id>/status/`

Есть action статуса:

- `bpms/chat_ai/views.py:167`

Но текущий фронт его не использует. Polling статуса в UI нет.

## 3. Intents API

`IntentModelViewSet`:

- `bpms/chat_ai/views.py:175`

Используемые фронтом операции:

- `DELETE /chat_ai/intents/<id>/`
- `PATCH /chat_ai/intents/<id>/update-value/`
- `PATCH /chat_ai/intents/<id>/` — фронт использует для сохранения `related_object`

Неиспользуемый фронтом endpoint:

- `POST /chat_ai/intents/<id>/materialize/` — есть на бэке, но не используется текущим UI

Поиск по фронту `materialize` ничего не дал.

## LLM pipeline внутри backend

Основной пайплайн:

- `bpms/chat_ai/utils/messages.py:348` — `process_message`

### Шаг 1. Классификация

- `bpms/chat_ai/utils/messages.py:146` — `classify_message`

Вызывает роль `intent_classifier` через `invoke_role_prompt(...)`.

Ожидаемый ответ: одно из

- `task`
- `event`
- `meet`
- `report`
- `unknown`

### Шаг 2. Парсинг intents

Если intent не `unknown`, вызывается ещё один prompt:

- `intent_parser`
- или `intent_parser_report`

Код:

- `bpms/chat_ai/utils/messages.py:384`

Ожидается массив объектов с `intent_type` и полями raw-data.

### Шаг 3. Генерация текста ответа бота

- `bpms/chat_ai/utils/messages.py:314` — `generate_bot_reply`

Сейчас это не отдельный LLM-вызов, а простая серверная функция-шаблон:

- если intents найдены, пишет "Я выявил N намерений..."
- если нет — общий текст "Принял сообщение..."

### Шаг 4. Создание bot-message

- `bpms/chat_ai/utils/messages.py:115` — `_create_bot_message`

Bot-message:

- привязывается к чату
- указывает `reply_to = user_message`
- получает `is_bot = true`
- сразу ставится в `status = done`

### Шаг 5. Создание `IntentModel`

Для каждого распарсенного intent создаётся запись через `IntentCreateSerializer`.

- `bpms/chat_ai/serializers.py:132`

При создании сразу запускается `build_resolutions(instance, request)`.

## Как вызывается LLM

Универсальный вызов:

- `bpms/chat_ai/utils/messages.py:184` — `invoke_role_prompt`

Настройки берутся из:

- `AIChatRoleModel`
- `AIProvider`

Модели:

- `bpms/chat_ai/models.py`

### Ветка `provider.code == "gos24.kz"`

- `bpms/chat_ai/utils/messages.py:215`

Используется HTTP POST на `provider.base_url` c Ollama-подобным payload:

- `model`
- `system`
- `prompt`
- `options.temperature`
- `options.top_p`
- `options.num_predict`
- `options.num_ctx`
- опционально `format`

Особенности:

- query string вроде `chat_ai_classify&message=...` / `chat_ai_intents&message=...` дописывается прямо к URL
- timeout у `requests.post` — до `600` секунд на read
- retries — до `10` попыток на 502/503/504 и timeout

### Ветка остальных провайдеров

- `bpms/chat_ai/utils/messages.py:282`

Используется `openai.OpenAI(...).chat.completions.create(...)`.

### Учёт токенов

После каждого LLM-вызова создаётся `TokenUsage`:

- `bpms/chat_ai/utils/messages.py:303`

## Как из raw intents получается форма на фронте

Логика в:

- `bpms/chat_ai/utils/intents.py`

Ключевые шаги:

- `find_candidates_for_reference_fields` — ищет кандидатов для ссылочных полей
- `create_values_for_all_fields` — пытается автоматически выбрать `value`
- `fill_resolved_from_values` — строит `resolved_data`
- `update_intent_status` — ставит `ready` или `resolving`
- `build_resolutions` — первичная сборка
- `build_resolved_data` — повторная сборка после ручных правок

Код:

- `bpms/chat_ai/utils/intents.py:72`
- `bpms/chat_ai/utils/intents.py:114`
- `bpms/chat_ai/utils/intents.py:201`
- `bpms/chat_ai/utils/intents.py:257`
- `bpms/chat_ai/utils/intents.py:306`
- `bpms/chat_ai/utils/intents.py:360`

### Поиск кандидатов

Для ссылочных полей используется метадата поля:

- `model`
- `data_path`

Механика:

1. Из `raw_data[field]` берётся строка.
2. Для ссылочных полей она режется по запятым.
3. По каждому имени вызывается `model_class.get_filtered_select_queryset(search_name, request)`.
4. Кандидаты превращаются в snapshots через `model_class.get_snapshot(...)`.

Именно эти `candidates` фронт затем рендерит в селектах.

### Статусы полей

Для каждого поля в `resolutions` живут:

- `candidates`
- `value`
- `resolved`
- `status`

Глобальный статус intent:

- `resolving` — не все required поля определены
- `ready` — все required поля есть
- `done` — объект уже создан и сохранён в `related_object`
- `failed` — создание объекта не удалось

## Что рендерит фронт для intents

Сериализация bot-message:

- `bpms/chat_ai/serializers.py:60`
- `bpms/chat_ai/serializers.py:76`

Backend вкладывает в сообщение массив `intents`.

Фронт:

- `src/modules/AIAssistant/Drawer/Message/BotMessage.vue`
- `src/modules/AIAssistant/Drawer/Message/IntentsSwitch.vue`
- `src/modules/AIAssistant/Drawer/Message/IntentsWidgets/IntentWidget.vue`

### Уточнение значений

При изменении поля фронт через debounce вызывает:

- `PATCH /chat_ai/intents/<id>/update-value/`

Код:

- `src/modules/AIAssistant/Drawer/Message/ResolutionsWidgets/Widgets/mixins.js:136`
- `bpms/chat_ai/views.py:187`

Backend обновляет `resolutions[field].value`, затем пересчитывает `resolved_data` и `status`.

### Создание целевого объекта

Текущий фронт обычно не использует backend `materialize`.

Вместо этого он:

1. Берёт `intent_type.metadata.backend_base_url`
2. Собирает payload из `resolutions`
3. Делает прямой POST в целевой бизнес-endpoint
4. После успеха делает `PATCH /chat_ai/intents/<id>/` и сохраняет `related_object`

Код:

- `src/modules/AIAssistant/Drawer/Message/IntentsWidgets/IntentWidget.vue:255`
- `src/modules/AIAssistant/Drawer/Message/IntentsWidgets/IntentWidget.vue:212`

### Отчёты

Для report intents фронт ожидает бинарный файл:

- `responseType: 'blob'`
- затем скачивает файл локально

Код:

- `src/modules/AIAssistant/Drawer/Message/IntentsWidgets/IntentWidget.vue:138`
- `src/modules/AIAssistant/Drawer/Message/IntentsWidgets/IntentWidget.vue:244`

## Реальная сквозная последовательность

```text
AIButton click
-> route query ?ai_chat=true
-> getChat()
-> GET /api/v1/chat_ai/chats/
-> getMessage()
-> GET /api/v1/chat_ai/messages/?chat=<id>

sendMessage()
-> optimistic add user message
-> POST /api/v1/chat_ai/messages/
-> backend creates user message (queued)
-> backend process_message()
-> classify via LLM
-> parse intents via LLM
-> create bot message
-> create IntentModel + resolutions
-> return bot message with intents
-> frontend renders bot card + intent widgets

user edits intent field
-> PATCH /api/v1/chat_ai/intents/<id>/update-value/
-> backend rebuild_resolved_data()

user clicks create
-> POST metadata.backend_base_url
-> PATCH /api/v1/chat_ai/intents/<id>/ { related_object }
```

## Наблюдения и риски

### 1. Нет стриминга и нет polling статуса

Frontend ждёт один длинный HTTP-ответ от `POST /chat_ai/messages/`.

Следствие:

- промежуточный прогресс не отображается
- endpoint `/messages/<id>/status/` в текущем UI не используется

### 2. Таймауты фронта и бэка сильно расходятся

Фронт:

- `axios timeout = 60000` — `src/config/axios.js:8`

Бэкенд/LLM:

- read timeout до `600` секунд
- плюс retry цикл

Следствие:

- фронт может показать локальную ошибку раньше, чем backend закончит обработку
- при этом backend всё равно может позже создать bot-message

### 3. User-message на фронте optimistic и не reconciled

В текущей сессии у пользовательского сообщения может остаться локальный `uuid`, а не реальный backend-id. Серверный user-message фронт в ответе не получает.

### 4. `materialize` есть, но UI его не использует

С точки зрения реальной механики ассистент сейчас не завершает intent через единый `chat_ai` endpoint, а уходит напрямую в бизнесовые API через `metadata.backend_base_url`.

### 5. UI использует только первый чат

Backend умеет список чатов, но текущий drawer не даёт выбирать чат и всегда берёт `results[0]`.

### 6. В коде видны потенциальные ограничения по безопасности/доступам

Наблюдение по текущему коду:

- `AIChatViewSet` защищён `AIBotEnabled`
- `AIMessageViewSet` и `IntentModelViewSet` — только `IsAuthenticated`
- `AIMessageModel` не переопределяет `get_queryset`, значит базовый queryset берётся как `is_active=True`
- фильтрация сообщений идёт по `chat` query param, но в самом queryset сообщения не ограничены автором чата

Файлы:

- `bpms/chat_ai/views.py:37`
- `bpms/chat_ai/views.py:103`
- `bpms/chat_ai/views.py:175`
- `bpms/chat_ai/models.py:202`
- `common/models.py:417`

Это выглядит как место, которое стоит отдельно перепроверить на предмет доступа к чужим chat/message/intents по известным id.

## Ключевые файлы для дальнейшей доработки

Если нужно что-то менять в поведении ассистента, в первую очередь смотреть сюда:

- фронт:
  - `src/modules/AIAssistant/store/actions.js`
  - `src/modules/AIAssistant/Drawer/Body.vue`
  - `src/modules/AIAssistant/Drawer/Footer.vue`
  - `src/modules/AIAssistant/Drawer/Message/IntentsWidgets/IntentWidget.vue`
  - `src/modules/AIAssistant/Drawer/Message/ResolutionsWidgets/Widgets/mixins.js`
- бэкенд:
  - `bpms/chat_ai/views.py`
  - `bpms/chat_ai/serializers.py`
  - `bpms/chat_ai/utils/messages.py`
  - `bpms/chat_ai/utils/intents.py`
  - `bpms/chat_ai/models.py`
  - `users/views.py`
