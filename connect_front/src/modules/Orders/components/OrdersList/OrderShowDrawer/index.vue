<template>
    <a-drawer
        :width="drawerWidth"
        class="detail_order_drawer"
        :class="[isMobile && 'detail_mobile_drawer', (isLogistic && isDelivered || orderActions && orderActions.edit) && 'logistic_order_drawer']"
        :visible="visible"
        :closable="false"
        :zIndex="1025"
        @close="visible=false"
        :afterVisibleChange="afterVisibleChange">
        <div class="drawer_header flex items-center justify-between">
            <a-skeleton
                v-if="loading"
                active
                :paragraph="{ rows: 1 }" />
            <template v-else>
                <template v-if="order">
                    <h1 v-if="order.operation_type && order.operation_type.code == '40'" class="truncate">
                        Заказ №{{order.counter}} от {{ $moment(order.created_at).format('DD.MM.YYYY') }}, на сумму {{ priceFormatter(order.amount) }} <template v-if="order.currency">{{ order.currency.icon }}</template>
                    </h1>
                    <h1 v-if="order.operation_type && order.operation_type.code == '20'" class="truncate">
                        КП №{{order.counter}} от {{ $moment(order.created_at).format('DD.MM.YYYY') }}, на сумму {{ priceFormatter(order.amount) }} <template v-if="order.currency">{{ order.currency.icon }}</template>
                    </h1>
                </template>
            </template>
            <div class="pl-2">
                <a-button
                    type="link"
                    class="ml-2 text-current"
                    icon="close"
                    @click="visible = false" />
            </div>
        </div>
        <div class="drawer_body order_body">
            <div
                v-if="loading"
                class="p-3">
                <a-skeleton
                    active
                    :paragraph="{ rows: 6 }" />
            </div>
            <template v-else>
                <template v-if="order">
                    <!-- DESKTOP -->
                    <template v-if="!isMobile">
                        <div class="header_tabs_wrap">
                            <a-tabs
                                :activeKey="tabKey"
                                class="header_tabs"
                                @change="changeTab">
                                <a-tab-pane
                                    key="order"
                                    tab="Заказ"></a-tab-pane>
                                <a-tab-pane
                                    key="products"
                                    tab="Содержимое">
                                </a-tab-pane>
                                <a-tab-pane
                                    v-if="order.attachments && order.attachments.length"
                                    key="files">
                                    <template #tab>
                                        <div class="flex">
                                            <span>Файлы</span>
                                            <a-badge class="ml-1" :count="order.attachments.length"></a-badge>
                                        </div>

                                    </template>
                                </a-tab-pane>
                                <a-tab-pane
                                    key="comments">
                                    <template #tab>
                                        <div class="flex">
                                            <span>{{$t('task.comments') }}</span>
                                            <a-badge class="ml-1" :count="commentsCount"></a-badge>
                                        </div>

                                    </template>
                                </a-tab-pane>
                                <a-tab-pane
                                    key="addition"
                                    tab="Доп. поля">
                                </a-tab-pane>
                            </a-tabs>
                        </div>
                        <a-tabs
                            :activeKey="tabKey"
                            class="content_tabs">
                            <a-tab-pane
                                key="order"
                                tab="Заказ">
                                <Info
                                    :order="order"
                                    :id="id"
                                    @update:order="updateOrder" />
                            </a-tab-pane>
                            <a-tab-pane
                                key="products"
                                tab="Содержимое">
                                <Products
                                    :isLogistic="isLogistic"
                                    :key="productsKey"
                                    ref="orderProducts"
                                    :actionLoading="actionLoading"
                                    :order="order"
                                    :id="id" />
                            </a-tab-pane>
                            <a-tab-pane
                                v-if="order.attachments && order.attachments.length"
                                key="files"
                                tab="Файлы">
                                <Files :order="order" />
                            </a-tab-pane>
                            <a-tab-pane
                                key="comments"
                                tab="Комментарии">
                                <Comments :id="id" @added="getCommentsCount" />
                            </a-tab-pane>
                            <a-tab-pane
                                key="addition"
                                tab="Доп. поля">
                                <PvhWidget
                                    edit
                                    :formView="true"
                                    :order="order" />
                            </a-tab-pane>
                        </a-tabs>
                    </template>
                    <!-- MOBILE -->
                    <template v-else>
                        <div class="order_content_mobile">
                            <Info
                                :order="order"
                                :id="id"
                                @update:order="updateOrder" />
                            <div class="order_collapse_mobile">
                                <a-collapse
                                    :bordered="false"
                                    v-model="expanded" >
                                    <a-collapse-panel
                                        key="products"
                                        header="Содержимое заказа">
                                        <Products
                                            :key="productsKey"
                                            :isLogistic="isLogistic"
                                            ref="orderProducts"
                                            :actionLoading="actionLoading"
                                            :order="order"
                                            :id="id"
                                            :showTitle="false"  />
                                    </a-collapse-panel>
                                    <a-collapse-panel
                                        key="comments"
                                        header="Комментарии">
                                        <Comments
                                            :id="id"
                                            @added="getCommentsCount"
                                            :showTitle="false"  />
                                    </a-collapse-panel>
                                    <a-collapse-panel
                                        key="files"
                                        header="Файлы">
                                        <Files
                                            :order="order"
                                            :showTitle="false" />
                                    </a-collapse-panel>
                                </a-collapse>
                            </div>
                        </div>
                    </template>
                </template>
            </template>
        </div>
        <template v-if="isLogistic && isDelivered || orderActions && orderActions.shipment">
            <div class="drawer_footer">
                <a-spin
                    v-if="actionLoading"
                    size="small" />
                <a-button
                    v-if="orderActions && orderActions.edit"
                    type="primary"
                    :class="!isMobile && 'mr-1'"
                    @click="editOrder()">
                    Редактировать
                </a-button>
                <!--<a-button
                    v-if="orderActions && orderActions.shipment"
                    type="primary"
                    :loading="chipLoading"
                    @click="shipAll">
                    Отгрузить заказ
                </a-button>-->
            </div>

            <a-modal
                v-if="orderActions && orderActions.shipment"
                :zIndex="1500"
                title="Подтверждение оплаты"
                :visible="paymentVisible"
                @cancel="paymentVisible = false">
                <div class="flex justify-between text-base">
                    <span class="font-semibold">К оплате:</span>
                    <span>{{ order.amount }}</span>
                </div>
                <div class="mt-4 flex justify-between text-base">
                    <span class="font-semibold">Способ оплаты:</span>
                    <span>{{ payType }}</span>
                </div>
                <template #footer>
                    <div class="flex">
                        <a-button
                            block
                            size="large"
                            :loading="paymentLoading"
                            type="primary"
                            @click="confirmPayment">
                            Подтвердить оплату
                        </a-button>
                        <a-button
                            block
                            size="large"
                            @click="paymentVisible = false">
                            Отменить
                        </a-button>
                    </div>
                </template>

            </a-modal>
        </template>

    </a-drawer>
