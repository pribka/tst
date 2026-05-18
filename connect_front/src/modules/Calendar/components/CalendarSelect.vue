<template>
    <component
        ref="calendarSelectWidget"
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
        dbName: { type: String, default: 'old_select' },
        storeName: { type: String, default: 'projects_select' },
        dbId: { type: String, default: 'user' },
        inputType: {
            type: String,
            default: 'button'
        },
        placeholder: {
            type: String,
            default: ''
        },
        showClear: {
            type: Boolean,
            default: true
        },
        usePopupContainer: {
            type: Boolean,
            default: false
        },
        customPopupContainer: {
            type: [Function, Object],
            default: () => {}
        },
        selectFirst: {
            type: Boolean,
            default: false
        },
        initLoading: {
            type: Boolean,
            default: false
        }
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
                return () => import(/* webpackMode: "lazy" */ './CalendarSelectWidget/Mobile.vue')
            }
            return () => import(/* webpackMode: "lazy" */ './CalendarSelectWidget/Desktop.vue')
        }
    },
    methods: {
        openSelect() {
            const widget = this.$refs.calendarSelectWidget
            if (widget && typeof widget.openSelect === 'function')
                widget.openSelect()
        },
        open() {
            this.openSelect()
        }
    }
}
</script>
