<template>
    <DrawerTemplate
        :width="drawerWidth"
        class="ticket_drawer"
        xHidden
        v-model="visible"
        destroyOnClose
        useCopyLink
        useOpenLink
        :link="{
            ticketView: ticket ? ticket.id : null,
            ttab: tab
        }"
        @afterVisibleChange="afterVisibleChange"
        @close="visible = false">

        <template v-if="ticket" #title>
            <div class="w-full flex items-center justify-between" style="width: 100%;">
                <!-- ❗️УБРАЛ truncate отсюда, иначе он режет иконку -->
                <div class="text-base font-semibold label flex ticket-title" style="width: 100%; min-width: 0;">
                    <span style="color:#888888; flex: 0 0 auto;">#{{ ticket.number }}</span>

                    <div style="width: 100%; margin-left: 5px; min-width: 0;">
                        <!-- EDIT MODE -->
                        <div
                            v-if="isFormEditEnabled"
                            class="ticket-name-edit">
                            <a-input
                                style="font-size: 18px;"
                                v-model="form.name"
                                ref="nameInput"
                                class="font-semibold ticket-name-input"
                                size="small"
                                :placeholder="$t('helpdesk.appeal_name')"
                                @change="dataChange({field: 'name', useTimer: true})"
                                @keydown.native="onNameKeydown" />
                        </div>

                        <!-- VIEW MODE -->
                        <div
                            v-else
                            class="ticket-name-view">

                            <!-- ✅ truncate теперь только на тексте -->
                            <span class="ticket-name-text truncate">
                                {{ ticket.name }}
                            </span>
                        </div>
                    </div>
                </div>

                <div class="flex items-center gap-3 pl-3">
                    <a-button
                        v-if="isFormEditEnabled"
                        type="primary"
                        shape="round"
                        @click="saveEditMode">
                        {{ $t('helpdesk.save') }}
                    </a-button>
                    <a-button
                        v-if="canStartTicketCall"
                        type="flat_primary"
                        shape="round"
                        icon="fi-rr-phone-flip"
                        flaticon
                        :loading="callLoading"
                        @click="startTicketCall()">
                        {{ $t('chat.call') }}
                    </a-button>
                    <a-button
                        v-if="actions && actions.take && !$store.state.isMobile"
                        icon="fi-rr-user-add"
                        flaticon
                        shape="round"
                        type="flat_primary"
                        @click="takeItem()">
                        {{ $t('helpdesk.take_ticket') }}
                    </a-button>
                    <a-button
                        v-if="edit && !isEditMode"
                        type="ui"
                        shape="circle"
                        flaticon
                        ghost
                        v-tippy
                        :content="$t('edit')"
                        icon="fi-rr-edit"
                        @click="enableEditMode" />
                    <a-button
                        v-if="actions && actions.delete"
                        type="ui"
                        shape="circle"
                        flaticon
                        ghost
                        v-tippy
                        :content="$t('helpdesk.delete')"
                        icon="fi-rr-trash"
                        @click="deleteTicket()" />
                </div>
            </div>
        </template>

        <template v-if="ticket" #tabs>
            <div class="drawer_tabs">
                <a-tabs
                    v-model="tab"
                    :showContent="false"
                    @change="changeTab">
                    <a-tab-pane key="info">
                        <template #tab>
                            {{ $t('helpdesk.basic_information') }}
                        </template>
                    </a-tab-pane>

                    <a-tab-pane key="tasks" v-if="infoRouter.key ==='ticketView'">
                        <template #tab>
                            <div class="flex items-center">
                                <span>{{ $t('helpdesk.ticket_tasks') }}</span>
                                <a-badge
                                    v-if="taskCount"
                                    class="ml-1"
                                    :count="taskCount"
                                    :overflow-count="99" />
                            </div>
                        </template>
                    </a-tab-pane>

                    <a-tab-pane key="calls" v-if="infoRouter.key ==='ticketView'">
                        <template #tab>
                            {{ $t('helpdesk.calls') }}
                        </template>
                    </a-tab-pane>

                    <a-tab-pane key="files" v-if="infoRouter.key ==='ticketView'">
                        <template #tab>
                            <div class="flex items-center">
                                <span>{{ $t('helpdesk.files') }}</span>
                                <a-badge
                                    v-if="filesCount"
                                    class="ml-1"
                                    :count="filesCount"
                                    :overflow-count="99" />
                            </div>
                        </template>
                    </a-tab-pane>

                    <a-tab-pane key="clients-tickets" v-if="infoRouter.key ==='ticketView'">
                        <template #tab>
                            {{ $t('helpdesk.change_history') }}
                        </template>
                    </a-tab-pane>

                    <a-tab-pane key="accounting" v-if="infoRouter.key ==='ticketView'">
                        <template #tab>
                            {{ $t('helpdesk.work_efforts') }}
                        </template>
                    </a-tab-pane>

                    <a-tab-pane key="nomenclature" v-if="infoRouter.key ==='ticketView'">
                        <template #tab>
                            {{ $t('helpdesk.nomenclature') }}
                        </template>
                    </a-tab-pane>
                </a-tabs>
            </div>
        </template>

        <template v-if="ticket">
            <a-tabs
                :activeKey="tab"
                :showBar="false"
                class="body_tab h-full">
                <a-tab-pane key="info" class="flex flex-col">
                    <Info
                        ref="ticketInfoRef"
                        :ticket="ticket"
                        :callLoading="callLoading"
                        :startTicketCall="startTicketCall"
                        :takeItem="takeItem"
                        :showChat="showChat"
                        :edit="isFormEditEnabled"
                        :canEdit="edit"
                        :tab="tab"
                        :actionsTakeDelete="actionsTakeDelete"
                        :slaLoading="slaLoading"
                        :getSLA="getSLA"
                        :slaInfo="slaInfo"
                        :ticketType="ticketType"
                        :forceReload="forceReload"
                        :getActions="getActions"
                        :actions="actions"
                        :getTicket="getTicket"
                        :listPageName="listPageName"
                        :listModel="listModel" />
                </a-tab-pane>

                <a-tab-pane key="tasks" v-if="infoRouter.key ==='ticketView'">
                    <component :is="taskComp" :ticket="ticket" :actions="actions" />
                </a-tab-pane>

                <a-tab-pane key="calls" v-if="infoRouter.key ==='ticketView'">
                    <component :is="callsComp" :ticket="ticket" :actions="actions" />
                </a-tab-pane>

                <a-tab-pane key="files" v-if="infoRouter.key ==='ticketView'">
                    <HelpDeskFiles :isOperator="edit" :isAuthor="edit" :ticket="ticket"/>
                </a-tab-pane>

                <a-tab-pane key="clients-tickets" v-if="infoRouter.key ==='ticketView'">
                    <component :is="ticketsComp" :ticket="ticket" :actions="actions" :model="model" :pageName="pageName" />
                </a-tab-pane>

                <a-tab-pane key="knowledge-base">
                    {{ $t('helpdesk.basic_information') }}
                </a-tab-pane>

                <a-tab-pane key="accounting" v-if="infoRouter.key ==='ticketView'">
                    <component :is="accountingComp" :ticket="ticket" :actions="actions" :getTimer="getTimer"  />
                </a-tab-pane>

                <a-tab-pane key="nomenclature" v-if="infoRouter.key ==='ticketView'">
                    <component :is="nomenclatureComp" :ticket="ticket" :actions="actions" />
                </a-tab-pane>
            </a-tabs>
        </template>

        <template #footer>
            <div class="w-full">
                <div class="chat-float" :class="!showChat && 'is-collapsed'">
                    <ChatList
                        :infoRouter="infoRouter"
                        v-if="ticket && ticket.id"
                        ref="chatList"
                        :ticket="ticket"
                        :edit="edit"
                        :actions="actions"
                        :showChat="showChat"
                        :changeShowChat="changeShowChat" />
                </div>
                <div class="w-full flex items-center">
                    <TicketActions
                        v-if="ticket"
                        ref="ticketActionsRef"
                        :ticket="ticket"
                        :edit="edit"
                        :actionsTakeDelete="actionsTakeDelete"
                        :slaLoading="slaLoading"
                        :getSLA="getSLA"
                        :slaInfo="slaInfo"
                        :ticketType="ticketType"
                        :forceReload="forceReload"
                        :getActions="getActions"
                        :actions="actions"
                        :getTicket="getTicket"
                        :listPageName="listPageName"
                        :listModel="listModel" />
                </div>
            </div>
        </template>
    </DrawerTemplate>
