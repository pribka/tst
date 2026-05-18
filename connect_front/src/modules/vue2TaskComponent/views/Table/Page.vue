<template>
    <TaskPageSwitch 
        main
        model="tasks.TaskModel"
        :tableType="tableType"
        :hash="false"
        :taskType="taskType"
        :queryParams="queryParams"
        :showPageTitle="showPageTitle"
        :pageConfig="pageConfig"
        :name="nameKey"
        :pageName="page_name">
        <slot />
    </TaskPageSwitch>
</template>

<script>
import viewProps from '../../mixins/viewProps.js'
import '../../assets/main.scss'
import { mapState } from 'vuex'
export default {
    name: 'TaskViewTable',
    components: { 
        TaskPageSwitch: () => import('../../components/TaskList/TaskPageSwitch.vue')
    },
    mixins: [viewProps],
    props: {
        page_name: {
            type: String,
            default: ''
        },
        tableType: {
            type: String,
            default: 'tasks'
        },
        showPageTitle: {
            type: Boolean,
            default: false
        }

    },
    computed: {
        ...mapState({
            viewType: state => state.task.mobileViewType
        }),
        isMobile() {
            return this.$store.state.isMobile
        },
        isKanban() {
            return this.viewType[this.taskType] === 'kanban'
        },
        hasPadding() {
            return !this.isMobile || !this.isKanban
        }
    },
    data() {
        return {
            queryParams: {},
            nameKey: this.$route.name
        }
    }

}
</script>

<style lang="scss">
.table_page{ 
    .list_table{
        display: flex;
        flex-direction: column;
        height: 100%;
        .table_container{
            flex-grow: 1;
        }
    }
}
</style>