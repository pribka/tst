<template>
    <div>
        <a-spin :spinning="listLoading">
            <a-table
                v-if="orderTableInfo"
                :columns="orderTableInfo"
                :data-source="listOrders"
                :pagination="false"
                :scroll="scroll"
                :size="tableSize"
                @change="handleTableChange"
                :locale="{
                    emptyText: $t('task.no_data')
                }"
                :row-key="record => record.id">
                <div slot="id" slot-scope="text, record">
                    <OrderName :record="record" />
                </div>
                <template slot="warehouse" slot-scope="text">
                    <span v-if="text" class="item_name ">{{text.name}}</span>
                </template>
                <template slot="user" slot-scope="text">
                    <span v-if="text" class="item_name ">
                        <Profiler
                            :user="text"
                            :avatarSize="22" />
                    </span>
                </template>
                <template slot="contractor"  slot-scope="text, record">
                    <span v-if="getOrderCustomerName(text, record)" class="item_name ">
                        {{ getOrderCustomerName(text, record) }}
                    </span>
                </template>
                <template slot="contractor_member"  slot-scope="text, record">
                    <span v-if="!record.customer_contract && text" class="item_name ">{{text.name}}</span>
                </template>
                <template slot="contract"  slot-scope="text, record">
                    <span v-if="getOrderContractName(text, record)" class="item_name ">
                        {{ getOrderContractName(text, record) }}
                    </span>
                </template>
                <template slot="pay_type"  slot-scope="text">
                    <span v-if="text" class="item_name ">{{text.name}}</span>
                </template>
                <template slot="orders_table_info"  slot-scope="text">
                    <span v-if="text" class="item_name ">{{text}}</span>
                    <span v-else>-</span>
                </template>

                <template slot="warehouse"  slot-scope="text, record">
                    <span v-if="record" class="item_name ">{{record.warehouse.name}}</span>
                </template>

                <template slot="delivery_date_plan"  slot-scope="text, record">
                    <span class="flex items-center"
                          v-if="record.delivery_date_plan.delivery_date_plan_lte !== null ||
                              record.delivery_date_plan.delivery_date_plan_gte !== null" >
                        <a-icon  type="clock-circle" />
                        От {{$moment(record.delivery_date_plan.delivery_date_plan_gte).format('D MMMM, HH:mm')}} <br>
                        До {{$moment(record.delivery_date_plan.delivery_date_plan_lte).format('D MMMM, HH:mm')}}
                    </span>
                </template>

                <template slot="created_at"  slot-scope="text, record">
                    <DateWidget :date="record.created_at" noColor/>
                </template>

                <template slot="execute_status"  slot-scope="text, record">
                    <div class="flex items-center">
                        <Status
                            icon
                            statusType="Статус выполнения"
                            iconType="fi-rr-time-past"
                            :status='record.execute_status'/>
                        <Status
                            v-if="record.payment_status"
                            icon
                            class="ml-1"
                            statusType="Статус оплаты"
                            extraInfo="Печать документа"
                            :id="record.id"
                            :statusRecord="record"
                            :click="getInvoicePayment"
                            iconType="fi-rr-wallet"
                            :status='record.payment_status'/>
                        <Status
                            v-if="record.delivery_status"
                            icon
                            class="ml-1"
                            statusType="Статус доставки"
                            iconType="fi-rr-truck-side"
                            :status='record.delivery_status'/>
                    </div>
                </template>

                <template slot="operation_type"  slot-scope="text">
                    <span>{{text.name}}</span>
                </template>

                <template slot="amount"  slot-scope="text, record">
                    <template v-if="text">
                        {{ priceFormatter(text) }} <template v-if="record.currency">{{ record.currency.icon }}</template>
                    </template>
                </template>

                <template slot="mustpaid"  slot-scope="text">
                    <template v-if="text">
                        {{ priceFormatter(text) }}
                    </template>
                </template>

                <template slot="actions" slot-scope="text, record">
                    <Actions :record="record" :openOrder="openOrderOnly" />
                </template>

            </a-table>
        </a-spin>

        <Pager
            ref="Pager"
            class="pt-1"
            :hash="false"
            :changePage="changePage"
            :changeSize="changeSize"
            :page_size="pageSize"
            :scrollElements="[
                '.orderslist_table .ant-table-body-inner',
                '.orderslist_table .ant-table-body'
            ]"
            :page="page"
            :count="currentOrdersCount" />
    </div>

</template>

