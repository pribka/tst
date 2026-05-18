<template>
    <div>
        <span
            v-if="!item.price_by_catalog"
            class="product-card__price"
            @click="$emit('click')">
            Цена по запросу
        </span>
        <div v-else class="flex items-start flex-col">
            <a-tooltip title="Цена по прайсу">
                <span
                    class="product-card__price "
                    @click="$emit('click')">
                    {{ price_by_catalog }} {{ item.currency.icon }}
                </span>
            </a-tooltip>

            <!--<a-tooltip title="Цена по прайсу">-->
            <!--<span-->
            <!--class="product-card__price_catalog"-->
            <!--@click="$emit('click')">-->
            <!--{{ price_by_catalog }} {{ item.currency.icon }}-->
            <!--</span>-->
            <!--</a-tooltip>-->

        </div>
    </div>
</template>

<script>
import product from '../mixins/product'
export default {
    mixins: [product],
    props: {
        item: Object,
    }
}
</script>

<style lang="scss" scoped>
.product-card__price{
  font-size: 17px;
  font-weight: 600;

}
.product-card__price_catalog{
    font-size: 15px;
  font-weight: 300;
 color: #999;
}
</style>>

