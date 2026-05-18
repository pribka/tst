<template>
    <div>
        <component :is="taskShowDrawerAsync" v-if="$route.query.task" />
        <component :is="sprintShowDrawerAsync" v-if="$route.query.sprint" />

        <EditDrawer />
        <CreateDrawer />
        <SprintEndDrawer />
        <AddTaskDrawer />
        <AddTaskListDrawer />
        <EditModal />
    </div>
</template>

<script>
import store from './store/index'
export default {
    name: 'TaskInit',
    components: {
        EditDrawer: () => import('./components/EditDrawer'),
        CreateDrawer: () => import('./components/Sprint/CreateDrawer.vue'),
        SprintEndDrawer: () => import('./components/Sprint/SprintEndDrawer.vue'),
        AddTaskDrawer: () => import('./components/Sprint/AddTaskDrawer/index.vue'),
        AddTaskListDrawer: () => import('./components/Sprint/AddTaskListDrawer.vue'),
        EditModal: () => import('./components/EditModal/index.vue')
    },
    data() {
        return {
            taskShowDrawerAsync: null,
            sprintShowDrawerAsync: null
        }
    },
    watch: {
        '$route.query.task': {
            immediate: true,
            handler(v) {
                if (v && !this.taskShowDrawerAsync)
                    this.taskShowDrawerAsync = () => import(/* webpackChunkName: "task-show-drawer" */ './components/TaskShowDrawer')
            }
        },
        '$route.query.sprint': {
            immediate: true,
            handler(v) {
                if (v && !this.sprintShowDrawerAsync)
                    this.sprintShowDrawerAsync = () => import(/* webpackChunkName: "sprint-show-drawer" */ './components/Sprint/SprintShowDrawer/index.vue')
            }
        }
    },
    created() {
        if (!this.$store.hasModule('task')) {
            this.$store.registerModule('task', store)
            this.$store.dispatch('task/initFormInfo')
        }
    }
}
</script>
