# CRM Customer Flow: лид, паспорт клиента, контракт, работы и оплаты

Дата фиксации: 2026-05-10.
Обновление MVP: 2026-05-11.
Методика актуализирована: 2026-05-12.

> Статус на 2026-05-13: документ оставлен как историческая фиксация старой попытки вокруг `crm.DealModel`. Для новой CRM-декомпозиции источник истины - `CRM_TZ/`.
>
> Актуальная модель CRM MVP: "Интерес" = `bpms.tasks.TaskModel` с `task_type_id='interest'`; `crm.DealModel` считается неудачным прототипом и не используется как опорная сущность. Карточка интереса должна идти через `TaskShowDrawer`. CRM-клиент/паспорт клиента = `help_desk.CustomerCardModel`; внешний клиент/контрагент из 1С = `catalogs.ExternalCustomerModel`, связанный через `CustomerCardModel.external_customer` и `CustomerContractModel.external_customer`. `catalogs.ContractorModel` в новой трактовке - дерево наших организаций/подразделений, где ведется учет и доступы; в CRM его нельзя использовать как клиента. `PotentialContractorModel` - временный черновик лида до создания/привязки `CustomerCardModel`. Заказ идет через существующий Orders-контур, но ему нужен bridge к `CustomerCardModel`, `ExternalCustomerModel` и исходному интересу. Контракт заключается с внешним клиентом/клиентской карточкой/заказом, а не с интересом.

## Стратегия CustomerCardModel, ExternalCustomerModel и ContractorModel для новой CRM

В CRM MVP нельзя вести две параллельные клиентские реальности. Единая пользовательская сущность "клиент" в разделе "Продажи" должна быть `CustomerCardModel`, потому что она уже связывает HelpDesk, задачи, контакты, клиентский паспорт и обслуживаемые карточки.

`ExternalCustomerModel` - внешний клиент из 1С. Это ближайший кандидат на юридическую/учетную клиентскую сущность, потому что он уже используется в `CustomerContractModel.external_customer`, `CustomerCardModel.external_customer`, поиске несвязанных внешних клиентов и bind-flow `external_customer/bind`.

`ContractorModel` не должен быть клиентом CRM. В текущей системе он фактически описывает наши организации, подразделения, контур учета, права пользователей, номенклатуру и источник 1С-доступа. Поэтому `GoodsOrderModel.contractor` надо читать как учетную организацию заказа, а не как покупателя. Старые verbose_name и старые interest-поля могут называть его "клиентом/контрагентом", но новую CRM-логику на этом строить нельзя.

Для договоров целевая связка - `CustomerContractModel.external_customer` плюс обслуживаемые карточки через `CustomerContractServicedCardModel`. Одиночное поле `CustomerContractModel.customer_card` уже помечено в модели как "не использовать", поэтому новую CRM-логику на нем не строим.

Целевой поток:

```text
HelpDesk lead / ручной ввод / внешний источник
    -> interest TaskModel(task_type='interest', customer_card=<CRM-клиент>)
    -> потребности клиента на интересе
    -> если нужен учет/1С: CustomerCardModel.external_customer или привязка к ExternalCustomerModel
    -> GoodsOrderModel(contractor=<наша учетная организация>, customer_card=<CRM-клиент>, external_customer=<внешний клиент>, source_interest=<interest>)
```

На переходный период `TaskModel.contractor`, `TaskModel.potential_contractor` и `CustomerCardModel.customer` сохраняются для совместимости, старых данных и текущих serializer-flow, но новый CRM UI должен читать и писать `TaskModel.customer_card` как основное поле клиента, а связь с 1С-клиентом брать через `external_customer`.

## Методика сделок

Сделка - это не форма лида и не сам контракт. `DealModel` является агрегатом CRM-цикла: он собирает источник, паспорт клиента, контракт, работы, оплаты и результат в одну управляемую историю.

