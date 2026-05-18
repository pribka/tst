<template>
    <div>
        <a-table
            :columns="columns"
            :pagination="false"
            :data-source="productList"
            :scroll="{ x: 750, y: 500 }"
            :locale="{
                emptyText: $t('task.no_data')
            }"
            :row-key="record => record.id">
            <span
                slot="filterIcon"
                slot-scope="filtered"
                class="flex items-center justify-center">
                <i class="fi fi-rr-search" :class="filtered && 'blue_color'"></i>
            </span>

            <div
                slot="filterDropdown"
                slot-scope="{ setSelectedKeys, selectedKeys, confirm, clearFilters, column }"
                style="padding: 8px">
                <a-input
                    v-ant-ref="c => (searchInput = c)"
                    :placeholder="$t('task.search_by_name')"
                    :value="selectedKeys[0]"
                    style="width: 188px; margin-bottom: 8px; display: block;"
                    @change="e => setSelectedKeys(e.target.value ? [e.target.value] : [])"
                    @pressEnter="() => handleSearch(selectedKeys, confirm, column.dataIndex)"/>
                <a-button
                    type="primary"
                    size="small"
                    style="width: 90px; margin-right: 8px"
                    @click="() => handleSearch(selectedKeys, confirm, column.dataIndex)">
                    {{ $t('task.find') }}
                </a-button>
                <a-button size="small" style="width: 90px" @click="() => handleReset(clearFilters)">
                    {{ $t('task.reset') }}
                </a-button>
            </div>

            <span
                slot="name"
                slot-scope="text, record">
                <div class="good_name font-medium">
                    {{ text }}
                </div>
                <div class="mt-2 font-light">
                    {{ $t('task.product_code') }}: {{ record.code }}
                </div>
            </span>
            <span
                slot="amount"
                slot-scope="text">
                {{ price(text) }}
            </span>
            <span
                slot="actions"
                slot-scope="text, record"
                class="flex">
                <template v-if="record.quantity_success && Number(record.quantity_success) > 0">
                    <!-- <template v-if="record.attachments.length || record.comment.length">
                        <a-button
                            class="mb-1 ant-btn-icon-only"
                            v-tippy="{ inertia : true}"
                            content="Информация"
                            @click="openInfo(record)">
                            <i class="fi fi-rr-info"></i>
                        </a-button>
                    </template> -->
                </template>
                <template v-else>
                    <a-button
                        class="mb-1 ant-btn-icon-only"
                        v-tippy="{ inertia : true}"
                        :content="$t('task.full_shipment')"
                        type="primary"
                        ghost
                        :loading="fullLoading && fullLoading[record.id]"
                        @click="fullShipment(record)">
                        <i class="fi fi-rr-boxes"></i>
                    </a-button>
                    <a-button
                        class="ant-btn-icon-only ml-1"
                        v-tippy="{ inertia : true}"
                        :content="$t('task.incomplete_shipment')"
                        type="danger"
                        ghost
                        @click="incompleteModal(record)">
                        <i class="fi fi-rr-truck-loading"></i>
                    </a-button>
                </template>
            </span>
        </a-table>

        <ProductModal 
            :visibleInfo="visibleInfo"
            :afterCloseInfo="afterCloseInfo"
            :infoData="infoData"
            :closeInfoModal="closeInfoModal"
            :visible="visible"
            :incomplete="incomplete"
            :afterClose="afterClose"
            :closeFormModal="closeFormModal"
            :updateProductList="updateProductList" />
    </div>
</template>

<script>
import mixins from './mixins'
import ProductModal from './ProductModal.vue'
export default {
    mixins: [mixins],
    components: {
        ProductModal
    },
    props: {
        task: {
            type: Object,
            required: true
        },
        activeKey: {
            type: [String, Number],
            default: 'default'
        },
        productList: {
            type: Array,
            default: () => []
        },
        isOperator: {
            type: Boolean,
            default: false
        }
    },
    computed: {
        columns() {
            let cols = [
                {
                    title: this.$t('task.product'),
                    dataIndex: 'name',
                    key: 'name',
                    width: 320,
                    scopedSlots: {
                        customRender: 'name',
                        filterDropdown: 'filterDropdown',
                        filterIcon: 'filterIcon'
                    },
                    onFilter: (value, record) =>
                        record.good.name
                            .toString()
                            .toLowerCase()
                            .includes(value.toLowerCase()),
                    onFilterDropdownVisibleChange: visible => {
                        if (visible) {
                            setTimeout(() => {
                                this.searchInput.focus()
                            }, 0)
                        }
                    }
                },
                {
                    title: this.$t('task.quantity'),
                    dataIndex: 'quantity',
                    key: 'quantity',
                    sorter: (a, b) => Number(a.quantity) - Number(b.quantity)
                }, 
                {
                    title: this.$t('task.shipped'),
                    dataIndex: 'quantity_success',
                    key: 'quantity_success',
                    sorter: (a, b) => Number(a.quantity_success) - Number(b.quantity_success),
                    scopedSlots: { customRender: 'quantity_success' }
                },
                {
                    title: this.$t('task.cost'),
                    dataIndex: 'amount',
                    key: 'amount',
                    sorter: (a, b) => Number(a.amount) - Number(b.amount),
                    scopedSlots: { customRender: 'amount' }
                },
                {
                    title: this.$t('task.request_count'),
                    dataIndex: 'count',
                    key: 'count',
                    sorter: (a, b) => Number(a.quantity) - Number(b.quantity)
                }
            ]

            // if(this.activeKey !== 'default' && this.isOperator) {
            //     cols.push({
            //         title: '',
            //         dataIndex: 'id',
            //         key: 'id',
            //         scopedSlots: { customRender: 'actions' }
            //     })
            // }

            return cols
        }
    }
}
</script>

<style lang="scss" scoped>
.file_list{
    .item_file{
        &:not(:last-child){
            margin-bottom: 10px;
        }
        img{
            width: 100%;
            object-fit: cover;
            vertical-align: middle;
            -o-object-fit: cover;
        }
    }
}
.good_name{
    display: -webkit-box;
    -webkit-line-clamp: 3;
    -webkit-box-orient: vertical;
    overflow: hidden;
    text-overflow: ellipsis;
    word-break: break-word;
    max-width: 280px;
}
</style>