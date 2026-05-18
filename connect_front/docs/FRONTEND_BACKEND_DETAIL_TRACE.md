# Frontend Backend Detail Trace

Дата прогона: 2026-05-10.

Сценарии прогонялись в видимом Chrome через локальный frontend `http://d.centersoft.kz:8080` под пользователем `pribka@mail.ru`. Лог снимался внутри страницы hook'ом на `fetch` и `XMLHttpRequest`, то есть фиксировались именно запросы, которые делает frontend.

Полный плоский лог лежит локально:

```text
.codex_runtime/frontend_backend_browser_api_20260510_145502.flat.json
```

В прогоне зафиксировано 66 XHR-запросов. Ниже только продуктовые запросы, без фоновых уведомлений, виджетов, чата, календаря и bootstrap-запросов.

## Сценарий: Деталка Задачи

Открытие:

```text
http://d.centersoft.kz:8080/?task=4e3e3fca-36f9-11f1-8285-0242ac110011
```

Ключевая цепочка:

```text
GET 200 /api/v1/tasks/task/4e3e3fca-36f9-11f1-8285-0242ac110011/
GET 200 /api/v1/tasks/task_status/?task_type=task
GET 200 /api/v1/attachments/4e3e3fca-36f9-11f1-8285-0242ac110011/aggregate/
GET 200 /api/v1/tasks/4e3e3fca-36f9-11f1-8285-0242ac110011/action_info/
GET 200 /api/v1/tasks/4e3e3fca-36f9-11f1-8285-0242ac110011/time_tracking/duration/
GET 200 /api/v1/comments/?page=1&page_size=15&reverse=true&model=tasks&related_object=4e3e3fca-36f9-11f1-8285-0242ac110011
GET 200 /api/v1/reactions/?page_size=10
GET 200 /api/v1/vote/4e3e3fca-36f9-11f1-8285-0242ac110011/
```

Что frontend получает как инструкции:

- detail endpoint возвращает объект задачи и UI-метаданные деталки;
- `tabs` задают вкладки и Vue-компоненты: `task:TaskInfo`, `accounting:TaskWorkTime`, `events:TaskEvents`, `files:TaskFiles`, `history:TaskHistory`;
- `aside_settings` задает поля правой сводки: `owner`, `visors`, `organization`, `project`, `operator`, `workgroup`, `showParent`, `showStatus`, `showCreated`, `showDeadline`, `showPriority`, `date_start_plan`;
- `editable` и `can_update_status` управляют доступностью редактирования и смены статуса;
- `action_info` задает доступные действия: `edit`, `update_tags`, `change_cooperator_status`, `copy`, `share`, `add_subtask`, `can_use_timer`, `add_to_work_plan`, `create_accounting`, `edit_accounting`, `delete_accounting`, `change_status`, `update_operator`, `unset_sprint`;
- `task_status` подгружает список статусов по `task_type=task`;
- comments/reactions/vote включаются вкладкой/блоком обсуждения.

Вывод: drawer задачи строится по backend payload. Frontend только мапит `tabs[].component` на локальный компонент из `TaskShowDrawer/TabWidgets` и отображает действия из `action_info`.

## Сценарий: Деталка Проекта, Вкладка Задач

Открытие:

```text
http://d.centersoft.kz:8080/?viewProject=4ef415ce-da79-11ec-b14f-0242ac110007&tab=tasks
```

Ключевая цепочка деталки:

```text
GET 200 /api/v1/work_groups/workgroups/4ef415ce-da79-11ec-b14f-0242ac110007/
GET 200 /api/v1/work_groups/workgroups/4ef415ce-da79-11ec-b14f-0242ac110007/my_role/
GET 200 /api/v1/work_groups/workgroups/4ef415ce-da79-11ec-b14f-0242ac110007/action_info/
GET 200 /api/v1/attachments/4ef415ce-da79-11ec-b14f-0242ac110007/aggregate/
```

Ключевая цепочка вложенного списка задач проекта:

```text
GET 200 /api/v1/app_info/active_filters/?model=tasks.TaskModel&page_name=tasks.project_4ef415ce-da79-11ec-b14f-0242ac110007
GET 200 /api/v1/table_info/?model=tasks.TaskModel&page_name=tasks.project_4ef415ce-da79-11ec-b14f-0242ac110007&table_type=project-tasks
GET 200 /api/v1/tasks/task/my_tasks_count/?page_name=tasks.project_4ef415ce-da79-11ec-b14f-0242ac110007&filters={"project":"4ef415ce-da79-11ec-b14f-0242ac110007"}
GET 200 /api/v1/tasks/task/list/?page_name=tasks.project_4ef415ce-da79-11ec-b14f-0242ac110007&page_size=15&page=1&filters={"project":"4ef415ce-da79-11ec-b14f-0242ac110007","parent":null}&task_type=task,stage,milestone
```

Что frontend получает как инструкции проекта:

- detail endpoint возвращает `tabs`, `metadata`, `with_chat`, `linked_chat`, `linked_chat_id`;
- tabs проекта: `about`, `news`, `tasks`, `gant`, `sprint`, `analytics`, `participants`, `calendar`, `meetings`, `group_files`, `chat_files`;
- у `participants` есть дочерние пункты `employees` и `organizations`;
- `tabs[].onlyDesktop`, `tabs[].onlyMobile`, `tabs[].mainPage`, `tabs[].child` управляют верхним меню и адаптивной видимостью;
- `action_info` в этом прогоне вернул `create_task`, `add_event`, `create_file`, `open_chat`;
- `my_role` вернул роль пользователя в проекте и используется для доступов/состояний внутри drawer.

Что frontend получает как инструкции списка задач проекта:

- `active_filters` возвращает include/exclude фильтры, активные фильтры, теги, search, ordering и `others`;
- `table_info` возвращает пользовательские или дефолтные настройки таблицы: `columns`, `page_size`, `ordering`;
- прямой бизнес-контекст проекта передается не как сохраненный фильтр пользователя, а как query `filters={"project": "...", "parent": null}`;
- `task_type=task,stage,milestone` ограничивает список задачами, этапами и вехами проекта.

В trace есть один сопутствующий `403` на aggregate attachments для связанного объекта, не для самого проекта:

```text
GET 403 /api/v1/attachments/4ef4d9c8-da79-11ec-b14f-0242ac110007/aggregate/
```

Основная деталка проекта и список задач проекта отработали с `200`.

## Стандарт Из Trace

- Каждый visible-прогон сценария должен логировать браузерные XHR/fetch запросы, а не только прямые API-запросы из терминала.
- Detail endpoint отвечает за данные и часть UI-инструкций.
- `action_info` отвечает за действия и доступность команд.
- `active_filters` отвечает за состав и состояние фильтров.
- `table_info` отвечает за пользовательские/дефолтные настройки таблицы.
- `tasks/task/list` и аналогичные list endpoints отвечают за данные, применяя прямой `filters`, сохраненный `FiltersStore`, сортировку, поиск и permissions.
