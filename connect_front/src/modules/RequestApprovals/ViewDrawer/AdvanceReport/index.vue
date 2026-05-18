<template>
    <div class="advance_report" ref="mainWrapper">
        <div class="flex items-center justify-between mb-3">
            <div class="text-lg font-semibold flex items-center">
                <i class="fi fi-rr-memo-circle-check mr-2" /> {{ $t('approvals.advance_report') }}
            </div>
            <template v-if="canCreate">
                <a-button
                    v-if="isMobile"
                    type="primary"
                    icon="fi-rr-plus"
                    shape="circle"
                    flaticon
                    :disabled="detailReload"
                    @click="openCreate" />
                <a-button
                v-else
                    type="primary"
                    icon="fi-rr-plus"
                    flaticon
                    :disabled="detailReload"
                    @click="openCreate">
                    {{ $t('Add') }}
                </a-button>
            </template>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-3 gap-2 md:gap-3 mb-3">
            <div class="stat_item">
                <div class="stat_label">{{ $t('approvals.issued') }}</div>
                <div class="stat_value">{{ formatMoney(issuedAmount) }}</div>
            </div>
            <div class="stat_item">
                <div class="stat_label">{{ $t('approvals.reported') }}</div>
                <div class="stat_value">{{ formatMoney(reportedAmount) }}</div>
            </div>
            <div class="stat_item">
                <div class="stat_label">{{ toReturnLabel }}</div>
                <div class="stat_value" :class="{ text_red: toReturnAmount > 0, green: toReturnAmount < 0 }">
                    {{ formatMoney(toReturnAmount) }}
                </div>
            </div>
        </div>

        <div v-if="finActionsBlockShow && isMobile" class="flex flex-col flex-wrap gap-y-1">
            <transition name="slide-fade">
                <a-button 
                    v-if="reportedAmount && actions.approve_advance_report && actions.approve_advance_report.availability"
                    type="primary" 
                    size="large" 
                    icon="fi-rr-check-circle"
                    flaticon
                    block
                    style="padding-left: 20px;padding-right: 20px;"
                    :loading="approveLoading"
                    @click="approveAdvanceReportHandler()">
                    {{ $t('approvals.approve_advance_report') }}
                </a-button>
            </transition>

            <transition name="slide-fade">
                <div v-if="actions && actions.notify_fin_service && actions.notify_fin_service.availability" class="mb-2">
                    <a-button 
                        type="flat_primary" 
                        icon="fi-rr-bell" 
                        flaticon 
                        block
                        :loading="finLoading"
                        size="large"
                        @click="notifyFinServiceHandler()">
                        {{ $t('approvals.notify_fin_service') }}
                    </a-button>
                </div>
            </transition>
        </div>

        <component 
            :is="listView"
            ref="listView"
            :setAmount="setAmount"
            :getPopupMainContainer="getPopupMainContainer"
            :removeItem="removeItem"
            :canDelete="canDelete"
            :toNumber="toNumber"
            :canUpdate="canUpdate"
            :openAttachments="openAttachments"
            :openEdit="openEdit"
            :formatMoney="formatMoney"
            :approvals="approvals" />

        <div v-if="finActionsBlockShow && !isMobile" class="flex items-center flex-wrap gap-y-1 gap-2">
            <transition name="slide-fade">
                <a-button 
                    v-if="reportedAmount && actions.approve_advance_report && actions.approve_advance_report.availability"
                    type="primary" 
                    size="large" 
                    icon="fi-rr-check-circle"
                    flaticon
                    style="padding-left: 20px;padding-right: 20px;"
                    :loading="approveLoading"
                    @click="approveAdvanceReportHandler()">
                    {{ $t('approvals.approve_advance_report') }}
                </a-button>
            </transition>
            <transition name="slide-fade">
                <div v-if="actions && actions.notify_fin_service && actions.notify_fin_service.availability" class="mt-1">
                    <a-button 
                        type="flat_primary" 
                        icon="fi-rr-bell" 
                        flaticon 
                        :loading="finLoading"
                        size="large"
                        @click="notifyFinServiceHandler()">
                        {{ $t('approvals.notify_fin_service') }}
                    </a-button>
                </div>
            </transition>
        </div>

        <a-modal
            v-model="modalVisible"
            :title="editMode ? $t('approvals.edit_advance_report') : $t('approvals.add_advance_report')"
            destroyOnClose
            width="520px"
            @afterVisibleChange="afterVisibleChange"
            @cancel="closeModal()">
            <div ref="modal_wrapper">
                <a-form-model ref="form" :model="form" :rules="rules">
                    <a-form-model-item :label="$t('approvals.date')" prop="date" class="mb-2">
                        <a-date-picker
                            v-model="form.date"
                            format="DD.MM.YYYY"
                            size="large"
                            :getCalendarContainer="getPopupContainer"
                            :inputReadOnly="false"
                            valueFormat="YYYY-MM-DD"
                            class="w-full" />
                    </a-form-model-item>

                    <div class="grid grid-cols-1 md:grid-cols-2 gap-2 mb-2 md:mb-3">
                        <a-form-model-item :label="$t('approvals.cost_item')" prop="cost_item" class="mb-0">
                            <DSelect
                                v-model="form.cost_item"
                                size="large"
                                apiUrl="/catalogs/cost_items/"
                                :params="{
                                    contractor: approvals.organization.id
                                }"
                                oneSelect
                                firstSelected
                                valueKey="id"
                                labelKey="name"
                                listObject="results"
                                :default-active-first-option="false"
                                :filter-option="false"
                                :not-found-content="null" />
                        </a-form-model-item>

                        <a-form-model-item :label="$t('approvals.amount')" prop="amount" class="mb-0">
                            <a-input
                                v-model="form.amount"
                                ref="amount_input"
                                :placeholder="$t('approvals.print_amount')"
                                size="large"
                                @input="onAmountPaidInput"
                                @blur="onAmountPaidBlur"
                                @pressEnter="submit()" />
                        </a-form-model-item>
                    </div>

                    <a-form-model-item :label="$t('approvals.comment')" class="mb-2">
                        <div class="textarea_wrapper">
                            <a-textarea
                                v-model="form.description"
                                class="textarea_input"
                                ref="descriptionTextArea"
                                :maxLength="descriptionMaxCount"
                                :placeholder="$t('approvals.comment')"
                                @input="adjustHeight" />
                            <div class="description_length">
                                {{ form.description.length }}/{{ descriptionMaxCount }}
                            </div>
                        </div>
                    </a-form-model-item>
                </a-form-model>

                <a-form-model-item 
                        :label="$t('approvals.attachments')" 
                        prop="attachments" 
                        class="mb-0">
                        <a-button
                            type="link"
                            size="small"
                            class="p-0"
                            @click="openFileModal">
                            + {{ $t('approvals.select_file') }}
                        </a-button>

                        <div v-show="form.attachments.length">
                            <p>{{ $t('approvals.attachments_selected') }}</p>
                            <FileAttach
                                ref="fileAttach"
                                :zIndex="1100"
                                class="task_files_list"
                                :attachmentFiles="form.attachments"
                                :maxMBSize="50"
                                createFounder
                                listType="picture"
                                :showDeviceUpload="true"/>
                        </div>
                    </a-form-model-item>
            </div>
            <template #footer>
                <div class="flex items-center gap-2 w-full" :class="!isMobile && 'justify-end'">
                    <a-button type="primary" :loading="loading" :block="isMobile" @click="submit()">
                        {{ editMode ? $t('save') : $t('send') }}
                    </a-button>
                    <a-button type="ui" ghost :disabled="loading" :block="isMobile" @click="closeModal()">
                        {{ $t('Cancel') }}
                    </a-button>
                </div>
            </template>
        </a-modal>

        <a-modal
            v-model="attachmentsVisible"
            :title="$t('approvals.attachments')"
            destroyOnClose
            width="520px"
            @afterVisibleChange="afterAttachmentsVisibleChange"
            @cancel="closeAttachmentsModal()">

            <component
                v-if="attachmentsItem"
                :is="showFiles"
                :sourceId="attachmentsItem.id"
                useIconButton
                :createFounder="false"
                :showHeader="false"
                :isFounder="false"
                widgetEmbed
                :isStudent="false" />

            <template #footer>
                <a-button type="ui" ghost :block="isMobile" @click="closeAttachmentsModal()">
                    {{ $t('Cancel') }}
                </a-button>
            </template>
        </a-modal>
    </div>
