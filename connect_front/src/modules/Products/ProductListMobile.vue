<template>
    <div class="products" :class="webview && 'no_padding'">
        <div class="search_filter" :class="webview && 'no_padding'">
            <h1 v-if="pageH1Title" class="m_page_title">
                {{ pageH1Title }}
            </h1>
            <div :class="webview ? 'no_sticky' : 'm_filter_row'" class="flex items-center">
                <Search 
                    placeholder="Наименование товара или артикул" 
                    :model="model" 
                    :page_name ="page_name" />
                <GridTypeMobile class="products_option ml-2"/>
            </div>
        </div>
        <template v-if="!embded">
            <a-button
                v-if="config && config.order_setting && config.order_setting.show_create_order_button"
                block
                type="primary"
                class="mb-2 flex items-center justify-center"
                size="large"
                @click="openCart()">
                <i class="fi fi-rr-shopping-cart-check mr-2"></i>
                Оформить заказ
            </a-button>
            <a-button
                v-if="config && config.order_setting && config.order_setting.show_create_returns_order_button"
                block
                type="primary"
                ghost
                class="mb-2 flex items-center justify-center"
                size="large"
                @click="openReturnCart()">
                <i class="fi fi-rr-box mr-2"></i>
                Оформить заказ
            </a-button>
        </template>
        <div class="products_wrapper">
            <component
                v-if="config && config.product_setting && config.product_setting.product_history"
                :is="historyComponent" 
                :openDetail="openDetail" /> 

            <div 
                v-if="emptyGoods" 
                class="pt-8">
                <a-empty>
                    <template #description>
                        По данному запросу товары отсутствуют
                    </template>
                </a-empty>
            </div>
            <div :class="listType === 'ProductCard' ? 'grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4' : 'list_grid'">
                <component
                    v-for="item, index in productLit.results" 
                    :key="index" 
                    :is="cardComponent"
                    :injectGoods="injectGoods"
                    :item="item"
                    :addText="addText"
                    :embded="embded"
                    :embdedCheckStock="embdedCheckStock"
                    :addProduct="addProduct"
                    :createEmptyOrder="createEmptyOrder"
                    @click="openDetail(item.id)"  /> 
            </div>
            <InfiniteLoading
                :identifier="infinitiKey"
                @infinite="getGoods">
                <div slot="spinner" >
                    <a-spin class="mt-4"/>
                </div>
                <div slot="no-more"></div>
                <div slot="no-results"></div>
            </InfiniteLoading>
        </div>

        <div class="float_add">
            <SortMobile
                class="products_option mb-2"
                :model="model" 
                :page_name="page_name" />
            <div class="filter_slot">
                <PageFilter 
                    class="products_option"
                    vertical
                    hideResetBtn
                    buttonsActive
                    :model="model" 
                    :page_name ="page_name"/>
            </div>
            <Categories 
                class="products_option"
                :page_name="page_name"
                :model="model" />
        </div>
    </div>
</template>

