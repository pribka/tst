# Product Development Standard

Дата фиксации: 2026-05-10.

Документ фиксирует стандарт построения продуктовых разделов на примере задач и проектов: из каких частей состоят списки, деталки, вложенные списки и как фронт должен договариваться с бэком.

## Базовый принцип

Продуктовый экран не должен быть изолированной ручной реализацией. Нормальный путь: backend отдает маршруты, таблицы, фильтры, вкладки и доступные действия; frontend собирает из этого единый UI-каркас и добавляет только поведение конкретного продукта.

Ключевые понятия:

- `model` - backend model label, например `tasks.TaskModel` или `workgroups.WorkgroupModel`.
- `page_name` - уникальный ключ состояния страницы: фильтры, сортировки, настройки таблицы и reload-события.
- `tableType` - вариант таблицы внутри одной модели: `tasks`, `interests`, `projects`, `project-tasks`.
- `endpoint` - фактическая точка данных списка.
- `params.filters` - жесткий контекст страницы, например `project=<id>` во вкладке задач проекта.

## Стандарт Списка

Любой продуктовый список состоит из пяти слоев.

1. **Route/PageWidget**

   Backend routes из `/api/v1/app_info/routes/` выбирают `pageWidget`, а frontend загружает компонент из `src/views/Dashboard/PageWidgets`.

   PageWidget обязан определить:

   - `model`
   - `page_name`
   - `tableType`
   - продуктовый тип, если он влияет на endpoint или фильтры
   - верхний `PageFilter`, если фильтр находится на уровне страницы

2. **Module Shell**

   Модульный экран собирается через `ModuleWrapper`: слоты заголовка, левая/правая панель действий, кнопки создания, справка, настройки и тело списка.

   Для новых разделов это стандартный каркас. Исключение допустимо только для сильно специализированного рабочего места, но фильтры и backend-контракт должны оставаться теми же.

3. **Filter Layer**

   `PageFilter` всегда получает минимум:

   ```vue
   <PageFilter
       :model="model"
       :page_name="page_name" />
   ```

   Фронт получает конфигурацию фильтров через:

   ```text
   GET /api/v1/app_info/active_filters/?model=<model>&page_name=<page_name>
   ```

   Сохранение фильтра идет через:

   ```text
   POST /api/v1/app_info/chosen_filters/
   ```

   После сохранения фильтра frontend обязан перезагрузить список через стандартные события:

   ```text
   update_filter_<model>
   update_filter_<page_name>
   update_filter_<model>_<page_name>
   ```

4. **List Body**

   Основной стандарт для desktop - `UniversalTable`.

   Минимальный контракт:

   ```vue
   <UniversalTable
       :model="model"
       :pageName="page_name"
       :tableType="tableType"
       :endpoint="endpoint"
       :params="params"
       :openHandler="openHandler" />
   ```

   `UniversalTable` сам:

   - запрашивает структуру колонок через `table/getTableInfo`;
   - грузит данные из `endpoint`;
   - передает `page_name`, `page`, `page_size`, `ordering` и `params`;
   - слушает reload-события фильтров;
   - умеет точечно обновлять строки через `table_row_<page_name>`.

   Mobile-списки могут быть кастомными infinite list, но обязаны использовать тот же `model`, `page_name`, endpoint и фильтры.

5. **Backend List Contract**

   Backend отвечает за структуру, доступы и queryset.

   Модель должна определить:

   - `get_table_columns()`
   - `get_additional_table_columns()`, если часть колонок нужна как фильтры/доп. поля
   - `get_filter_fields(request=...)`, если состав фильтров зависит от `page_name`
   - `search_input()`
   - `get_data_path()`
   - `get_serializer_class(action=...)`
   - `get_queryset(request)`

   ViewSet или list-view должен:

   - принимать `page_name`, `page`, `page_size`, `ordering`, `filters`;
   - применять прямой `filters` из query params;
   - применять сохраненный `FiltersStore` по `author + model + page_name`;
   - применять search и ordering;
   - применять permissions на backend, а не только скрывать строки на frontend.

## Backend-Driven Инструкции Списка

Список строится по инструкциям backend, а не только по локальному Vue-коду.

`UniversalTable` через `table/getTableInfo` запрашивает пользовательские/дефолтные настройки таблицы:

```text
GET /api/v1/table_info/?model=<model>&page_name=<page_name>&table_type=<tableType>
```

