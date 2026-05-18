<template>
    <a-drawer
        title="Выберите склад отгрузки"
        placement="right"
        :zIndex="1050"
        class="select_warehouse_drawer"
        :width="windowWidth > 960 ? 400 : '100%'"
        :visible="visible"
        :destroyOnClose = "true"
        @close="closeDrawer()">
        <WarehousesList 
            :markedWarehouseHandler="markedWarehouseHandler"
            :warehouseList="warehouseList"
            :closeDrawer="closeDrawer"/>
    </a-drawer>
</template>

<script>
import { mapState } from 'vuex'
import WarehousesList from './WarehousesList.vue'
export default {
    props: {
        markedWarehouseHandler: {
            type: Function,
            default: () => {}
        },
        warehouseList: {
            type: Array,
            default: () => []
        }
    },
    components: {
        WarehousesList
    },
    computed: {
        ...mapState({
            windowWidth: state => state.windowWidth
        })
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
        },

    }
}
</script>

<style lang="scss">
.select_warehouse_drawer{
    .ant-drawer-body,
    .ant-drawer-wrapper-body{
        overflow-y: auto;
    }
    .ant-drawer-body{
        padding: 0px;
    }
}
</style>