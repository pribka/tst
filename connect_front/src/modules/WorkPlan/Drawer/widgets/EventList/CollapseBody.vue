<template>
    <Accounting 
        :event="event" 
        :actions="actions"
        @change="changeHandler" />
</template>

<script>
export default {
    props: {
        event: {
            type: Object,
            required: true
        },
        storeKey: {
            type: String,
            required: true
        }
    },
    components: {
        Accounting: () => import('@apps/Calendar/components/Accounting/index.vue')
    },
    computed: {
        actions() {
            return this.event.actions || null 
        }
    },
    methods: {
        changeHandler() {
            
        }
    }
}
</script>