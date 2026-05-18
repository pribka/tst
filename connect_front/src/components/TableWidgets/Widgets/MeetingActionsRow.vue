<template>
    <Actions 
        :item="record"
        :page_name="pageName" />
</template>

<script>
export default {
    components: {
        Actions: () => import('@apps/vue2MeetingComponent/components/CardActions.vue')
    },
    props: {
        openTableSettings: {
            type: Function,
            default: () => {}
        },
        record: {
            type: Object,
            required: true
        },
        pageName: String,

    }
}
</script>