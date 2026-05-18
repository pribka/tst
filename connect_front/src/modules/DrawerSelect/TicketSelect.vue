<template>
    <component
        :is="viewComponent"
        v-bind="componentBinds"
        v-on="$listeners" />
</template>

<script>
export default {
    inheritAttrs: false,
    props: {
        value: { type: [Object, Array, String] },
        selectProject: { type: Function, default: () => {} },
        inputType: { type: String, default: 'button' },
        placeholder: { type: String, default: '' },
        showClear: { type: Boolean, default: true },
        usePopupContainer: { type: Boolean, default: false },
        customPopupContainer: { type: [Function, Object], default: () => {} },
        showArrow: { type: Boolean, default: false }
    },
    computed: {
        componentBinds() {
            return {
                ...this.$attrs,
                ...this.$props
            }
        },
        isMobile() {
            return this.$store.state.isMobile
        },
        viewComponent() {
            if (this.isMobile) {
                return () => import(/* webpackMode: "lazy" */ './TicketSelectWidget/Mobile.vue')
            }
            return () => import(/* webpackMode: "lazy" */ './TicketSelectWidget/Desktop.vue')
        }
    }
}
</script>