Главное правило: стадия сделки должна выводиться из фактов связанных объектов, а не переключаться декоративной кнопкой. Если пользователь нажимает этап в drawer, интерфейс должен открыть связанную сущность или действие, которое создает недостающий объект. Например, этап "Паспорт клиента" открывает создание/выбор клиента, а не просто меняет `stage`.

Коротко:

```text
обращение-лид -> сделка -> паспорт клиента -> контракт -> работы -> оплаты -> результат
```

При этом паспорт клиента (`CustomerCardModel`) живет дольше одной сделки. Контракт (`CustomerContractModel`) является этапом/результатом сделки, но не заменяет сделку. Оплаты и тарифы должны быть отдельным учетным слоем, а не ручными полями внутри сделки.

## Актуальная механика MVP

### 1. Создание лида

Пользователь в `/deals` нажимает создание сделки. В режиме сделок frontend не открывает форму `DealModel`; он переводит пользователя в HelpDesk:

```text
/helpdesk/unconfirmed_appeals?createLead=1
```

Кодовые точки frontend:

- `src/modules/Deals/index.vue::openAdd()` - переводит на создание обращения.
- `src/modules/HelpDesk/index.vue::openLeadFromQuery()` - ловит `createLead=1`.
- `src/modules/HelpDesk/index.vue::addLeadTicket()` - открывает создание тикета с `{ ticket_type: 'lead' }`.

После сохранения обращения backend получает `HelpDeskTicketModel(ticket_type_id='lead')`. Это явный источник сделки. Сделку отдельно руками для лида создавать нельзя.

Кодовые точки backend:

- `help_desk/models.py::HelpDeskTicketModel.save()` вызывает `ensure_deal_for_lead_ticket()` после commit.
- `crm/deals_services.py::ensure_deal_for_lead_ticket()` создает или обновляет `DealModel(source_ticket=<ticket>)`.

Если у обращения пока техническая unknown-карточка клиента, сделка получает стадию `lead`. Ответственным становится специалист тикета, если он есть, иначе автор.

### 2. Квалификация и паспорт клиента

Квалификация - это не отдельная анкета в сделке. Это момент, когда лид получил реальный `CustomerCardModel`.

Есть два рабочих пути:

1. Создать новую карточку клиента из лида.
2. Привязать контакт/обращение к существующей карточке клиента.

Кодовые точки:

- `help_desk/serializers.py::CustomerCardModelCreateSerializer` принимает `lead=<ticket_id>`.
- При создании карточки serializer переносит `lead.customer_card` на новую карточку и обновляет контакт.
- `help_desk/views.py::ContactPersonViewSet.set_customer_card()` переносит лидовые обращения контакта с unknown-карточки на выбранную карточку.
- После переноса снова вызывается `ensure_deal_for_lead_ticket()`.

После появления реальной карточки `DealModel.customer_card` заполняется, а стадия становится `qualification`.

### 3. Контракт

Контракт создается из сделки или импортируется из внешней системы. В обоих случаях контракт должен быть связан со сделкой через `CustomerContractModel.deal`.

Кодовые точки:

- `src/modules/Deals/components/DealDrawerDriver.vue::createContractFromDeal()` открывает контрактный drawer с предзаполненными `deal`, `organization`, `customer_card`, `amount`, `date_end`.
- `customer_contracts/models.py::CustomerContractModel.save()` вызывает `attach_contract_to_deal()`.
- `crm/deals_services.py::attach_contract_to_deal()` привязывает контракт к существующей открытой сделке клиента или создает сделку-контейнер для импортированного контракта.

Если контракт существует, но еще не подписан/не активен, стадия сделки - `proposal`. Если контракт активен, подписан или фактически существует, стадия - `production`.

### 4. Производство и работы

Производство - это не отдельная форма сделки. Это факт того, что по контракту пошли задачи и обращения.

Связи работ:

- `TaskModel.contract -> CustomerContractModel`
- `TaskModel.customer_card -> CustomerCardModel`
- `HelpDeskTicketModel.analytics_key -> CustomerContractProjectModel`
- `CustomerContractProjectModel -> контракт + проект`

