<template>
    <a-drawer
        :width="drawerWidth"
        :visible="detailVisible"
        :closable="false"
        class="product_drawer"
        :afterVisibleChange="afterVisibleChange"
        :zIndex="1600"
        @close="detailVisible = false">
        <div class="flex justify-between items-baseline"
             :class="isMobile ? 'drawer_head_mobile' : 'drawer_head'">
            <a-skeleton
                v-if="detailLoad"
                active
                :paragraph="{ rows: 1 }" />
            <template v-else>
                <div>
                    <h1
                        v-if="item"
                        class="font-semibold text-base mb-2">
                        {{item.name}}
                    </h1>
                    <Breadcrumps 
                        v-if="item" 
                        :category="item.category[0]" />
                </div>
            </template>
            <a-button
                type="link"
                class="text-current"
                icon="close"
                @click="detailVisible = false" />
        </div>
        <div class="drawer_body">
            <div class="grid gap-9"
                 :class="isMobile ? 'grid-cols-1 detail_prod_mobile' : 'grid-cols-2 detail_prod'">
                <div
                    ref="detailProductLightWrap"
                    class="detail_images"
                    :key="item ? item.id : null">
                    <template v-if="detailLoad">
                        <a-skeleton 
                            active 
                            :paragraph="{ rows: 6 }" />
                    </template>
                    <template>
                        <swiper class="swiper_top swiper_block" :options="swiperOption">
                            <a-spin
                                v-if="imgLoading"
                                class="flex justify-center" />
                            <swiper-slide
                                v-for="(img_item, index) in galeryImages"
                                :key="`${img_item.id}_${index}_top`"
                                v-show="!detailLoad">
                                <a
                                    :href="img_item.path"
                                    class="dp_lgth image_elem"
                                    :data-exthumbimage="img_item.path"
                                    :title="'Артикул ' + (item.article_number ?  item.article_number : 'не указан')">
                                    <div class="image_wrap">
                                        <img
                                            class="swiper-lazy"
                                            :alt="'Артикул ' + (item.article_number ?  item.article_number : 'не указан')"
                                            :src="img_item.path" />
                                    </div>
                                </a>
                            </swiper-slide>
                            <div class="swiper-pagination" slot="pagination"></div>
                            <div
                                class="swiper_btn-next swiper-button-next swiper_btn"
                                slot="button-next">
                                <a-icon type="right" />
                            </div>
                            <div
                                class="swiper_btn-prev swiper-button-prev swiper_btn"
                                slot="button-prev">
                                <a-icon type="left" />
                            </div>
                        </swiper>
                    </template>
                    <div 
                        v-if="!detailLoad && emptyGallery" 
                        class="swiper_block empty_img">
                        <div class="image_elem">
                            <div class="image_wrap">
                                <img
                                    class="lazyload"
                                    alt="Нет изображения"
                                    :data-src="require('./assets/noimage_product.svg')"/>
                            </div>
                        </div>
                    </div>
                </div>
                <div class="detail_info">
                    <template v-if="detailLoad">
                        <a-skeleton 
                            active 
                            :paragraph="{ rows: 6 }" />
                    </template>
                    <template v-else>
                        <template v-if="item">

                            <div 
                                v-if="item.description" 
                                class="text-base desc">
                                {{ item.description }}
                            </div>

                            <a-tag
                                v-if="item && item.goods_type"
                                class="product_type mb-3"
                                :class="item.goods_type.color">
                                {{item.goods_type.name}}
                            </a-tag>

                            <h3 class="font-semibold mb-3">
                                <div>
                                    По прайсу:
                                </div>
                                <span class="text-2xl">
                                    {{ price_by_catalog }} {{item.currency.icon }}
                                </span>
                            </h3>
                            <!--<h3 class="font-light mb-3 " style="color: #999;">-->
                            <!--<div>По прайсу:</div>-->
                            <!--<span class="text-xl">-->
                            <!--{{ price_by_catalog  }} {{item.currency.icon }}-->
                            <!--</span>-->
                            <!--</h3>-->
                            <div class="art mb-2">
                                Артикул: {{item.article_number}}
                            </div>

                            <div class="mb-7 flex">
                                <Availability 
                                    size="default" 
                                    :item="item"/>
                            </div>

                            <div
                                v-if="item.in_cart && !checkStock"
                                class="product-card__actions">
                                <a-button
                                    type="primary"
                                    size="large"
                                    icon="check"
                                    class="in_cart px-14"
                                    @click="detailOpenCart()">
                                    В корзине
                                </a-button>
                            </div>
                            <template v-else>
                                <div 
                                    v-if="item.price_by_catalog" 
                                    class="product-card__actions cart_btns">
                                    <div 
                                        v-if="cartMinAdd > 0" 
                                        class="counter_input flex items-center"
                                        :class="!isMobile || 'counter_input_mobile'">
                                        <div 
                                            class="btn minus" 
                                            @click="minus()">
                                            <a-icon type="minus" />
                                        </div>
                                        <a-input-number
                                            v-if="remnantControl"
                                            v-model="count"
                                            size="large"
                                            style="width: 100%;"
                                            :min="cartMinAdd"
                                            :max="item.available_count"
                                            :formatter="countFormatter"
                                            :default-value="cartMinAdd"
                                            @change="changeInputCount"
                                            @pressEnter="disabledCart ? () => {} : addCartSwitch()" />
                                        <a-input-number
                                            v-else
                                            v-model="count"
                                            size="large"
                                            style="width: 100%;"
                                            :min="cartMinAdd"
                                            :formatter="countFormatter"
                                            :default-value="cartMinAdd"
                                            @change="changeInputCount"
                                            @pressEnter="disabledCart ? () => {} : addCartSwitch()" />
                                        <div 
                                            class="btn plus" 
                                            @click="plus()">
                                            <a-icon type="plus" />
                                        </div>
                                    </div>
                                    <a-button
                                        size="large"
                                        type="primary"
                                        :block="isMobile"
                                        :loading="loading"
                                        class="px-7"
                                        :disabled="disabledCart"
                                        icon="shopping-cart"
                                        @click="addCartSwitch()">
                                        В корзину
                                    </a-button>

                                </div>
                                <div 
                                    v-else 
                                    class="product-card__actions">
                                    <a-button
                                        type="primary"
                                        class="px-14"
                                        size="large">
                                        Сделать запрос
                                    </a-button>
                                </div>
                            </template>

                            <div 
                                v-if="checkReturn" 
                                class="flex">
                                <div 
                                    class="mt-3 back_button" 
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
                        </template>
                    </template>
                </div>

            </div>
            <SimilarProducts 
                v-if="!detailLoad" 
                :id="id" />
        </div>
        <template v-if="item">
            <component
                :is="warehouseWidget"
                :product="item"
                :visible="visible"
                :handleCancel="handleCancel"
                :warehouseList="warehouseList"
                :addCartWarehouse="addCartWarehouse"
                :loading="loading"
                :count="count"
                :changeCount="changeCount"
                :zIndex="1700" />
            <component
                :is="warehouseRWidget"
                :product="item"
                :visible="rVisible"
                :handleCancel="handleReturnCancel"
                :warehouseList="rWarehouseList"
                :addCartWarehouse="addCartRWarehouse"
                :loading="rLoading"
                :count="count"
                :zIndex="1700" />
        </template>
    </a-drawer>
