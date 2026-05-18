<template>
    <DrawerTemplate
        :width="drawerWidth"
        class="ticket_drawer"
        v-model="visible"
        destroyOnClose
        :disabledBodyPadding="isMobileChat"
        @afterVisibleChange="afterVisibleChange"
        @close="visible = false">
        <template v-if="ticket" #title>
            <div class="w-full flex items-center justify-between">
                <div class="drawer_title">
                    #{{ ticket.number }}
                </div>
                <div class="flex items-center pl-3">
                    <a-button
                        v-if="actions && actions.delete"
                        type="ui"
                        shape="circle"
                        flaticon
                        ghost
                        v-tippy
                        :content="$t('helpdesk.delete')"
                        icon="fi-rr-trash"
                        class="mr-3"
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
                            {{ isMobile ? $t('helpdesk.information') : $t('helpdesk.basic_information') }}
                        </template>
                    </a-tab-pane>
                    <a-tab-pane v-if="isMobile" key="chat">
                        <template #tab>
                            {{ $t('helpdesk.chat') }}
                        </template>
                    </a-tab-pane>
                    <a-tab-pane v-if="taskCount > 0" key="tasks">
                        <template #tab>
                            {{ $t('helpdesk.ticket_tasks') }}
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
                <a-tab-pane v-if="isMobile" key="chat" class="flex flex-col">
                    <Chat
                        :ticket="ticket"
                        :actions="actions" />
                </a-tab-pane>
                <a-tab-pane key="info" class="flex flex-col">
                    <Info
                        ref="ticketSidebar"
                        :ticket="ticket"
                        :edit="edit"
                        :tab="tab"
                        :ticketType="ticketType"
                        :forceReload="forceReload"
                        :getActions="getActions"
                        :actions="actions"
                        :getTicket="getTicket"
                        :listPageName="listPageName"
                        :listModel="listModel" />
                </a-tab-pane>
                <a-tab-pane v-if="taskCount > 0" key="tasks">
                    <Tasks
                        :ticket="ticket"
                        :actions="actions" />
                </a-tab-pane>
            </a-tabs>
        </template>
    </DrawerTemplate>
</template>