</template>

<script>
import eventBus from '@/utils/eventBus'
import { clearTabQuery } from '@/utils/routerUtils.js'
import { errorHandler } from '@/utils/index.js'
import { startMeetingCall } from '@apps/vue2MeetingComponent/utils/call'
let timer;

export default {
    components: {
        DrawerTemplate: () => import('@/components/DrawerTemplate.vue'),
        Info: () => import('./tabs/Info.vue'),
        HelpDeskFiles: () => import('./tabs/HelpDeskFiles.vue'),
        TicketActions: () => import('./tabs/TicketActions.vue'),
        ChatList: () => import('./components/ChatList/index.vue'),
    },
    computed: {
        windowWidth() { return this.$store.state.windowWidth },
        infoRouter() {
            if (this.$route.query.ticketView){
                return {
                    uid:this.$route.query.ticketView,
                    key:'ticketView'
                }

            }else{
                return {
                    uid:this.$route.query.requestView,
                    key:'requestView'
                }
            }
        },
        drawerWidth() { return this.windowWidth > 1660 ? 1660 : '100%' },
        ticketType() { return this.ticket?.ticket_type?.code || 'issue' },
        edit() {
            return this.actions?.edit?.availability || false
        },
        canStartTicketCall() {
            return Boolean(this.ticket?.id) && !this.$store.state.isMobile
        },
        isFormEditEnabled() {
            return this.edit && this.isEditMode
        },
        listModel() { return 'help_desk.HelpDeskTicketModel' },
        listPageName() { return this.ticketType === 'lead' ? 'help_desk.UnconfirmedAppealsPage' : 'help_desk.HelpDeskTicketModel_page' },
        taskComp() { return this.tab === 'tasks' ? () => import('./tabs/Tasks/index.vue') : null },
        callsComp() { return this.tab === 'calls' ? () => import('./tabs/Calls.vue') : null },
        ticketsComp() { return this.tab === 'clients-tickets' ? () => import('./tabs/History.vue') : null },
        nomenclatureComp() { return this.tab === 'nomenclature' ? () => import('./tabs/Nomenclature.vue') : null },
        accountingComp() { return this.tab === 'accounting' ? () => import('./tabs/Accounting') : null }
    },
    watch: {
        '$route.query'(val) {
            if(val.ticketView) this.visible = true
            if(val.requestView) this.visible = true
        },
        edit(val) {
            if (!val) {
                this.isEditMode = false
                this.isNameEditing = false
            }
        }

    },
    mounted() {
        if(this.$route.query?.ticketView) this.visible = true
        if(this.$route.query?.requestView) this.visible = true
    },
    data() {
        return {
            model: "help_desk.HelpDeskTicketModel",
            pageName: "",
            visible: false,
            ticket: null,
            slaLoading: false,
            tab: 'info',
            loading: false,
            actions: null,
            slaInfo: null,
            showChat: false,
            isNameEditing: false,
            isEditMode: false,
            callLoading: false,
            filesCount: 0,
            taskCount: 0,
            form: { name: "" },
            pendingRequestViewAfterClose: null,
        }
    },
    sockets: {
        ticket_update({data}) {
            if(data && data?.id === this.ticket?.id) {
                this.ticket = data
                this.getTaskCount(data.id)
                const query = {...this.$route.query}
                this.getActions(query)
            }
        }
    },
    methods: {
        changeShowChat(value) { this.showChat = value },

        async startTicketCall() {
            if (!this.ticket?.id) return

            await startMeetingCall({
                endpoint: '/meetings/calls/start/',
                requestUrl: '/meetings/calls/start/',
                method: 'post',
                payload: {
                    ticket_id: this.ticket.id
                },
                context: {
                    ticketId: this.ticket.id,
                    source: 'ticket'
                },
                setLoading: value => {
                    this.callLoading = value
                }
            })
        },

        getTaskPageName(ticketId = this.ticket?.id || this.infoRouter?.uid) {
            return ticketId ? `tasks.TaskModel.Tickets_${ticketId}` : ''
        },

        async getTaskCount(ticketId = this.ticket?.id) {
            if (!ticketId) {
                this.taskCount = 0
                return
            }
            try {
                const params = {
                    page_size: 1,
                    page: 1,
                    page_name: this.getTaskPageName(ticketId),
                    filters: JSON.stringify({ reason: ticketId })
                }
                const { data } = await this.$http.get('/tasks/task/list/', { params })
                this.taskCount = Number(data?.count || 0)
            } catch (error) {
                this.taskCount = 0
                errorHandler({ error, show: false })
            }
        },

        handleTaskCreated() {
            if (this.visible && this.ticket?.id) {
                this.getTaskCount()
            }
        },

        async getFilesCount() {
            try {
                if (!this.ticket?.id) return
                const { data } = await this.$http(`attachments/${ this.ticket.id }/aggregate/`)
                this.filesCount = Number(data?.files || 0)
            } catch (e) {
                this.filesCount = 0
            }
        },

        startNameEdit() {
            if (!this.isFormEditEnabled) return
            this.isNameEditing = true
            this.form.name = this.ticket?.name || ""
            this.$nextTick(() => this.$refs.nameInput?.focus?.())
        },

        enableEditMode() {
            if (!this.edit) return
            this.isEditMode = true
            this.initEdit()
            this.isNameEditing = true
            this.form.name = this.ticket?.name || ""
            this.$nextTick(() => {
                this.$refs.ticketInfoRef?.initEdit?.()
                this.$refs.nameInput?.focus?.()
            })
        },

        async saveEditMode() {
            if (!this.isFormEditEnabled) return
            await this.stopNameEdit(true)
            const isSaved = await this.$refs.ticketInfoRef?.saveEdit?.()
            if (isSaved === false) return
            await this.getTicket(true, false)
            this.isEditMode = false
            this.$message.success(this.$t('Changes saved'))
        },

        async stopNameEdit(save = true) {
            if (!this.isNameEditing) return
            this.isNameEditing = false

            if (!save) {
                this.form.name = this.ticket?.name || ""
                clearTimeout(timer)
                return
            }

            const newVal = (this.form.name || "").trim()
            const oldVal = (this.ticket?.name || "").trim()
            if (!newVal || newVal === oldVal) {
                this.form.name = this.ticket?.name || ""
                clearTimeout(timer)
                return
            }

            clearTimeout(timer)
            await this.patchField(newVal, 'name')
        },

        onNameKeydown(e) {
            if (e.key === 'Enter') { e.preventDefault(); this.stopNameEdit(true) }
            if (e.key === 'Escape') { e.preventDefault(); this.stopNameEdit(false) }
        },

        initEdit() {
            if (this.edit) this.form = { name: this.ticket.name }
            this.isNameEditing = false
        },

        dataChange({ field, useTimer = false, valueKey = false, multiple = false }) {
            let value = this.form[field]
            if(valueKey) value = multiple ? this.form[field].map(fld => fld[valueKey]) : this.form[field][valueKey]

            if(useTimer) {
                clearTimeout(timer)
                timer = setTimeout(() => this.patchField(value, field), 600)
            } else {
                this.patchField(value, field)
            }
        },

        async patchField(value, field) {
            try {
                if(field === 'name' && !value) {
                    this.$message.warning(this.$t('helpdesk.name_required_warning'))
                    return false
                }
                const { data } = await this.$http.patch(`/help_desk/tickets/${this.ticket.id}/`, {
                    [field]: value,
                    metadata: this.form.metadata
                })
                if (data) {
                    if (this.ticket && data[field] !== undefined) this.$set(this.ticket, field, data[field])
                    const kanbanObj = { ...data }
                    if (kanbanObj.sla?.sla) kanbanObj.sla = kanbanObj.sla.sla
                    eventBus.$emit('UPDATE_TICKET_KANBAN', kanbanObj)
                    if (this.$store.hasModule('workplan')) {
                        this.$store.dispatch('workplan/updateItem', {
                            item: { id: this.ticket.id },
                            list: 'ticketList'
                        })
                    }
                }
            } catch(error) {
                if(error?.non_field_errors?.length && error.non_field_errors[0].includes("не является ответственным")) {
                    this.forceReload(false)
                }
                errorHandler({error})
            }
        },

        actionsTakeDelete() {
            if(this.actions.take) this.$delete(this.actions, 'take')
        },

        takeItem() {
            this.$confirm({
                title: this.$t('helpdesk.take_ticket'),
                content: this.$t('helpdesk.take_message'),
                cancelText: this.$t('no'),
                okText: this.$t('yes'),
                onOk: async () => {
                    try {
                        const { data } = await this.$http.post(`/help_desk/tickets/${this.ticket.id}/take/`)
                        if(data) {
                            this.actionsTakeDelete()
                            this.getTicket(false, true, true)
                            eventBus.$emit(`update_filter_${this.listModel}_${this.listPageName}`)
                            eventBus.$emit('UPDATE_TICKET_KANBAN', data)
                            if (this.$store.hasModule('workplan')) {
                                this.$store.dispatch('workplan/updateItem', {
                                    item: { id: this.ticket.id },
                                    list: 'ticketList'
                                })
                            }
                        }
                    } catch(error) {
                        errorHandler({error})
                    }
                }
            })
        },

        getTimer() {
            this.$nextTick(() => {
                this.$refs.ticketInfoRef?.updateTimer?.()
                this.$refs.ticketActionsRef?.updateTimer?.()
            })
        },

        deleteTicket() {
            this.$confirm({
                title: this.$t('helpdesk.confirm_delete_ticket'),
                closable: true,
                maskClosable: true,
                cancelText: this.$t('helpdesk.cancel'),
                okText: this.$t('helpdesk.delete'),
                okType: 'danger',
                zIndex: 999999,
                onOk: () => new Promise((resolve, reject) => {
                    this.$http.post('/table_actions/update_is_active/', [{ id: this.ticket.id, is_active: false }])
                        .then(() => {
                            this.$message.success(this.$t('helpdesk.ticket_deleted'))
                            eventBus.$emit(`update_filter_${this.listModel}_${this.listPageName}`)
                            eventBus.$emit('DELETE_TICKET_KANBAN', this.ticket)
                            if (this.$store.hasModule('workplan')) {
                                this.$store.dispatch('workplan/deleteItem', {
                                    item: this.ticket,
                                    list: 'ticketList'
                                })
                            }
                            this.visible = false
                            resolve()
                        })
                        .catch((error) => {
                            errorHandler({error})
                            reject()
                        })
                })
            })
        },

        changeTab(val) {
            const query = {...this.$route.query}
            query.ttab = val
            this.$router.push({query})
        },

        async getActions(query) {
            try {
                var urlActions =`/help_desk/tickets/${query.requestView}/for_client/action_info/`
                if (this.infoRouter.key ==='ticketView'){
                    urlActions =`/help_desk/tickets/${this.infoRouter.uid}/action_info/`
                }
                const { data } = await this.$http.get(urlActions)

                if(data?.actions) this.actions = data.actions

                if (this.infoRouter.key !=='ticketView'){
                    urlActions =`/help_desk/tickets/${this.infoRouter.uid}/action_info/`
                    let data_actions = await this.$http.get(urlActions)
                    if (data_actions.data.actions?.edit?.availability){
                        const next = clearTabQuery({
                            ...this.$route.query,
                            ticketView: this.infoRouter.uid,
                            requestView: undefined,
                            ttab: undefined
                        })
                        this.$router.replace({
                            name: this.$route.name,
                            params: this.$route.params,
                            query: next
                        })
                    }

                }
            } catch(e) {
                console.log(e)
            }
        },

        forceReload(loading = true) {
            this.actions = null
            this.ticket = null
            this.tab = 'info'
            this.isEditMode = false
            this.isNameEditing = false
            this.filesCount = 0
            this.taskCount = 0
            this.getTicket(false, loading)
        },

        switchTicketViewToRequestView(ticketId) {
            this.pendingRequestViewAfterClose = ticketId
            this.visible = false
        },

        async openRequestViewAfterTicketClose(ticketId) {
            this.actions = null
            this.ticket = null
            this.slaInfo = null
            this.tab = 'info'
            this.isEditMode = false
            this.isNameEditing = false
            this.filesCount = 0
            this.taskCount = 0

            const next = clearTabQuery({
                ...this.$route.query,
                ticketView: undefined,
                requestView: ticketId,
                ttab: undefined
            })

            Object.keys(next).forEach(k => {
                if (next[k] === undefined || next[k] === null || next[k] === '') delete next[k]
            })

            await this.$router.replace({
                name: this.$route.name,
                params: this.$route.params,
                query: next
            }).catch(() => {})
        },

        async getSLA() {
            try {
                this.slaLoading = true
                const { data } = await this.$http.get(`/sla/${this.infoRouter.uid}/value/`)
                if(data?.sla) this.slaInfo = data
            } catch(error) {
                console.log(error)
            } finally {
                this.slaLoading = false
            }
        },

        async getTicket(reload = false, loading = true, initEdit = false) {
            const routeInfo = { ...this.infoRouter }
            try {
                if(loading) this.loading = true
                const query = {...this.$route.query}
                var urlTicket = `/help_desk/tickets/${routeInfo.uid}/for_client/detail/`
                if (routeInfo.key ==='ticketView'){
                    urlTicket =`/help_desk/tickets/${routeInfo.uid}/`
                }
                const { data } = await this.$http.get(urlTicket)
                if(data) {
                    this.getSLA()
                    if(!reload) {
                        await this.getActions(query)
                        if (this.infoRouter.key ==='ticketView'){
                            this.pageName = `list_help_desk.tickets_${data.id}`
                        }else{
                            this.pageName = `list_help_desk_request.tickets_${data.id}`
                        }

                    }
                    this.ticket = data
                    await this.getTaskCount(data.id)
                    await this.getFilesCount()

                    if(initEdit) {
                        this.$nextTick(() => {
                            this.$refs.ticketInfoRef?.initEdit?.()
                            this.$refs.ticketActionsRef?.initEdit?.()
                        })
                    }
                }
                this.initEdit()
            } catch(error) {
                if(error?.status === 403 && routeInfo.key === 'ticketView' && routeInfo.uid) {
                    this.switchTicketViewToRequestView(routeInfo.uid)
                    return
                }
                this.visible = false
                errorHandler({error})
            } finally {
                if(loading) this.loading = false
            }
        },

        async afterVisibleChange(vis) {
            if(vis) {
                if(this.$route.query?.ttab) this.tab = this.$route.query.ttab
                this.getTicket()
                const taskPageName = this.getTaskPageName(this.infoRouter?.uid)
                eventBus.$on('ticket_detail_reload', () => this.getTicket())
                eventBus.$on('ticket_detail_reload_force', () => this.forceReload())
                eventBus.$on('ticket_in_client_reload', () => this.getTicket())
                eventBus.$on('ticket_drawer_close', () => { this.visible = false })
                eventBus.$on(`TASK_CREATED_task_${taskPageName}`, this.handleTaskCreated)
                eventBus.$on(`update_filter_${taskPageName}`, this.handleTaskCreated)
                eventBus.$on('TASK_CREATED_task', this.handleTaskCreated)
            } else {
                const pendingRequestView = this.pendingRequestViewAfterClose
                this.pendingRequestViewAfterClose = null
                const taskPageName = this.getTaskPageName(this.infoRouter?.uid)
                await this.closeDrawer()
                eventBus.$off('ticket_detail_reload')
                eventBus.$off('ticket_in_client_reload')
                eventBus.$off('ticket_detail_reload_force')
                eventBus.$off('ticket_drawer_close')
                eventBus.$off(`TASK_CREATED_task_${taskPageName}`, this.handleTaskCreated)
                eventBus.$off(`update_filter_${taskPageName}`, this.handleTaskCreated)
                eventBus.$off('TASK_CREATED_task', this.handleTaskCreated)

                if (pendingRequestView) {
                    await this.$nextTick()
                    await this.openRequestViewAfterTicketClose(pendingRequestView)
                }
            }
        },

        async closeDrawer() {
            this.tab = 'info'
            this.actions = null
            this.ticket = null
            this.slaInfo = null
            this.isEditMode = false
            this.isNameEditing = false
            this.filesCount = 0
            this.taskCount = 0

            const next = clearTabQuery({
                ...this.$route.query,
                ticketView: undefined,
                requestView: undefined,
                ttab: undefined
            })

            Object.keys(next).forEach(k => {
                if (next[k] === undefined || next[k] === null || next[k] === '') delete next[k]
            })

            const same = JSON.stringify(this.$route.query) === JSON.stringify(next)
            if (same) return

            return this.$router.replace({
                name: this.$route.name,
                params: this.$route.params,
                query: next
            }).catch(() => {})
        }
    }
}
</script>

