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
        selectedItems: {
            type: Array,
            default: () => []
        },
        dbName: { type: String, default: 'old_select' },
        storeName: { type: String, default: 'support_users_mini_select' },
        dbId: { type: String, default: 'support_user_mini' },
        placement: {
            type: String,
            default: 'bottomRight'
        },
        apiUrl: {
            type: String,
            default: ''
        },
        pageName: {
            type: String,
            default: 'support_users_mini_drawer'
        },
        pageSize: {
            type: Number,
            default: 15
        },
        disabled: {
            type: Boolean,
            default: false
        },
        showSearch: {
            type: Boolean,
            default: true
        },
        showRecent: {
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
                return () => import('./WikiUserMiniSelectWidget/Mobile.vue')
            }
            return () => import('./WikiUserMiniSelectWidget/Desktop.vue')
        }
    }
}
</script>
