<template>
    <WidgetWrapper :widget="widget">
        <InvestProjectsWidget />
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
        InvestProjectsWidget: () => import('./components/InvestProjects'),
        WidgetWrapper: () => import('../WidgetWrapper.vue')
    },
}
</script>