<template>
    <div>
        <div class="warehouses_list">
            <a-radio-group v-model="selectedWarehouse">
                <a-list class="list"
                        item-layout="horizontal"
                        :data-source="warehouseList">
                    <a-list-item slot="renderItem" slot-scope="item">
                        <a-radio :value="item.id" class="ml-4"> {{ item.name }} </a-radio>
                    </a-list-item>
                </a-list>
            </a-radio-group>
        </div>
        <div class="mx-5">
            <a-button
                type="primary"
                class="mt-5 w-full"
                :disabled="!selectedWarehouse"
                @click="returnWarehouse">
                {{ buttonText || "Выбрать" }}
            </a-button>
        </div>
    </div>
</template>
  
<script>
export default {
    name: 'WarehousesList',
    props: {
        buttonText: {
            type: String,
            default: ''
        },
        markedWarehouseHandler: {
            type: Function,
            default: () => {}
        },
        closeDrawer: {
            type: Function,
            default: () => {}
        },
        warehouseList: {
            type: Array,
            default: () => []
        }
    },
    data() {
        return {
            selectedWarehouse: null
        };
    },
    methods: {
        returnWarehouse() {
            this.markedWarehouseHandler(this.selectedWarehouse)
            this.closeDrawer()
        }
    }
}
</script>

<style lang="scss">
.warehouses_list {
    .list {
        max-height: 78vh;
        overflow-y: auto;
    }
    .ant-radio-group {
        width: 100%;
    }
    .ant-list {
        width: 100%;
    }
}
</style>