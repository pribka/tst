<template>
    <WidgetWrapper :widget="widget">
        <Calendar defaultType="multiMonthYear" class="year_widget" />
    </WidgetWrapper>
</template>

<script>
export default {
    props: {
        widget: {
            type: Object,
            required: true
        }
    },
    components: {
        WidgetWrapper: () => import('../WidgetWrapper.vue'),
        Calendar: () => import('@apps/Calendar/Widget.vue')
    },
}
</script>

<style lang="scss" scoped>
.year_widget{
    &::v-deep{
        .fc-h-event{
            background-color: transparent!important;
            border-color: transparent!important;
        }
    }
}
</style>