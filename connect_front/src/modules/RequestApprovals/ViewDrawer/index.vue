<template>
    <DrawerTemplate
        v-model="visible"
        :width="drawerWidth"
        destroyOnClose
        useCopyLink
        :class="isMobile && 'approvals_mobile_drawer'"
        :loading="detailLoading"
        useOpenLink
        :link="{
            approvals: approvals ? approvals.id : null,
            stab: tab
        }"
        @afterVisibleChange="afterVisibleChange"
        @close="visible = false">
        <template #title>
            <div v-if="approvals" class="drawer_title">
                <span v-if="approvals.number" style="color: rgb(136, 136, 136);">#{{ approvals.number }}</span> {{ approvals.request_type.name }}
            </div>
        </template>
        <template #rightHeader>
            <div v-if="approvals" class="flex items-center gap-2">
                <a-tag v-if="!isMobile" :color="approvals.status.color" contrastText useTextColor size="large" class="main_status">
                    {{ approvals.status.name }}
                </a-tag>
                <a-button
                    v-if="actions && actions.update && actions.update.availability"
                    type="ui"
                    ghost
                    flaticon
                    :disabled="loading"
                    v-tippy
                    :content="$t('edit')"
                    shape="circle"
                    icon="fi-rr-edit"
                    @click="edit()" />
                <a-button
                    v-if="actions && actions.delete && actions.delete.availability"
                    type="ui"
                    ghost
                    flaticon
                    :disabled="loading"
                    v-tippy
                    :content="$t('remove')"
                    shape="circle"
                    icon="fi-rr-trash"
                    @click="deleteHandler()" />
            </div>
        </template>
        <template #aside>
            <Aside 
                v-if="approvals" 
                :approvals="approvals" 
                :loading="loading"
                :closeDrawer="closeDrawer" 
                :moneyUnderReport="moneyUnderReport"
                :formInfo="formInfo" 
                :actions="actions"
                @on-rework="approvalsOnRework" />
            <div v-else />
        </template>
        <template #aside_bottom>
            <template v-if="approvals && actions">
                <div
                    class="font-semibold flex items-center justify-between block_header"
                    :class="[attachmentsOpen && 'open mb-3', isMobile && 'cursor-pointer']"
                    @click="toggleAttachments">
                    {{ $t('approvals.attachments') }}
                    <i
                        v-if="isMobile"
                        class="fi fi-rr-angle-small-down bt_arrow"
                        :class="attachmentsOpen && 'is_open'" />
                </div>

                <div v-show="attachmentsOpen">
                    <component
                        :is="showFiles"
                        :sourceId="approvals.id"
                        useIconButton
                        :createFounder="false"
                        :showHeader="false"
                        :isFounder="actions.update && actions.update.availability ? true : false"
                        widgetEmbed
                        :isStudent="actions.update && actions.update.availability ? true : false" />
                </div>
            </template>
            <div v-else />
        </template>
        <template v-if="!isMobile && approvals" #body_header>
            <Steps ref="stepsBlock" :approvals="approvals" />
        </template>
        <div v-if="approvals" :class="`${approvals.id}_body_wrap`">
            <RejectedMessage :approvals="approvals" />
            <template v-if="approvals.description">
                <div :class="isMobile && 'py-2 mt-2'" class="mb-4">
                    <div
                        class="mb-1 text-sm font-semibold">
                        {{ formInfo.description ? formInfo.description.label : $t('approvals.description_label') }}
                    </div>
                    <TextViewer 
                        class="body_text" 
                        :body="approvals.description" />
                </div>
            </template>
            <div v-if="approvals.event_date_start || approvals.event_date_end" class="flex items-center gap-7 mb-4">
                <div v-if="approvals.event_date_start">
                    <div
                        class="mb-1 text-sm font-semibold">
                        {{ formInfo.event_date_start ? formInfo.event_date_start.label : $t('approvals.date_start') }}
                    </div>
                    <div class="flex items-center">
                        <i class="fi fi-rr-calendar-day mr-1" />
                        {{ $moment(approvals.event_date_start).format('DD.MM.YYYY') }}
                    </div>
                </div>
                <div v-if="approvals.event_date_end">
                    <div
                        class="mb-1 text-sm font-semibold">
                        {{ formInfo.event_date_end ? formInfo.event_date_end.label : $t('approvals.date_end') }}
                    </div>
                    <div class="flex items-center">
                        <i class="fi fi-rr-calendar-day mr-1" />
                        {{ $moment(approvals.event_date_end).format('DD.MM.YYYY') }}
                    </div>
                </div>
            </div>
            <div v-if="showAdvanceReport" class="mt-4 mb-4">
                <component 
                    :is="advanceReportComp"
                    :actions="actions"
                    :pageName="pageName"
                    :getDetail="getDetail"
                    :model="model"
                    :approveAdvanceReport="approveAdvanceReport"
                    :notifyFinService="notifyFinService"
                    :detailReload="detailReload"
                    :approvals="approvals" />
            </div>


            <div class="mb-5">
                <div
                    class="text-lg font-semibold flex items-center justify-between block_header mb-3">
                    <div class="flex items-center">
                        <i class="fi fi-rr-comment-alt mr-2" />
                        {{ $t('comments') }}
                    </div>
                </div>
                <vue2CommentsComponent
                    :bodySelector="`${approvals.id}_body_wrap`"
                    :related_object="approvals.id"
                    initScroll
                    :mentionsData="routeUsers"
                    model="processes" />
            </div>

            <div ref="historyBlock" class="history_block">
                <div
                    class="text-lg font-semibold flex items-center justify-between block_header"
                    :class="[isMobile ? 'cursor-pointer block_header_btn' : 'mb-3', historyOpen && 'open mb-3']"
                    @click="toggleHistory">
                    <div class="flex items-center">
                        <i class="fi fi-rr-clock mr-2" /> {{ $t('approvals.history') }}
                    </div>
                    <i
                        v-if="isMobile"
                        class="fi fi-rr-angle-small-down bt_arrow"
                        :class="historyOpen && 'is_open'" />
                </div>

                <div v-show="!isMobile || historyOpen">
                    <History
                        :related_object="approvals.id"
                        injectContainer
                        ref="historyList"
                        :page_size="5"
                        :injectContainerSelector="injectContainerSelector"
                        filterPrefix="approvals"
                        modelLabel="processes.WorkflowRequestModel" />
                </div>
            </div>
        </div>
        <template #footer>
            <div v-if="approvals && actions" class="w-full flex items-center gap-2">
                <a-button 
                    v-if="actions.start && actions.start.availability"
                    type="primary" 
                    size="large" 
                    flaticon
                    icon="fi-rr-play"
                    :block="isMobile"
                    style="padding-left: 30px;padding-right: 30px;"
                    :loading="loading"
                    @click="approvalsStart()">
                    {{ $t('approvals.send_btn') }}
                </a-button>
                <template v-else>
                    <template v-if="actions.give_money && actions.give_money.availability">
                        <a-button 
                            type="primary" 
                            size="large" 
                            icon="fi-rr-coins"
                            flaticon
                            :block="isMobile"
                            style="padding-left: 20px;padding-right: 20px;"
                            :loading="loading"
                            @click="visibleGiveMoney()">
                            {{ $t('approvals.give_money') }}
                        </a-button>
                        <GiveMoneyModal
                            :approvals="approvals"
                            :pageName="pageName"
                            :getDetail="getDetail"
                            :model="model"
                            ref="giveMoneyModal" />
                    </template>

                    <a-button 
                        v-if="actions.approve && actions.approve.availability"
                        :type="inReviewLpr ? 'success' : 'primary'" 
                        size="large" 
                        icon="fi-rr-check-circle"
                        flaticon
                        :block="isMobile"
                        style="padding-left: 20px;padding-right: 20px;"
                        :loading="loading"
                        @click="approvalsApprove()">
                        {{ inReviewLpr ? $t('approvals.lrp_approve') : $t('approvals.approve') }}
                    </a-button>
                    <a-button 
                        v-if="actions.reject && actions.reject.availability"
                        type="flat_danger" 
                        size="large" 
                        :block="isMobile"
                        :loading="loading"
                        @click="rejectVisible()">
                        {{ $t('approvals.reject') }}
                    </a-button>

                    <a-button 
                        v-if="!isMobile && actions.on_rework && actions.on_rework.availability"
                        type="flat_primary" 
                        size="large" 
                        flaticon
                        :block="isMobile"
                        style="padding-left: 30px;padding-right: 30px;"
                        :loading="loading"
                        @click="approvalsOnRework()">
                        {{ $t('approvals.on_rework') }}
                    </a-button>

                    <RejectModal 
                        :approvals="approvals"
                        :pageName="pageName"
                        :getDetail="getDetail"
                        :model="model"
                        ref="rejectModal" />
                </template>
            </div>
            <div v-else></div>
        </template>
    </DrawerTemplate>