`CustomerContractModel.recalculate_hours_fact()` собирает фактические часы из задач и обращений через `AccumulationRegister.quantity_fact`. Если по контракту есть фактические часы, сделка переходит в `closing`.

### 5. Оплаты и закрытие

Сейчас стадия `closing` называется "Оплаты", но полноценной модели оплат в проверенном коде нет. Это временный proxy-этап: он показывает, что работы уже есть и пора закрывать период, акты, сверку часов и оплату.

Правильное развитие:

- добавить отдельную модель оплат/начислений;
- добавить ценовую политику клиента по часам;
- показывать сводку оплат и работ на паспорте клиента и в контракте.

Когда контракт получает статус `completed`, сделка переходит в `won`. `lost` остается ручным финальным исходом, когда сделку нужно закрыть как потерянную.

## Как вычисляется стадия

Функция-источник: `crm/deals_services.py::resolve_deal_stage_code()`.

Стадия сделки вычисляется из фактов агрегата:

1. `lead` - есть исходное обращение-лид, но нет реального `CustomerCardModel`.
2. `qualification` - лид получил реальную карточку клиента, то есть начат паспорт клиента.
3. `proposal` - к сделке привязан контракт.
4. `production` - контракт активен/подписан, работы находятся в исполнении.
5. `closing` - есть фактический объем работ, стадия используется как временный proxy для оплат/актов, пока отдельная платежная модель к сделке не подключена.
6. `won` - контракт завершен.
7. `lost` - ручной финальный отказ, если сделку надо закрыть как потерянную.

Технически есть `POST /api/v1/crm/deals/deals/<id>/transition_stage/`, но для нормального CRM-flow его нельзя использовать как основной способ движения сделки. Любой ручной переход, который противоречит фактам, будет переигран `sync_deal_stage()` при следующей синхронизации. Исключение - `lost`, потому что это финальное бизнес-решение, а не вывод из контракта.

## Как frontend должен работать со сделкой

Страница `/deals` имеет два режима:

- `mode=deals` - основной CRM-режим, список `crm.DealModel`;
- `mode=contracts` - совместимый режим старого списка контрактов.

Основные запросы режима сделок:

```text
GET /api/v1/crm/deals/deals/?page=1&page_size=30
GET /api/v1/crm/deals/deals/stage_summary/
GET /api/v1/crm/deals/deals/form_info/
GET /api/v1/crm/deals/deals/<id>/
GET /api/v1/crm/deals/deals/<id>/action_info/
```

Drawer открывается query-параметром:

```text
/deals?mode=deals&deal=<deal_id>
```

Backend detail возвращает `flow_steps`. Это инструкция для drawer, из каких этапов состоит агрегат:

```text
Обращение / лид
Паспорт клиента
Контракт
Производство / работы
Оплаты
Результат
```

Кнопка на связанном объекте называется "Подробнее" и должна открывать связанную сущность через query:

```text
ticket      -> ticketView=<id>
customer    -> client=<id>
contract    -> contract=<id>
task        -> task=<id>
meeting     -> meeting=<id>
order       -> order=<id>
```

Если у этапа нет объекта, кнопка должна запускать создание этого объекта. Например, у `qualification` без карточки клиента показывается "Создать паспорт клиента из лида".

## Событийная карта

