import moment from 'moment'

export const dateFormat = date => {
    return moment(date).format('YYYY-MM-DDTHH:mm:ss.SSSZ')
}

export const storeKeyDefault = 'main'
export const task_type = 'task'
export const page_size = 10

export const taskModel = {
    loading: false,
    empty: false,
    task_type: task_type,
    page_size: page_size,
    page: 1,
    next: true,
    count: 0,
    results: [],
    search: ""
}

export const taskFields = {
    visors: [],
    cooperators: [],
    attachments: [],
    description: "",
    dead_line: null,
    date_start_plan: null,
    is_auction: false,
    parent: null,
    project: null,
    priority: 2,
    reason: null,
    task_points: [],
    p_contractor_company: "",
    p_contractor_name: "",
    email: "",
    phone: "",
    prerequisites: [],
    task_type: 'task',
    lead_source: null,
    tmp_phone: null,
    workgroup: null,
    is_indefinite: true,
    contractor: null,
    is_need_to_make_event: false,
    metadata: {
        cooperators: [],
        visors: []
    }
}

export function dailyItemGenerate(item) {
    return {
        ...item,
        dLoading: false,
        loading: false,
        edited: false,
        oldDescription: item.description,
        task: item.task || null,
        work_type: item.work_type?.code || null,
        duration_fact: (!item.duration_fact || item.duration_fact === '0.00') ? undefined : Number(item.duration_fact),
        duration_plane: (!item.duration_plane || item.duration_plane === '0.00') ? undefined : Number(item.duration_plane)
    }
}

export function dailyGenerate(data) {
    return {
        ...data,
        plane_items: data.plane_items.map(item => dailyItemGenerate(item))
    }
}