## Эндпоинты:

### Рабочий график

__GET__, __PUT__ ```/api/v1/workload/schedules/{profile}/schedule/```

- profile: id (uid)

Пример:

```json
Запрос:
{
    "work_days": {
        "friday": false,
        "monday": true,
        "sunday": false,
        "tuesday": true,
        "saturday": false,
        "thursday": true,
        "wednesday": true
    },
    "start_hour": "08:00:00",
    "end_hour": "18:00:00",
    "break_exist": false,
    "break_start": "12:00:00",
    "break_end": "15:00:00"
}

Ответ:
{
    "id": "577f95c7-4685-11ef-b227-c46e1f601213",
    "profile": "2a63225f-3392-11ef-8995-c46e1f601213",
    "work_days": {
        "friday": false,
        "monday": true,
        "sunday": false,
        "tuesday": true,
        "saturday": false,
        "thursday": true,
        "wednesday": true
    },
    "start_hour": "08:00:00",
    "end_hour": "18:00:00",
    "break_exist": false,
    "break_start": "12:00:00",
    "break_end": "15:00:00",
    "work_hours": "10:00:00"
}
```

### Исключения

__GET__ ```/api/v1/workload/exception_dates/```

Список всех исключений в базе.

__GET__ ```/api/v1/workload/exception_dates/{profile}/exceptions/?year=2024```

Список исключений отдельного пользователя.

- profile: id (uid)

Пример:

```json
Ответ:
[
    {
        "start_date": "2024-08-05",
        "end_date": "2024-08-16",
        "parent_id": "b219ff1e-47a5-11ef-97cd-c46e1f601213",
        "name": "test 2222",
        "profile": "2a63225f-3392-11ef-8995-c46e1f601213",
        "exception_type": "off",
        "is_repeatable": true,
        "repeat_frequency": "monthly",
        "start_hour": "09:00:00",
        "end_hour": "18:00:00",
        "repeat_end": "2025-12-17"
    },
    {
        "start_date": "2024-09-05",
        "end_date": "2024-09-16",
        "parent_id": "b219ff1e-47a5-11ef-97cd-c46e1f601213",
        "name": "test 2222",
        "profile": "2a63225f-3392-11ef-8995-c46e1f601213",
        "exception_type": "off",
        "is_repeatable": true,
        "repeat_frequency": "monthly",
        "start_hour": "09:00:00",
        "end_hour": "18:00:00",
        "repeat_end": "2025-12-17"
    }
]
```

__POST__ ```/api/v1/workload/exception_dates/```

Пример:

```json
Запрос (единичное событие):
{
    "exception_type": "off",
    "start_date": "2024-07-08",
    "end_date": "2024-07-09",
    "profile": "2a63225f-3392-11ef-8995-c46e1f601213",
    "name": "test 1"
}

Ответ:
{
    "id": "8883f2ae-468f-11ef-ba66-c46e1f601213",
    "name": "test 1",
    "exception_type": "off",
    "profile": "2a63225f-3392-11ef-8995-c46e1f601213",
    "repeat_frequency": "",
    "start_date": "2024-07-08",
    "end_date": "2024-07-09",
    "is_repeatable": false,
    "repeat_end": null,
    "start_hour": "09:00:00",
    "end_hour": "18:00:00"
}

Запрос (повторяющееся событие):
{
    "profile": "2a63225f-3392-11ef-8995-c46e1f601213",
    "exception_type": "off",
    "name": "test",
    "start_date": "2024-01-02",
    "end_date": "2024-02-02",
    "is_repeatable": true,
    "repeat_frequency": "daily",
    "repeat_end": "2024-03-02"
}

Ответ:
{
    "id": "6675b58b-4463-11ef-8f6c-c46e1f601213",
    "name": "test",
    "exception_type": "off",
    "profile": "2a63225f-3392-11ef-8995-c46e1f601213",
    "repeat_frequency": "daily",
    "start_date": "2024-01-02",
    "end_date": "2024-02-02",
    "is_repeatable": true,
    "repeat_end_choise": "never",
    "repeat_end": "2024-03-02",
    "start_hour": "09:00:00",
    "end_hour": "19:00:00"
}
```

__PUT__ ```/api/v1/workload/exception_dates/{exception}```

- exception: id (uid)

Пример:

```json
Запрос:
{
    "exception_type": "no_standart",
    "start_date": "2024-07-07"
}

Ответ:
{
    "id": "8883f2ae-468f-11ef-ba66-c46e1f601213",
    "name": "test 1",
    "exception_type": "no_standart",
    "profile": "2a63225f-3392-11ef-8995-c46e1f601213",
    "repeat_frequency": "",
    "start_date": "2024-07-07",
    "end_date": "2024-07-09",
    "is_repeatable": false,
    "repeat_end": null,
    "start_hour": "09:00:00",
    "end_hour": "18:00:00"
}
```

__DELETE__ ```/api/v1/workload/exception_dates/{exception}```

- exception: id (uid)

__GET__ ```/api/v1/workload/exception_dates/{profile}/exceptions/action_info/?related_object={uid}```

- exception: id (uid)
- related_object: uid объекта, с которого переходит текущий пользователь

Пример:

```json
Ответ:
{
    "actions": {
        "watch": {
            "availability": true
        },
        "create": {
            "availability": true
        },
        "update": {
            "availability": true
        },
        "delete": {
            "availability": true
        }
    }
}
```

### Загруженность

__GET__ ```/api/v1/workload/?related_object=6d5fff82-3c80-11ef-99fb-c46e1f601213&start=2024-07-01&end=2024-07-05```

uid оргазизации, проекта или команды.

Пример:

