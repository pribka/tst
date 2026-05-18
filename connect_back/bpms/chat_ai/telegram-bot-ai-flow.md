# Telegram AI Bot: обработка свободного текста

Документ фиксирует текущий механизм из `welcome_bot.py`, через который Telegram-бот принимает свободный текст и превращает его, например, в намерение `create_task`, а затем в задачу BPMS.

## Где находится механизм

- `welcome_bot.py` в корне проекта - основная runtime-точка Telegram-бота.
- `telegram_bot/base.py` создает `welcome_bot = telebot.TeleBot(TG_BOT_TOKEN)`.
- `bot-delans.conf` запускает корневой файл командой `python /app/welcome_bot.py`.
- `bpms/chat_ai/` хранит модели, сериализаторы и утилиты для чатов, сообщений и намерений.
- `hz.json` в корне содержит экспорт конфигурации `chat_ai`: типы намерений и роли LLM. Runtime читает эти настройки из БД, а не напрямую из `hz.json`.
- Для заявок на согласование добавлена data migration `0025_workflow_request_intent.py`: она создает intent type, classifier prompt, отдельный parser prompt и человекочитаемые подписи в БД.

## Запуск и вход в Telegram

`welcome_bot.py` инициализирует Django, импортирует `welcome_bot` и в конце запускает:

```python
welcome_bot.infinity_polling()
```

Все текстовые сообщения, которые не перехватили более специфичные handlers меню/статусов, попадают в универсальный обработчик:

```python
@welcome_bot.message_handler(func=lambda message: True)
def fallback_handler(message):
    ...
    _tg_ai_handle_dialog_input(message, profile, incoming_text)
```

Голосовые и аудио сообщения идут похожим путем: `fallback_voice_handler()` сначала распознает звук через `_tg_ai_extract_voice_text()`, затем передает полученный текст в `_tg_ai_handle_dialog_input()`.

Доступ к AI-боту проверяется по профилю:

- профиль ищется по `telegram_id` через `_get_profile_by_chat_id(chat_id)`;
- у профиля должен быть пользователь;
- пользователь должен быть authenticated;
- у профиля должен быть включен флаг `use_ai_bot`.

## Сессионный контекст

Для AI-диалога бот хранит состояние в Django cache:

- ключ: `tg_ai_dialog:<profile_id>`;
- TTL: 12 часов;
- в `chunks` складываются последние текстовые сообщения пользователя;
- хранится максимум 12 chunks.

Когда пользователь пишет новое сообщение после предыдущего результата, бот деактивирует активные намерения предыдущего bot-message:

```python
previous_bot_message_id = state.get("last_bot_message_id")
if previous_bot_message_id:
    _tg_ai_deactivate_intents_for_bot_message(previous_bot_message_id)
```

Это важно: уточнение не патчит старое намерение. Бот пересобирает `session_text` из накопленных chunks и заново классифицирует/парсит весь диалог. Старые pending-intents становятся неактивными.

## Классификация свободного текста

Главная функция обработки:

```python
def _tg_ai_handle_dialog_input(message, profile, incoming_text):
    ...
    intent_label, intents = _tg_ai_classify_and_parse(session_text)
```

`_tg_ai_classify_and_parse()` делает два LLM-вызова:

1. Классификатор `intent_classifier`.

   Он получает весь `session_text` и должен вернуть одну строку из:

   ```text
   task, event, meet, report, workflow_request, unknown
   ```

   Код передает в provider JSON schema `INTENT_CLASSIFIER_SCHEMA`.

2. Парсер намерения.

   Если классификатор вернул не `unknown`, бот вызывает роль:

   - `intent_parser` для `task`, `event`, `meet`;
   - `intent_parser_report` для `report`, если такая роль есть в БД.
   - `intent_parser_workflow_request` для `workflow_request`, если такая роль есть в БД.

   Парсер получает контекст с текущей датой и днем недели:

   ```python
   {
       "current_date": datetime.today().strftime("%Y-%m-%d"),
       "current_weekday": datetime.today().strftime("%A"),
   }
   ```

   Ответ парсера ожидается как JSON-массив объектов. Код использует мягкую схему `INTENT_RESPONSE_SOFT_SCHEMA`, поэтому конкретные поля фактически задаются prompt-ом роли в БД.

