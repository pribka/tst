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
        dbName: { type: String, default: 'old_select' },
        storeName: { type: String, default: 'organizations_select' },
        dbId: { type: String, default: 'user' },
        placeholder: {
            type: String,
            default: ''
        },
        opnUserSetting: {
            type: Function,
            default: () => {}
        },
        inputType: {
            type: String,
            default: 'button'
        },
        placement: {
            type: String,
            default: 'topLeft'
        },
        autoAdjustOverflow: {
            type: Boolean,
            default: true
        },
        showDefaultOrganizationSwitcher: {
            type: Boolean,
            default: true
        },
        apiUrl: {
            type: String,
            default: '/users/my_organizations/'
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
                return () => import(/* webpackMode: "lazy" */ './OrgSelectWidget/Mobile.vue')
            }
            return () => import(/* webpackMode: "lazy" */ './OrgSelectWidget/Desktop.vue')
        }
    }
}
</script>
