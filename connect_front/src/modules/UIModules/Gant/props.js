export default {
    props: {
        useProgress: {
            type: Boolean,
            default: true
        },
        useLinks: {
            type: Boolean,
            default: false
        },
        useGridResize: {
            type: Boolean,
            default: true
        },
        scrollSize: {
            type: Number,
            default: 15
        },
        selectTask: {
            type: Boolean,
            default: true
        },
        dateFormat: {
            type: String,
            default: "%d-%m-%Y %H:%i"
        },
        dateGrid: {
            type: String,
            default: "%Y-%m-%d"
        },
        taskDate: {
            type: String,
            default: "%d %F %Y"
        },
        timePicker: {
            type: String,
            default: "%H:%i"
        },
        resizeRows: {
            type: Boolean,
            default: true
        },
        maxZoomLevel: {
            type: Number,
            default: 4
        },
        minZoomLevel: {
            type: Number,
            default: 0
        },
        scaleHeight: {
            type: Number,
            default: 50
        },
        showTodayMarker: {
            type: Boolean,
            default: true
        },
        orderBranch: {
            type: Boolean,
            default: true
        },
        page_name: {
            type: String,
            required: true
        },
        useProjects: {
            type: Boolean,
            default: false
        },
        pageModel: {
            type: String,
            default: 'workgroups.WorkgroupModel'
        },
        related_object: {
            type: [String, Number],
            default: null
        },
        useEdit: {
            type: Boolean,
            default: true
        },
        inject: {
            type: Boolean,
            default: false
        },
        formParams: {
            type: Object,
            default: () => {}
        },
        onlyTask: {
            type: Boolean,
            default: false
        },
        forceStartDate: {
            type: String,
            default: ''
        },
        forceEndDate: {
            type: String,
            default: ''
        },
        useForceDatesMarks: {
            type: Boolean,
            default: true
        },
        durationUnit: {
            type: String,
            default: 'minute'
        },
        durationStep: {
            type: Number,
            default: 1
        }
    }
}