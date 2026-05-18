export default {
    computed: {
        miniMenu() {
            return this.$store.state.miniMenu
        },
        sidebarTemplate() {
            return this.$store.state.sidebarTemplate
        },
        asideWidth() {
            if(this.config?.aside_setting?.width) {
                return this.config.aside_setting.width
            } else
                return 300
        }
    },
    created() {
        this.$store.commit('INIT_SIDEBAR_TEMPLATE')
    }
}