</template>

<script>
import { errorHandler } from '@/utils/index.js'
import eventBus from '@/utils/eventBus'

export default {
    name: 'AdvanceReport',
    components: {
        DSelect: () => import('@apps/DrawerSelect/Select.vue'),
        FileAttach: () => import("@apps/vue2Files/components/FileAttach")
    },
    props: {
        model: {
            type: String,
            required: true
        },
        pageName: {
            type: String,
            required: true
        },
        approvals: {
            type: Object,
            required: true
        },
        actions: {
            type: Object,
            default: () => null
        },
        getDetail: {
            type: Function,
            default: () => {}
        },
        detailReload: {
            type: Boolean,
            default: false
        },
        historyReload: {
            type: Function,
            default: () => {}
        },
        notifyFinService: {
            type: Function,
            default: () => {}
        },
        approveAdvanceReport: {
            type: Function,
            default: () => {}
        }
    },
    data() {
        return {
            finLoading: false,
            descriptionMaxCount: 1024,
            needCheckAfterReload: false,
            loading: false,
            rows: [],
            count: 0,
            page: 1,
            pageSize: 15,
            pageSizeOptions: ['15', '30', '50'],
            modalVisible: false,
            editMode: false,
            editId: null,
            amountSum: 0,
            approveLoading: false,
            attachmentsItem: null,
            attachmentsVisible: false,
            form: {
                date: null,
                cost_item: null,
                amount: "",
                description: '',
                attachments: []
            },
            rules: {
                date: [{ required: true, message: this.$t('field_required'), trigger: 'change' }],
                cost_item: [{ required: true, message: this.$t('field_required'), trigger: 'change' }],
                amount: [{ required: true, message: this.$t('field_required'), trigger: 'blur' }]
            }
        }
    },
    computed: {
        finActionsBlockShow() {
            return this.actions?.notify_fin_service?.availability || this.actions?.approve_advance_report?.availability && this.reportedAmount ? true : false
        },
        showFiles() {
            if(this.attachmentsItem && this.attachmentsVisible)
                return () => import('@apps/vue2Files')
            return null
        },
        listView() {
            if(this.isMobile)
                return () => import('./List.vue')
            return () => import('./Table.vue')
        },
        toReturnLabel() {
            return this.toReturnAmount < 0 ? this.$t('approvals.overspending') : this.$t('approvals.to_return')
        },
        canCreate() {
            return this.actions?.create_advance_report?.availability ? true : false
        },
        canUpdate() {
            return this.actions?.update_advance_report?.availability ? true : false
        },
        canDelete() {
            return this.actions?.delete_advance_report?.availability ? true : false
        },
        issuedAmount() {
            return this.toNumber(this.approvals?.amount_paid)
        },
        reportedAmount() {
            const n = this.toNumber(this.amountSum)
            if(n > 0) return n
            return this.rows.reduce((acc, r) => acc + this.toNumber(r.amount), 0)
        },
        toReturnAmount() {
            return this.issuedAmount - this.reportedAmount
        },
        isMobile() {
            return this.$store.state.isMobile
        },
    },
    methods: {
        async approveAdvanceReportHandler() {
            try {
                this.approveLoading = true
                await this.approveAdvanceReport()
            } catch(e) {

            } finally {
                this.approveLoading = false
            }
        },
        async notifyFinServiceHandler() {
            try {
                this.finLoading = true
                await this.notifyFinService()
            } catch(e) {

            } finally {
                this.finLoading = false
            }
        },
        closeAttachmentsModal() {
            this.attachmentsVisible = false
        },
        afterAttachmentsVisibleChange(vis) {
            if(!vis) {
                this.attachmentsItem = null
            }
        },
        openAttachments(item) {
            this.attachmentsItem = item
            this.attachmentsVisible = true
        },
        openFileModal() {
            this.$nextTick(() => {
                this.$refs.fileAttach.openFileModal()
            })
        },
        onAmountPaidInput(e) {
            let v = String(e.target.value || '')

            v = v.replace(',', '.')
            v = v.replace(/[^\d.]/g, '')

            const parts = v.split('.')
            const intPart = parts[0]
            const decPart = parts[1] ? parts[1].slice(0, 2) : ''

            v = `${intPart}${parts.length > 1 ? '.' + decPart : ''}`

            this.form.amount = this.formatThousands(v)
        },
        onAmountPaidBlur() {
            let v = String(this.form.amount || '').replace(/\s/g, '')

            if (!v) {
                this.form.amount = ''
                return
            }

            let parts = v.split('.')
            let intPart = (parts[0] || '').replace(/\D/g, '') || '0'
            let decPart = (parts[1] || '').replace(/\D/g, '').slice(0, 2)

            decPart = decPart.padEnd(2, '0')

            this.form.amount = this.formatThousands(`${intPart}.${decPart}`)
        },
        normalizeAmount(value) {
            if (value === undefined || value === null || value === '') return ''

            const str = String(value).replace(/\s/g, '').replace(',', '.')
            if (!str) return ''

            const parts = str.split('.')
            const intPart = (parts[0] || '').replace(/\D/g, '') || '0'
            const decPart = (parts[1] || '').replace(/\D/g, '').slice(0, 2)

            const fixedDec = decPart.padEnd(2, '0')
            return this.formatThousands(`${intPart}.${fixedDec}`)
        },
        formatThousands(value) {
            if (!value) return ''

            const parts = String(value).split('.')
            const intPart = (parts[0] || '').replace(/\B(?=(\d{3})+(?!\d))/g, ' ')
            const decPart = parts[1] !== undefined ? `.${parts[1]}` : ''

            return `${intPart}${decPart}`
        },
        setRews(row) {
            this.rows = row
        },
        setAmount(amount) {
            this.amountSum = amount
            if(this.needCheckAfterReload) {
                this.needCheckAfterReload = false
                this.checkReportedAndRefresh()
            }
        },
        afterVisibleChange(vis) {
            if(vis) {
                this.$nextTick(() => {
                    if(this.$refs.amount_input)
                        this.$refs.amount_input.focus()
                })
            }
        },
        getPopupMainContainer() {
            return this.$refs.mainWrapper
        },
        checkReportedAndRefresh() {
            const issued = this.toNumber(this.issuedAmount)
            const reported = this.toNumber(this.reportedAmount)

            if(issued > 0 && reported >= issued) {
                
            }
        },
        adjustHeight(event) {
            const textarea = event.target
            textarea.style.height = 'auto'
            const maxHeight = window.innerHeight - 100
            textarea.style.height = `${Math.min(textarea.scrollHeight, maxHeight)}px`
        },
        getPopupContainer() {
            return this.$refs.modal_wrapper
        },
        closeModal() {
            this.modalVisible = false
            this.editMode = false
            this.editId = null
            this.form = {
                date: null,
                cost_item: null,
                amount: "",
                description: '',
                attachments: []
            }
        },
        openCreate() {
            this.editMode = false
            this.editId = null
            this.form = {
                date: this.$moment(),
                cost_item: null,
                amount: '',
                description: '',
                attachments: []
            }
            this.modalVisible = true
            this.$nextTick(() => {
                if(this.$refs.form) this.$refs.form.clearValidate()
            })
        },
        openEdit(item) {
            this.editMode = true
            this.editId = item.id
            this.form = {
                date: item.date ? this.$moment(item.date) : null,
                cost_item: item.cost_item?.id || item.cost_item || null,
                amount: item.amount ? this.normalizeAmount(item.amount) : '',
                description: item.description || '',
                attachments: item.attachments?.length ? item.attachments : []
            }
            this.modalVisible = true
            this.$nextTick(() => {
                if(this.$refs.form) this.$refs.form.clearValidate()
            })
        },
        async submit() {
            if(!this.$refs.form) return
            this.$refs.form.validate(async valid => {
                if(!valid) return
                try {
                    this.loading = true
                    const amount = this.form.amount
                        ? Number(
                            String(this.form.amount)
                                .replace(/\s/g, '')
                                .replace(',', '.')
                        )
                        : null

                    const payload = {
                        date: this.form.date ? this.$moment(this.form.date).format('YYYY-MM-DD') : null,
                        cost_item: this.form.cost_item,
                        amount,
                        description: this.form.description,
                        attachments: this.form.attachments
                    }

                    if(payload.attachments?.length)
                        payload.attachments = payload.attachments.map(file => file.id)

                    if(this.editMode && this.editId) {
                        await this.$http.put(`/processes/workflow_requests/advance_report/${this.editId}/update/`, {
                            id: this.editId,
                            ...payload
                        })
                    } else {
                        await this.$http.post(`/processes/workflow_requests/${this.approvals.id}/advance_report/create/`, payload)
                    }

                    this.modalVisible = false
                    this.needCheckAfterReload = true
                    this.$nextTick(() => {
                        if(this.$refs.listView)
                            this.$refs.listView.listReload()
                    })
                    this.historyReload()
                    //this.checkReportedAndRefresh()
                } catch(error) {
                    errorHandler({error})
                } finally {
                    this.loading = false
                }
            })
        },
        removeItem(item) {
            this.$confirm({
                title: this.$t('approvals.advance_report_delete'),
                closable: true,
                maskClosable: true,
                cancelText: this.$t('cancel'),
                okText: this.$t('remove'),
                okType: 'danger',
                zIndex: 999999,
                onOk: () => {
                    return new Promise((resolve, reject) => {
                        this.$http.post(`/processes/workflow_requests/advance_report/${item.id}/delete/`)
                            .then(() => {
                                this.$message.success(this.$t('approvals.advance_report_delete_success'))
                                this.needCheckAfterReload = true
                                this.historyReload()
                                this.$nextTick(() => {
                                    if(this.$refs.listView)
                                        this.$refs.listView.listReload()
                                })
                                resolve()
                            })
                            .catch((error) => {
                                errorHandler({error})
                                reject()
                            })
                    })
                }
            })
        },
        toNumber(v) {
            if(v == null) return 0
            const n = Number(String(v).replace(/\s/g, '').replace(',', '.'))
            return Number.isFinite(n) ? n : 0
        },
        formatMoney(v) {
            const n = this.toNumber(v)
            const hasFrac = Math.round(n * 100) % 100 !== 0
            const opts = hasFrac
                ? { minimumFractionDigits: 2, maximumFractionDigits: 2 }
                : { minimumFractionDigits: 0, maximumFractionDigits: 0 }
            return new Intl.NumberFormat('ru-RU', opts).format(n) + ' ₸'
        }
    }
}
</script>

