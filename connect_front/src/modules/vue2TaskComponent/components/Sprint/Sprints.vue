<template>
    <component 
        :is="pageWidget" 
        :inject="inject"
        :filters="filters"
        :showHead="showHead"
        :excludeCol="excludeCol"
        :pageName="pageName"
        :injectFormParams="injectFormParams"
        :excludeFields="excludeFields"
        :showCreateButton="showCreateButton"
        :model="model"/>
</template>

<script>
export default {
    props: {
        inject: {
            type: Boolean,
            default: false
        },
        filters: {
            type: Object,
            default: null
        },
        pageName: {
            type: String,
            default: "sprint_list"
        },
        showCreateButton: {
            type: Boolean,
            default: true
        },
        model: {
            type: String,
            default: 'tasks.TaskSprintModel'
        },
        excludeFields: {
            type: Array,
            default: () => []
        },
        injectFormParams: {
            type: Object,
            default: () => {}
        },
        showHead: {
            type: Boolean,
            default: true
        },
        excludeCol: {
            type: Array,
            default: () => []
        }
    },
    computed: {
        isMobile() {
            return this.$store.state.isMobile
        }
    },
    data() {
        return {
            pageWidget: null
        }
    },
    created() {
        this.pageWidget = this.isMobile
            ? () => import('./List.vue')
            : () => import('./ListDesctop.vue')
    }
}
</script>