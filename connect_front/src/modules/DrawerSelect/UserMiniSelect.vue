<template>
    <component
        :is="viewComponent"
        v-bind="componentBinds"
        v-on="$listeners">
        <template v-if="$scopedSlots.item" #item="slotProps">
            <slot name="item" v-bind="slotProps" />
        </template>
    </component>
</template>

<script>
export default {
    inheritAttrs: false,
    props: {
        value: { type: [Object, Array, String] },
        selectProject: { type: Function, default: () => {} },
        dbName: { type: String, default: 'old_select' },
        storeName: { type: String, default: 'users_mini_select' },
        dbId: { type: String, default: 'user_mini' },
        inputType: {
            type: String,
            default: 'button'
        },
        placeholder: {
            type: String,
            default: ''
        },
        candidates: {
            type: Array,
            default: () => {}
        },
        contractor: {
            type: String,
            default: ''
        },
        placement: {
            type: String,
            default: 'topLeft'
        },
        apiUrl: {
            type: String,
            default: '/contractor_permissions/app_sections/help_desk/members/'
        },
        pageName: {
            type: String,
            default: 'users_mini_drawer'
        },
        pageSize: {
            type: Number,
            default: 15
        },
        disabled: {
            type: Boolean,
            default: false
        },
        showIcon: {
            type: Boolean,
            default: true
        },
        showSearch: {
            type: Boolean,
            default: true
        },
        showRecent: {
            type: Boolean,
            default: true
        },
        size: {
            type: String,
            default: 'default'
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
                return () => import(/* webpackMode: "lazy" */ './UserMiniSelectWidget/Mobile.vue')
            }
            return () => import(/* webpackMode: "lazy" */ './UserMiniSelectWidget/Desktop.vue')
        }
    }
}
</script>
