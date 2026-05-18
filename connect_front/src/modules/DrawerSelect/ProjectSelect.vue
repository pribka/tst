<template>
    <component
        ref="projectSelectWidget"
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
        placement: {
            type: String,
            default: 'topLeft'
        },
        candidates: {
            type: Array,
            default: () => {}
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
        useInputIcon: {
            type: Boolean,
            default: false
        },
        showArrow: {
            type: Boolean,
            default: false
        },
        initList: {
            type: Boolean,
            default: false
        },
        autoAdjustOverflow: {
            type: Boolean,
            default: true
        },
        multiple: {
            type: Boolean,
            default: false
        },
        disabled: {
            type: Boolean,
            default: false
        },
        apiUrl: {
            type: String,
            default: '/work_groups/workgroups/'
        },
        params: {
            type: Object,
            default: () => ({})
        },
        pageSize: {
            type: [Number, String],
            default: null
        },
        resultsKey: {
            type: String,
            default: 'results'
        },
        stringifyFilters: {
            type: Boolean,
            default: false
        },
        showRecent: {
            type: Boolean,
            default: true
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
                return () => import(/* webpackMode: "lazy" */ './ProjectSelectWidget/Mobile.vue')
            }
            return () => import(/* webpackMode: "lazy" */ './ProjectSelectWidget/Desktop.vue')
        }
    },
    methods: {
        openSelect() {
            const widget = this.$refs.projectSelectWidget
            if (widget && typeof widget.openSelect === 'function')
                widget.openSelect()
        },
        open() {
            this.openSelect()
        }
    }
}
</script>
