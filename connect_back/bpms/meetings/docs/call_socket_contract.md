# Контракт Socket-событий по звонкам Help Desk (MVP)

Документ фиксирует текущий backend-контракт realtime-событий и логику дозвона для звонков в Help Desk.

## 1) Область действия

- Транспорт: существующий формат через событие `notify`.
- Канал доставки: Redis Pub/Sub `SOCKETIO_SYSTEM_CHANNEL`.
- События звонков:
  - `call_created`
  - `call_updated`
- Таргетинг: только список профилей (`recipients`), без комнат тикета.

## 2) Транспортный envelope

Все события звонков публикуются в формате:

```json
{
  "event": "notify",
  "data": {
    "message": {
      "event_type": "call_created|call_updated",
      "...": "payload звонка"
    },
    "recipients": ["<profile_uuid>", "<profile_uuid>"]
  }
}
```

## 3) Payload события (`data.message`)

- `event_type`: `call_created` или `call_updated`
- `call`: сериализованный звонок (`CallNotifySerializer`)
- `old_status`: предыдущий статус или `null`
- `new_status`: текущий статус звонка

## 4) Ключевая бизнес-логика очереди

Backend — единственный источник истины (frontend не принимает решения по локальному таймеру).

### 4.1 Режимы выбора целевого участника

Есть два режима:

1. **Стандартный (клиент звонит в поддержку)**
   - целевая очередь формируется из специалистов карточки клиента:
     - `is_active=True`
     - `accepts_calls=True`
     - сортировка: `is_reserve`, `call_priority`, `id`
   - звонок идет по очереди специалистов.

2. **Перезвон специалиста клиенту из существующего тикета**
   - если инициатор — специалист по тикету (либо текущий `ticket.specialist`, либо входит в `actual_specialists`) и у тикета есть `contact_person.user`,
   - целевой участник один: `contact_person.user`.
   - переключения на очередь специалистов в этом режиме нет.

### 4.2 Таймаут дозвона

- Текущее окно дозвона на одного target: `10 секунд` по умолчанию.
  - Если на старте звонка очередь состоит из ровно `1` target — `30 секунд`.
- По таймауту backend:
  - переводит дозвон на следующего участника очереди (если есть),
  - либо завершает звонок.

### 4.3 Финальные статусы при окончании дозвона

- `missed` — никто не ответил по таймауту.
- `cancelled_by_receiver` — текущий target явно нажал отклонение, и больше target в очереди нет.
- `cancelled_by_caller` — инициатор отменил звонок.
- `ended` — разговор был начат (`in_call`) и затем завершен.

## 5) Правила `accept/reject/cancel`

- `accept` / `reject` доступны только текущему `current_target_id`.
- `accept` / `reject` может выполнить:
  - специалист поддержки,
  - либо контактное лицо клиента (в сценарии перезвона специалиста клиенту).
- `cancel` доступен только инициатору звонка (`initiator_id`).

## 6) Правила доставки получателей (`recipients`)

### 6.1 `call_created`

В получатели попадают:

- инициатор звонка,
- текущий target (`current_target_id`),
- контактное лицо тикета (если есть `contact_person.user`).

### 6.2 `call_updated` (обычно)

Если recipients явно не переданы, берутся:

- инициатор,
- принявший (`accepted_by`), если есть,
- ответственный по тикету (`ticket.specialist`), если есть,
- контактное лицо тикета, если есть,
- все актуальные специалисты карточки клиента, принимающие звонки.

### 6.3 `call_updated` при переключении очереди

При переходе на следующего target backend явно добавляет:

- предыдущего target,
- нового target,

чтобы фронт гарантированно закрыл/открыл входящий экран нужным участникам.

## 7) Синхронизация завершения звонка и BBB

Синхронизация двусторонняя:

1. **Завершение из нашего UI звонка** (`/help_desk/calls/{id}/end`):
   - звонок переводится в `ended`,
   - backend отправляет команду `end` в BBB,
   - локальная встреча переводится в завершенную.

2. **Завершение из BBB UI / callback BBB** (`/api/v1/meetings/set_complete/`):
   - встреча переводится в завершенную,
   - backend синхронизирует связанный активный helpdesk-звонок в `ended`,
   - публикует `call_updated` и `ticket_update`.

## 8) Правила frontend (MVP)

- Показывать экран входящего звонка, если:
  - `status` в `connecting`/`ringing`,
  - и `current_target_id == my_profile_id`.
- Скрывать экран входящего, если:
  - `current_target_id != my_profile_id`,
  - или статус стал финальным (`cancelled_by_receiver`, `cancelled_by_caller`, `ended`, `missed`),
  - или статус стал `in_call`, но `accepted_by_id != my_profile_id`.
- Для инициатора/второй стороны:
  - `ringing`/`connecting` — экран ожидания,
  - `in_call` — активный звонок,
  - финальные статусы — закрытие звонка + отображение результата.

