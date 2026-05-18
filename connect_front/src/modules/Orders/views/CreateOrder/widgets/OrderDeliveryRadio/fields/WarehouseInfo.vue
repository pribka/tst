<template>
    <div class="warehouse_del">
        <h4 v-if="field.name">
            {{ field.name }}
        </h4>
        <div class="warehouse_list">
            <div 
                v-if="loading" 
                class="loader">
                <a-spin size="small" />
            </div>
            <template v-else>
                <div 
                    v-for="item in deliveryWarehouses" 
                    :key="item.id" 
                    class="item">
                    <div class="name">
                        {{ item.name }}
                    </div>
                    <div class="address">
                        {{ item.address }}
                    </div>
                    <div 
                        v-if="item.manager" 
                        class="manager info_item">
                        <div class="label">
                            Ответственное лицо:
                        </div>
                        <div class="val">
                            {{ item.manager.full_name }}
                        </div>
                    </div>
                    <div 
                        v-if="item.phone" 
                        class="phone info_item">
                        <div class="label">
                            Телефон:
                        </div>
                        <div class="val">
                            <a :href="`tel:${item.phone}`">
                                {{ item.phone }}
                            </a>
                        </div>
                    </div>
                </div>
            </template>
        </div>
    </div>
</template>

<script>
import eventBus from '@/utils/eventBus.js'
import { mapState } from 'vuex'

export default {
    props: {
        field: {
            type: Object,
            required: true
        },
        form: {
            type: Object,
            required: true
        },
        edit: {
            type: Boolean,
            default: false
        }
    },
    data() {
        return {
            loading: false
        }
    },
    computed: {
        ...mapState({
            deliveryWarehouses: state => state.orders.deliveryWarehouses
        }),
    },
    created() {
        this.warehouseList()
        eventBus.$on('change_in_goods_list', this.warehouseList)
    },
    beforeDestroy() {
        eventBus.$off('change_in_goods_list')
    },
    methods: {
        async warehouseList() {
            let response = {}
            if(!this.deliveryWarehouses?.length) {
                if(this.form?.delivery_warehouses && this.form?.delivery_warehouses.length) {
                    this.$store.commit('orders/SET_DELIVERY_WAREHOUSES', this.form.delivery_warehouses)
                } else {
                    this.loading = true
                    try {
                        if(this.edit) {
                            const params = {
                                order: this.form.id
                            }
                            response = await this.$http.get('/crm/shopping_cart/order_warehouses/', {params})
                        } else {
                            response = await this.$http.get(this.field.apiPath)
                        }
                    } catch(e) {
                        console.log(e)
                    } finally {
                        this.loading = false
                    }
                    if(response?.data?.length) {
                        this.$store.commit('orders/SET_DELIVERY_WAREHOUSES', response.data)
                    }
                }
            }
        }
    }
}
</script>

<style lang="scss" scoped>
.warehouse_del{
    background: #eff2f5;
    border-radius: var(--borderRadius);
    padding: 20px;
    h4{
        font-weight: 600;
        font-size: 18px;
        margin-bottom: 15px;
        margin-top: 0px;
        line-height: 24px;
    }
    .warehouse_list{
        .info_item{
            &:not(:last-child){
                margin-bottom: 10px;
            }
            .label{
                font-weight: 300;
            }
        }
        .item{
            &:not(:last-child){
                margin-bottom: 10px;
                padding-bottom: 10px;
                border-bottom: 1px solid #e3e3e3;
            }
            .name{
                font-weight: 600;
            }
            .address{
                font-weight: 300;
                &:not(:last-child){
                    margin-bottom: 10px;
                }
            }
        }
    }
}
</style>