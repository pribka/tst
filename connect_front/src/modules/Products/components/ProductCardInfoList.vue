<template>
    <a-card
        hoverable
        class="product_card_list"
        :class="!isMobile || 'product_card_list_mobile'">
        <div class="justify-between items-center"
             :class="isMobile || 'product-card__wrapper'" >
            <div class="flex pr-2">
                <div>
                    <div class="flex flex-col">
                        <h3
                            @click="$emit('click')"
                            class="product-card__title mb-1">
                            {{item.name}}
                        </h3>
                        <div class="flex items-center">
                            <span
                                @click="$emit('click')"
                                class="product-card__article">
                                {{item.article_number}}
                            </span>
                            <template v-if="isMobile">
                                <div class="flex ">
                                    <Availability
                                        :item="item"
                                        class="ml-2"
                                        @click="$emit('click')" />
                                    <div
                                        v-if="item.goods_type"
                                        @click="$emit('click')"
                                        class="flex">
                                        <a-tag
                                            class="product_type"
                                            :class="item.goods_type.color">
                                            {{item.goods_type.name}}
                                        </a-tag>
                                    </div>
                                </div>
                            </template>

                        </div>
                        <div
                            v-if="!isMobile"
                            class="flex items-center mt-2 flex-wrap">
                            <span
                                v-if="!item.price_by_catalog"
                                class="product-card__price">
                                Цена по запросу
                            </span>

                            <div
                                v-else
                                class="flex flex-col">
                                <template v-if="priceEdit">
                                    <component 
                                        :is="priceWidget" 
                                        :item="item" />
                                </template>
                                <a-tooltip 
                                    v-else 
                                    title="Цена по прайсу">
                                    <span
                                        class="product-card__price "
                                        @click="$emit('click')">
                                        {{ price_by_catalog }} {{ item.currency.icon }}
                                    </span>
                                </a-tooltip>

                                <!--<a-tooltip title="Цена по прайсу">-->
                                <!--<span -->
                                <!--class="product-card__price_catalog"-->
                                <!--@click="$emit('click')">-->
                                <!--{{ price_by_catalog }} {{ item.currency.icon }}-->
                                <!--</span>-->
                                <!--</a-tooltip>-->

                            </div>
                            <Availability
                                :item="item"
                                class="ml-3 xl:ml-5 2xl:ml-7" />

                            <div
                                v-if="item.goods_type"
                                class="flex ml-2"
                                @click="$emit('click')">
                                <a-tag
                                    class="product_type"
                                    :class="item.goods_type.color">
                                    {{item.goods_type.name}}
                                </a-tag>
                            </div>

                            <div
                                v-if="!embded && checkReturn"
                                class="ml-3 back_button"
                                @click="addReturnCartSwitch()">
                                <a-spin
                                    :spinning="rLoading"
                                    size="small">
                                    <span class="flex items-center">
                                        <i class="fi fi-rr-box mr-1"></i>
                                        Возврат
                                    </span>
                                </a-spin>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <div
                v-if="!checkStock"
                class="product-card__actions"
                :class="isMobile && 'mt-2'">
                <a-button
                    v-if="embded"
                    type="primary"
                    block
                    disabled
                    size="large"
                    icon="check"
                    class="in_cart">
                    Добавлено
                </a-button>
                <a-button
                    v-else
                    type="primary"
                    block
                    size="large"
                    icon="check"
                    class="in_cart"
                    @click="openCart()">
                    В корзине
                </a-button>
            </div>
            <template v-else>
                <div>
                    <div
                        v-if="item.price_by_catalog || !embdedCheckStock"
                        class="product-card__actions flex items-center mt-2"
                        :class="isMobile && 'justify-center'">
                        <template v-if="isMobile">
                            <div class="mr-2">
                                <span
                                    v-if="!item.price_by_catalog"
                                    class="product-card__price">
                                    Цена по запросу
                                </span>

                                <div
                                    v-else
                                    class="flex flex-col">
                                    <a-tooltip title="Цена по прайсу">
                                        <span
                                            class="product-card__price "
                                            @click="$emit('click')">
                                            {{ price_by_catalog }} {{ item.currency.icon }}
                                        </span>
                                    </a-tooltip>

                                </div>
                            </div>
                        </template>
                        <!--<div -->
                        <!--class="counter_input flex items-center mr-2">-->
                        <!--<div-->
                        <!--class="btn minus"-->
                        <!--@click="minus()">-->
                        <!--<a-icon type="minus" />-->
                        <!--</div>-->
                        <!--<a-input-number-->
                        <!--v-if="remnantControl"-->
                        <!--v-model="count"-->
                        <!--size="large"-->
                        <!--style="width: 100%;"-->
                        <!--:min="cartMinAdd"-->
                        <!--:max="item.available_count"-->
                        <!--:formatter="countFormatter"-->
                        <!--:default-value="cartMinAdd"-->
                        <!--@change="changeInputCount"-->
                        <!--@pressEnter="disabledCart ? () => {} : addCartSwitch()" />-->
                        <!--<a-input-number-->
                        <!--v-else-->
                        <!--v-model="count"-->
                        <!--size="large"-->
                        <!--style="width: 100%;"-->
                        <!--:min="cartMinAdd"-->
                        <!--:formatter="countFormatter"-->
                        <!--:default-value="cartMinAdd"-->
                        <!--@change="changeInputCount"-->
                        <!--@pressEnter="disabledCart ? () => {} : addCartSwitch()" />-->
                        <!--<div-->
                        <!--class="btn plus"-->
                        <!--@click="plus()">-->
                        <!--<a-icon type="plus" />-->
                        <!--</div>-->
                        <!--</div>-->
                        <a-button
                            v-if="embded"
                            size="large"
                            :block="isMobile"
                            :loading="loading"
                            :style="isMobile && 'min-width: 50px'"
                            type="primary"
                            :disabled="disabledCart"
                            icon="plus"
                            @click="addCartSwitch()">
                            <template v-if="!isMobile">
                                {{ addText }}
                            </template>
                        </a-button>
                        <a-button
                            v-else
                            size="large"
                            :block="isMobile"
                            :loading="loading"
                            :style="isMobile && 'min-width: 50px'"
                            type="primary"
                            :disabled="disabledCart"
                            icon="shopping-cart"
                            @click="addCartSwitch()">
                            <template v-if="!isMobile">
                                В корзину
                            </template>
                        </a-button>
                    </div>
                    <div
                        v-else
                        class="product-card__actions"
                        :class="isMobile && 'mt-2'">
                        <a-button
                            type="primary"
                            block
                            size="large">
                            Сделать запрос
                        </a-button>
                    </div>
                </div>
            </template>
        </div>
        <component
            :is="warehouseWidget"
            :product="item"
            :visible="visible"
            :handleCancel="handleCancel"
            :zIndex="wModalZIndex"
            :warehouseList="warehouseList"
            :addCartWarehouse="addCartWarehouse"
            :loading="loading"
            :createEmptyOrder="createEmptyOrder"
            :count="count"
            :embded="embded"
            :changeCount="changeCount" />
        <component
            :is="warehouseRWidget"
            :product="item"
            :visible="rVisible"
            :zIndex="wModalZIndex"
            :handleCancel="handleReturnCancel"
            :warehouseList="rWarehouseList"
            :addCartWarehouse="addCartRWarehouse"
            :loading="rLoading"
            :embded="embded"
            :count="count" />
    </a-card>
