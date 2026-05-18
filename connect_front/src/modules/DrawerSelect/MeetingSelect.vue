<template>
    <component
        :is="viewComponent"
        v-bind="$props"
        v-on="$listeners" />
</template>

<script>
export default {
    inheritAttrs: false,
    props: {
        value: { type: Object, default: null },
        placeholder: { type: String, default: '' },
        showClear: { type: Boolean, default: true },
        inputType: { type: String, default: 'defaultInput' },
        getPopupContainerFn: { type: Function, default: null }
    },
    computed: {
        isMobile() {
            return this.$store.state.isMobile
        },
        viewComponent() {
            if (this.isMobile) {
                return () => import(/* webpackMode: "lazy" */ './MeetingSelectWidget/Mobile.vue')
            }
            return () => import(/* webpackMode: "lazy" */ './MeetingSelectWidget/Desktop.vue')
        }
    }
}
</script>