</template>

<script>
import {mapState} from 'vuex'
import 'swiper/css/swiper.css'
import 'lazysizes'
import { Swiper, SwiperSlide } from 'vue-awesome-swiper'
import cart from './mixins/cart.js'
import returnMixins from './mixins/returnMixins.js'
import detail from './mixins/detail.js'
export default {
    mixins: [
        cart,
        detail,
        returnMixins
    ],
    components: {
        Swiper,
        SwiperSlide,
        Breadcrumps: () => import('./components/Breadcrumps.vue'),
        SimilarProducts: () => import('./components/SimilarProducts')
    },
    data() {
        return {
            detailVisible: false,
            imgLoading: false,
            swiperOption: {
                centeredSlides: true,
                lazy: false,
                preloadImages: true,
                pagination: {
                    el: '.swiper-pagination',
                    clickable: true
                },
                navigation: {
                    nextEl: '.swiper-button-next',
                    prevEl: '.swiper-button-prev'
                }
            },
            detailLoad: false,
            galeryImages: [],
            emptyGallery: false,
            index: null
        }
    },
    computed: {
        ...mapState({
            user: state => state.user.user,
            item: state => state.products.detail

        }),
        id(){
            return this.$route.query.viewGoods
        },
        drawerWidth() {
            if(this.windowWidth > 1100)
                return 1100
            else
                return this.windowWidth
        },
        isMobile() {
            return this.$store.state.isMobile
        }
    },
    watch: {
        '$route.query.viewGoods'() {
            if(this.$route.query?.viewGoods)
                this.startView()
        },
        '$route.query'(val) {
            if(!val.viewGoods)
                this.detailVisible = false
        }
    },
    created() {
        if(this.$route.query?.viewGoods)
            this.startView()
    },
    methods: {
        detailOpenCart() {
            this.detailVisible = false
            this.openCart()
        },
        afterVisibleChange(val) {
            if(!val)
                this.clear()
        },
        clear() {
            this.$store.commit('products/SET_DETAIL', null)

            let query = Object.assign({}, this.$route.query)
            if(query['viewGoods']){
                delete query['viewGoods']
                this.$router.replace({query})
            }
            this.galeryImages = []
            this.emptyGallery = false
            this.count = 0
            this.detail = false
        },
        startView() {
            this.detailVisible = true
            this.detail = true
            this.getData()
        },
        async getData() {
            try{
                this.detailLoad= true
                await this.$store.dispatch('products/getDetailGoods', this.id)
                await this.getGallery()
                this.saveHistory()

                setTimeout(() => {
                    this.initLightgallery()
                }, 10)
            }
            catch(e){
                if(e?.detail === 'Страница не найдена.') {
                    this.removeHistory(this.id)
                    this.detailVisible = false
                    this.$message.warning('Такого товара не существует либо он был удален')
                }
                console.error(e)
            }
            finally{
                this.detailLoad = false
            }
        },
        async getGallery() {
            this.imgLoading = true
            try{
                const { data } = await await this.$http(`/gallery/`, {params: {related_object: this.id}})
                if(data?.length) {
                    this.galeryImages = data
                } else {
                    this.emptyGallery = true
                }
            }
            catch(e){
                console.error(e)
            }
            finally {
                this.imgLoading = false
            }
        },
        initLightgallery() {
            if(this.galeryImages?.length) {
                this.$nextTick(() => {
                    const lightboxWrap = this.$refs[`detailProductLightWrap`],
                        lightbox = lightboxWrap.querySelectorAll('.dp_lgth')

                    if(lightbox?.length) {
                        lightGallery(lightboxWrap, {
                            selector: ".dp_lgth",
                            thumbnail: true,
                            animateThumb: true,
                            rotateLeft: true,
                            exThumbImage: "data-exthumbimage",
                            rotateRight: true,
                            flipHorizontal: false,
                            flipVertical: false,
                            fullScreen: true,
                            showThumbByDefault: true,
                            download: false,
                            speed: 300
                        })
                    }
                })
            }
        },
    }
}
</script>

