<template>
    <Accounting 
        :task="task" 
        :injectActions="actions"
        @change="changeHandler" />
</template>

<script>
export default {
    components: {
        Accounting: () => import('@apps/vue2TaskComponent/components/Accounting/index.vue')
    },
    props: {
        task: {
            type: Object,
            required: true
        }
    },
    computed: {
        actions() {
            return this.task.actions || null 
        }
    },
    methods: {
        changeHandler() {
            
        }
    }
}
</script>