export default {
    props: {
        pageConfig: {
            type: Object,
            default: () => null
        }
    },
    computed: {
        getRouteInfo() {
            return this.$store.getters['navigation/getRouteInfo'](this.$route.name)
        },
        addButton() {
            if(this.getRouteInfo?.pageActions?.add) {
                return {
                    label: this.getRouteInfo?.buttonConfig?.label || 'Оформить заказ'
                }
            } else
                return null
        }
    }
}