| Когда | Где во frontend | Где на backend | Что происходит со сделкой |
| --- | --- | --- | --- |
| Пользователь хочет создать новую сделку | `/deals`, кнопка создания, `Deals/index.vue::openAdd()` | Пока не вызывается `DealModel` API | Пользователя отправляем в создание обращения-лида, потому что сделка должна иметь источник |
| Создано обращение-лид | HelpDesk modal с `ticket_type='lead'` | `HelpDeskTicketModel.save()` -> `ensure_deal_for_lead_ticket()` | Создается или обновляется `DealModel.source_ticket`; стадия `lead` или `qualification`, если клиент уже реальный |
| Лиду назначили/создали клиента | `CreateClientModal`, `ClientForm`, `set_customer_card` | `CustomerCardModelCreateSerializer`, `ContactPersonViewSet.set_customer_card()` | `DealModel.customer_card` заполняется, стадия становится `qualification` |
| Из сделки создают контракт | `DealDrawerDriver::createContractFromDeal()` | `CustomerContractModel.save()` -> `attach_contract_to_deal()` | Контракт получает `deal`; стадия становится `proposal` или `production` |
| Контракт импортирован без сделки | Старый контрактный режим или импорт | `attach_contract_to_deal()` | Backend ищет открытую сделку клиента или создает сделку-контейнер |
| К контракту привязали клиентов/проекты | Contract drawer/workspace | `CustomerContractServicedCardModel`, `CustomerContractProjectModel` | Формируются analytics keys для обращений и работ |
| Появились работы | HelpDesk, Tasks | `TaskModel.contract`, `HelpDeskTicketModel.analytics_key`, `recalculate_hours_fact()` | Факт часов попадает в контракт; сделка может перейти в `closing` |
| Контракт завершен | Contract status | `resolve_deal_stage_code()` | Сделка переходит в `won` |
| Пользователь нажал этап в drawer | `DealDrawer` по `flow_steps` | Обычно backend не меняет stage | Открывается связанная сущность или действие создания недостающего объекта |

## Что нельзя делать в сделках

- Нельзя создавать лид как пустую `DealModel` без `source_ticket`. Такой лид нельзя объяснить и нельзя связать с реальным обращением.
- Нельзя использовать stage click как декоративный переход. Если нет клиента, контракта или работ, стадия должна показывать отсутствие факта, а не притворяться выполненной.
- Нельзя превращать контракт в замену сделки. Контракт - часть агрегата, а сделка - контейнер всего CRM-цикла.
- Нельзя смешивать оплаты и тарифы с полями сделки. Для этого нужны отдельные модели и сводка на паспорте клиента/контракте.
- Нельзя плодить фейковые helpdesk-тикеты для импортированных контрактов без явной продуктовой причины. Лучше завести отдельный `DealSourceModel`.

## Что сделано в MVP 2026-05-11

Вход в CRM-цикл теперь начинается не с ручной анкеты сделки, а с обращения. `HelpDeskTicketModel` с `ticket_type_id='lead'` является явным источником, а backend при сохранении такого обращения автоматически создает или обновляет связанную сделку через `DealModel.source_ticket`.

На локальной базе подготовлен демонстрационный набор из 12 активных сделок, у всех есть явное исходное обращение. Расклад по этапам: `lead` - 2, `qualification` - 3, `proposal` - 2, `production` - 2, `closing` - 2, `won` - 1. Старые искусственные `MVP:*` и безымянные лиды скрыты, чтобы список не выглядел мусорным.

Список сделок на frontend запрашивает `page_size=30`, поэтому весь MVP-набор виден на одном экране. Backend-список оптимизирован: вместо десятков секунд `/api/v1/crm/deals/deals/?page=1&page_size=30` локально отвечает примерно за 0.4-0.7 секунды.

Деталка сделки после оптимизации 2026-05-12 не должна строить тяжелые универсальные queryset задач/заказов до фильтрации по сделке. На локальном API `GET /api/v1/crm/deals/deals/<id>/` после прогрева отвечает примерно за 250-350 мс.

## Что уже есть

### 1. Первое обращение и стадия "Лид"

В коде нет нормального бизнес-сценария "тикет без `CustomerCardModel`". Поле у `HelpDeskTicketModel.customer_card` формально nullable, но рабочие сценарии завязаны на карточку: нумератор берет `self.customer_card.org_admin`, permissions идут через карточку, специалисты берутся из карточки.

Фактический паттерн уже есть другой:

1. Для неизвестного клиента создается техническая карточка клиента с `unknown=True`.
2. Для неизвестного отправителя создается `ContactPersonModel` с `unknown=True`.
3. Первое сообщение от такого контакта создает `HelpDeskTicketModel` с `ticket_type_id='lead'`.
4. Такой тикет называется "Лид" и попадает в отдельное представление лидов.

