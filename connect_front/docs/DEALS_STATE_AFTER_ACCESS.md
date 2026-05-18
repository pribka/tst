# Deals MVP: состояние после включения доступа `pribka@mail.ru`

Дата фиксации: 2026-05-10.

## Что включено локально

Для проверки под пользователем `pribka@mail.ru` в локальной БД включен раздел `deals`:

- `AppSectionModel(code='deals')` с route `pageWidget: Deals`.
- `Deals` добавлен в `global_front_settings.injectInit`.
- Пользователю выданы роли доступа к разделу и к организациям, где можно создавать контракты.
- Пароль для локального входа: `Codex12345!`, endpoint входа: `/users/login2/`.

## Текущее поведение `/deals`

Страница теперь работает как MVP CRM-раздела, а не только как список контрактов.

Есть два режима:

- `mode=deals` - основной режим, список `crm.DealModel`;
- `mode=contracts` - старый режим, список `customer_contracts.CustomerContractModel`.

Ключи режима сделок:

```text
model: crm.DealModel
page_name: page_list_deals_crm.DealModel
tableType: deals
endpoint: /crm/deals/deals/
detail query: ?deal=<id>
```

Ключи режима контрактов:

```text
model: customer_contracts.CustomerContractModel
page_name: page_list_contracts_v3_customer_contracts.CustomerContractModel
tableType: contracts
endpoint: /customer_contracts/
detail query: ?contract=<id>
```

## Backend-driven инструкции

Backend теперь отдает для сделок те же типы инструкций, которые мы используем как продуктовый стандарт:

```text
GET /api/v1/app_info/routes/meta/?name=deals
GET /api/v1/table_info/?model=crm.DealModel&page_name=page_list_deals_crm.DealModel&table_type=deals
GET /api/v1/app_info/active_filters/?model=crm.DealModel&page_name=page_list_deals_crm.DealModel
GET /api/v1/crm/deals/deals/form_info/
GET /api/v1/crm/deals/deals/stage_summary/
GET /api/v1/crm/deals/deals/<id>/action_info/
GET /api/v1/crm/deals/deals/<id>/
```

`form_info` возвращает поля формы, стадии, `stage_flow` и default stage. Frontend строит верхнюю линию стадий в drawer по этим данным.

`detail` сделки теперь дополнительно возвращает `flow_steps` и `current_stage_code`. Это основной контракт для drawer: стадия показывается как результат связанных сущностей, а не как самостоятельное поле формы.

`action_info` возвращает доступные действия:

- `edit`
- `delete`
- `create_contract`, если у сделки есть `customer_card`

`routes/meta` для `deals` возвращает `pageActions`:

```json
{
  "add": true,
  "add_deal": true,
  "add_contract": true,
  "modes": ["deals", "contracts"]
}
```

## UI MVP

Frontend `src/modules/Deals` теперь содержит:

- переключатель режимов `Сделки` / `Контракты`;
- стадийную полосу над списком сделок с количеством и суммой по стадиям;
- список сделок через `UniversalTable`;
- мобильные карточки сделок;
- drawer сделки с агрегатными шагами `Обращение -> Паспорт клиента -> Контракт -> Производство -> Оплаты -> Результат`;
- открытие сделки через `?deal=<id>`;
- создание паспорта клиента из лида через существующий `ClientForm` с передачей `lead`;
- создание контракта из сделки с предзаполненными `deal`, `organization`, `customer_card`, `amount`, `date_end`.

Контрактный режим сохранен для обратной совместимости и открывается через `?mode=contracts`.

## Демо-данные

Для завтрашнего показа локально создан набор данных:

```text
customer_card: MVP Demo Client
organization: Веб-разработка
contract: MVP-001
```

Сделки:

```text
MVP: lead from first request                  -> lead
MVP: customer passport and potential sales    -> qualification
MVP: contract for support hours               -> production
MVP: support work and payments summary        -> closing
```

`MVP: contract for support hours` связан с контрактом `MVP-001`.

## Что еще не закрыто

MVP закрывает сцену "воронка -> сделка -> контракт", но не закрывает всю CRM-экономику:

- нет модели оплат;
- нет модели ценовой политики клиента по часам;
- нет истории переходов стадий;
- нет отдельной модели источника сделки для импортированных контрактов;
- сводку по клиенту нужно выносить на `CustomerCardModel` detail.

Эти недостающие паттерны описаны в `docs/CRM_CUSTOMER_CONTRACT_FLOW.md`.
