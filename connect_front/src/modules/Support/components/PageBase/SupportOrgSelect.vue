<script>
export default {
    inheritAttrs: false,
    props: {
        value: {
            type: Object,
            default: null
        },
        selectProject: {
            type: Function,
            default: () => {}
        },
        dbName: {
            type: String,
            default: 'old_select'
        },
        storeName: {
            type: String,
            default: 'organizations_select'
        },
        dbId: {
            type: String,
            default: 'support_wiki'
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
            if(this.isMobile)
                return () => import(/* webpackMode: "lazy" */ './SupportOrgSelectWidget/Mobile.vue')

            return () => import(/* webpackMode: "lazy" */ './SupportOrgSelectWidget/Desktop.vue')
        }
    },
    render(h) {
        return h(this.viewComponent, {
            props: this.componentBinds,
            on: this.$listeners,
            scopedSlots: this.$scopedSlots
        }, this.$slots.default)
    }
}
</script>