## 9) Пример: создание звонка (первый target)

```json
{
  "event": "notify",
  "data": {
    "message": {
      "event_type": "call_created",
      "call": "<объект CallNotifySerializer>",
      "old_status": null,
      "new_status": "ringing"
    },
    "recipients": [
      "b37bb58a-1f95-4d7b-a0a3-a9fda0b2a98f",
      "005fac92-8de9-42fd-8efb-6c39f0788765"
    ]
  }
}
```

## 10) Пример: переключение на следующего target

```json
{
  "event": "notify",
  "data": {
    "message": {
      "event_type": "call_updated",
      "call": "<объект CallNotifySerializer>",
      "old_status": "ringing",
      "new_status": "ringing"
    },
    "recipients": [
      "005fac92-8de9-42fd-8efb-6c39f0788765",
      "7fd87f6f-7af2-4955-a39b-0739ce85dff3"
    ]
  }
}
```

## 11) Пример: звонок принят

```json
{
  "event": "notify",
  "data": {
    "message": {
      "event_type": "call_updated",
      "call": "<объект CallNotifySerializer>",
      "old_status": "ringing",
      "new_status": "in_call"
    },
    "recipients": [
      "b37bb58a-1f95-4d7b-a0a3-a9fda0b2a98f",
      "7fd87f6f-7af2-4955-a39b-0739ce85dff3"
    ]
  }
}
```

## 12) Примечания

- Параллельно с новыми call-событиями сохраняется `ticket_update` (обратная совместимость).
- При реконнекте клиент должен делать re-sync через REST (детали тикета/звонка).
- Контракт зафиксирован для MVP и может расширяться в следующих версиях.

## 13) Push-контракт для мобильных клиентов

Параллельно с socket-событиями backend отправляет data-only push через FCM.

### 13.1 Типы push-событий

- `type=call_invite`, `source=call_start` — старт входящего звонка.
- `type=call_update`, `source=call_updated` — изменение статуса/target звонка.

### 13.2 Базовые поля payload

- `notification_id` — id WebNotificationModel.
- `call_id` — id звонка.
- `call_status` — код статуса (`ringing`, `in_call`, `ended`, ...).
- `meeting_id` — id связанной встречи.
- `open_url` — ссылка для входа в звонок (`meeting.url_external`).
- `initiator_id` — id инициатора звонка.
- `current_target_id` — id текущего target звонка.
- `accepted_by_id` — id пользователя, принявшего звонок (если есть).
- `title`, `body`, `sent_at`.

### 13.3 Правило обработки на клиенте

Push может приходить с одним и тем же `call_status` для разных получателей (например `ringing` при переключении очереди).
Клиент должен ориентироваться не только на статус, но и на `current_target_id`:

- если `call_status` в `connecting/ringing` и `current_target_id == my_profile_id` — показывать/держать экран входящего;
- если `current_target_id != my_profile_id` — скрывать входящий экран/останавливать рингтон;
- для `in_call` учитывать `accepted_by_id`;
- для финальных статусов (`missed`, `cancelled_by_receiver`, `cancelled_by_caller`, `ended`) — завершать UI звонка.

### 13.4 Важное отличие от socket-контракта

- Socket-события `call_created/call_updated` — realtime канал состояния.
- Push-события — вспомогательный канал для background/locked-state устройства.
- После получения push клиенту рекомендуется делать re-sync через REST/socket при расхождении состояния.

## 14) Структура поля `call` (развернуто, один раз)

Ниже пример того, что backend кладет в `message.call` (объект `CallNotifySerializer`):

```json
{
  "id": "3cbf3d7a-8f53-45d3-b264-5f4eb8d9c95c",
  "status": {
    "id": "ringing",
    "name": "Дозвон",
    "code": "ringing"
  },
  "chat_uid": "chat_abc_123",
  "initiator": {
    "id": "b37bb58a-1f95-4d7b-a0a3-a9fda0b2a98f",
    "name": "Иванов Иван"
  },
  "accepted_by": null,
  "current_target": {
    "id": "005fac92-8de9-42fd-8efb-6c39f0788765",
    "name": "Петров Петр"
  },
  "ring_attempt": 1,
  "ring_started_at": "2026-03-18T12:01:10Z",
  "started_at": "2026-03-18T12:01:10Z",
  "answered_at": null,
  "ended_at": null,
  "meeting": {
    "id": "d816cc88-e5be-4a24-a014-42cde93f3502",
    "url_external": "https://.../connect_external/...",
    "url": "https://.../connect/...",
    "status": "online"
  },
  "created_at": "2026-03-18T12:01:10Z"
}
```

Примечание:
- `initiator`, `accepted_by`, `current_target` сериализуются `CachedAppUserPreviewSerializer` (финальный набор полей берется из этого сериализатора).
- `meeting` формируется через `meeting.get_connect_info()`.
