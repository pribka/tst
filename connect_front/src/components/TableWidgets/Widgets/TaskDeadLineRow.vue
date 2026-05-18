<template>
    <DeadLine 
        :taskStatus="record.status" 
        :date="text" />
</template>

<script>
export default {
    props: {
        text: {
            type: String
        },
        record: {
            type: Object,
            required: true
        }
    },
    components: {
        DeadLine: () => import('@apps/vue2TaskComponent/components/DeadLine')
    }
}
</script>