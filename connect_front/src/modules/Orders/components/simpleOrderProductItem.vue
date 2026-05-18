<template>
    <div
        :class="widgetData.nds_column ? 'grid-cols-[40px,1fr,120px,120px,100px,120px]' : 'grid-cols-[40px,1fr,120px,120px,120px]'"
        class="warehouse_select order_p_item table_row grid">
        <div class="table_data_cell flex items-center justify-center">
            <div class="flex flex-col items-center justify-center">
                {{itemNumber}}
            </div>
        </div>
        <div class="table_data_cell flex items-start">
            <div class="cart_info w-full">
                <div class="w-full">
                    <h3>
                        {{ goods.name }}
                    </h3>
                    <span
                        v-if="goods.article_number"
                        class="custom_article">
                        АРТ.{{ goods.article_number }}
                    </span>
                </div>
            </div>
        </div>
        <div class="table_data_cell price flex items-center justify-center">
            <template>
                {{ price }} {{ goods.currency.icon }}
            </template>
        </div>
        <div class="table_data_cell count flex items-center justify-center">
            <template>
                {{ quantity }}
            </template>
        </div>
        <div
            v-if="widgetData.nds_column"
            class="table_data_cell count flex items-center justify-center">
            {{ item.amount_nds }}
        </div>
        <div class="table_data_cell price_end flex items-center justify-center font-semibold flex-wrap content-center">
            <template>
                {{ quantityItems }}
            </template>
        </div>
    </div>
</template>

<script>
let time;
import { priceFormatter } from '@/utils'
export default {
    props: {
        itemNumber: {
            type: Number,
            default: null
        },
        item: {
            type: Object,
            required: true
        },
        widgetData: {
            type: Object,
            required: true
        },
    },
    computed: {
        goods() {
            return this.item.goods
        },
        price() {
            if(this.item.custom_price)
                return priceFormatter(this.item.custom_price)
            else
                return priceFormatter(this.goods.price)
        },
        quantityItems() {
            if(this.item.custom_price)
                return priceFormatter(this.item.custom_price * this.item.quantity)
            else
                return priceFormatter(this.goods.price * this.item.quantity)
        },
        quantity() {
            return Number(this.item.quantity).toFixed(3)
        }
    },
    data() {
        return {
        }
    },
    created() {
    },
    methods: {
    }
}
</script>

<style lang="scss" scoped>
.order_p_item{
    h3{
        font-size: 14px;
        transition: all 0.3s color;
        line-height: 20px;
        padding-right: 10px;
        word-break: break-word;
        -webkit-hyphens: auto;
        -ms-hyphens: auto;
        hyphens: auto;
        font-weight: 400;
        display: -webkit-box;
        -webkit-line-clamp: 2;
        -webkit-box-orient: vertical;
        overflow: hidden;
    }
    .price_end{
        font-weight: 600;
    }
}

.table_data_cell {
    padding: 5px 5px;

    &:not(:last-child) {
        border-right: 1px solid var(--border2);
    }
}
.table_row {
    &:not(:last-child) {
        border-bottom: 1px solid var(--border2);
    }
}
</style>

<style>
.table_data_cell .count_input .ant-input-number {
    flex-grow: 1;
    max-width: max-content;
}
</style>