</template>

<script>
import { clearTabQuery } from '@/utils/routerUtils.js'
import { errorHandler } from '@/utils/index.js'
import eventBus from '@/utils/eventBus'
import { mapState } from 'vuex'
export default {
    components: {
        DrawerTemplate: () => import('@/components/DrawerTemplate.vue'),
        TextViewer: () => import('@apps/CKEditor/TextViewer.vue'),
        Aside: () => import('./Aside.vue'),
        Steps: () => import('./Steps.vue'),
        RejectModal: () => import('./RejectModal.vue'),
        GiveMoneyModal: () => import('./GiveMoneyModal.vue'),
        RejectedMessage: () => import('./RejectedMessage.vue'),
        History: () => import('@apps/History/index.vue'),
        vue2CommentsComponent: () => import('@apps/vue2CommentsComponent')
    },
    computed: {
        ...mapState({
            user: state => state.user.user
        }),
        issuedAmount() {
            if(!this.approvals)
                return null
            return this.toNumber(this.approvals?.amount_paid)
        },
        routeUsers() {
            if (!this.approvals) return []

            const currentUserId = this.user?.id || null

            const routeUsers = (this.approvals.routes || [])
                .flatMap(route => route.request_route_user_through || [])
                .map(item => item.user)
                .filter(Boolean)

            const author = this.approvals.author ? [this.approvals.author] : []

            const allUsers = [...routeUsers, ...author]
                .filter(user => user.id !== currentUserId)

            const map = new Map()
            allUsers.forEach(user => {
                if (!map.has(user.id)) {
                    map.set(user.id, user)
                }
            })

            return Array.from(map.values())
        },
        showFiles() {
            if(this.approvals && this.actions && this.attachmentsOpen)
                return () => import('@apps/vue2Files')
            return null
        },
        showAdvanceReport() {
            return this.approvals.money_under_report ? true : false
        },
        advanceReportComp() {
            if(this.showAdvanceReport)
                return () => import('./AdvanceReport/index.vue')
            return null
        },
        isMobile() {
            return this.$store.state.isMobile
        },
        drawerWidth() {
            const baseWidth = 1270
            const offset = 40
            return this.windowWidth > baseWidth + offset
                ? baseWidth
                : this.windowWidth
        },
        windowWidth() {
            return this.$store.state.windowWidth
        },
        inReviewLpr() {
            return this.approvals.status?.code === 'in_review_lpr' ? true : false
        }
    },
    watch: {
        '$route.query'(val) {
            if(val.approvals)
                this.visible = true
        }
    },
    data() {
        return {
            model: 'processes.WorkflowRequestModel',
            pageName: 'page_list_processes.WorkflowRequestModel',
            loading: false,
            formInfo: null,
            visible: false,
            actions: null,
            approvals: null,
            detailLoading: false,
            detailReload: false,
            tab: 'info',
            historyOpen: true,
            attachmentsOpen: false
        }
    },
    mounted() {
        if(this.$route.query?.approvals)
            this.visible = true

        this.applyMobileCollapses()
    },
    sockets: {
        workflow_request_update({data}){
            if(data?.id === this.approvals?.id)
                this.updateDetail(data)
        }
    },
    methods: {
        notifyFinService() {
            this.$confirm({
                title: `${this.$t('approvals.notify_fin_service')}?`,
                closable: true,
                maskClosable: false,
                cancelText: this.$t('cancel'),
                okText: this.$t('yes'),
                zIndex: 999999,
                onOk: () => {
                    return new Promise((resolve, reject) => {
                        this.$http.post(`/processes/workflow_requests/${this.approvals.id}/advance_report/notify_fin_service/`)
                            .then(() => {
                                this.$message.success(this.$t('approvals.notify_fin_service_success'))
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
        updateDetail(data) {
            this.markNewCommentsSeen(data)
            this.approvals = data
            this.getActions()
        },
        markNewCommentsSeen(approvals) {
            if (!approvals?.id) return

            this.$set(approvals, 'has_new_comments', false)
            eventBus.$emit('request_approvals_comments_seen', {
                id: approvals.id,
                has_new_comments: false
            })
        },
        toNumber(v) {
            if(v == null) return 0
            const n = Number(String(v).replace(/\s/g, '').replace(',', '.'))
            return Number.isFinite(n) ? n : 0
        },
        applyMobileCollapses() {
            const open = !this.isMobile
            this.historyOpen = open
            this.attachmentsOpen = open
        },
        toggleHistory() {
            if(!this.isMobile) return
            this.historyOpen = !this.historyOpen
        },
        toggleAttachments() {
            if(!this.isMobile)
                return
            this.attachmentsOpen = !this.attachmentsOpen
        },
        injectContainerSelector() {
            return this.$refs.historyBlock
        },
        deleteHandler() {
            this.$confirm({
                title: this.$t('approvals.delete_message'),
                closable: true,
                maskClosable: true,
                cancelText: this.$t('cancel'),
                okText: this.$t('remove'),
                okType: 'danger',
                zIndex: 999999,
                onOk: () => {
                    return new Promise((resolve, reject) => {
                        this.$http.post('/table_actions/update_is_active/', [{ id: this.approvals.id, is_active: false }])
                            .then(() => {
                                this.$message.success(this.$t('approvals.delete_success'))
                                eventBus.$emit(`update_filter_${this.model}_${this.pageName}`)
                                this.visible = false
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
        visibleGiveMoney() {
            this.$nextTick(() => {
                if(this.$refs.giveMoneyModal)
                    this.$refs.giveMoneyModal.openModal()
            })
        },
        rejectVisible() {
            this.$nextTick(() => {
                if(this.$refs.rejectModal)
                    this.$refs.rejectModal.openRejectModal()
            })
        },
        approveAdvanceReport() {
            this.$confirm({
                title: `${this.$t('approvals.approve_advance_report')}?`,
                closable: true,
                maskClosable: false,
                cancelText: this.$t('cancel'),
                okText: this.$t('yes'),
                zIndex: 999999,
                onOk: async () => {
                    try {
                        this.loading = true
                        const { data } = await this.$http.post(`/processes/workflow_requests/${this.approvals.id}/advance_report/approve/`)
                        if(data) {
                            this.$nextTick(() => {
                                if(this.$refs.stepsBlock)
                                    this.$refs.stepsBlock.getSteps()
                            })
                        }
                    } catch(error) {
                        errorHandler({error})
                    } finally {
                        this.loading = false
                    }
                }
            })
        },
        moneyUnderReport() {
            this.$confirm({
                title: `${this.approvals.money_under_report ? this.$t('approvals.no_money_under_report') : this.$t('approvals.money_under_report')}?`,
                closable: true,
                maskClosable: false,
                cancelText: this.$t('cancel'),
                okText: this.$t('yes'),
                zIndex: 999999,
                onOk: async () => {
                    try {
                        this.loading = true
                        const { data } = await this.$http.post(`/processes/workflow_requests/${this.approvals.id}/money_under_report/`, {
                            money_under_report: !this.approvals.money_under_report
                        })
                    } catch(error) {
                        errorHandler({error})
                    } finally {
                        this.loading = false
                    }
                }
            })
        },
        approvalsApprove() {
            this.$confirm({
                title: this.inReviewLpr ? this.$t('approvals.lrp_approve_message') : this.$t('approvals.approve_message'),
                closable: true,
                maskClosable: false,
                cancelText: this.$t('cancel'),
                okText: this.inReviewLpr ? this.$t('approvals.lrp_approve') : this.$t('approvals.approve'),
                zIndex: 999999,
                onOk: async () => {
                    try {
                        this.loading = true
                        const { data } = await this.$http.post(`/processes/workflow_requests/${this.approvals.id}/approve/`)
                        if(data) {
                            this.$nextTick(() => {
                                if(this.$refs.stepsBlock)
                                    this.$refs.stepsBlock.getSteps()
                            })
                        }
                    } catch(error) {
                        errorHandler({error})
                    } finally {
                        this.loading = false
                    }
                }
            })
        },
        async approvalsStart() {
            try {
                this.loading = true
                const { data } = await this.$http.post(`/processes/workflow_requests/${this.approvals.id}/start/`)
                if(data) {
                    this.$nextTick(() => {
                        if(this.$refs.stepsBlock)
                            this.$refs.stepsBlock.getSteps()
                    })
                }
            } catch(error) {
                errorHandler({error})
            } finally {
                this.loading = false
            }
        },
        async approvalsOnRework() {
            this.$confirm({
                title: this.$t('approvals.on_rework_message'),
                closable: true,
                maskClosable: false,
                cancelText: this.$t('cancel'),
                okText: this.$t('approvals.on_rework'),
                zIndex: 999999,
                onOk: async () => {
                    try {
                        this.loading = true
                        const { data } = await this.$http.post(`/processes/workflow_requests/${this.approvals.id}/on_rework/`)
                        if(data) {
                            this.$message.success(this.$t('approvals.on_rework_success'))
                            this.$nextTick(() => {
                                if(this.$refs.stepsBlock)
                                    this.$refs.stepsBlock.getSteps()
                            })
                        }
                    } catch(error) {
                        errorHandler({error})
                    } finally {
                        this.loading = false
                    }
                }
            })
        },
        edit() {
            eventBus.$emit(`edit_request_approvals`, this.approvals)
        },
        async getActions() {
            try {
                const { data } = await this.$http.get(`/processes/workflow_requests/${this.$route.query.approvals}/action_info/`)
                if(data?.actions)
                    this.actions = data.actions
                else
                    this.actions = null
            } catch(error) {
                errorHandler({error, show: false})
            }
        },
        async getFormInfo(approvals) {
            try {
                const { data } = await this.$http.get('/processes/workflow_requests/form_info/', {
                    params: {
                        request_type: approvals.request_type.code
                    }
                })
                if(data) {
                    this.formInfo = data
                }
            } catch(error) {
                errorHandler({error, show : null})
            }
        },
        async getDetail(reload = false) {
            try {
                if(!reload)
                    this.detailLoading = true
                else
                    this.detailReload = true
                const { data } = await this.$http.get(`/processes/workflow_requests/${this.$route.query.approvals}/`)
                if(data) {
                    this.markNewCommentsSeen(data)
                    await this.getFormInfo(data)
                    await this.getActions()
                    if(this.formInfo)
                        this.approvals = data
                    if(!this.isMobile)
                        this.attachmentsOpen = true
                    if(reload) {
                        this.$nextTick(() => {
                            if(this.$refs.stepsBlock)
                                this.$refs.stepsBlock.getSteps()
                        })
                    }
                }
            } catch(error) {
                this.visible = false
                errorHandler({error})
            } finally {
                if(!reload)
                    this.detailLoading = false
                else
                    this.detailReload = false
            }
        },
        afterVisibleChange(vis) {
            if(vis) {
                this.getDetail()
                if(this.$route.query?.approvals) {
                    eventBus.$on(`update_request_approvals_${this.$route.query.approvals}`, () => {
                        this.getDetail(true)
                    })
                }
            } else {
                if(this.$route.query?.approvals)
                    eventBus.$off(`update_request_approvals_${this.$route.query.approvals}`)
                this.closeDrawer()
            }
        },
        closeDrawer() {
            this.actions = null
            this.approvals = null
            this.formInfo = null

            const next = clearTabQuery({
                ...this.$route.query,
                approvals: undefined,
                atab: undefined
            })

            Object.keys(next).forEach(k => {
                if (next[k] === undefined || next[k] === null || next[k] === '') delete next[k]
            })

            const same = JSON.stringify(this.$route.query) === JSON.stringify(next)
            if (same) return

            this.$router.replace({
                name: this.$route.name,
                params: this.$route.params,
                query: next
            })
        }
    }
}
</script>

<style lang="scss">
.approvals_mobile_drawer{
    .drawer_body{
        .drawer_row{
            display: flex;
            width: 100%;
            flex-direction: column-reverse;
            margin: 0px!important;
            .drawer_col{
                padding: 0px!important;
                &:not(:last-child){
                    margin-top: 20px;
                }
            }
        }
    }
}
</style>

<style lang="scss" scoped>
.history_block{
    .block_header{
        &.block_header_btn{
            padding: 10px 15px;
            background: #F8F9FD;
            border-radius: 12px;
            color: #000;
        }
    }
}
.block_header{
    .bt_arrow{
        transition: all 0.3s cubic-bezier(0.645, 0.045, 0.355, 1);
    }
    &.open{
        .bt_arrow{
            transform: rotate(180deg);
        }   
    }
}
.main_status{
    padding: 0 20px;
    border-radius: 30px;
}
</style>