<style lang="scss" scoped>
.slide-fade-enter-active {
    transition: all .3s ease;
}
.slide-fade-leave-active {
    transition: all .3s cubic-bezier(1.0, 0.5, 0.8, 1.0);
}
.slide-fade-enter,
.slide-fade-leave-to {
    transform: translateY(-10px);
    opacity: 0;
}
.textarea_wrapper{
    position: relative;
    .description_length{
        position: absolute;
        bottom: 10px;
        right: 10px;
        z-index: 5;
        color: #888;
        font-size: 13px;
        line-height: 13px;
    }
    .textarea_input{
        margin-bottom: 0px!important;
        padding-bottom: 25px;
    }
}

.advance_report{
    .stat_item{
        border: 1px solid #E5E7EF;
        border-radius: 12px;
        padding: 10px 14px;
        background: #fff;
        @media (min-width: 768px) {
            padding: 14px;
        }
    }
    .stat_label{
        font-size: 12px;
        opacity: .65;
        @media (min-width: 768px) {
            margin-bottom: 4px;
        }
    }
    .stat_value{
        font-size: 18px;
        font-weight: 700;
    }
    .green{
        color: #16a34a;
    }
    .text_red{
        color: #ef4444;
    }
}

.desc_2_lines{
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
    white-space: pre-wrap;
    line-height: 18px;
}

.popover_desc{
    white-space: pre-wrap;
    font-size: 13px;
    line-height: 18px;
    max-height: 200px;
    overflow-y: auto;
}
</style>