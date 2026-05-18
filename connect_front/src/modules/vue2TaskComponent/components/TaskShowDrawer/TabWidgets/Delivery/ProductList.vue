<template>
    <div class="product_list">
        <div 
            v-for="item in productList" 
            :key="item.id" 
            class="product_list_card">
            <div class="name break-words">
                {{ item.name }}
            </div>
            <div class="product_info">
                <div 
                    v-if="item.contractor" 
                    class="item">
                    <div>
                        {{$t('task.delivery.client')}}: {{ item.contractor.name }}
                    </div>
                    <div 
                        v-if="item.contractor.phone" 
                        class="flex items-center">
                        <i class="fi fi-rr-phone-call mr-2"></i>
                        <a :href="`tel:${item.contractor.phone}`">
                            {{ item.contractor.phone }}
                        </a>
                    </div>
                    <div 
                        v-if="item.contractor.email" 
                        class="flex items-center">
                        <i class="fi fi-rr-envelope mr-2"></i>
                        <a :href="`mailto:${item.contractor.email}`">
                            {{ item.contractor.email }}
                        </a>
                    </div>
                </div>
                <div 
                    v-if="item.delivery_point" 
                    class="item">
                    {{$t('task.delivery.address')}}: {{ item.delivery_point.name }}
                </div>
                <div class="item">
                    {{$t('task.count')}}: {{ item.quantity }} {{ item.measure_unit_name_short && item.measure_unit_name_short  }}
                </div>

                <div 
                    v-if="item.warehouses && item.warehouses.length" 
                    class="item">
                    {{ $t('task.loaded') }}:
                    <div v-for="loaded in item.warehouses" :key="loaded.id" class="mt-1">
                        {{ loaded.name }}: {{ loaded.quantity_loaded }} {{ loaded.measure_unit_name_short && loaded.measure_unit_name_short  }}
                    </div>
                </div>

                <div 
                    v-if="item.quantity_success" 
                    class="item">
                    {{ $t('task.shipped') }}: {{ item.quantity_success }} {{ item.measure_unit_name_short && item.measure_unit_name_short  }}
                </div>

                <div class="item">
                    {{ $t('task.cost') }}: {{ price(item.amount) }}
                </div>
                <div class="item flex items-center">
                    <template v-if="item.quantity_success && Number(item.quantity_success) > 0">
                        <template v-if="(item.attachments && item.attachments.length) || (item.comment && item.comment.length)">
                            <a-button
                                class="flex items-center justify-center"
                                block
                                @click="openInfo(item)">
                                <i class="fi fi-rr-info mr-1"></i>
                                {{ $t('task.information') }}
                            </a-button>
                        </template>
                    </template>
                    <template v-else>
                        <template v-if="activeKey !== 'default' && isOperator">
                            <a-button
                                class="flex items-center justify-center"
                                block
                                ghost
                                type="primary"
                                :loading="fullLoading && fullLoading[item.id]"
                                @click="fullShipment(item)">
                                {{ $t('task.full_shipment') }}
                            </a-button>
                            <a-button
                                class="flex items-center ml-1 justify-center"
                                block
                                ghost
                                type="danger"
                                @click="incompleteModal(item)">
                                {{ $t('task.incomplete_shipment') }}
                            </a-button>
                        </template>
                    </template>
                </div>
            </div>
        </div>
        <ProductModal 
            :visibleInfo="visibleInfo"
            :afterCloseInfo="afterCloseInfo"
            :infoData="infoData"
            :closeInfoModal="closeInfoModal"
            :visible="visible"
            :incomplete="incomplete"
            :afterClose="afterClose"
            :closeFormModal="closeFormModal"
            :updateProductList="updateProductList" />
    </div>
</template>

<script>
import mixins from './mixins'
import ProductModal from './ProductModal.vue'
export default {
    mixins: [mixins],
    components: {
        ProductModal
    },
    props: {
        task: {
            type: Object,
            required: true
        },
        activeKey: {
            type: [String, Number],
            default: 'default'
        },
        productList: {
            type: Array,
            default: () => []
        },
        isOperator: {
            type: Boolean,
            default: false
        }
    }
}
</script>

<style lang="scss" scoped>
.product_list_card{
    border: 1px solid var(--borderColor);
    padding: 12px;
    &:not(:last-child){
        margin-bottom: 10px;
    }
    .name{
        font-weight: 600;
        margin-bottom: 8px;
        border-bottom: 1px solid var(--borderColor);
        padding-bottom: 8px;
    }
    .product_info{
        .item{
            &:not(:last-child){
                margin-bottom: 6px;
            }
        }
    }
}   
</style>