<script>
import Pager from '../Pager.vue'
import Actions from '../Actions.vue'
import eventBus from '@/utils/eventBus.js'
import DateWidget from '../DateWidget.vue'
import Status from '../Status.vue'
import { priceFormatter } from '@/utils'
import OrderName from '../OrderName.vue'
export default {
    name: "OrderTable",
    components:
    { Pager,
        Actions,
        DateWidget,
        Status,
        OrderName
    },
    props: {
        filters: {
            type: Object,
            default: null
        },
        pageName: {
            type: String,
            default: "crm.GoodsOrderModel_list"
        }
    },
    data() {
        return {
            listOrders: [],
            listLoading: false,
            page: 1,
            pageSize: 15,
            model: "crm.GoodsOrderModel",
            currentOrdersCount: 0,
            ordering: null,

            columns: [
                {
                    title: '№',
                    dataIndex: 'id',
                    key: 'id',
                    scopedSlots: { customRender: 'id' },
                    width:  120,

                },
                /*{
                    title: "Cклад отгрузки",
                    dataIndex: 'warehouse',
                    key: 'warehouse',

                    scopedSlots: { customRender: 'warehouse' },
                    width: 130,

                },*/

                {
                    title: 'Клиент',
                    dataIndex: 'contractor',
                    key: 'contractor',
                    sorter: true,
                    scopedSlots: { customRender: 'contractor' },
                    width: 130,
                },
                {
                    title: 'Контрагент',
                    dataIndex: 'contractor_member',
                    key: 'contractor_member',
                    sorter: true,
                    scopedSlots: { customRender: 'contractor_member' },
                    width: 130,
                },
                {
                    title: 'Договор',
                    dataIndex: 'contract',
                    key: 'contract',
                    sorter: true,
                    scopedSlots: { customRender: 'contract' },
                    width: 150,
                },
                {
                    title: 'Количество',
                    dataIndex: 'quantity',
                    key: 'quantity',
                    sorter: true,
                    width: 120,
                },
                {
                    title: 'Сумма',
                    dataIndex: 'amount',
                    key: 'amount',
                    width: 110,
                    sorter: true,
                    scopedSlots: { customRender: 'amount' },
                },
                {
                    title: 'Создан',
                    dataIndex: 'created_at',
                    key: 'created_at',
                    width: 120,
                    sorter: true,
                    scopedSlots: { customRender: 'created_at' },
                },
                {
                    title: 'Статус',
                    dataIndex: 'operation_type',
                    width: 160,
                    sorter: true,
                    fixed: 'right',
                    scopedSlots: { customRender: 'operation_type' },
                },

                {
                    title: 'Стадия',
                    dataIndex: 'execute_status',
                    sorter: true,
                    width: 110,
                    fixed: 'right',
                    scopedSlots: { customRender: 'execute_status' },
                },

                {
                    title: '',
                    dataIndex: 'actions',
                    key: 'actions',
                    fixed: 'right',
                    scopedSlots: { customRender: 'actions' },
                    width: 140

                }
            ]
        }
    },
    computed: {
        orderTableInfo() {
            return this.$store.state.orders.orderTableInfo
        },
        config() {
            return this.$store.state.config.config
        },
        tableSize() {
            return this.config?.theme?.tableSize ? this.config.theme.tableSize : 'small'
        },
        tableScroll() {
            if(this.windowWidth > 1650)
                return false
            else
                return  1400
        },
        scroll() {
            return {
                x: this.tableScroll,
                y: 'calc(100vh - 272px)'
            }
        },
    },
    methods: {
        priceFormatter,
        getOrderCustomerName(text, record) {
            return record?.customer_card?.name || text?.name || ''
        },
        getOrderContractName(text, record) {
            if(record?.customer_contract) {
                return record.customer_contract.number || record.customer_contract.string_view || ''
            }
            return text?.name || ''
        },
        async getInvoicePayment(id, record) {
            this.loadingInvoice = true
            await this.getFiles(`crm/orders/${id}/pay_file/`, record)
            this.loadingInvoice = false
        },
        async  getFiles(endoint, record){
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
        scrollTop() {
            document.body.scrollIntoView({ behavior: 'smooth', block: 'start' })
        },
        handleTableChange(pagination, filters, sorter) {
            let params = null
            if(sorter.order) {
                params = `${sorter.order === "ascend" ? '' : '-'}${sorter.field}`
            } else {
                params = null
            }

            if(params) {
                this.ordering = params
            }

            this.scrollTop()
            this.page = 1
            this.listOrders = []
            this.getOrders()
        },
        async getOrders() {
            try{
                this.listLoading = true
                await this.$store.dispatch('orders/getOrderTableInfo')
                const {data} = await this.$http.get(`/crm/orders/`,
                    { params: {
                        page_size: this.pageSize,
                        page: this.page,
                        page_name: this.pageName,
                        filters: this.filters,
                        ordering: this.ordering
                    }})
                if(data) {
                    this.listOrders = data.results
                    this.currentOrdersCount = data.count
                }
            }
            catch(e) {
                console.error(e)
            }
            finally{
                this.listLoading = false
            }
        },
        changePage(page) {
            this.page = page
            this.getOrders()
        },
        changeSize(size){
            this.page = 1
            this.pageSize = size
            this.getOrders()
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
        pageReload() {
            this.page = 1
            this.getOrders()
        },
    },

    mounted() {
        this.getOrders()
        eventBus.$on('update_order_list', () => {
            this.pageReload()
        })
        eventBus.$on(`update_filter_${this.model}`, () => {
            this.pageReload()
        })
        eventBus.$on('update_order_table', data => {
            if(this.listOrders?.length) {
                const index = this.listOrders.findIndex(f => f.id === data.id)
                if(index !== -1) {
                    this.$set(this.listOrders, index, data)
                }
            }
        })
    },
    beforeDestroy() {
        eventBus.$off(`update_filter_${this.model}`)
        eventBus.$off('update_order_list')
        eventBus.$off('update_order_table')
    }
}
</script>
