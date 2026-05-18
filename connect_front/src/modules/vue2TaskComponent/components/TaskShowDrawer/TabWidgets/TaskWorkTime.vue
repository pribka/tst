<template>
    <Accounting :task="task" :injectActions="actions" tableFullHeight />
</template>

<script>
import { mapGetters } from 'vuex'
export default {
    components: {
        Accounting: () => import('../../Accounting/index.vue')
    },
    props: {
        task: {
            type: Object,
            required: true
        }
    },
    computed: {
        ...mapGetters({
            taskActions: 'task/taskActions'
        }),
        actions() {
            const actions = this.taskActions(this.task.task_type, this.task.id)
            return actions ? actions.actions : null
        }
    }
}
</script>