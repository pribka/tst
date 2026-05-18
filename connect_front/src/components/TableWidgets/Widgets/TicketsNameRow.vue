<template>
    <div class="cursor-pointer" @click="openClient()">
        {{ record.name }}
    </div>
</template>

<script>
import eventBus from '@/utils/eventBus'
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
            const query = {...this.$route.query}
            if(!query.ticketView) {
                query.ticketView = this.record.id
                this.$router.push({query})
            } else {
                eventBus.$emit('ticket_drawer_close')
                setTimeout(() => {
                    query.ticketView = this.record.id
                    this.$router.push({query})
                }, 500)
            }
        }
    }
}
</script>