Этот endpoint обслуживает `common.views.TableInfoView`. Backend берет настройки из cache или `FiltersStore.filters.table_settings`, а если их нет - из `common.table_settings.DEFAULT_TABLE_SETTINGS[tableType]`.

Фактический payload для `UniversalTable`:

- `columns` - порядок колонок, поля, renderers, slots, ширины, сортировки, fixed/visible/hidable;
- `page_size` - размер страницы;
- `ordering` - сортировка таблицы.

Отдельно существует `GET /api/v1/app_info/table_info/?model=<model>`, который возвращает `model.get_table_structure()` с `table_columns`, `data_path`, `context_menu`, `pageConfig` и базовой metadata модели. Его не надо путать с рабочим `/api/v1/table_info/`, который был зафиксирован в браузерном trace для `UniversalTable`.

`PageFilter` отдельно запрашивает фильтры:

```text
GET /api/v1/app_info/active_filters/?model=<model>&page_name=<page_name>
```

Backend возвращает не просто список полей, а состояние фильтра:

- доступные include/exclude фильтры;
- сохраненные значения из `FiltersStore`;
- активные теги фильтра;
- search value;
- ordering;
- `others` для дополнительных виджетов.

Итог: frontend обязан отображать колонки, фильтры и настройки таблицы из backend payload. Хардкод на frontend допустим только для layout-обвязки и редких специальных виджетов строк.

## Примеры Списков

**Задачи**

Frontend-цепочка:

```text
src/views/Dashboard/PageWidgets/PageTask.vue
src/modules/vue2TaskComponent/views/Table/Page.vue
src/modules/vue2TaskComponent/components/TaskList/TaskTablePage.vue
src/components/TableWidgets/UniversalTable.vue
```

Ключи:

```text
model: tasks.TaskModel
page_name: page_list_<task_type>_task.TaskModel
tableType: tasks | interests | logistic
endpoint: /tasks/task/list/?task_type=<task_type>
```

Backend:

```text
bpms/tasks/apiviews.py -> ListTaskView
bpms/tasks/utils.py -> get_task_queryset()
bpms/tasks/models.py -> TaskModel.get_table_columns(), get_filter_fields()
```

Особенность задач: сначала применяется общий `get_filter_queryset()`, затем task-specific фильтры (`task_type`, `parent`, `project`, `status`, сроки, роли), затем permissions.

**Проекты**

Frontend-цепочка:

```text
src/views/Dashboard/PageWidgets/projects.vue
src/modules/Projects/init.vue
src/modules/Projects/index.vue
src/modules/Projects/components/ListInit.vue
src/modules/Projects/components/TestTable.vue
src/components/TableWidgets/UniversalTable.vue
```

Ключи:

```text
model: workgroups.WorkgroupModel
page_name: page_list_projects.WorkgroupModel
tableType: projects
endpoint: /work_groups/workgroups/?is_project=1
openHandler: query.viewProject = <id>
```

Backend:

```text
bpms/workgroups/viewsets.py -> WorkGroupViewSet.list()
bpms/workgroups/utils.py -> get_workgroup_queryset()
bpms/workgroups/models.py -> WorkgroupModel.get_table_columns(), get_filter_fields()
```

Особенность проектов: `WorkgroupModel.get_filter_fields()` меняет состав фильтров по `page_name`; для `page_list_project...` скрывается `public_or_private`, для `page_list_workgroup...` скрываются дедлайн и завершенность.

**Сделки и контракты**

Frontend-цепочка:

```text
src/modules/Deals/index.vue
src/modules/Deals/init.vue
src/modules/Deals/components/DealStageStrip.vue
src/modules/Deals/components/DealDrawerDriver.vue
src/components/TableWidgets/UniversalTable.vue
```

Ключи:

```text
model: crm.DealModel
page_name: page_list_deals_crm.DealModel
tableType: deals
endpoint: /crm/deals/deals/
openHandler: query.deal = <id>
```

Backend:

```text
crm/deals_views.py -> DealViewSet
crm/deals_models.py -> DealModel.get_queryset()
common/table_settings.py -> DEFAULT_TABLE_SETTINGS["deals"]
```

Особенность сделок: стадийная полоса списка строится по backend payload `form_info` и `stage_summary`, а drawer строит агрегатный маршрут по `flow_steps` из detail сделки. Стадия сделки не должна быть декоративным ручным полем: она выводится из фактов `source_ticket`, `customer_card`, `customer_contract`, работ и оплат. Режим контрактов остается рядом как совместимый view той же страницы, но не заменяет `DealModel`.

