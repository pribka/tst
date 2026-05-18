import moment from 'moment'
import { storeKeyDefault, task_type, page_size, taskModel } from '../utils.js'

export default () => ({
    viewType: {
        main: 'list'
    },
    activeTab: {
        [storeKeyDefault]: 'tasks'
    },
    role: {
        main: null
    },
    ticketRole: {
        main: null
    },
    day_statistics: {
        [storeKeyDefault]: {
            loading: false,
            data: null
        }
    },
    reportSettings: {
        [storeKeyDefault]: null
    },
    ai_intents: {
        [storeKeyDefault]: {
            loading: false,
            data: null
        }
    },
    consolidationKeyResults: {
        loading: false,
        data: null
    },
    consolidationDashboard: {
        loading: false,
        data: null
    },
    consolidationReportSettings: {},
    consolidationWidgetReports: {},
    project: {},
    workgroup: {},
    user: {
        [storeKeyDefault]: []
    },
    tabsCount: {
        [storeKeyDefault]: null
    },
    mainDate: {
        [storeKeyDefault]: [moment().clone().startOf('day'), moment().clone().endOf('day')]
    },
    employeesDateRange: [
        moment().clone().startOf('day'),
        moment().clone().endOf('day')
    ],
    consolidationFilters: {
        scope: null,
        relatedObject: null
    },
    taskSearch: {
        [storeKeyDefault]: {
            search: ""
        }
    },
    taskList: {
        [storeKeyDefault]: {...taskModel}
    },
    taskFocusList: {
        [storeKeyDefault]: {...taskModel}
    },
    taskOtherList: {
        [storeKeyDefault]: {...taskModel}
    },
    eventList: {
        [storeKeyDefault]: {
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
    },
    dayPulseList: {
        [storeKeyDefault]: {
            loading: false,
            empty: false,
            page_size: 20,
            page: 1,
            next: true,
            count: 0,
            results: [],
            search: ""
        }
    },
    dayPulseCategories: {
        loading: false,
        loaded: false,
        results: []
    },
    meetingList: {
        [storeKeyDefault]: {
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
    },
    ticketList: {
        [storeKeyDefault]: {
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
    },
    ticketOtherList: {
        [storeKeyDefault]: {
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
    }
})
