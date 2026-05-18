export default {
    task: {
        type: Object,
        required: true
    },
    getPopupContainer: {
        type: Function,
        default: () => {}
    },
    pageModel: {
        type: String,
        required: true
    },
    pageName: {
        type: String,
        required: true
    },
    actions: {
        type: Object,
        default: () => null
    },
    editTime: {
        type: Function,
        default: () => {}
    },
    deleteHandler: {
        type: Function,
        default: () => {}
    },
    tableFullHeight: {
        type: Boolean,
        default: false
    },
    minHeight: {
        type: Number,
        default: 300
    },
    excludeCol: {
        type: Array,
        default: () => []
    },
    isModerator: { type: Boolean, default: false }
}