</template>

<script>
import { mapState } from 'vuex'
import { priceFormatter } from '@/utils'
import eventBus from '@/utils/eventBus'
export default {
    name: 'OrderDrawer',
    components: {
        Files: () => import('./Files.vue'),
        Products: () => import('./Products.vue'),
        Info: () => import('./Info.vue'),
        Comments: () => import('./Comments.vue'),
        PvhWidget: () => import('./PvhWidget.vue')
    },
    data() {
        return {
            order: {},
            loading: false,
            loadingBtn: false,
            activeItems: true,
            visible: false,
            tabKey: 'order',
            commentsCount: 0,
            productsKey: 1,
            expanded: '',
            isLogistic: false,
            paymentVisible: false,
            paymentLoading: false,
            actionLoading: false,
            chipLoading: false
        }
    },
    computed: {
        ...mapState({
            user: state => state.user.user,
            windowWidth: state => state.windowWidth,
            orderActions: state => state.orders.orderActions
        }),

        drawerWidth() {
            if(this.windowWidth > 1200)
                return 1200
            else
                return this.windowWidth
        },
        id(){
            return this.$route.query.order
        },
        isMobile() {
            return this.$store.state.isMobile
        },
        payType() {
            return this.order?.pay_type?.name
        },
        isDelivered() {
            return this.order?.delivery_status?.code !== 'delivered'
        }
    },
    watch: {
        '$route.name'() {
            this.visible = false
        },
        '$route.query'(val) {
            if(val.order) {
                if(val.logistic)
                    this.isLogistic = true
                this.openOrderDrawer()
            }
        },
        visible(val) {
            if(val) {
                this.getOrder()
                this.getCommentsCount()
            }
        }
    },
    methods: {
        priceFormatter,
        updateOrder(data){
            this.order = data
            this.productsKey++
        },
        editOrder() {
            eventBus.$emit('orderEdit', this.order)
        },
        changeTab(val) {
            this.tabKey = val

            let query = JSON.parse(JSON.stringify(this.$route.query))
            query.otab = val
            this.$router.push({query})
        },
        afterVisibleChange(val) {
            if(!val) {
                this.close()
            } else {
                // this.getOrderPay()
            }
        },
        async getActions() {
            try {
                this.actionLoading = true
                await this.$store.dispatch('orders/getOrderActions', {
                    id: this.order.id
                })
            } catch(e) {
                console.log(e)
            } finally {
                this.actionLoading = false
            }
        },
        async getCommentsCount(){
            let {data} = await this.$http('comments/count/', {params: {related_object: this.id}})
            this.commentsCount = Number(data)
        },
        async getOrder(){
            try{
                this.loading = true

                const {data} = await this.$http(`crm/orders/${this.id}/`)
                if(data) {
                    this.order = data
                    this.getActions()
                }
            }
            catch(e){
                if(e?.detail === 'Страница не найдена.') {
                    this.visible = false
                    this.$message.warning('Такого заказа не существует либо он был удален')
                }
                console.error(e)
            }
            finally{
                this.loading = false
            }
        },

        close() {
            let query = Object.assign({}, this.$route.query)
            if(query.order) {
                if(query.otab)
                    delete query.otab
                delete query.order
                this.$router.push({query})
            }
            this.$store.commit('orders/SET_ORDER_ACTIONS', null)
            this.clear()
        },
        clear(){
            if(this.$refs['orderProducts'])
                this.$refs['orderProducts'].clear()

            this.tabKey = 'order'
            this.order = null
            this.isLogistic = false
        },
        openOrderDrawer() {
            this.visible = true

            const query = JSON.parse(JSON.stringify(this.$route.query))
            if(query.otab)
                this.tabKey = query.otab
        },
        async shipAll() {
            if(this.order?.pay_type.required && this.order.payment_status.code !== 'paid')
                this.paymentVisible = true
            else
                await this.deliveryOrder()
        },
        async confirmPayment() {
            try {
                this.paymentLoading = true
                await this.$http.post(`crm/orders/${this.order.id}/is_paid/`)
                await this.deliveryOrder()
            } catch(error) {
                console.log(error)
                this.$message.error('Что-то пошло не так')
            } finally {
                this.paymentLoading = false
                this.paymentVisible = false
            }
        },
        async deliveryOrder() {
            try {
                this.chipLoading = true
                const { data } = await this.$http.post(`/crm/orders/${this.order.id}/goods/to_delivery/`)
                if(data) {
                    this.order.delivery_status = data.delivery_status
                    this.order.success_date = data.success_date
                    this.$message.info('Заказ успешно отгружен')
                }
            } catch(e) {
                console.log(e)
            } finally {
                this.chipLoading = false
            }
        }
    },
    mounted () {
        eventBus.$on('OPEN_ORDER_RELOAD', () => {
            this.getOrder()
        })
        if(this.$route.query?.order) {
            this.openOrderDrawer()
        }
    },
    beforeDestroy () {
        eventBus.$off('OPEN_ORDER_RELOAD')
    }
}
</script>