```json
Ответ:
[
    {
        "id": "5bd7976f-4778-11ef-8872-c46e1f601213",
        "date": "2024-07-03",
        "profile": "2a63225f-3392-11ef-8995-c46e1f601213",
        "tasks": [
            {
                "id": "1aaf2f22-3bab-11ef-8064-c46e1f601213",
                "name": "Play Button",
                "dead_line": "2024-07-05T12:00:00+05:00",
                "date_start_plan": "2024-07-03T13:00:00+05:00"
            }
        ],
        "tasks_num": 1,
        "hours": {
            "start_hour": "10:00:00",
            "end_hour": "18:00:00",
            "work_hours": "07:00:00"
        },
        "total_duration": "05:00:00",
        "percents": 71.43,
        "overload": false,
        "color": "#f7ade3"
    },
    {
        "id": "5be1b5eb-4778-11ef-9c20-c46e1f601213",
        "date": "2024-07-04",
        "profile": "2a63225f-3392-11ef-8995-c46e1f601213",
        "tasks": [
            {
                "id": "1aaf2f22-3bab-11ef-8064-c46e1f601213",
                "name": "Play Button",
                "dead_line": "2024-07-05T12:00:00+05:00",
                "date_start_plan": "2024-07-03T13:00:00+05:00"
            }
        ],
        "tasks_num": 1,
        "hours": {
            "start_hour": "10:00:00", // начало рабочего дня
            "end_hour": "18:00:00",  // конец рабочего дня
            "work_hours": "07:00:00"  // кол-во рабочих дней (с учётом обеда или без)
        },
        "total_duration": "07:00:00",  // общее время задач на день
        "percents": 100.0, // процентное отношение затрат на задачи к рабочим часам
        "overload": false,
        "color": "#f7ade3"
    },
    {
        "id": "5be87014-4778-11ef-b86b-c46e1f601213",
        "date": "2024-07-05",
        "profile": "2a63225f-3392-11ef-8995-c46e1f601213",
        "tasks": [
            {
                "id": "1aaf2f22-3bab-11ef-8064-c46e1f601213",
                "name": "Play Button",
                "dead_line": "2024-07-05T12:00:00+05:00",
                "date_start_plan": "2024-07-03T13:00:00+05:00"
            }
        ],
        "tasks_num": 1,
        "hours": {
            "start_hour": "10:00:00",
            "end_hour": "18:00:00",
            "work_hours": "07:00:00"
        },
        // обновил получение
        // "total_duration": "02:00:00",
        // "percents": 28.57,
        "overload": false,
        "color": "#f7ade3"
    }
]
```

### Участники

__GET__ ```/api/v1/workload/{related_object}/members/```

- related_object: id (uid)

Пример:

```json
Ответ:
[
    {
        "full_name": "Сагитов ТагирЯндекс",
        "checked": true,
        "id": "46abc7f2-c4b5-4d2f-a92a-46a22a2b1d4f",
        "overload_dates": [
            {
                "date": "2024-07-08",
                "percents": 150,
            },
            {
                "date": "2024-08-09",
                "percents": 130,
            }
        ]
    },
    {
        "full_name": "Антонов Кирилл",
        "checked": true,
        "id": "59f3addb-0633-47d8-af9f-a107dccc07c2"
    },
    {
        "full_name": "admin admin",
        "checked": true,
        "id": "2a63225f-3392-11ef-8995-c46e1f601213"
    },
    {
        "full_name": "Усович Руслан",
        "checked": false,
        "id": "eb5c50bb-cab8-4001-966d-8fa612bbe33e"
    },
    {
        "full_name": "Приб Константин Андреевич",
        "checked": false,
        "id": "35112317-f2fe-11e8-80fd-305a3a75264b"
    },
    {
        "full_name": "Антюхова Анастасия",
        "checked": false,
        "id": "db67de05-fb11-4743-a1bf-9b3be44eb8c2"
    },
    {
        "full_name": "Сагитова Мария",
        "checked": false,
        "id": "3a6c2944-8a4b-11ec-96fa-0242ac110006"
    }
]
```

### Обновить список участников для отображения загруженности

__POST__ ```/api/v1/workload/{related_object}/check_members/```

- related_object: id (uid)

Пример:

```json
Запрос:
[
    "59f3addb-0633-47d8-af9f-a107dccc07c2",
    "2a63225f-3392-11ef-8995-c46e1f601213",
    "46abc7f2-c4b5-4d2f-a92a-46a22a2b1d4f"
]

Ответ:
[
    "59f3addb-0633-47d8-af9f-a107dccc07c2",
    "2a63225f-3392-11ef-8995-c46e1f601213",
    "46abc7f2-c4b5-4d2f-a92a-46a22a2b1d4f"
]

или

Запрос:
"all"

Ответ:
"all"

Устанавливает флажки всем участникам
```

### Задача

__POST__ ```/api/v1/workload/task_duration/```

Пример:

```json
Запрос:
{
    "is_distributed": true,
    "start": "2024-01-01",
    "end": "2024-01-03"
}
Ответ:
{
    "id": "a5d8239c-58d9-11ef-a500-c46e1f601213",
    "task": null,
    "is_distributed": true,
    "durations": [
        {
            "date": "2024-01-01",
            "hours": 0
        },
        {
            "date": "2024-01-02",
            "hours": 0
        },
        {
            "date": "2024-01-03",
            "hours": 0
        }
    ]
}
```

__POST__ ```/api/v1/workload/check_overload/```

Пример:

```json
Запрос:
{
    "operator": "2a63225f-3392-11ef-8995-c46e1f601213",
    "date": "2024-07-03",
    "hours": 5
}
Ответ:
{
    "overload": true
}
```
