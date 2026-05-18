<template>
    <div class="cursor-pointer" @click="openClient()">
        {{ record.name }}
    </div>
</template>

<script>
export default {
    props: {
        main: { // Если вставляем этот компонент куда то помимо страницы задач, тут надо ставить false
            type: Boolean,
            default: false
        },
        record: {
            type: Object,
            required: true
        },
        text: {
            type: [Object, Number, String],
        },
        expandedRowKeys: {
            type: Array,
        },
        expanded: {
            type: Number,
        },
        extendDrawer: {
            type: Boolean,
            default: false
        },
        showChildren: { // Показывать или возможность раскрыть задачу с подзадачами
            type : Boolean,
            default: true
        },
        indent: {
            type: Object,
        },
        column: {
            type: Object,
            default: () => null
        },
        openTask: {
            type: Function,
            default: () => {}
        },
        reloadTask: {
            type: Function,
            default: () => {}
        },
        pageName: {
            type: String,
            default: ''
        }
    },
    methods: {
        openClient() {
            const query = Object.assign({}, this.$route.query)
            if(query.client !== this.record.id) {
                query.client = this.record.id
                this.$router.push({query})
            } else {
                delete query.client
                this.$router.replace({ query })
                    .then(() => {
                        query.client = this.record.id
                        this.$router.replace({ query })
                    })
            }
        }
    }
}
</script>