<template>
    <component
        :is="widget"
        :hideSidebar="hideSidebar"
        :embded="embded"
        :injectGoods="injectGoods"
        :embdedCheckStock="embdedCheckStock"
        :addProduct="addProduct"
        :page_name="page_name"
        :createEmptyOrder="createEmptyOrder"
        :addText="addText"
        :webview="webview"
        :showGrid="showGrid"
        :showSort="showSort"
        :showSearch="showSearch"
        :topPanelSticky="topPanelSticky"
        :hideTopPanel="hideTopPanel" />
</template>

<script>
export default {
    props: {
        hideSidebar: {
            type: Boolean,
            default: false
        },
        hideTopPanel: {
            type: Boolean,
            default: false    
        },
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
        isMobile() {
            return this.$store.state.isMobile
        },
        widget() {
            if(this.isMobile)
                return () => import('./ProductListMobile.vue')
            return () => import('./ProductList.vue')
        }
    },
    created () {
        this.$store.commit('products/INIT_GOODS_LIST', this.page_name)
    }
}
</script>