Кодовые точки:

- `help_desk/utils.py::get_or_create_unknown_customer_card()` создает "Неизвестная организация".
- `help_desk/utils.py::create_unknown_contact_person()` создает "Новый контакт".
- `help_desk/utils.py` в telegram `/start` без авторизации тоже создает unknown card/contact.
- `help_desk/models.py::ContactPersonMessageModel.save()` при `customer_card.unknown=True` создает тикет типа `lead`.
- `help_desk/views.py::HelpDeskTicketViewSet.get_queryset()` при `display=leads` показывает лиды, иначе исключает их из обычного списка.

Локальная БД на момент проверки:

```text
unknown_cards: 1
unknown_contacts: 3
lead_tickets: 4
lead_tickets_unknown_card: 3
tickets_without_card: 0
```

Вывод: стадия "Лид" уже частично реализована через `HelpDeskTicketModel(ticket_type='lead')` плюс техническую `CustomerCardModel(unknown=True)`. Чистого сценария "обращение без CustomerCardModel" нет, и лучше его не вводить.

### 2. Рождение CustomerCardModel из лида

Превращение лида в нормального клиента тоже уже есть.

`CustomerCardModelCreateSerializer` принимает поле `lead`:

```text
lead = HelpDeskTicketModel.objects.filter(ticket_type_id='lead', is_active=True)
```

При создании карточки с `lead=<ticket_id>` serializer:

- создает новую `CustomerCardModel`;
- переносит `lead.customer_card` на новую карточку;
- переносит `lead.contact_person.customer_card` на новую карточку;
- снимает `unknown=False` с контакта.

Есть и второй путь, через уже существующую карточку:

```text
POST /api/v1/help_desk/contact_persons/<id>/set_customer_card/
```

Он назначает контактному лицу карточку клиента и переносит тикеты этого контакта с unknown-карточки на выбранную карточку.

Frontend-точка:

- `src/modules/HelpDesk/components/Tickets/TicketDrawer/tabs/CreateClientModal.vue`
- модалка выбора/создания клиента отправляет `set_customer_card`.
- при создании клиента из лида frontend передает `lead: this.$route.query.ticketView`.

Итого: "лид -> паспорт клиента" уже заложен, но нужен явный продуктовый UI-стандарт, чтобы это было не случайной модалкой в тикете, а частью CRM-цикла.

### 3. Контракт и текущий Deals

Контракты уже связаны со сделками:

- `CustomerContractModel.deal -> crm.DealModel`
- при сохранении нового контракта без сделки вызывается `ensure_deal_for_customer_contract()`;
- миграция `customer_contracts/0008_customercontractmodel_deal.py` уже создавала сделки для существующих контрактов.

Маппинг статусов контракта в стадии сделки сейчас такой:

```text
contract exists, but not active/signed -> deal.stage=proposal
contract.status=active      -> deal.stage=production
contract.status=on_pause    -> deal.stage=production
contract.hours_fact > 0     -> deal.stage=closing
contract.status=completed   -> deal.stage=won
is_signed/is_exists=true    -> deal.stage=production
source_ticket without real customer -> deal.stage=lead
real customer without contract      -> deal.stage=qualification
```

Стадии сделок уже есть:

```text
lead, qualification, proposal, production, closing, won, lost
```

После MVP-правки frontend `/deals` показывает два режима: основной список `crm.DealModel` и совместимый режим контрактов `CustomerContractModel`. Текущее состояние зафиксировано в `docs/DEALS_STATE_AFTER_ACCESS.md`.

### 4. Клиенты и проекты внутри контракта

Это уже правильно нащупано:

- `CustomerContractServicedCardModel` связывает контракт с обслуживаемыми клиентскими карточками.
- `CustomerContractProjectModel` связывает контракт с проектом и служит analytics key для обращений.
- `CustomerContractViewSet` уже имеет endpoints `service_cards`, `service_cards/bind`, `service_cards/unbind`.
- `CustomerContractAnalyticsKeysAPIView` отдает доступные связки контракт/проект по выбранной карточке клиента.

