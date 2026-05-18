export default {
    props: {
        field: {
            type: Object,
            required: true
        },
        form: {
            type: Object,
            required: true
        },
        task: {
            type: Object,
            default: () => null
        },
        formSubmit: {
            type: Function,
            required: true
        },
        code: {
            type: [String, Number],
            required: true
        },
        edit: {
            type: Boolean,
            default: false
        }
    },
    computed: {
        fieldSize() {
            return this.field.size ? this.field.size : 'default'
        },
        fieldDisabled() {
            return this.field.disabled ? this.field.disabled : false
        },
        fieldPlaceholder() {
            return this.field.placeholder ? this.field.placeholder : ''
        }
    }
}