<style lang="scss">
.detail_order_drawer{
    .content_tabs{
        height: 100%;
        overflow-x: auto;
        .ant-tabs-bar{
            display: none;
        }
        .ant-tabs-content{
            height: calc(100% - 44px);
        }
        .ant-tabs-tabpane{
            overflow-y: auto;
            padding: 20px;
        }
    }
    .header_tabs{
        .ant-tabs-bar{
            margin: 0px;
            border: 0px;
        }
        .ant-tabs-content{
            display: none;
        }
    }
    .ant-drawer-body{
        padding: 0px;
        height: 100%;
    }
    .ant-drawer-content,
    .ant-drawer-wrapper-body{
        overflow: hidden;
    }
    .drawer_header{
        .ant-skeleton-paragraph{
            display: none;
        }
        .ant-skeleton-title{
            margin-top: 0px;
        }
    }
    .product_list{
        .product_item{
            &:not(:last-child){
                margin-bottom: 15px;
                padding-bottom: 15px;
                border-bottom: 1px solid var(--border2);
            }
        }
    }
}

.detail_mobile_drawer {
    .ant-collapse-header {
        font-weight: 500;
    }
}

.order_content_mobile {
    padding: 15px;
    overflow-y: auto;
    height: calc(var(--vh, 1vh) * 100 - 50px);
}
.order_collapse_mobile {
    margin: 0 -15px;
    .ant-collapse-content-box {
        padding-top: 5px;
        padding: 15px;
    }
}
.order_block{
    &:not(:last-child) {
        margin-bottom: 15px;
    }
    h2{
        margin-bottom: 15px;
        font-weight: 600;
        font-size: 16px;
    }
}
</style>

<style scoped lang="scss">
.detail_order_drawer{
    .header_tabs_wrap{
        padding-left: 20px;
        padding-right: 20px;
        border-bottom: 1px solid var(--border2);
        .header_tabs{
            margin-bottom: -1px;
        }
    }
    .drawer_header{
        height: 50px;
        border-bottom: 1px solid var(--border2);
        padding: 0 10px 0 20px;
        h1{
            font-size: 17px;
            font-weight: 600;
            margin: 0px;
        }
    }
    .drawer_body{
        height: calc(100% - 50px);
        overflow: hidden;
    }
}
.detail_mobile_drawer {
    .drawer_header {
        padding: 0 10px 0 15px;
    }
    .header_tabs_wrap{
        padding-left: 15px;
        padding-right: 15px;
    }
}
.logistic_order_drawer {

    .drawer_header {
        height: 50px;
    }
    .drawer_body {
        height: calc(100% - 100px);
    }
    .drawer_footer {
        height: 50px;
        padding: 0 20px;
        display: flex;
        align-items: center;
        border-top: 1px solid var(--border2);
    }
}
</style>