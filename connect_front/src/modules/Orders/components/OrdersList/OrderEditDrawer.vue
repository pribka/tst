<template>
    <a-drawer
        :width="widthDrawer"
        class="order_edit_drawer"
        :visible="visible"
        :closable="false"
        destroyOnClose
        :zIndex="1050"
        :afterVisibleChange="afterVisibleChange"
        @close="closeDrawer()">
        <div class="drawer_header flex justify-between items-center">
            <span class="text-base font-semibold truncate">
                Редактировать заказ {{ orderCounter }}
            </span>
            <a-button 
                icon="close" 
                class="text_current"
                type="link"
                @click="visible = false" />
        </div>
        <div class="drawer_body">
            <div 
                v-if="loading" 
                class="flex justify-center pt-4">
                <a-spin />
            </div>
            <CreateOrder 
                v-if="injectOrder"
                :closeDrawer="closeDrawer"
                edit
                :injectOrder="injectOrder" />
        </div>
    </a-drawer>
</template>

<script>
import eventBus from '@/utils/eventBus'
import { mapState } from 'vuex'
export default {
    components: {
        CreateOrder: () => import('../../views/CreateOrder')
    },
    computed: {
        ...mapState({
            windowWidth: state => state.windowWidth
        }),
        widthDrawer() {
            if(this.windowWidth > 1200)
                return 1200
            else
                return this.windowWidth
        },
        orderCounter() {
            return this.injectOrder?.counter ? this.injectOrder.counter : ''
        },
    },
    data() {
        return {
            visible: false,
            injectOrder: null,
            loading: false
        }
    },
    methods: {
        closeDrawer() {
            this.visible = false
            this.$store.commit('orders/SET_ORDER_ACTIONS', null)
        },
        async getOrder(order) {
            try {
                this.loading = true
                const { data } = await this.$http.get(`/crm/orders/${order.id}/`)
                if(data) {
                    this.injectOrder = data
                }
            } catch(e) {
                console.log(e)
                this.$message.error('Ошибка')
            } finally {
                this.loading = false
            }
        },
        afterVisibleChange(vis) {
            if(!vis) {
                this.injectOrder = null
                this.$store.commit('orders/CLEAR_CREATE_ORDERS')
                this.$store.commit('orders/CLEAR_ORDER_DISPLAY_LIST')
                this.$store.commit('orders/RESET_DELIVERY_WAREHOUSES')
            }
        }
    },
    mounted() {
        eventBus.$on('orderEdit', order => {
            this.getOrder(order)
            this.visible = true
        })
    },
    beforeDestroy() {
        eventBus.$off('orderEdit')
    }
}
</script>

<style lang="scss">
.order_edit_drawer{
    .ant-drawer-content,
    .ant-drawer-wrapper-body{
        overflow: hidden;
    }
    .ant-drawer-body{
        padding: 0px;
        height: 100%;
        overflow: hidden;
    }
}
</style>

<style lang="scss" scoped>
.order_edit_drawer{
    .drawer_header{
        border-bottom: 1px solid var(--border2);
        padding-left: 15px;
        padding-right: 15px;
        height: 40px;
    }
    .drawer_body{
        height: calc(100% - 40px);
        overflow-y: auto;
    }
}
</style>