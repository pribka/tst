<template>
    <div 
        v-if="historyGoods.length" 
        class="history_product grid">
        <h4>Недавно просмотренные</h4>
        <div class="slider_wrap">
            <swiper :options="swiperOption">
                <swiper-slide 
                    v-for="item in historyGoods" 
                    :key="item.id"
                    class="product_slider">
                    <ProductCard 
                        :item="item" 
                        @click="openDetail(item.id)"  />
                </swiper-slide>
                <swiper-slide class="dym_slide" />
                <div 
                    class="his-button-prev prd_btn" 
                    slot="button-prev">
                    <a-icon type="left" />
                </div>
                <div 
                    class="his-button-next prd_btn" 
                    slot="button-next">
                    <a-icon type="right" />
                </div>
            </swiper>
        </div>
    </div>
</template>

<script>
import { mapState } from 'vuex'
import ProductCard from "./ProductCard"
import { Swiper, SwiperSlide } from "vue-awesome-swiper"
import 'swiper/css/swiper.css'
export default {
    props: {
        openDetail: {
            type: Function,
            default: () => {}
        }
    },
    components: {
        ProductCard,
        Swiper,
        SwiperSlide
    },
    computed: {
        ...mapState({
            historyGoods: state => state.products.historyGoods
        })
    },
    data() {
        return {
            loading: false,
            swiperOption: {
                spaceBetween: 20,
                slidesPerView: 'auto',
                navigation: {
                    nextEl: '.his-button-next',
                    prevEl: '.his-button-prev'
                }
            }
        }
    },
    created() {
        this.getGoodsHistory()
    },
    methods: {
        async getGoodsHistory() {
            try {
                this.loading = true
                await this.$store.dispatch('products/getGoodsHistory')
            } catch(e) {
                console.log(e)
            } finally {
                this.loading = false
            }
        }
    }
}
</script>

<style lang="scss" scoped>
.history_product{
    border-bottom: 1px solid var(--border2);
    padding-bottom: 30px;
    margin-bottom: 30px;
    .slider_wrap{
        overflow: hidden;
        position: relative;
        margin-right: -30px;
        &::after{
            content: "";
            position: absolute;
            right: 0;
            width: 30px;
            z-index: 10;
            top: 0;
            height: 100%;
            /* Permalink - use to edit and share this gradient: https://colorzilla.com/gradient-editor/#ffffff+0,ffffff+100&0+0,0.6+87 */
            background: -moz-linear-gradient(left,  rgba(255,255,255,0) 0%, rgba(255,255,255,0.6) 87%, rgba(255,255,255,0.6) 100%); /* FF3.6-15 */
            background: -webkit-linear-gradient(left,  rgba(255,255,255,0) 0%,rgba(255,255,255,0.6) 87%,rgba(255,255,255,0.6) 100%); /* Chrome10-25,Safari5.1-6 */
            background: linear-gradient(to right,  rgba(255,255,255,0) 0%,rgba(255,255,255,0.6) 87%,rgba(255,255,255,0.6) 100%); /* W3C, IE10+, FF16+, Chrome26+, Opera12+, Safari7+ */
            filter: progid:DXImageTransform.Microsoft.gradient( startColorstr='#00ffffff', endColorstr='#99ffffff',GradientType=1 ); /* IE6-9 */
        }
    }
    h4{
        font-size: 16px;
        margin-bottom: 10px;
        font-weight: 300;
    }
    .product_slider{
        width: 20%;
        @media (max-width: 1665px) {
            width: 22%;
        }
        @media (max-width: 1551px) {
            width: 24%;
        }
        @media (max-width: 1451px) {
            width: 28%;
        }
        @media (max-width: 1351px) {
            width: 32%;
        }
        @media (max-width: 1251px) {
            width: 36%;
        }
        @media (max-width: 1151px) {
            width: 40%;
        }
        @media (max-width: 1051px) {
            width: 50%;
        }
        @media (max-width: 850px) {
            width: 25%;
        }
    }
    .dym_slide{
        width: 20px;
    }
    .prd_btn{
        position: absolute;
        top: 50%;
        width: 40px;
        height: 40px;
        background: rgba(0, 0, 0, 0.3);
        color: #fff;
        z-index: 10;
        font-size: 20px;
        margin-top: -15px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        &:hover{
            background: rgba(0, 0, 0, 0.4);
        }
        &.his-button-prev{
            left: 20px;
        }
        &.his-button-next{
            right: 20px;
        }
        &.swiper-button-disabled{
            display: none;
        }
    }
}
</style>