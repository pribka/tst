<template>
    <WidgetWrapper :widget="widget" :class="isMobile && 'mobile_widget'">
        <div class="widget_scroll">
            <NewsList />
        </div>
    </WidgetWrapper>
</template>

<script>
import { mapState } from 'vuex'
export default {
    components: {
        WidgetWrapper: () => import('../WidgetWrapper.vue'),
        NewsList: () => import('@apps/Support/components/NewsDrawer/NewsInjectList.vue')
    },
    props: {
        widget: {
            type: Object,
            required: true
        }
    },
    computed: {
        ...mapState({
            user: state => state.user.user
        }),
        isMobile() {
            return this.$store.state.isMobile
        }
    }
}
</script>

<style lang="scss" scoped>
.widget_scroll{
    overflow-y: auto;
    height: 100%;
}
.mobile_widget{
    .widget_scroll{
        height: 400px;
    }
}
</style>