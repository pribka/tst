<template>
    <a-dropdown 
        :trigger="['click']" 
        @visibleChange="visibleChange"
        :getPopupContainer="getPopupContainer">
        <a-button 
            type="ui" 
            ghost 
            flaticon 
            shape="circle"
            :loading="loading"
            size="small"
            icon="fi-rr-menu-dots-vertical"
            :destroyPopupOnHide="false" />
        <a-menu slot="overlay">
            <a-menu-item key="open" class="flex items-center" @click="openClient()">
                <i class="fi fi-rr-link-alt mr-2" />
                {{ $t('helpdesk.open') }}
            </a-menu-item>
            <a-menu-item v-if="useSpam && record.contact_person && record.contact_person.unknown" key="take" class="flex items-center" @click="maskAsSpam(record.contact_person)">
                <i class="fi fi-rr-message-xmark mr-2" />
                {{ $t('helpdesk.to_spam') }}
            </a-menu-item>
            <template v-if="actions">
                <!--<template v-if="statusList.length">
                    <a-menu-item 
                        v-for="status in filteredStatusList" 
                        :key="status.code" 
                        class="flex items-center" 
                        @click="changeStatus(status.code)">
                        <a-badge :color="status.color" class="mr-2" />
                        {{ status.name }}
                    </a-menu-item>
                </template>-->
                <a-menu-item v-if="actions.take" key="take" class="flex items-center" @click="takeItem()">
                    <i class="fi fi-rr-user-add mr-2" />
                    {{ $t('helpdesk.take_ticket') }}
                </a-menu-item>
                <template v-if="actions.delete">
                    <a-menu-divider />
                    <a-menu-item key="delete" class="flex items-center" @click="deleteItem()">
                        <i class="fi fi-rr-trash mr-2" />
                        {{ $t('remove') }} 
                    </a-menu-item>
                </template>
            </template>
            <a-menu-item v-if="listLoading">
                <div class="flex justify-center">
                    <a-spin size="small" />
                </div>
            </a-menu-item>
        </a-menu>
    </a-dropdown>
</template>

<script>
import eventBus from '@/utils/eventBus'
import { mapState } from 'vuex'
import { errorHandler } from '@/utils/index.js'
export default {
    props: {
        main: { // Если вставляем этот компонент куда то помимо страницы задач, тут надо ставить false
            type: Boolean,
            default: false
        },
        record: {
            type: Object,
            required: true
        },
        text: {
            type: [Object, Number, String],
        },
        expandedRowKeys: {
            type: Array,
        },
        expanded: {
            type: Number,
        },
        extendDrawer: {
            type: Boolean,
            default: false
        },
        showChildren: { // Показывать или возможность раскрыть задачу с подзадачами
            type : Boolean,
            default: true
        },
        indent: {
            type: Object,
        },
        column: {
            type: Object,
            default: () => null
        },
        openTask: {
            type: Function,
            default: () => {}
        },
        reloadTask: {
            type: Function,
            default: () => {}
        },
        pageName: {
            type: String,
            default: ''
        },
        colParams: {
            type: Object,
            default: () => null
        }
    },
    computed: {
        ...mapState({
            user: state => state.user.user
        }),
        filteredStatusList() {
            return this.statusList.filter(status => status.code !== this.record.status?.code)
        },
        useSpam() {
            return this.colParams?.useSpam || false
        }
    },
    data() {
        return {
            loading: false,
            listLoading: false,
            actions: null,
            statusList: [],
            listModel: "help_desk.HelpDeskTicketModel",
        }
    },
    methods: {
        maskAsSpam(contactPerson) {
            this.$http.post(`help_desk/contact_persons/${contactPerson.id}/mark_as_spam/`)
                .then(({ data }) => {
                    if(data) {
                        this.$message.success(this.$t('helpdesk.contact_marked_spam'))
                        eventBus.$emit('ticket_drawer_close')
                    }
                })
                .catch((error) => {
                    errorHandler({error})
                })
        },
        takeItem() {
            this.$confirm({
                title: this.$t('helpdesk.take_ticket'),
                content: this.$t('helpdesk.take_message'),
                cancelText: this.$t('no'),
                okText: this.$t('yes'),
                onOk: async () => {
                    try {
                        const { data } = await this.$http.post(`/help_desk/tickets/${this.record.id}/take/`)
                        if(data) {
                            eventBus.$emit(`update_filter_${this.listModel}_${this.pageName}`)
                            eventBus.$emit('UPDATE_TICKET_KANBAN', data)
                        }
                    } catch(error) {
                        errorHandler({error})
                    }
                }
            })
        },
        async changeStatus(status) {
            try {
                this.loading = true
                const { data } = await this.$http.put(`/help_desk/tickets/${this.record.id}/status/`, {
                    status
                })
                if(data) {
                    eventBus.$emit(`update_filter_${this.listModel}_${this.pageName}`)
                    eventBus.$emit('STATUS_TICKET_KANBAN', {
                        task: data,
                        status
                    })
                }
            } catch(error) {
                errorHandler({error})
            } finally {
                this.loading = false
            }
        },
        deleteItem() {
            this.$confirm({
                title: 'Вы действительно хотите удалить тикет?',
                closable: true,
                maskClosable: true,
                cancelText: 'Отмена',
                okText: 'Удалить',
                okType: 'danger',
                zIndex: 999999,
                onOk: () => {
                    return new Promise((resolve, reject) => {
                        this.$http.post('/table_actions/update_is_active/', [{ id: this.record.id, is_active: false }])
                            .then(() => {
                                this.$message.success('Тикет удален')
                                eventBus.$emit(`update_filter_${this.listModel}_${this.pageName}`)
                                eventBus.$emit('DELETE_TICKET_KANBAN', this.record)
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
        openClient() {
            const query = {...this.$route.query}
            if(!query.ticketView) {
                query.ticketView = this.record.id
                this.$router.push({query})
            } else {
                eventBus.$emit('ticket_drawer_close')
                setTimeout(() => {
                    query.ticketView = this.record.id
                    this.$router.push({query})
                }, 500)
            }
        },
        async getActions() {
            if(!this.actions) {
                try {
                    this.loading = true
                    this.listLoading = true
                    const { data } = await this.$http.get(`/help_desk/tickets/${this.record.id}/action_info/`)
                    if(data?.actions) {
                        /*if(data.actions?.change_status?.availability) {
                            this.statusList = data.actions.change_status.available_statuses
                        }*/
                        this.actions = data.actions
                    }
                } catch(error) {
                    errorHandler({error, show: false})
                } finally {
                    this.loading = false
                    this.listLoading = false
                }
            }
        },
        async getStatus() {
            if(!this.statusList?.length) {
                try {
                    const { data } = await this.$http.get('/help_desk/tickets/statuses/')
                    if(data?.length) {
                        this.statusList = data
                    }
                } catch(error) {
                    errorHandler({error, show: false})
                }
            }
        },
        visibleChange(visible) {
            if(visible) {
                this.getActions()
            }
        },
        getPopupContainer() {
            return this.colParams.getPopupContainer()
        }

    }
}
</script>