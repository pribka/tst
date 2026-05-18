<template>
    <a-drawer
        title="Товары"
        placement="right"
        :zIndex="1100"
        class="products_drawer"
        :width="widthDrawer"
        :visible="visible"
        @close="closeDrawer()">
        <Products
            embded 
            :addProduct="addProduct"
            :page_name="page_name"
            :addText="addText"
            :createEmptyOrder="createEmptyOrder"
            :embdedCheckStock="embdedCheckStock"
            :injectGoods="injectGoods" />
    </a-drawer>
</template>

<script>
import eventBus from '@/utils/eventBus.js'
import { mapState } from 'vuex'
export default {
    props: {
        addProduct: {
            type: Function,
            default: () => {}
        },
        injectGoods: {
            type: Object,
            default: () => null
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
        }
    },
    components: {
        Products: () => import('./index.vue')
    },
    computed: {
        ...mapState({
            windowWidth: state => state.windowWidth
        }),
        widthDrawer() {
            if(this.windowWidth > 1200)
                return this.windowWidth - 250
            else
                return this.windowWidth
        }
    },
    data() {
        return {
            visible: false
        }
    },
    methods: {
        toggleDrawer() {
            this.visible = !this.visible
        },
        closeDrawer() {
            this.toggleDrawer()
            if(this.createEmptyOrder)
                eventBus.$emit('update_order_cart')
        }
    }
}
</script>

<style lang="scss">
.products_drawer{
    .ant-drawer-body,
    .ant-drawer-wrapper-body{
        overflow: hidden;
    }
    .ant-drawer-body{
        height: calc(100% - 40px);
        padding: 0px;
        overflow-y: auto;
    }
    .filter_row{
        position: relative;
        &.products_list_header{
            top: 0px;
        }
    }
    .products{
        .products_wrapper{
            overflow: initial;
        }
    }
}
</style>