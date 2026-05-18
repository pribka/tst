export default {
    props: {
        task: {
            type: Object,
            default: () => null
        },
        item: {
            type: String,
            required: true
        }
    }
}