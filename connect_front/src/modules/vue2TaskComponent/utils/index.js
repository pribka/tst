import { i18n } from '@/config/i18n-setup'

export const priorityList = [
    {
        name: i18n.t('task.ultralow'),
        icon: 'fi-rr-hourglass-start',
        value: 0,
        color: '#444648',
        i18n: 'ultralow'
    },
    {
        name: i18n.t('task.low'),
        icon: 'fi-rr-clock',
        value: 1,
        color: '#A8C985',
        i18n: 'low'
    },
    {
        name: i18n.t('task.middle'),
        icon: 'fi-rr-exclamation',
        value: 2,
        color: '#FF9A01',
        i18n: 'middle'
    },
    {
        name: i18n.t('task.tall'),
        icon: 'fi-rr-bolt',
        value: 3,
        color: '#FF9A01',
        i18n: 'tall'
    },
    {
        name: i18n.t('task.veryhigh'),
        icon: 'fi-rr-flame',
        value: 4,
        color: '#FF5C5C',
        i18n: 'veryhigh'
    }
]

export const replaceFlatArray = (array) => {
    let newArray = []
    array.forEach(item => {
        newArray.push(item)
        if (item.children && item.children.length) {
            newArray = newArray.concat(replaceFlatArray(item.children))
        }
    })
    return newArray
}

export const formModel = {
    metadata: {
        visors: [],
        cooperators: [],
    },
    reasonObject: null,
    organization: null,
    parent: null,
    project: null,
    contract: null,
    customer_card: null,
    workgroup: null,
    operator: null,
    owner: null,
    visors: [],
    result: "",
    cooperators: [],
    prerequisites: [],
    attachments: [],
    dead_line: null,
    name: "",
    description: "",
    priority: 2,
    is_indefinite: false,
    date_start_plan: null,
    reason: null,
    is_auction: false,
    task_type: "task",
    tmp_phone: null,
    contractor: null,
    p_contractor_name: "",
    p_contractor_company: "",
    phone: "",
    email: "",
    lead_source: null,
    is_need_to_make_event: false,
}

export const checkDate = (data, type) => {
    if (data[type]) {
        return data[type];
    } else if (data.project?.[type]) {
        return data.project[type];
    }

    return null;
};
export const checkDateDeadLine = (data, type) => {
    if (data.project?.[type]) {
        return data.project[type];
    } else if (data[type]) {
        return data[type];
    }

    return null;
};