<style lang="scss" scoped>
/* ==========================
   ЗАГОЛОВОК: ИМЯ + КАРАНДАШ
   ========================== */

.ticket-title{
    overflow: visible; /* важно: не режем иконку */
    min-width: 0;
}

.ticket-name-view,
.ticket-name-edit{
    display: flex;
    align-items: center;
    gap: 8px;
    width: 100%;
    min-width: 0;
    overflow: visible;
}

/* truncate только на тексте */
.ticket-name-text{
    min-width: 0;
    flex: 1 1 auto;
}

/* input не должен выдавливать иконку */
.ticket-name-input{
    flex: 1 1 auto;
    min-width: 0;
    width: 100% !important;
}

.ticket-name-edit .ticket-name-input::v-deep .ant-input{
    border: 1px solid #d9d9d9 !important;
    border-radius: 6px;
    background: #fff;
}

/* ==========================
   ВСПЛЫВАЮЩИЙ ЧАТ
   ========================== */
.chat-float{
    position: fixed;
    right: 40px;
    bottom: 40px;
    width: 800px;
    height: 600px;
    max-height: calc(100vh - 200px);
    z-index: 1000;
    min-width: 0;
}
.chat-float.is-collapsed{
    width: 50px;
    height: 50px;
}

@media (max-width: 768px) {
    .chat-float{
        bottom: 120px;
        left: 16px;
        right: 16px;
        width: auto;
        height: 70vh;
        max-height: calc(100vh - 200px);
    }
    .chat-float.is-collapsed{
        left: auto;
        width: 56px;
        height: 56px;
        right: 16px;
    }
}
</style>