Экспорт `hz.json` показывает текущую конфигурацию ролей:

- `intent_classifier`: provider `gos24.kz`, model `qwen3:8b`, temperature `0.00`;
- `intent_parser`: provider `gos24.kz`, model `qwen3:8b`, temperature `0.10`;
- `intent_parser_report`: provider `gos24.kz`, model `qwen3:8b`, temperature `0.10`.
- `intent_parser_workflow_request`: provider `gos24.kz`, model `qwen3:8b`, temperature `0.10`.

`_tg_ai_call_provider()` поддерживает два режима:

- если `provider.code == "gos24.kz"` - обычный `requests.post()` на `provider.base_url` с payload формата Ollama-like: `model`, `system`, `prompt`, `stream`, `options`, опционально `format`;
- иначе - OpenAI-compatible client через `OpenAI(api_key=..., base_url=...)`.

## Что возвращает parser для задачи

Для создания задачи parser должен вернуть объект с типом:

```json
{
  "intent_type": "create_task",
  "name": "Краткое название",
  "description": "Описание или null",
  "operator": "Основной исполнитель или null",
  "date_start_plan": "YYYY-MM-DD или YYYY-MM-DDTHH:MM или null",
  "dead_line": "YYYY-MM-DDTHH:MM или null",
  "project": "Проект или null",
  "cooperators": "Другие исполнители через запятую или null",
  "visors": "Получатели результата через запятую или null",
  "workgroup": "Рабочая группа или null"
}
```

В `hz.json` у `create_task` дополнительно описан optional `parent`, но текущий prompt/parser-format и Telegram preview order его не запрашивают. Поэтому, если prompt роли в БД не менялся отдельно, свободный текст не заполняет `parent`.

## Что возвращает parser для заявки

Для заявки на согласование classifier возвращает `workflow_request`, а parser-role `intent_parser_workflow_request` должен вернуть объект:

```json
{
  "intent_type": "create_workflow_request",
  "request_type": "finance",
  "organization": "Организация или null",
  "project": "Проект или null",
  "description": "Текст обоснования или null",
  "amount_requested": "1000 или null",
  "dead_line": "YYYY-MM-DDT18:00 или null",
  "event_date_start": "YYYY-MM-DD или YYYY-MM-DDTHH:MM или null",
  "event_date_end": "YYYY-MM-DD или YYYY-MM-DDTHH:MM или null",
  "money_under_report": "да или null"
}
```

`request_type` - это разновидность заявки, а не отдельная бизнес-сущность:

- `finance` - финансовая заявка, деньги, аванс, оплата, подотчет;
- `trip` - командировка;
- `vacation` - отпуск;
- `other` - прочая заявка.

В локальной базе активный финансовый тип может называться не `finance`, а, например, `finance_x`. Поэтому materializer принимает parser-код `finance`, но выбирает активный тип заявки с кодом `finance` или активный код с префиксом `finance`.

## Сохранение AI-сообщений

После классификации бот создает или находит чат:

```python
AIChatModel(name="Telegram AI Chat", chat_author=profile)
```

Затем сохраняет:

1. пользовательское `AIMessageModel` с исходным текстом;
2. bot `AIMessageModel` с ответом и preview результата.

Если найдено намерение, бот вызывает:

```python
_tg_ai_create_intents_for_bot_message(bot_message, intents, request)
```

Для каждого объекта из JSON-массива:

- `intent_type` вынимается отдельно;
- остальные поля становятся `raw_data`;
- `source_object` указывает на bot-message;
- создание идет через `IntentCreateSerializer`.

## Как raw_data превращается в resolved_data

