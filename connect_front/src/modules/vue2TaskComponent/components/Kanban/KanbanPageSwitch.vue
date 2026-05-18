<template>
    <component 
        :is="pageWidget" 
        :implementId="implementId"
        :implementType="implementType"
        :formParams="formParams"
        :queryParams="queryParams"
        :taskType="taskType"
        :main="main"
        :extendDrawer="extendDrawer"
        :showPageTitle="showPageTitle"
        :pageConfig="pageConfig">
        <slot />
    </component>
</template>

<script>
export default {
    props: {
        pageConfig: {
            type: Object,
            default: () => null
        },
        implementId: {
            type: [String, Number],
            default: null
        },
        implementType: {
            type: String,
            default: ''
        },
        formParams: { // Заполнитель данных в форме по умолчанию
            type: Object,
            default: () => {}
        },
        queryParams: {
            type: Object,
            default: () => null
        },
        taskType: {
            type: String,
            default: 'task'
        },
        extendDrawer: {
            type: Boolean,
            default: false
        },
        showPageTitle: {
            type: Boolean,
            default: false
        },
        main: { 
            type: Boolean,
            default: false
        },

    },
    computed: {
        isMobile() {
            return this.$store.state.isMobile
        },
        pageWidget() {
            if(this.isMobile) {
                return () => import('./KanbanMobile.vue')
            } else {
                return () => import('./KanbanListDesctop.vue')
            }
        }
    }
}
</script>