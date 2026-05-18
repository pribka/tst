<template>
    <a-spin :spinning="loading" size="small">
        <a-table
            :columns="columns"
            :data-source="rows"
            size="small"
            :locale="{
                emptyText: $t('no_data')
            }"
            :pagination="false"
            rowKey="id">

            <template slot="date" slot-scope="text, record">
                <span class="tabular-nums">{{ $moment(record.date).format('DD.MM.YYYY') }}</span>
            </template>

            <template slot="cost_item" slot-scope="text, record">
                <span class="truncate block max-w-[420px]">{{ costItemLabel(record) }}</span>
            </template>

            <template slot="description" slot-scope="text, record">
                <a-popover
                    v-if="record.description"
                    placement="topLeft"
                    :getPopupContainer="getPopupMainContainer"
                    :overlayStyle="{ maxWidth: '500px' }">
                    <template #content>
                        <div class="popover_desc">
                            {{ record.description }}
                        </div>
                    </template>

                    <div class="desc_2_lines">
                        {{ record.description }}
                    </div>
                </a-popover>

                <span v-else class="opacity-60">—</span>
            </template>

            <template slot="amount" slot-scope="text, record">
                <span class="font-semibold whitespace-nowrap tabular-nums">
                    {{ formatMoney(record.amount) }}
                </span>
            </template>

            <template slot="actions" slot-scope="text, record">
                <div class="flex items-center justify-end">
                    <a-button
                        v-if="record.attachments && record.attachments.length"
                        type="ui"
                        ghost
                        class="!px-0"
                        v-tippy
                        :content="$t('approvals.attachments')"
                        icon="fi-rr-folder"
                        flaticon
                        @click="openAttachments(record)" />
                    <a-button
                        v-if="canUpdate"
                        type="link"
                        class="!px-0"
                        v-tippy
                        :content="$t('edit')"
                        icon="fi-rr-edit"
                        flaticon
                        @click="openEdit(record)" />
                    <a-button
                        v-if="canDelete"
                        type="link"
                        class="!px-0 text-red-500"
                        icon="fi-rr-trash"
                        v-tippy
                        :content="$t('remove')"
                        flaticon
                        @click="removeItem(record)" />
                </div>
            </template>
        </a-table>

        <div class="flex justify-end mt-3">
            <a-pagination
                :show-size-changer="pageSizeOptions.length > 1"
                :page-size="pageSize"
                :pageSizeOptions="pageSizeOptions"
                class="pt-1 pager_wrapper"
                :current="page"
                hideOnSinglePage
                :defaultPageSize="Number(pageSize)"
                @showSizeChange="onPageSizeChange"
                @change="onPageChange"
                :total="Number(count)"
                show-less-items>
                <template slot="buildOptionText" slot-scope="props">
                    {{ props.value }}
                </template>
            </a-pagination>
        </div>
    </a-spin>
</template>

<script>
import { errorHandler } from '@/utils/index.js'
export default {
    props: {
        getPopupMainContainer: {
            type: Function,
            default: () => {}
        },
        formatMoney: {
            type: Function,
            default: () => {}
        },
        openAttachments: {
            type: Function,
            default: () => {}
        },
        removeItem: {
            type: Function,
            default: () => {}
        },
        openEdit: {
            type: Function,
            default: () => {}
        },
        canDelete: {
            type: Boolean,
            default: false
        },
        canUpdate: {
            type: Boolean,
            default: false
        },
        approvals: {
            type: Object,
            required: true
        },
        toNumber: {
            type: Function,
            default: () => {}
        },
        setAmount: {
            type: Function,
            default: () => {}
        },
        setRews: {
            type: Function,
            default: () => {}
        }
    },
    computed: {
        columns() {
            return [
                {
                    title: this.$t('approvals.date'),
                    key: 'date',
                    dataIndex: 'date',
                    scopedSlots: { customRender: 'date' },
                    width: 140
                },
                {
                    title: this.$t('approvals.cost_item'),
                    key: 'cost_item',
                    dataIndex: 'cost_item',
                    scopedSlots: { customRender: 'cost_item' }
                },
                {
                    title: this.$t('approvals.comment'),
                    key: 'description',
                    dataIndex: 'description',
                    scopedSlots: { customRender: 'description' }
                },
                {
                    title: this.$t('approvals.amount'),
                    key: 'amount',
                    dataIndex: 'amount',
                    scopedSlots: { customRender: 'amount' },
                    align: 'right',
                    width: 160
                },
                {
                    title: '',
                    key: 'id',
                    scopedSlots: { customRender: 'actions' },
                    align: 'right',
                    width: 110
                }
            ]
        },
    },
    data() {
        return {
            loading: false,
            rows: [],
            count: 0,
            page: 1,
            pageSize: 15,
            pageSizeOptions: ['15', '30', '50'],
        }
    },
    created() {
        this.fetchList()
    },
    methods: {
        listReload() {
            this.fetchList()
        },
        costItemLabel(item) {
            return item?.cost_item?.name || item?.cost_item?.string_view || item?.cost_item_name || '—'
        },
        onPageChange(p) {
            this.page = p
            this.fetchList()
        },
        onPageSizeChange(current, size) {
            this.pageSize = Number(size)
            this.page = 1
            this.fetchList()
        },
        async fetchList() {
            if(!this.approvals?.id) return
            try {
                this.loading = true
                const { data } = await this.$http.get(
                    `/processes/workflow_requests/${this.approvals.id}/advance_report/list/`,
                    { params: { page: this.page, page_size: this.pageSize } }
                )

                const list = Array.isArray(data?.results) ? data.results : Array.isArray(data) ? data : []
                this.rows = list
                this.count = Number(data?.count || list.length || 0)
                this.setRews(list)
                this.setAmount(this.toNumber(data?.amount_sum))
            } catch(error) {
                this.rows = []
                this.count = 0
                this.setAmount(0)
                this.setRews([])
                errorHandler({error, show: false})
            } finally {
                this.loading = false
            }
        },
    }
}
</script>