`IntentCreateSerializer.create()`:

1. создает `IntentModel`;
2. ставит `status_id = "resolving"`;
3. вызывает `build_resolutions(instance, request)`;
4. сохраняет обновленный intent.

`build_resolutions()` строит данные по шагам.

### 1. Кандидаты для ссылочных полей

`find_candidates_for_reference_fields()` смотрит metadata типа намерения:

```json
"fields": {
  "operator": {
    "type": "ForeignKey",
    "model": "users.ProfileModel",
    "data_path": "/search/?model=users.ProfileModel"
  }
}
```

Если у поля есть `model` и AI передал значение, код ищет кандидатов через `find_candidates_for_model()`:

- сначала через модельный `get_filtered_select_queryset(search_name, request)`;
- затем берет `model_class.get_snapshot(instance.pk)`;
- если результат пустой или есть ошибка, есть fallback по БД с токенным поиском.

`data_path` превращается в query params отдельного request для конкретного поля. Например, для проекта в `create_task` используются фильтры:

```text
/search/?model=workgroups.WorkgroupModel&is_project=1&filters={"is_finished":false}
```

Для рабочей группы:

```text
/search/?model=workgroups.WorkgroupModel&is_project=0&filters={"is_finished":false}
```

### 2. Выбор значения

`create_values_for_all_fields()` формирует `values_map`:

- для `ForeignKey` и `ManyToManyField` вызывает `resolve_reference_field_value()`;
- для `DateTimeField` принимает только форматы `YYYY-MM-DD` и `YYYY-MM-DDTHH:MM`;
- для текстовых полей берет строку из `raw_data` или default из metadata.

`reference_matching.py` разбивает ФИО/названия на части, нормализует `е/ё`, чистит пунктуацию и выбирает только однозначного кандидата. Если есть несколько одинаково хороших кандидатов, поле остается нерешенным.

### 3. resolved_data

`fill_resolved_from_values()` превращает выбранные объекты в payload для целевого serializer:

- `ForeignKey` -> один `id`;
- `ManyToManyField` -> список `id`;
- текст/даты -> готовое значение.

После этого в `resolved_data` добавляются `fixed_values` из metadata.

Для `create_task` из `hz.json`:

```json
{
  "task_type": "task"
}
```

### 4. Статусы

`update_field_statuses()` ставит статус каждому полю:

- required + resolved -> `ready`;
- required + empty -> `missing`;
- optional + resolved -> `ready`;
- optional + empty -> `optional`.

`update_intent_status()` ставит всему intent:

- `ready`, если все required-поля готовы;
- иначе `resolving`.

Для задачи required-полем является `name`, поэтому задача может быть готова к выполнению даже без исполнителя, проекта или срока.

## Preview в Telegram

Бот формирует пользователю понятный preview:

- тип намерения: `Создание задачи`, `Создание события`, `Создание онлайн-встречи`, `Создание заявки на согласование`;
- заполненные поля;
- поля, которые не удалось сопоставить в базе;
- пустые поля.

Если есть созданные intent-id, сообщение отправляется с inline-кнопками:

- `Готово` -> callback `tgai_confirm_<bot_message_id>`;
- `Отмена` -> callback `tgai_cancel_<bot_message_id>`.

## Подтверждение и создание задачи

После нажатия `Готово` срабатывает:

```python
@welcome_bot.callback_query_handler(func=lambda call: call.data.startswith(TG_AI_CALLBACK_CONFIRM_PREFIX))
def tg_ai_confirm_handler(call):
```

Проверки:

- профиль найден по `telegram_id`;
- `use_ai_bot` включен;
- bot-message принадлежит этому профилю;
- есть активные intents;
- есть intents со статусом `ready`.

Каждый ready intent исполняется через:

```python
_tg_ai_materialize_intent(intent_obj, request)
```

Для обычных объектов код берет target из metadata:

```json
"target": {
  "model": "tasks.TaskModel",
  "action": "create"
}
```

