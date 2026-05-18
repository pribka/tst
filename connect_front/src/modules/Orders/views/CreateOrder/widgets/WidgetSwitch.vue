<template>
    <div class="order_block"
         :class="!isMobile || 'order_block_mobile'"
         :data-guide-id="guideId">
        <div class="label">
            <i 
                class="fi icon" 
                :class="[item.icon, item.title && 'mr-2']"></i>
            {{ item.title }}
        </div>
        <component 
            ref="widgetSwitch"
            :is="widget"
            :form="form"
            :reload="reload"
            :amount="amount"
            :edit="edit"
            :setOrderLoader="setOrderLoader"
            :getFormRef="getFormRef"
            :reloadAmount="reloadAmount"
            :injectContractorFilter="injectContractorFilter"
            :sourceCustomerContractId="sourceCustomerContractId"
            :changeContract="changeContract"
            :setOrderFormCalculated="setOrderFormCalculated"
            :item="item"
            :payDatePlanRequired="payDatePlanRequired"
            :isOrderDrawer="isOrderDrawer"
            :createEmptyOrder="createEmptyOrder"/>
    </div>
</template>

<script>
export default {
    props: {
        isOrderDrawer: {
            type: Boolean,
            default: false
        },
        item: {
            type: Object,
            required: true
        },
        form: {
            type: Object,
            required: true
        },
        changeContract: {
            type: Function,
            default: () => {}
        },
        setOrderFormCalculated: {
            type: Function,
            default: () => {}
        },
        reload: {
            type: Boolean,
            default: false
        },
        reloadAmount: {
            type: Function,
            default: () => {}
        },
        amount: {
            type: [String, Number],
            required: true
        },
        getFormRef: {
            type: Function,
            default: () => {}
        },
        edit: {
            type: Boolean,
            default: false
        },
        setOrderLoader: {
            type: Function,
            default: () => {}
        },
        payDatePlanRequired: {
            type: Boolean,
            default: false
        },
        createEmptyOrder: {
            type: Boolean,
            default: false
        },
        injectContractorFilter: {
            type: Object,
            default: () => {}
        },
        sourceCustomerContractId: {
            type: String,
            default: ''
        }
    },
    computed: {
        widget() {
            return () => import(`./${this.item.widget}`)
                .then(module => {
                    return module
                })
                .catch(e => {
                    console.log('error')
                    return import(`./NotWidget.vue`)
                })
        },
        isMobile() {
            return this.$store.state.isMobile
        },
        guideId() {
            if (this.item.widget === 'OrderType') {
                return 'crm-order-customer'
            }
            if (this.item.widget === 'OrderCart') {
                return 'crm-order-cart'
            }
            return null
        }
    }
}
</script>

<style lang="scss" scoped>
.order_block{
    border: 1px solid var(--border2);
    position: relative;
    padding: 30px;
    border-radius: var(--borderRadius);
    .label{
        font-weight: 600;
        font-size: 15px;
        background: #fff;
        padding: 0 10px;
        position: absolute;
        top: 0;
        left: 20px;
        z-index: 1;
        line-height: 18px;
        margin-top: -9px;
        color: #000;
        display: flex;
        align-items: center;
        .icon{
            color: var(--blue);
        }
    }
    &:not(:last-child){
        margin-bottom: 30px;
    }
}
.order_block_mobile {
    padding: 0px;
    padding-top: 15px;

    border: none;
    .label{
        left: 0;

        padding: 0;

        background-color: transparent;
    }
}
</style>
