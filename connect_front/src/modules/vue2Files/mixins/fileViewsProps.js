export default {
    props: {
        fileList: {
            type: Array,
            default: () => []
        },
        setCurrentSource: {
            type: Function,
            default: () => {}
        },
        isMyFiles: {
            type: Boolean,
            default: false
        }
    },
}