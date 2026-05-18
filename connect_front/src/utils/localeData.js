export const statusList = [
    {
        name: 'new',
        name2: 'to_new',
        actionHidden: true,
        color: 'blue',
        rule: 'operator'
    },
    {
        name: 'in_work',
        name2: 'to_work',
        rule: 'operator',
        color: 'purple'
    },
    {
        name: 'on_pause',
        name2: 'to_pause',
        rule: 'operator',
        color: 'orange'
    },
    {
        name: 'on_check',
        name2: 'to_check',
        rule: 'operator',
        color: 'cyan'
    },
    {
        name: 'on_rework',
        name2: 'to_rework',
        color: 'red'
    },
    {
        name: 'completed',
        name2: 'to_completed',
        color: 'green'
    }
]
export const priorityList = [
    {
        name: 'Низкий',
        value: 1,
        color: 'success',
        i18n: 'low'
    },
    {
        name: 'Средний',
        value: 2,
        color: 'warning',
        i18n: 'middle'
    },
    {
        name: 'Высокий',
        value: 3,
        color: 'error',
        i18n: 'tall'
    }
]