MVP-правило 2026-05-11: кнопка создания в режиме сделок ведет пользователя в создание обращения-лида в HelpDesk. Сделка появляется автоматически после сохранения `HelpDeskTicketModel(ticket_type_id='lead')`; отдельную форму "создать сделку" для лида использовать нельзя, иначе теряется источник и ломается CRM-агрегат.

## Стандарт Деталки

Деталка продукта открывается не локальным состоянием компонента, а query-параметром. Это дает прямую ссылку, восстановление состояния после reload и единый UX.

Стандартные query-параметры:

```text
?task=<id>          - деталка задачи
?viewProject=<id>   - деталка проекта/группы
?stab=<code>        - активная вкладка задачи
?tab=<code>         - активная вкладка проекта
```

Деталка состоит из шести слоев.

1. **Lazy Entry**

   Корневой `init.vue` модуля следит за query и лениво подключает drawer. Пример: `vue2TaskComponent/init.vue` подключает `TaskShowDrawer`, `Projects/init.vue` подключает `Projects/MainPage`.

2. **Drawer Shell**

   Стандартный контейнер - `DrawerTemplate`.

   Обязательные зоны:

   - `title` - имя объекта, номер/аватар, быстрые действия;
   - `aside` - сводка, участники, метаданные, состояние;
   - `tabs` - навигация по разделам деталки;
   - body - активная вкладка;
   - `footer` - основные действия, если они нужны постоянно.

3. **Detail Fetch**

   Данные деталки грузятся отдельным endpoint:

   ```text
   GET /api/v1/tasks/task/<id>/
   GET /api/v1/work_groups/workgroups/<id>/
   ```

   Если права/роли/действия не входят в основной serializer, они грузятся отдельными action endpoints:

   ```text
   GET /api/v1/tasks/<id>/action_info/
   GET /api/v1/work_groups/workgroups/<id>/action_info/
   GET /api/v1/work_groups/workgroups/<id>/my_role/
   ```

4. **Tabs Contract**

   Backend возвращает список вкладок. Frontend не должен сам решать, какие вкладки существуют для объекта.

   Минимальная структура вкладки:

   ```json
   {
     "code": "about",
     "name": "Подробнее",
     "component": "TaskAbout",
     "showAside": true
   }
   ```

   Для задач компонент вкладки подгружается динамически через `TaskShowDrawer/TabWidgets/TabSwitch.vue` из поля `tab.component`.

   Для проектов backend возвращает `tabs`, а `Projects/MainPage/index.vue` мапит `tab.name` на frontend-компонент в `pageWidget()`.

5. **Actions Contract**

   Действия должны приходить с backend. Frontend только отображает доступное.

   Примеры действий:

   - edit
   - delete
   - create_task
   - add_member
   - create_chat
   - project_finish

   Нельзя считать скрытую кнопку проверкой безопасности. Backend permission остается обязательным.

6. **Nested Lists**

   Вложенные списки внутри деталки - это полноценные списки со своим `page_name`.

   Пример задач проекта:

   ```text
   page_name: tasks.project_<project_id>
   model: tasks.TaskModel
   endpoint: /tasks/task/list/
   params.filters: { project: <project_id>, parent: null }
   tableType: project-tasks
   ```

   Жесткий контекст (`project`, `parent`, `workgroup`) передается через `params.filters`, а пользовательские фильтры сохраняются отдельно в `FiltersStore` по `page_name`.

## Runtime Flow Деталки

Реальный прогон локального frontend/backend под пользователем `pribka@mail.ru` показал такой flow.

Открытие задачи:

```text
row click
  -> router query task=<task_id>
  -> TaskShowDrawer.openTaskDrawer()
  -> GET /api/v1/tasks/task/<task_id>/
  -> GET /api/v1/attachments/<task_id>/aggregate/
  -> action components request GET /api/v1/tasks/<task_id>/action_info/
```

Основной detail payload задачи уже содержит UI-инструкции:

