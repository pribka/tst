<template>
    <a-card
        hoverable
        class="product_card"
        :class="isMobile && 'product_card_mobile'">
        <div
            class="product-card__wrapper h-full"
            :class="!item.price_by_catalog ?'justify-around': 'justify-between'">
            <div class="image_wrapper">

                <a-tag
                    v-if="item.goods_type"
                    class="product_type"
                    :class="item.goods_type.color"
                    @click="$emit('click')">
                    {{item.goods_type.name}}
                </a-tag>

                <div
                    v-if="!embded && checkReturn"
                    class="back_button"
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

                <div
                    class="image"
                    @click="$emit('click')">
                    <img
                        v-if="item.image"
                        class="product-card__image lazyload"
                        :alt="item.name"
                        :data-src="item.image"/>
                    <img
                        v-else
                        class="product-card__image lazyload"
                        :alt="item.name"
                        :data-src="require('../assets/noimage_product.svg')"/>
                </div>
            </div>
            <div class="pt-2">
                <div class="flex flex-col">
                    <h3
                        class="product-card__title mb-1"
                        @click="$emit('click')">
                        {{item.name}}
                    </h3>
                    <div
                        class="mt-2 mb-3"
                        :class="isMobile && 'flex'">
                        <span
                            class="product-card__article"
                            @click="$emit('click')">
                            {{item.article_number}}
                        </span>
                        <Availability
                            v-if="isMobile"
                            :item="item"/>
                    </div>
                    <div
                        v-if="!isMobile"
                        class="flex justify-between items-center">
                        <ProductPrice :item="item" />
                        <Availability :item="item"/>
                    </div>
                </div>
                <div
                    v-if="!checkStock"
                    class="product-card__actions">
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
                    <div
                        v-if="item.price_by_catalog || !embdedCheckStock"
                        class="product-card__actions"
                        :class="cartMinAdd <= 0 ? 'fill_button' : 'grid'">
                        <div
                            v-if="isMobile"
                            class="flex justify-center items-center">
                            <ProductPrice
                                class="ml-3 mr-3"
                                :item="item" />
                        </div>

                        <!--<div-->
                        <!--class="counter_input flex items-center">-->
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
                            type="primary"
                            :loading="loading"
                            block
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
                            type="primary"
                            :loading="loading"
                            block
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
                        class="product-card__actions">
                        <a-button
                            type="primary"
                            block
                            size="large">
                            Сделать запрос
                        </a-button>
                    </div>
                </template>
            </div>
        </div>
        <component
            :is="warehouseWidget"
            :product="item"
            :visible="visible"
            :handleCancel="handleCancel"
            :warehouseList="warehouseList"
            :addCartWarehouse="addCartWarehouse"
            :loading="loading"
            :count="count"
            :zIndex="wModalZIndex"
            :createEmptyOrder="createEmptyOrder"
            :embded="embded"
            :changeCount="changeCount" />
        <component
            :is="warehouseRWidget"
            :product="item"
            :visible="rVisible"
            :handleCancel="handleReturnCancel"
            :warehouseList="rWarehouseList"
            :addCartWarehouse="addCartRWarehouse"
            :loading="rLoading"
            :zIndex="wModalZIndex"
            :embded="embded"
            :count="count" />
    </a-card>
</template>

<script>
import product from '../mixins/product'
import ProductPrice from './ProductPrice.vue'

export default {
    mixins: [product],
    components: { ProductPrice },
    computed: {
        isMobile() {
            return this.$store.state.isMobile
        }
    }
}
</script>

<style lang="scss">
.product_card{
  border-radius: var(--borderRadius);
  .ant-card-body{
    height: 100%;
  }
  .product-card__actions{
    border-top: 1px solid var(--border2);
    margin-top: 15px;
    .ant-btn-primary{
      font-size: 14px;
      padding-left: 4px;
      padding-right: 4px;
    }
    &:not(.grid){
      .ant-btn-primary{
        border-radius: 0 0 var(--borderRadius) var(--borderRadius);
      }
    }
    &.grid{
      .ant-btn-primary{
        border-radius: 0 0 var(--borderRadius) 0;
      }
    }
    .counter_input{
      .ant-input-number-handler-wrap{
        display: none;
      }
      .ant-input-number{
        border-radius: 0px;
        border: 0px;
        font-size: 14px;
      }
      input{
        text-align: center;
      }
    }
  }
}

.product_card_mobile{
  .product-card__actions{
    .btn{
      &.minus{
        border-radius: 0 !important;
      }
    }
    .ant-btn-icon-only {
      width: 100%;
    }
  }
}
</style>

<style scoped lang="scss">
.product-card__wrapper{
  display: flex;
  flex-direction: column;
  // justify-content: space-between;
}
.back_button{
    font-size: 12px;
    background: #eff2f5;
    border-radius: var(--borderRadius);
    padding: 2px 8px;
    line-height: 20px;
    position: absolute;
    top: 0;
    right: 0;
    z-index: 3;
    i{
        font-size: 10px;
    }
    &:hover{
        color: var(--blue);
    }
}
.product_card{
    .delete_cart{
      display: none;
    }
  .product-card__actions{
    grid-template-columns: repeat(2, minmax(0, 1fr));
    margin-left: -15px;
    margin-right: -15px;
    margin-bottom: -15px;
    .ant-btn{
      &[disabled]{
        border: 0px;
      }
    }
    /*&:hover{
      .delete_cart{
        display: block;
      }
      .in_cart{
        display: none;
      }
    }*/
    .btn{
      height: 40px;
      display: flex;
      align-items: center;
      justify-content: center;
      padding: 0 10px;
      transition: all 0.3s linear;
      -moz-user-select: none;
      -khtml-user-select: none;
      user-select: none;
      transition: all 0.3s cubic-bezier(0.645, 0.045, 0.355, 1);
      &:hover{
        color: var(--blue);
        background: #eff2f5;
      }
      &.plus{
        border-left: 0px;
      }
      &.minus{
        border-radius: 0 0 0 var(--borderRadius);
        border-right: 0px;
      }
      &:hover{
        border-color: var(--blue);
      }
    }
  }
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
  padding-bottom: 80%;
  position: relative;
  flex-grow: 1;
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
}

.product-card__title{
   hyphens: auto;
   font-weight: 400;
    display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  word-break: break-word;
  transition: all 0.3s cubic-bezier(0.645, 0.045, 0.355, 1);
  &:hover{
    opacity: 0.7;
  }
}

</style>

<style lang="scss" scoped>
.product_card{
  .product_type{
    position: absolute;
    top: 0;
    left: 0;
    z-index: 3;
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
}
</style>