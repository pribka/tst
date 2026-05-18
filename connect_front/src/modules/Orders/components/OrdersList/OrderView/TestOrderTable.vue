<template>
    <div class="flex flex-grow">
        <UniversalTable
            :model="model"
            :pageName="pageName"
            :tableType="tableType"
            :params="tableParams"
            :getDataHook="hydrateCrmCustomers"
            :excludeCol="excludeCol"
            :openHandler="openOrderOnly"
            :endpoint="endpoint"
            :getInvoicePayment="getInvoicePayment" />
    </div>
</template>

<script>
import eventBus from '@/utils/eventBus.js'
import { priceFormatter } from '@/utils'
export default {
    name: "OrderTable",
    components: { 
        UniversalTable: () => import('@/components/TableWidgets/UniversalTable')
    },
    props: {
        filters: {
            type: Object,
            default: null
        },
        pageName: {
            type: String,
            default: "crm.GoodsOrderModel_list"
        },
        params: {
            type: Object,
            default: () => ({})
        },
        excludeCol: {
            type: Array,
            default: () => []
        }
    },
    data() {
        return {
            model: "crm.GoodsOrderModel",
            tableType: 'orders',
            currentOrdersCount: 0,
        }
    },
    computed: {
        endpoint() {
            return `/crm/orders/`
        },
        tableParams() {
            return {
                filters: this.filters,
                ...this.params
            }
        },
        config() {
            return this.$store.state.config.config
        },
    },
    methods: {
        priceFormatter,
        async getInvoicePayment(id, record) {
            this.loadingInvoice = true
            await this.getFiles(`crm/orders/${id}/pay_file/`, record)
            this.loadingInvoice = false
        },
        async getFiles(endoint, record){
            try{
                const response = await this.$http.get(endoint, {
                    responseType: 'blob'
                })
                const url = window.URL.createObjectURL(new Blob([response.data]))
                const link = document.createElement('a')
                link.href = url
                link.setAttribute('download', `Счет №${record.counter} от ${this.$moment().format('DD.MM.YYYY')}.pdf`)
                document.body.appendChild(link)
                link.click()
            }
            catch(error){
                console.log("error", error)
                this.$message.warning(error.error_str)
            }
        },
        hydrateCrmCustomers(data) {
            const rows = data?.results || []
            rows.forEach(row => this.hydrateCrmCustomer(row))
        },
        async hydrateCrmCustomer(row) {
            const contract = row?.customer_contract
            const contractId = contract?.id || contract
            if(!contractId || row?.customer_card?.name) {
                return
            }
            try {
                const { data } = await this.$http.get(`/customer_contracts/${contractId}/`)
                if(data?.customer_cards?.length === 1) {
                    this.$set(row, 'customer_card', data.customer_cards[0])
                    eventBus.$emit('update_table_row_data')
                }
            } catch(e) {
                console.log(e)
            }
        },
        openOrderOnly(id) {
            console.log(id, 'id')
            let query = Object.assign({}, this.$route.query)

            if(!query?.order || query.order !== id) {
                query.order = id
                this.$router.push({query})
            }
        },
        async openOrder(record){
            try {
                const { data } = await this.$http.get(`/crm/orders/${record.id}/action_info/`)
                if(data?.actions?.edit) {
                    eventBus.$emit('orderEdit', record)
                } else {
                    let query = Object.assign({}, this.$route.query)

                    if(!query?.order || query.order !== record.id) {
                        query.order = record.id
                        this.$router.push({query})
                    }
                }
            } catch(e) {
                console.log(e)
            }
        },
    },
}
</script>
