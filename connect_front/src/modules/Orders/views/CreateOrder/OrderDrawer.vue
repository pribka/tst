<template>
    <a-drawer
        placement="right"
        :zIndex="1001"
        class="order_drawer"
        :width="widthDrawer"
        :visible="visible"
        :destroyOnClose = "true"
        @close="closeDrawer()">
        <CreateOrder
            :injectContractor="injectContractor"
            :closeDrawer="closeDrawer"
            :injectContractorFilter="injectContractorFilter"
            :crmSourceInterestId="crmSourceInterestId"
            :crmCustomerContractId="crmCustomerContractId"
            :isOrderDrawer=true />
    </a-drawer>
</template>

<script>
import eventBus from '@/utils/eventBus.js'
import { mapState } from 'vuex'
export default {
    props: {
        contractorID: {
            type: String,
            default: ''
        },
        contrsctorDeliveryPoint: {
            type: String,
            default: ''
        },
        injectContractor: {
            type: Object,
            default: () => {}
        },
        addProduct: {
            type: Function,
            default: () => {}
        },
        injectGoods: {
            type: Object,
            default: () => null
        },
        embdedCheckStock: {
            type: Boolean,
            default: true
        },
        page_name: {
            type: String,
            default: "crm.order_create_drawer_page"
        },
        addText: {
            type: String,
            default: "Добавить"
        },
        createEmptyOrder: {
            type: Boolean,
            default: false
        },
        crmSourceInterestId: {
            type: String,
            default: ''
        },
        crmCustomerContractId: {
            type: String,
            default: ''
        },
        injectContractorFilter: {
            type: Object,
            default: () => {}
        }
    },
    components: {
        CreateOrder: () => import('@apps/Orders/views/CreateOrder/index.vue')
    },
    computed: {
        ...mapState({
            windowWidth: state => state.windowWidth
        }),
        widthDrawer() {
            if(this.windowWidth > 1200)
                return this.windowWidth - 250
            else
                return this.windowWidth
        },
    },
    data() {
        return {
            visible: false
        }
    },
    methods: {
        toggleDrawer() {
            this.visible = !this.visible
        },
        closeDrawer() {
            this.toggleDrawer()
            this.$store.commit('orders/SET_ORDER_ACTIONS', null)
            if(this.page_name === 'crm.list_order_page')
                eventBus.$emit('update_order_list')
        }
    }
}
</script>

<style lang="scss">
.order_drawer{
    .ant-drawer-body,
    .ant-drawer-wrapper-body{
        overflow-y: auto;
    }
    .ant-drawer-body{
        height: calc(100% - 40px);
        padding: 0px;
    }
}
</style>
