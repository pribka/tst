# Meeting Sections (MeetingSectionModel) — документация для фронта

## Намерения в собраниях «Моего дня» (new)

> Примечание: в эти эндпойнты передавать **все те же GET-параметры**, что и в списки «Моего дня»
> (например: `start` / `end` — период, а также фильтры по пользователям, проекту и команде).

### 1) Статистика по выявленным намерениям в собраниях «Моего дня»

`GET /api/v1/meetings/sections/my_day_intents_statistics/`

Пример:
```http
GET http://d.centersoft.kz:8080/api/v1/meetings/sections/my_day_intents_statistics/?start=2025-11-26T21:00:00.000Z&end=2025-11-27T20:59:59.999Z
```

Пример ответа:
```json
{
  "sections_count": 3,
  "intents": {
    "total": 8,
    "accepted": 0,
    "deleted": 0,
    "unprocessed": 8
  }
}
```

Где:
- `sections_count` — количество секций (сессий) встреч за выбранный период и фильтры.
- `intents.total` — всего выявленных намерений.
- `intents.accepted` — намерения, которые пользователь принял/создал (или помечены как принятые).
- `intents.deleted` — намерения, которые пользователь удалил/отклонил.
- `intents.unprocessed` — намерения, которые ещё не обработаны.

### 2) Все выявленные намерения в секциях «Моего дня» (с разбивкой по секциям)

`GET /api/v1/meetings/sections/my_day_intents/`

> Ответ **без пагинации**.

Пример:
```http
GET http://d.centersoft.kz:8080/api/v1/meetings/sections/my_day_intents/?start=2025-11-26T21:00:00.000Z&end=2025-11-27T20:59:59.999Z
```

Пример ответа (сокращён до **одного намерения**):
```json
[
  {
    "id": "ae4f34d8-cb8c-11f0-99e4-c90183cb67cd",
    "meeting": {
      "id": "eb20038a-ba0f-11f0-9125-0242ac11000f",
      "name": "МИТ",
      "related_object": null
    },
    "summary": "1. _Обсуждались технические проблемы с учетными записями и организациями..._",
    "transcribe": "совещания спринта 2025-12-11",
    "intents": [
      {
        "id": "b881e663-d988-11f0-8c2f-2f9120dea4b6",
        "is_active": true,
        "created_at": "2025-12-15T10:36:08.306410+03:00",
        "intent_type": {
          "code": "create_task",
          "name": "Задача",
          "btn_title_create": "Создать задачу",
          "btn_title_open": "Открыть задачу",
          "btn_title_delete": "Удалить задачу"
        },
        "status": "ready",
        "related_object": null,
        "resolutions": {
          "name": {
            "value": "Доработка полей с датами",
            "status": "ready",
            "resolved": "Доработка полей с датами",
            "candidates": []
          },
          "description": {
            "value": "Доработать маску для полей с датами и проверить совпадение времени",
            "status": "ready",
            "resolved": "Доработать маску для полей с датами и проверить совпадение времени",
            "candidates": []
          },
          "dead_line": {
            "value": "2025-12-15T18:00:00",
            "status": "ready",
            "resolved": "2025-12-15T18:00:00",
            "candidates": []
          }
        }
      }
    ]
  }
]
```

---

## Цель

Показать пользователю **дополнительную информацию по собраниям** (`PlannedMeetingModel`).

Теперь **одно собрание делится на отдельные сессии** (`MeetingSectionModel`).

- **Сессия** — временной отрезок от начала до завершения (статусы: `online` / `ended`).
- У каждой сессии может быть **несколько видеозаписей** (`MeetingRecordsModel`, поле `section`).
- Из видеозаписей с помощью ИИ извлекается:
  - **транскрибация** (полный текст, поле `transcribe`),
  - **краткое содержание** (поле `summary`),
  - **намерения** (поле `intents`) — задачи/события/собрания, которые хотели создать в процессе обсуждения.

## Общие заметки

- **Base URL**: `http://d.centersoft.kz:8000/api/v1/meetings/`
---

## 1) Список сессий (секций) собрания

**GET** `sections/`  
Пример:

`http://d.centersoft.kz:8000/api/v1/meetings/sections/?meeting=89aef8cc-ceaa-11f0-9d2b-cb0daeaaaa99`

### Query params

- **meeting**: UUID собрания (`PlannedMeetingModel.id`) — *обязателен*.

### Ответ (пример)

