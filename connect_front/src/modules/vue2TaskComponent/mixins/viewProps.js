export default {
    props: {
        taskType: {
            type: String,
            default: 'task'
        },
        pageConfig: {
            type: Object,
            default: () => null
        }
    }
}