- `tabs` - какие вкладки показать;
- `tabs[].code` - ключ вкладки и query `stab`;
- `tabs[].component` - Vue-компонент из `TaskShowDrawer/TabWidgets`;
- `tabs[].showAside` - показывать ли aside для вкладки;
- `tabs[].disabledWrapper` - отключить стандартную body-обертку;
- `tabs[].counter` - вкладка поддерживает счетчик;
- `aside_settings` - какие поля и ссылки показывать в правой сводке;
- `statWidgets` - статистические виджеты шапки/aside;
- `show_step` - нужен ли верхний статусный stepper;
- `editable`, `can_update_status` - runtime-доступы для UI;
- `metadata`, `logistic_tabs`, `route_points` - дополнительные инструкции для вариантов задачи.

`action_info` задачи возвращает отдельный слой инструкций:

```text
actions.edit.availability
actions.copy.availability
actions.share.availability
actions.add_subtask.availability
actions.change_status.available_statuses
actions.change_cooperator_status.available_statuses
actions.can_use_timer.availability
actions.create_accounting.availability
actions.update_operator.availability
```

То есть footer/dropdown/status controls не должны сами решать доступность действий и набор статусов.

Открытие проекта:

```text
row click
  -> router query viewProject=<project_id>
  -> Projects/MainPage.startView()
  -> GET /api/v1/work_groups/workgroups/<project_id>/
  -> GET /api/v1/work_groups/workgroups/<project_id>/my_role/
  -> GET /api/v1/work_groups/workgroups/<project_id>/action_info/
  -> tab-specific requests after active tab render
```

Detail payload проекта содержит UI-инструкции:

- `tabs` - верхнее меню деталки;
- `tabs[].name` - ключ вкладки и query `tab`;
- `tabs[].menuName` - i18n-ключ подписи;
- `tabs[].title` - backend title вкладки;
- `tabs[].icon` - иконка меню;
- `tabs[].onlyDesktop` / `tabs[].onlyMobile` - адаптивная видимость;
- `tabs[].mainPage` - какую внутреннюю страницу открыть для групповой вкладки;
- `tabs[].child` - дочерние пункты меню, например participants -> employees/organizations;
- `with_chat`, `linked_chat`, `linked_chat_id` - включение вкладки/действия чата;
- `metadata` - дополнительные настройки деталки, например участники.

`action_info` проекта возвращает доступные действия:

```text
actions.create_task.availability
actions.add_event.availability
actions.create_file.availability
actions.open_chat.availability
actions.edit.availability
actions.delete.availability
actions.project_finish.availability
```

Набор зависит от роли пользователя и состояния проекта. В конкретном локальном прогоне для открытого проекта пришли `create_task`, `add_event`, `create_file`, `open_chat`.

## Примеры Деталок

**Деталка задачи**

Frontend:

```text
src/modules/vue2TaskComponent/init.vue
src/modules/vue2TaskComponent/components/TaskShowDrawer/index.vue
src/modules/vue2TaskComponent/components/TaskShowDrawer/TabWidgets/TabSwitch.vue
src/modules/vue2TaskComponent/store/actions.js -> getFullTask()
```

API:

```text
GET /tasks/task/<id>/
GET /tasks/<id>/action_info/
GET /attachments/<id>/aggregate/
```

Backend:

```text
TaskModelViewSet.retrieve()
DetailTaskSerializer
AppInfo code: tasks_<task_type>_detail_info
```

`DetailTaskSerializer` добавляет runtime-данные: viewers, delivery points, cooperators, key results, `tabs`, `logistic_tabs`, `in_favorites`. Поэтому вкладки и часть поведения деталки являются backend-driven.

**Деталка проекта**

Frontend:

```text
src/modules/Projects/init.vue
src/modules/Projects/MainPage/index.vue
src/modules/Projects/MainPage/PagesSwitch/*
```

API:

```text
GET /work_groups/workgroups/<id>/
GET /work_groups/workgroups/<id>/my_role/
GET /work_groups/workgroups/<id>/action_info/
```

Backend:

```text
WorkGroupViewSet.retrieve()
WorkGroupViewSet.get_action_info()
WorkgroupDetailSerializer
AppInfo code: project_tabs | workgroup_tabs
```

Проектная деталка использует backend tabs, роли и actions. Вкладка задач проекта является эталонным примером вложенного списка: она имеет свой `PageFilter`, view switch table/kanban, `StatusFilters` и `UniversalTable` с прямым `filters.project`.

**Деталка сделки**

Frontend:

```text
src/modules/Deals/components/DealDrawerDriver.vue
src/modules/Deals/components/DealDrawer.vue
src/modules/Deals/AddDrawer/index.vue
```