Затем:

1. получает модель через `apps.get_model("tasks", "TaskModel")`;
2. берет serializer через `model_class.get_serializer_class(action="create")`;
3. передает туда `intent_obj.resolved_data`;
4. выполняет `serializer.is_valid(raise_exception=True)`;
5. сохраняет объект внутри `user_context(request.user)`;
6. записывает созданный объект в `intent_obj.related_object`;
7. переводит intent в `done`.

Для задачи это означает создание `tasks.TaskModel` штатным serializer-ом задачи, а не ручное создание модели в Telegram-коде.

Для `create_workflow_request` есть специальный слой `bpms/chat_ai/utils/workflow_requests.py`, потому что serializer заявки ожидает не только поля модели, но и `route` в `initial_data`.

Этот слой делает следующее:

- определяет `request_type` по parser-коду и активным `WorkflowRequestTypeModel`;
- определяет доступную организацию пользователя по тем же правам, что frontend-select `/contractor_permissions/organizations/` (`request_approvals_manager`, `request_approvals_admin`);
- собирает маршрут из `WorkflowRequestRouteTemplateModel` и `WorkflowPositionUserModel` по предкам организации;
- если на позиции ровно один пользователь, выбирает его автоматически, как frontend;
- если согласующих несколько или нет обязательного согласующего, не угадывает и возвращает ошибку;
- передает полный payload, включая `route`, в `WorkflowRequestCreateSerializer`.

После создания заявка остается в статусе `draft`. Старт согласования по-прежнему делает штатный endpoint заявки (`start`), а не Telegram materializer.

После успешного создания `_tg_ai_build_frontend_object_url()` вернет ссылку:

```text
<FRONTEND_URL>/?task=<task_id>
```

Для заявки ссылка строится так:

```text
<FRONTEND_URL>/?approvals=<workflow_request_id>
```

## Отмена и уточнение

`Отмена`:

- деактивирует intents по bot-message;
- чистит cache-сессию;
- убирает кнопки.

Если intent не готов (`resolving`), `Готово` не создает объект. Бот просит уточнить детали. Следующее сообщение пользователя попадет в `chunks`, старый intent будет деактивирован, а новый intent будет построен по объединенному `session_text`.

## Короткая схема

```text
Telegram text/voice
  -> fallback_handler / fallback_voice_handler
  -> _tg_ai_handle_dialog_input()
  -> cache session chunks
  -> intent_classifier: task/event/meet/report/workflow_request/unknown
  -> intent_parser / intent_parser_report / intent_parser_workflow_request
  -> AIChatModel + AIMessageModel(user/bot)
  -> IntentCreateSerializer
  -> build_resolutions()
  -> IntentModel(raw_data, resolutions, resolved_data, status)
  -> Telegram preview + [Готово] [Отмена]
  -> tg_ai_confirm_handler()
  -> _tg_ai_materialize_intent()
  -> target model serializer или workflow request helper
  -> tasks.TaskModel / event / meeting / report / WorkflowRequestModel
```

## Что важно помнить при доработках

- Runtime-настройки intent types и LLM roles берутся из БД; экспорт `hz.json` полезен как снимок, но не является runtime-источником.
- Новые intent/prompts для заявок должны попадать в БД через миграции, а не ручной правкой админки.
- Telegram-код не должен знать детали создания задачи: он должен отдавать `resolved_data` в serializer целевой модели.
- Для заявок исключение только одно: маршрут согласования собирается отдельным helper-ом, потому что `route` нужен serializer-у в `initial_data`, но не является обычным полем `WorkflowRequestModel`.
- Уточняющие сообщения пересобирают intent из всего сессионного текста, а не обновляют старый intent.
- Для задач сейчас фактически достаточно `name`, потому что остальные поля optional в metadata.
- Ссылочные поля безопасно заполняются только при однозначном сопоставлении кандидата; неоднозначность оставляет поле пустым/нерешенным.
