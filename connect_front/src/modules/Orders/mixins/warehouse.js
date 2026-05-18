import { mapState } from 'vuex'
export default {
    computed: {
        ...mapState({
            warehouseFormInfo: state => state.orders.warehouseFormInfo
        })
    },
    data() {
        return {
            loadingWarehouseForm: false
        }
    },
    methods: {
        async getWarehouseFormInfo (goods = null) {
            if(!this.warehouseFormInfo) {
                try {
                    this.loadingWarehouseForm = true
                    await this.$store.dispatch('orders/getWarehouseFormInfo', goods)
                } catch(e) {
                    console.log(e)
                } finally {
                    this.loadingWarehouseForm = false
                }
            }
        }
    }
}