<template>
    <div class="flex items-center">
        <Profiler 
            v-for="user in uniqueUsers"
            :user="user"
            class="user_item"
            :avatarSize="22"
            :showUserName="false"
            :key="user.id" />
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
            type: [Object, Number, String, Array],
            default: () => []
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
    computed: {
        uniqueUsers() {
            const seen = new Set()
            return (this.record.actual_specialists || [])
                .filter(specialist => specialist && specialist.is_reserve === true)
                .map(specialist => specialist.user)
                .filter(user => {
                    if (!user || seen.has(user.id)) return false
                    seen.add(user.id)
                    return true
                })
        }
    }
}
</script>

<style lang="scss" scoped>
.user_item{
    &:not(:first-child){
        margin-left: -8px;
    }
}
</style>
