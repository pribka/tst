export default {
    intents: {
        type: Object,
        required: true
    },
    message: {
        type: Object,
        required: true
    },
    messageIndex: {
        type: Number,
        default: 0
    },
    intentIndex: {
        type: Number,
        default: 0
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
    },
    injectCreated: {
        type: Function,
        default: () => {}
    }
}