```json
[
  {
    "id": "ea6f866a-cea8-11f0-9d2b-cb0daeaaaa99",
    "status": "online",
    "date_start": "2025-12-01T14:28:53.148978+03:00",
    "date_end": null,
    "duration": null,
    "members": [
      {
        "user": {
          "id": "eb5c50bb-cab8-4001-966d-8fa612bbe33e",
          "avatar": {
            "path": "http://d.centersoft.kz:8000/media/avatars/dbc4fd28-0f1d-11ed-ae1b-0242ac110009.jpg"
          },
          "username": "Скрыто",
          "email": "holy.shift.friends@gmail.com",
          "full_name": "Усович Руслан",
          "first_name": "Руслан",
          "last_name": "Усович",
          "job_title": "Должность скрыта",
          "is_support": false,
          "last_activity": "2025-11-05T16:38:16.675311+03:00"
        },
        "duration": null
      }
    ],
    "intents": {
      "total": 6,
      "accepted": 0,
      "deleted": 0,
      "unprocessed": 6
    }
  }
]
```

### Поля

- **status**: `online` / `ended`
- **date_start/date_end**: время начала/окончания секции
- **duration**: длительность секции (может быть `null`; формат строки зависит от DRF DurationField, чаще всего `HH:MM:SS`)
- **members**: список участников секции:
  - **user**: краткая карточка пользователя
  - **duration**: длительность присутствия пользователя на секции (может быть `null`)
- **intents**: агрегированная статистика по намерениям, собранная со всех видеозаписей секции:
  - **total**: всего намерений
  - **accepted**: намерения, по которым уже **создан объект** (`related_object != null`)
  - **deleted**: удалённые намерения (`is_active=false`)
  - **unprocessed**: не обработанные (формула: `total - accepted - deleted`)

---

## 2) Деталка секции

**GET** `sections/<section_id>/`  
Пример:

`http://d.centersoft.kz:8000/api/v1/meetings/sections/c5c21902-cea9-11f0-9d2b-cb0daeaaaa99/`

### Что возвращает

- Метаданные секции (статус/времена/участники)
- **records** — список видеозаписей, привязанных к секции (минимальные поля)
- **transcribe** — объединённая транскрибация секции (склейка всех `records.transcribe` по `created_at`, через `\n`)
- **summary** — объединённое краткое содержание (склейка всех `records.summary` по `created_at`, через `\n`)
- **intents** — список намерений по всем записям секции (как в AI чат-боте)

### Ответ (пример)

```json
{
  "id": "c5c21902-cea9-11f0-9d2b-cb0daeaaaa99",
  "status": "online",
  "date_start": "2025-12-01T14:35:01.172185+03:00",
  "date_end": null,
  "duration": null,
  "members": [],
  "records": [
    {
      "id": "9591e688-ba21-11f0-8eda-0242ac110012",
      "url": "https://vks.gos24.kz/playback/presentation/2.3/58149d360c37d20a500d3018d6228f74d2786a21-1762318842121",
      "created_at": "2025-11-05T11:29:45.454696+03:00",
      "status": "done",
      "transcribe": "Настя+Костя. 10-12-2025"
    }
  ],
  "transcribe": "Настя+Костя. 10-12-2025",
  "summary": "1. Обсуждались способы улучшения извлечения намерений из транскрибаций с помощью моделей LLM.\n\n2. Договорено использовать модель Квен-3 для классификации задач и выявления намерений.\n\n3. Предусмотрено тестирование на более мощной модели Квен-14Б для сравнения результатов.\n\n4. Определены задачи по созданию endpoint для автоматического извлечения намерений из видеозаписей.\n\n5. Планируется разработка системы, которая будет генерировать summary и намерения из транскрибаций.\n\n6. Согласовано разделение данных на ключевые решения и отсеивание ненужной информации для улучшения качества результатов.\n\n7. Задано следующее действие: подготовить и отправить транскрибацию для тестирования на новых моделях.\n\n8. Определено, что для анализа нужно использовать только конкретные решения и договорённости, исключая нюансы и догадки.",
  "intents": [
    {
      "id": "a8effa3d-d987-11f0-8c2f-2f9120dea4b6",
      "is_active": true,
      "created_at": "2025-12-15T10:28:32.680387+03:00",
      "intent_type": {
        "code": "create_task",
        "name": "Задача",
        "btn_title_create": "Создать задачу",
        "btn_title_open": "Открыть задачу",
        "btn_title_delete": "Удалить задачу",
        "success_message": "Задача успешно создана",
        "metadata": {
          "backend_base_url": "/tasks/task/",
          "backend_base_url_full": "https://connect.gos24.kz/api/v1/tasks/task/",
          "get_parameter": "task",
          "target": { "model": "tasks.TaskModel", "action": "create" },
          "fixed_values": { "task_type": "task" },
          "fields": {
            "name": { "type": "CharField", "title": "Наименование", "widget": "InputField", "required": true },
            "description": { "type": "TextField", "title": "Описание", "widget": "TextareaField", "default": "", "required": false },
            "operator": { "type": "ForeignKey", "model": "users.ProfileModel", "title": "Ответственный", "widget": "UserSelect", "data_path": "/search/?model=users.ProfileModel", "required": false },
            "date_start_plan": { "type": "DateTimeField", "title": "Дата начала", "widget": "DateTimeField", "required": false },
            "dead_line": { "type": "DateTimeField", "title": "Дата завершения", "widget": "DateTimeField", "required": false },
            "project": { "type": "ForeignKey", "model": "workgroups.WorkgroupModel", "title": "Проект", "widget": "ProjectSelect", "data_path": "/search/?model=workgroups.WorkgroupModel&is_project=1&filters={\"is_finished\":false}", "required": false },
            "cooperators": { "type": "ManyToManyField", "model": "users.ProfileModel", "title": "Соисполнители", "widget": "UserSelect", "default": [], "data_path": "/search/?model=users.ProfileModel", "required": false },
            "visors": { "type": "ManyToManyField", "model": "users.ProfileModel", "title": "Наблюдатели", "widget": "UserSelect", "default": [], "required": false },
            "workgroup": { "type": "ForeignKey", "model": "workgroups.WorkgroupModel", "title": "Команда", "widget": "GroupSelect", "data_path": "/search/?model=workgroups.WorkgroupModel&is_project=0&filters={\"is_finished\":false}", "required": false }
          }
        }
      },
      "status": "ready",
      "related_object": null,
      "resolutions": {
        "name": { "value": "Извлечение намерений из транскрибации", "status": "ready", "resolved": "Извлечение намерений из транскрибации", "candidates": [] }
      }
    }
  ]
}
```

