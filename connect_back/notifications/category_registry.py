"""
Реестр категорий уведомлений для группировки в UI.
Ключ - код категории, значение - словарь с name_ru, name_kk и sort.
"""
NOTIFICATION_CATEGORIES = {
    'tasks': {
        'name_ru': 'Задачи',
        'name_kk': 'Тапсырмалар',
        'sort': 1,
    },
    'workflow_request': {
        'name_ru': 'Заявки',
        'name_kk': 'Өтінімдер',
        'sort': 2,
    },
    'meetings': {
        'name_ru': 'Собрания',
        'name_kk': 'Жиналыстар',
        'sort': 3,
    },
    'calls': {
        'name_ru': 'Звонки',
        'name_kk': 'Қоңыраулар',
        'sort': 4,
    },
    'groups': {
        'name_ru': 'Группы',
        'name_kk': 'Топтар',
        'sort': 5,
    },
    'projects': {
        'name_ru': 'Проекты',
        'name_kk': 'Жобалар',
        'sort': 6,
    },
    'calendar': {
        'name_ru': 'События',
        'name_kk': 'Оқиғалар',
        'sort': 7,
    },
    'okr': {
        'name_ru': 'OKR',
        'name_kk': 'OKR',
        'sort': 8,
    },
    'orders': {
        'name_ru': 'Заказы',
        'name_kk': 'Тапсырыстар',
        'sort': 9,
    },
    'consolidation': {
        'name_ru': 'Консолидация',
        'name_kk': 'Біріктіру',
        'sort': 10,
    },
    'help_desk': {
        'name_ru': 'Обращения',
        'name_kk': 'Өтінімдер',
        'sort': 11,
    },
    'my-bases': {
        'name_ru': 'Тикеты',
        'name_kk': 'Тикеттер',
        'sort': 12,
    },
    'organization': {
        'name_ru': 'Организации',
        'name_kk': 'Ұйымдар',
        'sort': 13,
    },
    'invest-project': {
        'name_ru': 'Инвестпроекты',
        'name_kk': 'Инвестициялық жобалар',
        'sort': 14,
    },
    'sports-facilities': {
        'name_ru': 'Спортивные объекты',
        'name_kk': 'Спорттық нысандар',
        'sort': 15,
    },
    'moderation': {
        'name_ru': 'Модерация',
        'name_kk': 'Модерация',
        'sort': 16,
    },
    'chat': {
        'name_ru': 'Чат',
        'name_kk': 'Чат',
        'sort': 17
    },
    'system': {
        'name_ru': 'Системные уведомления',
        'name_kk': 'Жүйелік хабарландырулар',
        'sort': 18,
    },
    'logistic_tasks': {
        'name_ru': 'Доставка',
        'name_kk': 'Жеткізу',
        'sort': 19,
    },
}

