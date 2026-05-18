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
        value: { type: [Object, String, Number], default: null },
        dbName: { type: String, default: 'old_select' },
        storeName: { type: String, default: 'api_select' },
        dbId: { type: String, default: 'api_select' },
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
        apiUrl: {
            type: String,
            required: true
        },
        params: {
            type: Object,
            default: () => ({})
        },
        listObject: {
            type: String,
            default: 'results'
        },
        valueKey: {
            type: String,
            default: 'id'
        },
        labelKey: {
            type: String,
            default: 'name'
        },
        searchKey: {
            type: String,
            default: 'text'
        },
        pageName: {
            type: String,
            default: ''
        },
        pageSize: {
            type: Number,
            default: 15
        },
        pagination: {
            type: Boolean,
            default: false
        },
        showIcon: {
            type: Boolean,
            default: false
        },
        iconClass: {
            type: String,
            default: 'fi-rr-folder'
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
            default: true
        },
        showClear: {
            type: Boolean,
            default: true
        },
        showArrow: {
            type: Boolean,
            default: true
        },
        size: {
            type: String,
            default: 'default'
        },
        title: {
            type: String,
            default: ''
        },
        searchPlaceholder: {
            type: String,
            default: ''
        },
        initList: {
            type: Boolean,
            default: true
        },
        useSearchApi: {
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
                return () => import(/* webpackMode: "lazy" */ './ContractSelectWidget/Mobile.vue')
            }
            return () => import(/* webpackMode: "lazy" */ './ContractSelectWidget/Desktop.vue')
        }
    },
    methods: {
        openSelect() {
            const widget = this.$refs.viewComponent
            if (widget && typeof widget.openSelect === 'function')
                widget.openSelect()
        },
        open() {
            this.openSelect()
        }
    }
}
</script>
