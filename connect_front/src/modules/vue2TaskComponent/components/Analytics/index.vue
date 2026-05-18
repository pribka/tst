<template>
    <component 
        :is="widget"
        :obj="obj"
        :pageSize="pageSize"
        :page_name="page_name"
        :model="model"
        :requestData="requestData"
        :queryParams="queryParams" />
</template>

<script>
export default {
    props: {
        obj: {
            type: [String, Number],
            default: () => null
        },
        pageSize: {
            type: Number,
            default: 30
        },
        page_name: {
            type: [String, Number],
            default: 'analytics_table'
        },
        model: {
            type: String,
            default: 'tasks.TaskModel'
        },
        queryParams: {
            type: Object,
            default: () => null
        },
        requestData: {
            type: Object,
            default: () => {}
        }
    },
    computed: {
        isMobile() {
            return this.$store.state.isMobile
        },
        widget() {
            if(this.isMobile) {
                return () => import('./Table.vue')
                return () => import('./List.vue')
            } else {
                return () => import('./Table.vue')
            }
        }
    }
}
</script>