Значит пункт "напихиваем в контракты клиентов и проекты" уже должен стать стандартом, а не дополнительной ручной логикой.

### 5. Работы по контракту: Ticket и Task

Работы уже можно привязывать к контрактам двумя способами:

- `HelpDeskTicketModel.analytics_key -> CustomerContractProjectModel`.
- `TaskModel.contract -> CustomerContractModel`.
- `TaskModel.customer_card -> CustomerCardModel`.

Фактические часы контракта считаются в `CustomerContractModel.recalculate_hours_fact()`:

- задачи берутся через `contract.tasks`;
- обращения берутся через analytics keys контракта;
- факт часов суммируется из `AccumulationRegister.quantity_fact`.

То есть пункт про объемы работ по контракту уже архитектурно поддержан. Не хватает нормального отчета и UI-сводки на паспорте клиента/контракте.

### 6. Оплаты

Полноценной модели оплат по `CustomerCardModel` или `CustomerContractModel` в проверенном коде не нашел.

Есть:

- `CustomerContractModel.amount` - сумма контракта;
- старые CRM-заказы/счета в `crm`;
- `billing.TariffModel`, но это тарифы доступа организаций к системе, а не тарифная политика клиента по часам.

Вывод: оплаты как часть клиентского цикла отсутствуют. Для этой стадии нужна отдельная модель платежей/начислений.

### 7. Ценовая политика

Клиентская ценовая политика по часам тоже отсутствует как явная доменная модель.

Нужен двухуровневый стандарт:

1. Дефолтная ценовая политика на `CustomerCardModel`.
2. Переопределения на `CustomerContractModel`, проекте или категории работ.

Правило расчета ставки:

```text
contract/project/category override > customer default > global default
```

Так не придется плодить разные тарифы в задачах и тикетах, а расчет сможет брать effective rate из одного места.

### 8. Сводные результаты

Лучшая точка для общей сводки - паспорт клиента (`CustomerCardModel` detail), потому что он объединяет:

- лиды и обращения;
- сделки;
- контракты;
- проекты;
- задачи и тикеты;
- фактические часы;
- суммы контрактов;
- оплаты;
- задолженность/перерасход часов;
- маржинальность, если есть внутренняя смета.

На контракте нужна более узкая сводка только по конкретному договору.

## Рекомендуемый стандарт CRM-цикла

### Объекты

- `HelpDeskTicketModel(ticket_type='lead')` - первичный входящий лид из обращения.
- `DealModel` - воронка, стадии, вероятность, ответственный, сумма, источник.
- `CustomerCardModel` - паспорт клиента.
- `CustomerContractModel` - договор/контракт.
- `CustomerContractServicedCardModel` - какие клиентские карточки обслуживает контракт.
- `CustomerContractProjectModel` - ключ аналитики контракт/проект для тикетов.
- `TaskModel` и `HelpDeskTicketModel` - фактические работы.
- `Payment/Invoice` - отсутствует, нужно добавить.
- `CustomerPricePolicy/ContractRateRule` - отсутствует, нужно добавить.

### Стадии

Рекомендуемый поток:

1. `lead` - входящее обращение, неизвестный контакт, возможная unknown-карточка.
2. `qualification` - создан паспорт клиента, заполнены контакты, БИН/реквизиты, потенциальные продажи.
3. `proposal` - коммерческое предложение, оценка часов/суммы.
4. `approval` - согласование условий, договора, скидки или лимитов.
5. `production` - контракт активен, идут работы.
6. `closing` - закрытие периода/договора, акты, сверка часов.
7. `won` - успешно закрыто/продлено.
8. `lost` - отказ/потеря сделки.

Пункты "оплаты", "тарифы" и "сводка" лучше не делать стадиями сделки. Это не этапы воронки, а учетные и аналитические слои, которые видны на паспорте клиента и контракте.