<script>
import eventBus from '@/utils/eventBus'
import { clearTabQuery } from '@/utils/routerUtils.js'
import { errorHandler } from '@/utils/index.js'
export default {
    components: {
        DrawerTemplate: () => import('@/components/DrawerTemplate.vue'),
        Info: () => import('./tabs/Info.vue'),
        Tasks: () => import('./tabs/Tasks/index.vue'),
        Chat: () => import('./tabs/chat.vue')
    },
    computed: {
        isMobile() {
            return this.$store.state.isMobile
        },
        windowWidth() {
            return this.$store.state.windowWidth
        },
        drawerWidth() {
            if(this.windowWidth > 1660)
                return 1660
            else {
                return '100%'
            }
        },
        ticketType() {
            if(this.ticket?.ticket_type?.code)
                return this.ticket.ticket_type?.code
            return 'issue'
        },
        edit() {
            if(this.ticket.status?.code === 'completed')
                return false
            return this.actions?.edit?.availability || false
        },
        listModel() {
            return 'help_desk.HelpDeskForClientTicketModel'
        },
        listPageName() {
            return 'help_desk.HelpDeskForClientTicketModel_page'
        },
        isMobileChat() {
            if(this.isMobile && this.tab === 'chat')
                return true
            return false
        }
    },
    watch: {
        '$route.query'(val) {
            if(val.requestView) {
                this.visible = true
            }
        }
    },
    mounted() {
        if(this.$route.query?.requestView) {
            this.visible = true
        }
    },
    data() {
        return {
            model: "help_desk.HelpDeskTicketModel",
            pageName: "",
            visible: false,
            ticket: null,
            tab: this.isMobile ? 'info' : 'info',
            loading: false,
            actions: null,
            taskCount: 0
        }
    },
    methods: {
        getTaskPageName(ticketId = this.ticket?.id || this.$route.query?.requestView) {
            return ticketId ? `tasks.TaskModel.Tickets_${ticketId}` : ''
        },
        async getTaskCount(ticketId = this.ticket?.id || this.$route.query?.requestView) {
            if(ticketId) {
                try {
                    const params = {
                        page_size: 1,
                        page: 1,
                        page_name: this.getTaskPageName(ticketId),
                        filters: JSON.stringify({ reason: ticketId })
                    }
                    const { data } = await this.$http.get('/tasks/task/list/', { params })
                    if(data) {
                        this.taskCount = data.count
                    }
                } catch(error) {
                    errorHandler({error, show: false})
                }
            } else {
                this.taskCount = 0
            }
        },
        handleTaskCreated() {
            if(this.visible) {
                this.getTaskCount()
            }
        },
        getTimer() {
            this.$nextTick(() => {
                if(this.$refs.ticketSidebar) {
                    this.$refs.ticketSidebar.updateTimer()
                }
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
                onOk: () => {
                    return new Promise((resolve, reject) => {
                        this.$http.post('/table_actions/update_is_active/', [{ id: this.ticket.id, is_active: false }])
                            .then(() => {
                                this.$message.success(this.$t('helpdesk.ticket_deleted'))
                                eventBus.$emit(`update_filter_${this.listModel}_${this.listPageName}`)
                                eventBus.$emit('DELETE_TICKET_KANBAN', this.ticket)
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
        changeTab(val) {
            const query = {...this.$route.query}
            query.rtab = val
            this.$router.push({query})
        },
        async getActions(query) {
            try {
                const { data } = await this.$http.get(`/help_desk/tickets/${query.requestView}/for_client/action_info/`)
                if(data?.actions) {
                    this.actions = data.actions
                }
            } catch(error) {
                errorHandler({error, show: false})
            }
        },
        forceReload(loading = true) {
            this.actions = null
            this.ticket = null
            this.tab = this.isMobile ? 'info' : 'info'
            this.getTicket(false, loading)
        },
        async getTicket(reload = false, loading = true) {
            try {
                if(loading)
                    this.loading = true
                const query = {...this.$route.query}
                const { data } = await this.$http.get(`/help_desk/tickets/${query.requestView}/for_client/detail/`)
                if(data) {
                    if(!reload) {
                        await this.getActions(query)
                        this.pageName = `list_help_desk_request.tickets_${data.id}`
                    }
                    this.ticket = data
                    await this.getTaskCount(data.id)
                }
            } catch(error) {
                this.visible = false
                errorHandler({error})
            } finally {
                if(loading)
                    this.loading = false
            }
        },
        afterVisibleChange(vis) {
            if(vis) {
                const taskPageName = this.getTaskPageName()
                if(this.$route.query?.rtab) {
                    if(!this.isMobile) {
                        if(this.$route.query.rtab === 'chat') {
                            const query = JSON.parse(JSON.stringify(this.$route.query))
                            delete query.rtab
                            this.$router.replace({query})
                            this.tab = 'info'
                        } else {
                            this.tab = this.$route.query.rtab
                        }
                    } else {
                        this.tab = this.$route.query.rtab
                    }
                }
                this.getTicket()
                this.getTaskCount()
                eventBus.$on('ticket_request_detail_reload', () => {
                    this.getTicket()
                })
                eventBus.$on('ticket_request_detail_reload_force', () => {
                    this.forceReload()
                })
                eventBus.$on('ticket_request_in_client_reload', () => {
                    this.getTicket()
                })
                eventBus.$on('ticket_request_drawer_close', () => {
                    this.visible = false
                })
                eventBus.$on(`TASK_CREATED_task_${taskPageName}`, this.handleTaskCreated)
                eventBus.$on(`update_filter_${taskPageName}`, this.handleTaskCreated)
                eventBus.$on('TASK_CREATED_task', this.handleTaskCreated)
            } else {
                const taskPageName = this.getTaskPageName()
                this.closeDrawer()
                eventBus.$off('ticket_request_detail_reload')
                eventBus.$off('ticket_request_in_client_reload')
                eventBus.$off('ticket_request_detail_reload_force')
                eventBus.$off('ticket_request_drawer_close')
                eventBus.$off(`TASK_CREATED_task_${taskPageName}`, this.handleTaskCreated)
                eventBus.$off(`update_filter_${taskPageName}`, this.handleTaskCreated)
                eventBus.$off('TASK_CREATED_task', this.handleTaskCreated)
            }
        },
        closeDrawer() {
            this.tab = this.isMobile ? 'info' : 'info'
            this.actions = null
            this.ticket = null
            this.taskCount = 0

            const next = clearTabQuery({
                ...this.$route.query,
                requestView: undefined,
                rtab: undefined
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