API:

```text
GET /crm/deals/deals/form_info/
GET /crm/deals/deals/<id>/
GET /crm/deals/deals/<id>/action_info/
POST /crm/deals/deals/
PUT /crm/deals/deals/<id>/
POST /crm/deals/deals/<id>/transition_stage/
```

Backend:

```text
DealDetailSerializer
DealCreateUpdateSerializer
DealViewSet.form_info()
DealViewSet.action_info()
DealViewSet.transition_stage()
```

Сделка использует тот же стандарт деталки: query `?deal=<id>`, drawer, backend-driven actions и отдельный payload для формы. Создание контракта из сделки открывает контрактный drawer с предзаполненными данными и сохраняет связь `CustomerContractModel.deal`.

## Правила page_name

`page_name` - не просто название страницы, а ключ состояния пользователя. Ошибка в `page_name` приводит к протеканию фильтров между экранами.

Правила:

- Для общего списка: `page_list_<domain>.<ModelLabel>`.
- Для вариантов одной модели добавлять тип: `page_list_<task_type>_task.TaskModel`.
- Для вложенных списков добавлять контекст: `tasks.project_<project_id>`.
- Не использовать один `page_name` для разных бизнес-контекстов.
- Если вкладки одного объекта имеют разные фильтры, у каждой вкладки должен быть свой `page_name`.
- Если меняется только визуальный режим, но бизнес-контекст тот же, `page_name` можно оставить общим.

## Где Должна Жить Логика

Backend:

- состав колонок;
- состав фильтров;
- permissions;
- доступные actions;
- список вкладок деталки;
- бизнес-фильтрация queryset;
- serializer для list/detail.

Frontend:

- layout;
- переключение table/kanban/mobile;
- открытие деталки через query;
- отображение backend-driven колонок, фильтров, tabs и actions;
- локальные UX-события reload/update;
- продуктовые формы создания/редактирования.

Жесткое правило: frontend не должен дублировать бизнес-доступы и состав данных, если это можно выразить на backend через модель, serializer, AppInfo или action_info.

## Что Считать Legacy

Есть старые реализации, которые можно поддерживать, но не копировать в новые разделы:

- отдельные `table_info` endpoints внутри продуктовых viewset, если ту же структуру можно отдать через `app_info/table_info`;
- ручные таблицы с колонками, зашитыми на frontend, если нет реальной причины уходить от `UniversalTable`;
- списки, которые не слушают стандартные `update_filter_*` события;
- деталки, открываемые только локальным состоянием без query-параметра;
- вкладки деталки, полностью зашитые на frontend без backend metadata.

## Чеклист Нового Продуктового Раздела

Frontend:

- PageWidget добавлен и связан с backend route.
- Есть `init.vue`, если модуль регистрирует store или lazy drawers.
- Главный экран использует `ModuleWrapper`.
- `PageFilter` получает корректные `model` и `page_name`.
- Desktop список использует `UniversalTable`.
- Mobile список сохраняет тот же API/filter contract.
- `openHandler` открывает деталку через query.
- Деталка собрана через `DrawerTemplate`.
- Вложенные списки имеют собственный `page_name`.

Backend:

- Модель определяет table/filter/search/data path contract.
- List endpoint применяет `get_filter_queryset()`.
- Direct `filters` используются для контекста страницы.
- Permissions применяются в queryset/detail/action endpoints.
- Detail serializer возвращает данные для header/aside/body.
- Tabs приходят из serializer или `AppInfo`.
- Actions приходят из `action_info`.

## Связанные Документы

- `docs/LOCAL_BACKEND_FRONTEND_INTERACTION.md` - локальная связка frontend/backend, auth, proxy, базовый request flow и общий паттерн фильтрации задач.
- `docs/FRONTEND_BACKEND_DETAIL_TRACE.md` - фактический браузерный trace открытия деталок задачи и проекта.
- `docs/CRM_CUSTOMER_CONTRACT_FLOW.md` - продуктовый стандарт CRM-цикла: лид, паспорт клиента, сделка, контракт, работы, оплаты и сводка.
- `docs/ARCHITECTURE.md` - server-driven routing и bootstrap приложения.
- `docs/STRUCTURE.md` - структура frontend-модулей.
- `docs/INTEGRATIONS.md` - REST, cookies, Socket.IO и внешние интеграции.
