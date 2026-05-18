import eventBus from '@/utils/eventBus'
export default {
    props: {
        record: {
            type: Object,
            default: ()=>{}
        },
        loading: {
            type: Boolean,
            default: false
        },
    },
    computed: {
        canAddTask() {
            return this.$store.state?.user?.user?.can_create_logistic_task
        },
        actionsList() {
            return this.$store.state.orders.orderActions
        }
    },
    data() {
        return {
            listLoading: false
        }
    },
    methods: {
        openOrder() {
            let query = Object.assign({}, this.$route.query)
            if(!query?.order || query.order !== this.record.id) {
                query.order = this.record.id
                this.$router.push({query})
            }
        },
        orderEdit() {
            eventBus.$emit('orderEdit', this.record)
        },
        async getActions() {
            try {
                this.listLoading = true
                await this.$store.dispatch('orders/getOrderActions', {
                    id: this.record.id
                })
            } catch(e) {
                console.log(e)
            } finally {
                this.listLoading = false
            }
        },
        visibleChange(vis) {
            if(vis) {
                this.getActions()
            } else {
                this.$store.commit('orders/SET_ORDER_ACTIONS', null)
            }
        }
    }
}