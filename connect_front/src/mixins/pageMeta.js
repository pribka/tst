import { mapState } from 'vuex'
export default {
    computed: {
        ...mapState({
            config: state => state.config.config
        }),
        siteName() {
            if(this.config?.site_setting?.site_name)
                return this.config.site_setting.site_name
            else
                return 'Деловое облако'
        },
        pageTitle() {
            if(this.$route?.meta?.title) {
                return `${this.$route.meta.title} | ${this.siteName}`
            } else {
                return this.siteName
            }
        }
    },
    metaInfo() {
        return {
            title: this.pageTitle
        }
    }
}