<script>
import InfiniteLoading from "vue-infinite-loading"
import eventBus from '@/utils/eventBus.js'
import { mapState } from 'vuex'
export default {
    name: "ProductsList",
    components: {
        InfiniteLoading,
        PageFilter: () => import('@/components/PageFilter'),
        Categories: () => import('./Categories/index.vue'),
        Search: () => import('@/components/PageFilter/includeWidget/Search.vue'),
        SortMobile: () => import('./components/SortMobile.vue'),
        GridTypeMobile: () => import('./components/GridTypeMobile.vue')
    },
    props: {
        embded: {
            type: Boolean,
            default: false  
        },
        injectGoods: {
            type: Object,
            default: () => null
        },
        addProduct: {
            type: Function,
            default: () => {}
        },
        embdedCheckStock: {
            type: Boolean,
            default: true
        },
        page_name: {
            type: String,
            default: "catalogs.goodsmodel_list_page"
        },
        addText: {
            type: String,
            default: "Добавить"
        },
        createEmptyOrder: {
            type: Boolean,
            default: false
        },
        webview: {
            type: Boolean,
            default: false
        },
        showGrid: {
            type: Boolean,
            default: true
        },
        showSort: {
            type: Boolean,
            default: true
        },
        showSearch: {
            type: Boolean,
            default: true
        },
        topPanelSticky: {
            type: Boolean,
            default: true
        }
    },
    computed: {
        ...mapState({
            goodsList: state => state.products.goodsList,
            goodsEmpty: state => state.products.goodsEmpty,
            historyGoods: state => state.products.historyGoods,
            listType: state => state.products.activeGridType,
            config: state => state.config.config
        }),
        cardComponent() {
            const type = this.listType
            return () => import(`./components/${type}.vue`)
                .then(module => {
                    return module
                })
                .catch(e => {
                    console.log('error')
                    return import(`./components/NotWidget.vue`)
                })
        },
        pageH1Title() {
            return this.$route?.meta?.title ? this.$route.meta.title : null
        },
        historyComponent() {
            return () => import('./components/GoodsHistory.vue')
        },
        productLit() {
            return this.goodsList[this.page_name] || {
                count: 0,
                next: true,
                results: []
            }
        },
        emptyGoods() {
            return this.goodsEmpty[this.page_name] || false
        }
    },
    watch: {
        '$route.query.category'() {
            this.onSearch()
        }
    },
    data(){
        return{
            loading: false,
            infinitiKey: 1,
            model: "catalogs.GoodsModel",
            activeSort:  {   
                name: 'Популярные',
                param: '-popularity',
            },
            sortedItems: [
                {   
                    name: 'Популярные',
                    param: '-popularity',
                    icon: 'fi-rr-star'
                },
                {
                    name: 'Новинки',
                    param: '-created_at',
                    icon: 'fi-rr-calendar-check'
                },
                {
                    name: 'Сначала дешевые',
                    param: 'price_by_catalog',
                    icon: 'fi-rr-sort-numeric-down'
                },
                {
                    name: 'Сначала дорогие',
                    param: '-price_by_catalog',
                    icon: 'fi-rr-sort-numeric-down-alt'
                }
            ]
        }
    },
    methods: {
        openCart() {
            eventBus.$emit('open_cart')
        },
        openReturnCart() {
            eventBus.$emit('open_return_cart')
        },
        changeSort(item){
            this.activeSort = item
            this.$store.commit('products/SET_ORDERING', item.param)
            this.onSearch()
        },
        onSearch(){
            this.$store.commit('products/SEARCH_HANDLER', this.page_name)
            this.infinitiKey++;
        },
        openDetail(id){
            let query = Object.assign({}, this.$route.query)
            if(!query?.viewGoods || query.viewGoods !== id) {
                query.viewGoods = id
                this.$router.push({query})
            }
        },
        async getGoods($state = null){
            if(!this.loading && this.productLit.next && !this.emptyGoods) {
                try{
                    this.loading = true
                    const data = await this.$store.dispatch('products/getGoods', {
                        page_name: this.page_name
                    })

                    if(data?.next) {
                        if($state)
                            $state.loaded()
                    } else {
                        if($state)
                            $state.complete()
                    }
                }
                catch(e){
                    this.loading = false
                    console.error(e)
                    if($state)
                        $state.complete()
                } finally {
                    this.loading = false
                }
            } else {
                if($state)
                    $state.complete()
            }
        }
    },
    mounted() {
        eventBus.$on(`update_filter_${this.model}_${this.page_name}`, () => {
            this.search =""
            this.onSearch()
        })
    },
    beforeDestroy() {
        eventBus.$off(`update_filter_${this.model}_${this.page_name}`)
        this.$store.commit('products/SEARCH_HANDLER', this.page_name)
    }
}
</script>

<style lang="scss" scoped>
.m_filter_row{
    padding-bottom: 10px;
}
.products_settings {
    padding: 8px 0;
}
.products_option {
    &:not(:last-child) {
        margin-right: 8px;
    }
}
.prod_sort{
    i{
        margin-left: 3px;
    }
}
.list_grid{
    .product_card_list{
        &:not(:last-child){
            margin-bottom: 15px;
        }
    }
}
.search_filter{
    width: 100%;
    min-width: 300px;
    &:not(.no_padding){
        padding-top: 15px;
    }
    .filter_wrap{
        overflow-y: auto;
        overflow-x: hidden;
        top: 20px;
        z-index: 10;
    }
}
.products_search_wrapp{
    padding-bottom: 10px;
    padding-top: 20px;
    background: #fff;
    position: sticky;
    top: 0;
    z-index: 10;
    margin-right: -30px;
    padding-right: 30px;
}
.products{
    grid-template-columns: 300px 1fr;
    gap: 15px;
    height: 100%;
    &.no_padding{
        padding: 0px 0px 20px 0px;
    }
    &:not(.no_padding){
        padding: 0px 15px 20px 15px;
    }
    .float_add{
        right: 7px;
    }
}

.products_list_header {
    top: var(--headerHeight);
    &:not(.no_sticky){
        background-color: var(--eBg);    
    }

}
</style>