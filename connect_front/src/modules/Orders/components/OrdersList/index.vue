<template>
    <div 
        class=" orderslist_table flex-grow flex flex-col"
        :class="isMobile ? 'orderlist_wrapper_mobile' : 'orderlist_wrapper'">
        <h1 v-if="isMobile && pageH1Title" class="m_page_title">
            {{ pageH1Title }}
        </h1>
        <div 
            v-if="!isMobile && showHeader"
            class="flex"
            :class="isMobile && 'filter_row main_filter_header'">
            <a-button
                v-show="addButton"
                size="large"
                :block="isMobile"
                class="mr-2"
                type="primary"
                @click="createOrder()">
                {{ addButton.label ? addButton.label : "Оформить заказ" }}
            </a-button>
            <PageFilter
                class="mb-2"
                :model="model"
                :key="pageName"
                size="large"
                :page_name="pageName"/>

            <component
                :is="settingsButtonWidget"
                class="ml-2"
                :pageName="pageName" />
        </div>
        <keep-alive>
            <component
                :is="viewWidget"
                :filters="filters"
                :params="params"
                :excludeCol="excludeCol"
                :pageName="pageName"/>
        </keep-alive>
        <component
            :is="addOrderDrawer"
            page_name="crm.list_order_page"
            :crmSourceInterestId="crmSourceInterestId"
            :crmCustomerContractId="crmCustomerContractId"
            ref="orderDrawer" />

        <div v-if="isMobile && showHeader" class="float_add">
            <div class="filter_slot">
                <PageFilter
                    class="mb-2"
                    :model="model"
                    :key="pageName"
                    size="large"
                    :page_name="pageName"/>
            </div>
            <a-button 
                v-if="addButton"
                flaticon
                shape="circle"
                size="large"
                type="primary"
                icon="fi-rr-plus"
                @click="createOrder()" />
        </div>
    </div>
</template>

<script>
import PageFilter from '@/components/PageFilter'
import config from '../../mixins/config'
import SettingsButton from '@/components/TableWidgets/SettingsButton'

export default {
    name: "OrderListInit",
    mixins: [
        config,
    ],
    components: {
        SettingsButton,
        PageFilter
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
        showHeader: {
            type: Boolean,
            default: true
        },
        crmSourceInterestId: {
            type: String,
            default: ''
        },
        crmCustomerContractId: {
            type: String,
            default: ''
        },
        excludeCol: {
            type: Array,
            default: () => []
        }
    },
    data(){
        return {
            model: "crm.GoodsOrderModel"
        }
    },
    computed: {
        isMobile() {
            return this.$store.state.isMobile
        },
        viewWidget() {
            if(this.isMobile)
                return () => import(/* webpackMode: "lazy" */'./OrderView/OrderList.vue')
            return () => import(/* webpackMode: "lazy" */'./OrderView/TestOrderTable.vue')
            // return () => import(/* webpackMode: "lazy" */'./OrderView/OrderTable.vue')
        },
        settingsButtonWidget() {
            if(this.isMobile)
                return null
            return () => import(/* webpackMode: "lazy" */'@/components/TableWidgets/SettingsButton')
        },
        addOrderDrawer() {
            return () => import('@apps/Orders/views/CreateOrder/OrderDrawer.vue')
        },
        pageH1Title() {
            return this.$route?.meta?.title ? this.$route.meta.title : null
        }
    },
    methods: {
        createOrder(attempt = 0) {
            this.$nextTick(() => {
                if(this.$refs['orderDrawer']) {
                    this.$refs['orderDrawer'].toggleDrawer()
                    return
                }
                if(attempt < 80) {
                    window.setTimeout(() => this.createOrder(attempt + 1), 150)
                }
            })
        }
    }
}
</script>

<style lang="scss" >
.orderlist_wrapper{
  padding: 20px 30px;

    .item_name{
        display: -webkit-box;
        -webkit-line-clamp: 2;
        -webkit-box-orient: vertical;
        overflow: hidden;
        text-overflow: ellipsis;
        transition: color 0.3s;
        word-break: break-word;
        cursor: pointer;
        &:hover{
            color: var(--primaryColor);
        }
        &.completed{
            color: var(--grayColor2);
            text-decoration: line-through;
        }
    }
}
.orderlist_wrapper_mobile {
      padding: 15px;
}
.orderlist_header_mobile {
    margin-top: -15px;
    padding-top: 15px;
    padding-bottom: 15px;
    
    top: var(--headerHeight);
    background-color: var(--eBg);
}
</style>