## Как быть с импортированными контрактами

Для контрактов, которые прилетели из другой системы, начинать сразу с контракта было нормально.

Но для целостной CRM-истории надо добавить источник сделки:

- лучший вариант: отдельная модель `DealSourceModel` с `source_type='imported_contract'`, ссылкой на контракт и признаком `synthetic=True`;
- компромиссный вариант: создать псевдо-лид тикет `HelpDeskTicketModel(ticket_type='lead')` с `metadata.imported_contract_id`, но это загрязнит helpdesk искусственными обращениями.

Я бы выбрал `DealSourceModel`, потому что импортированный контракт - это не реальное обращение клиента. Псевдотикет нужен только если продуктово важно видеть все источники строго через helpdesk.

## Можно ли использовать flow как в заявках на согласование

Да, но не копировать буквально `WorkflowRequestModel` как сделку.

У заявок сильный паттерн:

- backend отдает `form_info`;
- backend отдает `route_template`;
- frontend строит форму и маршрут согласования по инструкциям;
- `action_info` управляет действиями;
- статус/маршрут меняются на backend.

Для сделок стоит взять именно этот подход:

- `DealStageModel` остается стадиями CRM;
- backend отдает `stage_info/form_info` для текущей стадии;
- backend отдает `action_info` с допустимыми переходами;
- если стадия требует реального согласования, создается связанная `WorkflowRequestModel`;
- результат согласования двигает `DealModel.stage`.

Важная деталь: в ранних миграциях у `DealModel` были связи `approvals` и `documents`, но миграция `crm/0114_remove_dealmodel_legacy_fields.py` их удалила. Если возвращать связь согласований со сделками, лучше сделать новую явную модель, например `DealApprovalModel`, а не незаметно реанимировать старые поля.

## Недостающие паттерны

### DealSourceModel

Нужен источник сделки:

```text
deal
source_type: ticket | imported_contract | manual | email | call | telegram
source_ticket
source_contract
source_payload
synthetic
created_at
```

Это закроет импортированные контракты и реальные лиды одним механизмом.

### DealStageTransitionModel

Нужна история движения сделки:

```text
deal
from_stage
to_stage
author
comment
created_at
related_approval
```

Тогда стадийность будет аудируемой, а не просто текущим значением FK.

### CustomerPricePolicyModel

Дефолтные ставки клиента:

```text
customer_card
currency
hourly_rate
valid_from
valid_to
rules
```

### ContractRateRuleModel

Переопределения для договора:

```text
contract
project
category
hourly_rate
valid_from
valid_to
```

### CustomerPaymentModel

Учет оплат:

```text
customer_card
contract
amount
currency
period_from
period_to
paid_at
status
external_id
comment
```

### CustomerCard aggregates

На detail карточки клиента нужно отдавать агрегаты:

```text
contracts_count
contracts_amount
hours_plan
hours_fact
paid_amount
debt_amount
open_tickets_count
open_tasks_count
active_deals_count
last_activity_at
```

## Продуктовое решение

Я бы собрал это так:

1. Оставить `CustomerCardModel` паспортом клиента.
2. Сделать `DealModel` главным объектом воронки.
3. Лид из helpdesk при квалификации должен создавать/обновлять `DealModel(source_ticket=lead_ticket, stage=qualification, customer_card=...)`.
4. Контракт должен быть результатом стадии `approval/production`, а не заменой сделки.
5. Импортированные контракты должны иметь синтетический источник `imported_contract`, а не обязательно фейковый helpdesk-тикет.
6. Работы учитывать через уже существующие `TaskModel.contract`, `HelpDeskTicketModel.analytics_key` и work logs.
7. Оплаты и ценовую политику добавить отдельными моделями.
8. На паспорте клиента сделать сводку по всем связанным объектам.

Так сделки и контракты будут жить по тому же backend-driven принципу, что и заявки на согласование, но останутся CRM-доменом, а не превратятся в еще один вид заявки.