### Важные нюансы по `intents`

- `intents` собираются по всем записям секции (по `source_object_id in records[]`).
- Если намерение **активное** (`is_active=true`) — возвращается полная структура (как в AI чат-боте).
- Если намерение **удалено** (`is_active=false`) — возвращается укороченный объект:
  - `{ "id": "<uuid>", "is_active": false }`

---

## 3) “Перегенерация” — извлечение данных из транскрибации видеозаписи

> Доступно только от имени администратора (`IsAdminUser`). Может использоваться как кнопки “перегенерации” (если решите добавлять).

### 3.1 Извлечь намерения из транскрибации видеозаписи

**GET** `records/<record_id>/extract_intents/`

`http://d.centersoft.kz:8000/api/v1/meetings/records/560d371a-ba49-11f0-9951-0242ac11000f/extract_intents/`

Ответ: JSON с количеством найденных намерений по этой записи:

```json
{ "result": 6 }
```

### 3.2 Извлечь краткое содержание (summary) из транскрибации видеозаписи

**GET** `records/<record_id>/extract_summary/`

`http://d.centersoft.kz:8000/api/v1/meetings/records/9590b3b2-ba21-11f0-8eda-0242ac110012/extract_summary/`

Ответ: JSON с результатом выполнения (возвращаемое число - количество извлеченных пунктов):

```json
{ "result": 1 }
```

---

## 4) “Технические” — сброс признаков готовности для повторной обработки

> Доступно только администратору (`IsAdminUser`). Нужны, чтобы принудительно “прогнать ещё раз” крон/обработчики.

### 4.1 Сбросить `is_intents_ready=False` для всех записей, где он был True

**GET** `records/reset_intents_ready/`

`http://d.centersoft.kz:8000/api/v1/meetings/records/reset_intents_ready/`

Ответ:

```json
{ "updated": 123 }
```

### 4.2 Сбросить `is_summary_ready=False` для всех записей, где он был True

**GET** `records/reset_summary_ready/`

`http://d.centersoft.kz:8000/api/v1/meetings/records/reset_summary_ready/`

Ответ:

```json
{ "updated": 45 }
```

---

## 5) “Технические” — отладка: что не обработалось

> Доступно только администратору (`IsAdminUser`). Полезно, если прилетает много запросов в LLM и нужно понять, что зависло.

### 5.1 Список id необработанных видеозаписей по части извлечения summary

**GET** `records/pending_summary/`

`http://d.centersoft.kz:8000/api/v1/meetings/records/pending_summary/`

Ответ: массив UUID записей.

```json
[
  "9590b3b2-ba21-11f0-8eda-0242ac110012",
  "560d371a-ba49-11f0-9951-0242ac11000f"
]
```

### 5.2 Список id необработанных видеозаписей по части извлечения intents

**GET** `records/pending_intents/`

`http://d.centersoft.kz:8000/api/v1/meetings/records/pending_intents/`

Ответ: массив UUID записей.

```json
[
  "560d371a-ba49-11f0-9951-0242ac11000f"
]
```