<style lang="scss">
.product_drawer{
    .drawer_head{
        .ant-skeleton-paragraph{
            display: none;
        }
    }
    .ant-drawer-body{
        padding: 0px;
        overflow-y: auto;
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
                max-width: 80px;
                &:hover{
                    border-color: var(--border2);
                }
            }
            input{
                text-align: center;
            }
        }
        .counter_input_mobile{
            width: 100%;
            .ant-input-number{
                max-width: 100%;
            }
        }
    }
}
</style>

<style lang="scss" scoped>
.back_button{
    font-size: 12px;
    background: #eff2f5;
    border-radius: var(--borderRadius);
    padding: 2px 8px;
    line-height: 20px;
    cursor: pointer;
    i{
        font-size: 10px;
    }
    &:hover{
        color: var(--blue);
    }
}
.product_drawer{
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
    .detail_prod{
        padding: 20px 30px;
    }
    .detail_prod_mobile{
        padding: 20px 15px;
    }
    .drawer_head{
        padding: 10px 20px 10px 30px;
        border-bottom: 1px solid var(--border2);
    }
    .drawer_head_mobile{
        padding: 15px;
        border-bottom: 1px solid var(--border2);
    }
    .swiper_block{
        .swiper_preload{
            position: absolute;
            z-index: 10;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .image_elem{
            position: relative;
            display: block;
            width: 100%;
            .image_wrap{
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
                img{
                    object-fit: contain;
                    vertical-align: middle;
                    -o-object-fit: contain;
                    max-height: 80%;
                    transition: opacity 0.15s ease-in-out;
                    &.lazyloaded,
                    &.swiper-lazy-loaded{
                        opacity: 1;
                    }
                }
            }
        }
    }
    .gallery-thumbs{
        .image_wrap{
            border-radius: var(--borderRadius);
        }
        .thumb_slide{
            width: 81px;
            height: 81px;
            border: 1px solid var(--border2);
            border-radius: var(--borderRadius);
            cursor: pointer;
            &.swiper-slide-active{
                border-color: var(--blue);
            }
        }
        .image_elem{
            height: 100%;

        }
    }
    .swiper_btn{
        width: 34px;
        height: 34px;
        border-radius: 50%;
        background: rgba(0, 0, 0, 0.2);
        color: #fff;
        transition: background 0.15s ease-in-out, transform 0.15s ease-in-out;
        &.swiper_btn-next{
            transform: translateX(50px);
        }
        &.swiper_btn-prev{
            transform: translateX(-50px);
        }
        &:hover{
            background: rgba(0, 0, 0, 0.4);
        }
        &::after{
            display: none;
        }
        &.swiper-button-disabled{
            display: none;
        }
    }
    .detail_images{
        .empty_img{
            .image_elem{
                padding-bottom: 80%;
            }
        }
        .swiper_top{

            .image_elem{
                padding-bottom: 80%;
            }
        }
        &:hover{
            .swiper_btn{
                &.swiper_btn-next{
                    transform: translateX(0);
                }
                &.swiper_btn-prev{
                    transform: translateX(0);
                }
            }
        }
    }
    .desc{
        font-weight: 300;
        border-bottom: 1px solid var(--border2);
        padding-bottom: 25px;
        margin-bottom: 25px;
    }
    .product-card__actions{
        .counter_input{
            margin-right: 8px;
        }
        &.cart_btns{
            display: flex;
            align-items: center;
        }
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
            cursor: pointer;
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
}
</style>