export default {
    widgetKey: {
        type: [String, Number],
        required: true
    },
    resolution: {
        type: Object,
        required: true
    },
    intents: {
        type: Object,
        required: true
    },
    message: {
        type: Object,
        required: true
    },
    index: {
        type: Number,
        default: 0
    },
    messageIndex: {
        type: Number,
        default: 0
    },
    intentIndex: {
        type: Number,
        default: 0
    },
    formValidate: {
        type: Function,
        default: () => {}
    },
    isEdit: {
        type: Boolean,
        default: false
    },
    useInject: {
        type: Boolean,
        default: false
    },
    injectUpdate: {
        type: Function,
        default: () => {}
    },
    injectDelete: {
        type: Function,
        default: () => {}
    },
    injectChangeField: {
        type: Function,
        default: () => {}
    }
}