export default {
    props: {
        task: {
            type: Object,
            required: true
        },
        stat: {
            type: Object,
            required: true
        }
    },
    methods: {
        chartColor(index) {
            switch (index) {
            case 0:
                return '#80c6ff'
                break;
            case 1:
                return '#c2d88e'
                break;
            case 2:
                return '#ca97ca'
                break;
            case 3:
                return '#ffc618'
                break;
            case 4:
                return '#88c240'
                break;
            case 5:
                return '#008ffb'
                break;
            default:
                return '#816bf8'
            }
        }
    }
}