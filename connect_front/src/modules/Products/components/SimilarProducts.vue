<template>
    <div 
        v-if="allData && allData.length && id" 
        class="simular_products"> 
        <h3 class="block_label font-semibold text-lg mb-2">
            Похожие товары
        </h3>
        <div
            v-if="loading"
            class="grid gap-5 grid-cols-4 pl-5">
            <a-skeleton active />
            <a-skeleton active />
            <a-skeleton active />
            <a-skeleton active />
        </div>
        <swiper 
            v-else
            :options="swiperOption">
            <swiper-slide 
                v-for="item in allData" 
                :key="item.id"
                class="product_slider">
                <ProductCard 
                    :item="item" 
                    @click="openDetail(item.id)" />
            </swiper-slide>
            <swiper-slide class="dym_slide" />
            <div 
                class="prd-button-prev prd_btn" 
                slot="button-prev">
                <a-icon type="left" />
            </div>
            <div 
                class="prd-button-next prd_btn" 
                slot="button-next">
                <a-icon type="right" />
            </div>
        </swiper>
    </div>
</template>

<script>
import ProductCard from "./ProductCard"
import { Swiper, SwiperSlide } from "vue-awesome-swiper"
import 'swiper/css/swiper.css'
export default {
    components: {
        ProductCard,
        Swiper,
        SwiperSlide
    },
    props: {
        id: {
            type: [Number, String],
            default: () => null
        }
    },
    data(){
        return{
            loading: false,
            allData: [],
            swiperOption: {
                spaceBetween: 20,
                slidesPerView: 'auto',
                navigation: {
                    nextEl: '.prd-button-next',
                    prevEl: '.prd-button-prev'
                }
            }
        }
    },
    computed: {
        isMobile() {
            return this.$store.state.isMobile
        }
    },
    created(){
        this.getGoods()
    },
    methods: {
        async getGoods(){
            try {
                this.loading = true
                const { data } = await this.$http.get(`catalogs/goods/${this.id}/by_category/`)
                this.allData = data
            } catch(e) {
                console.log(e)
            } finally {
                this.loading = false
            }
        },
        openDetail(id){
            let query = Object.assign({}, this.$route.query)

            query.viewGoods = id
            this.$router.push({query})
        }
    }
}
</script>

<style lang="scss">
.simular_products{
    padding-bottom: 30px;
    .swiper-wrapper{
        padding-left: 20px;
    }
    .block_label{
        padding: 0 20px;
    }
    .product_slider{
        width: 25%;
        @media (max-width: 780px) {
            width: 40%;
        }
        @media (max-width: 700px) {
            width: 50%;
        }
        @media (max-width: 450px) {
            width: 70%;
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
        &.prd-button-prev{
            left: 20px;
        }
        &.prd-button-next{
            right: 20px;
        }
        &.swiper-button-disabled{
            display: none;
        }
    }
}
</style>