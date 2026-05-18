export default {
    props: {
        column: {
            type: Object,
            required: true
        },
        item: {
            type: [Object, Array, Boolean, Number, String]
        },
        row: {
            type: Object,
            default: () => null
        },
        code: {
            type: [String, Number],
            required: true
        },
        allColumns: {
            type: Array,
            default: () => []
        },
        task: {
            type: Object,
            default: () => null
        },
        actionsAsBlock: {
            type: Boolean,
            default: false
        },
        actionsButtonType: {
            type: String,
            default: null
        }
        
    }
}