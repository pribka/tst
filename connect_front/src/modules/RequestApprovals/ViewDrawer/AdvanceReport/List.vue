<template>
    <div>
        <a-spin :spinning="loading" size="small">
            <div v-if="rows.length" class="list_wrapper">
                <div v-for="item in rows" :key="item.id" class="list_card">
                    <div class="list_top">
                        <div class="list_date tabular-nums">
                            {{ $moment(item.date).format('DD.MM.YYYY') }}
                        </div>
                        <div class="list_amount tabular-nums">
                            {{ formatMoney(item.amount) }}
                        </div>
                    </div>

                    <div class="list_cost truncate">
                        {{ costItemLabel(item) }}
                    </div>

                    <div v-if="item.description" class="list_desc">
                        <div class="desc_3_lines">
                            {{ item.description }}
                        </div>

                        <a-button
                            v-if="isLongDescription(item.description)"
                            type="link"
                            class="more_btn"
                            @click="openDescription(item)">
                            {{ $t('approvals.more_details') }}
                        </a-button>
                    </div>

                    <div v-if="item.attachments && item.attachments.length" class="mt-2">
                        <a-button
                            type="link"
                            icon="fi-rr-folder"
                            style="padding-left: 0px;padding-right: 0px;"
                            flaticon
                            @click="openAttachments(item)">
                            {{ $t('approvals.attachments') }}
                        </a-button>
                    </div>

                    <div class="flex items-center gap-2 mt-2">
                        <a-button
                            v-if="canUpdate"
                            type="flat_primary"
                            block
                            @click="openEdit(item)">
                            {{ $t('edit') }}
                        </a-button>
                        <a-button
                            v-if="canDelete"
                            type="flat_danger"
                            block
                            @click="removeItem(item)">
                            {{ $t('remove') }}
                        </a-button>
                    </div>
                </div>
            </div>

            <div v-else class="empty_block">
                <span class="opacity-60">—</span>
            </div>

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

        <a-modal
            v-model="descModalVisible"
            :title="$t('approvals.comment')"
            destroyOnClose
            :footer="null"
            width="520px">
            <div class="desc_modal_text">
                {{ descModalText }}
            </div>

            <div class="flex justify-end mt-3">
                <a-button type="primary" block @click="descModalVisible = false">
                    {{ $t('close') }}
                </a-button>
            </div>
        </a-modal>
    </div>
</template>

<script>
import { errorHandler } from '@/utils/index.js'

export default {
    props: {
        getPopupMainContainer: {
            type: Function,
            default: () => {}
        },
        openAttachments: {
            type: Function,
            default: () => {}
        },
        formatMoney: {
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
    data() {
        return {
            loading: false,
            rows: [],
            count: 0,
            page: 1,
            pageSize: 15,
            pageSizeOptions: ['15', '30', '50'],

            descModalVisible: false,
            descModalText: ''
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
        isLongDescription(text) {
            if(!text) return false
            const t = String(text).trim()
            if(t.length > 180) return true
            if((t.match(/\n/g) || []).length >= 3) return true
            return false
        },
        openDescription(item) {
            this.descModalText = item?.description || ''
            this.descModalVisible = true
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
                this.setRews([])
                this.setAmount(0)
                errorHandler({error, show: false})
            } finally {
                this.loading = false
            }
        }
    }
}
</script>

<style lang="scss" scoped>
.list_wrapper{
    display: grid;
    grid-template-columns: 1fr;
    gap: 10px;
}

.list_card{
    border: 1px solid #E5E7EF;
    border-radius: 12px;
    padding: 12px;
    background: #fff;
}

.list_top{
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 10px;
    margin-bottom: 6px;
}

.list_date{
    font-weight: 600;
}

.list_amount{
    font-weight: 700;
    white-space: nowrap;
}

.list_cost{
    opacity: .85;
    margin-bottom: 6px;
}

.list_desc{
    font-size: 13px;
    line-height: 18px;
}

.desc_3_lines{
    display: -webkit-box;
    -webkit-line-clamp: 3;
    -webkit-box-orient: vertical;
    overflow: hidden;
    white-space: pre-wrap;
    line-height: 18px;
}

.more_btn{
    padding: 0px;
    height: auto;
    line-height: 16px;
    margin-top: 6px;
}

.empty_block{
    padding: 14px 0;
    text-align: center;
}

.desc_modal_text{
    white-space: pre-wrap;
    font-size: 14px;
    line-height: 20px;
}
</style>