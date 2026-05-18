
# 📊 System Fields в отчётах API

## 🔍 Описание

Параметр `system_fields` используется в GET-параметре `fields` и позволяет добавить в отчёт **системные нумерационные поля**:

- `index`: Сквозной номер строки.
- `group_index`: Номер строки внутри группы (`leveling`), если она задана.

## 🔑 Синтаксис

```json
"system_fields": [
  {"name": "index", "title": "№", "order": 6},
  {"name": "group_index", "title": "№ в группе", "order": 7}
]
```

| Поле          | Описание                                                                 |
|---------------|--------------------------------------------------------------------------|
| `name`        | Название системного поля (`index` или `group_index`)                     |
| `title`       | Заголовок столбца в HTML/Excel-отчёте                                    |
| `order`       | Порядок отображения столбца                                              |

## 📐 Логика работы

### `index`
Сквозная нумерация всех строк отчета, с учётом:
- Фильтров (`filters`)
- Сортировки (`ordering`)

**Реализация:**
```python
Window(expression=RowNumber(), order_by=...)
```

---

### `group_index`
Нумерация строк **внутри каждой группы**, если задан `leveling`.  
Если `leveling` отсутствует — работает как `index`.

**Реализация:**
```python
# если есть grouping
Window(expression=RowNumber(), partition_by=[F(...)], order_by=...)
# если нет grouping
Window(expression=RowNumber(), order_by=...)
```

---

## ⚙️ Влияние других параметров

| Параметр    | Влияние на system_fields                                |
|-------------|--------------------------------------------------------|
| `ordering`  | Определяет порядок строк для `index` и `group_index`   |
| `leveling`  | Влияет только на `group_index`                         |
| `filters`   | Учитываются перед нумерацией                           |
| `results`   | system_fields отображаются в HTML и Excel              |

---

## 📎 Пример запроса

```http
GET /api/v1/reports/taskexecutiontimemodel/?fields={
  "leveling": [{"name": "author", "title": "Сотрудник"}],
  "aggregates": [
    {"name": "plan_hours", "max": "task__execution_time_plan", "title": "План", "order": 4}
  ],
  "system_fields": [
    {"name": "index", "title": "№", "order": 6},
    {"name": "group_index", "title": "№ в группе", "order": 7}
  ]
}
&ordering=task__counter
&filters=[...]
&results=xls
```

## 📁 Используемые технологии

- Django 3.2+
- `Window`, `RowNumber` (из `django.db.models.functions`)