</template>
<script>
import product from '../mixins/product'
export default {
    mixins: [product],
    computed: {
        isMobile() {
            return this.$store.state.isMobile
        }
    }
}
</script>

<style lang="scss">
.product_card_list{
  border-radius: var(--borderRadius);
    .ant-card-body{
        height: 100%;
    }
    .product-card__actions{
        .ant-btn-primary{
            font-size: 14px;
        }
        .counter_input{
            .ant-input-number-handler-wrap{
                display: none;
            }
            .ant-input-number{
                border-radius: 0px;
                border-left: 0px;
                border-right: 0px;
                font-size: 14px;
                max-width: 60px;
                &:hover{
                    border-color: var(--border2);
                }
            }
            input{
                text-align: center;
                min-width: 60px;
            }
        }
    }
}
.product_card_list_mobile {
    .product-card__actions {
        justify-content: end;
        .counter_input{
            width: 100%;
            max-width: 140px;
            .ant-input-number {
                max-width: 100%;
            }
        }
    }
}
</style>

<style scoped lang="scss">
.product_type{
    border: 0px;
    &.geekblue{
      color: #1d39c4;
      background: #f0f5ff;
    }
    &.purple{
      color: #531dab;
      background: #f9f0ff;
    }
    &.magenta{
      color: #c41d7f;
      background: #fff0f6;
    }
}
.back_button{
    font-size: 12px;
    background: #eff2f5;
    border-radius: var(--borderRadius);
    padding: 2px 8px;
    line-height: 20px;
    i{
        font-size: 10px;
    }
    &:hover{
        color: var(--blue);
    }
}
.product-card__actions{
    .btn{
        height: 40px;
        display: flex;
        align-items: center;
        justify-content: center;
        padding: 0 6px;
        transition: all 0.3s linear;
        -moz-user-select: none;
        -khtml-user-select: none;
        user-select: none;
        transition: all 0.3s cubic-bezier(0.645, 0.045, 0.355, 1);
        border: 1px solid #e1e7ec;
        &:hover{
            color: var(--blue);
            background: #eff2f5;
        }
        &.plus{
            border-left: 0px;
            border-radius: 0 var(--borderRadius) var(--borderRadius) 0;
        }
        &.minus{
            border-radius: var(--borderRadius) 0 0 var(--borderRadius);
            border-right: 0px;
        }
    }
}
.product_card_list{
    .product-card__wrapper{
        display: flex;
    }
}
.product-card__price{
    font-size: 17px;
    font-weight: 600;
    @media (max-width: 1386px) {
        font-size: 14px;
    }
}
.product-card__price_catalog{
    font-size: 15px;
  font-weight: 300;
 color: #999;
}
.product-card__image{
  object-fit: contain;
  vertical-align: middle;
  -o-object-fit: contain;
  opacity: 0;
  transition: opacity .15s ease-in-out;
  max-height: 100%;
  &.lazyloaded{
    opacity: 1;
  }
}
.image_wrapper{
  position: relative;
  height: 70px;
  width: 70px;
  @media (max-width: 1386px) {
    height: 50px;
    width: 50px;
  }
  .image{
    margin: 0;
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    overflow: hidden;
    display: flex;
    align-items: center;
    justify-content: center;
  }
}
.product-card__article{
  font-size: 13px;
  font-weight: 300;
  @media (max-width: 1386px) {
    font-size: 11px;
  }
}

.product-card__title{
   font-weight: 400;
    word-break: break-word;
    transition: all 0.3s cubic-bezier(0.645, 0.045, 0.355, 1);
    &:hover{
        opacity: 0.7;
    }
}

</style>