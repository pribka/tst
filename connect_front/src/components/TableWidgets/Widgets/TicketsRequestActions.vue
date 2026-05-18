<template>
    <a-dropdown :trigger="['click']" @visibleChange="visibleChange">
        <a-button 
            type="ui" 
            ghost 
            flaticon 
            :loading="loading"
            size="small"
            icon="fi-rr-menu-dots-vertical"
            :destroyPopupOnHide="false" />
        <a-menu slot="overlay">
            <a-menu-item key="open" class="flex items-center" @click="openClient()">
                <i class="fi fi-rr-link-alt mr-2" />
                {{ $t('open') }}
            </a-menu-item>
            <template v-if="actions">
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
        }
    },
    computed: {
        ...mapState({
            user: state => state.user.user
        })
    },
    data() {
        return {
            loading: false,
            listLoading: false,
            actions: null,
            listModel: "help_desk.HelpDeskTicketModel",
        }
    },
    methods: {
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
                            .catch((e) => {
                                console.log(e)
                                reject()
                            })
                    })
                }
            })
        },
        openClient() {
            const query = {...this.$route.query}
            if(!query.requestView) {
                query.requestView = this.record.id
                this.$router.push({query})
            } else {
                eventBus.$emit('ticket_request_drawer_close')
                setTimeout(() => {
                    query.requestView = this.record.id
                    this.$router.push({query})
                }, 500)
            }
        },
        async getActions() {
            if(!this.actions) {
                try {
                    this.loading = true
                    this.listLoading = true
                    const { data } = await this.$http.get(`/help_desk/tickets/${this.record.id}/for_client/action_info/`)
                    if(data?.actions) {
                        this.actions = data.actions
                    }
                } catch(e) {
                    console.log(e)
                } finally {
                    this.loading = false
                    this.listLoading = false
                }
            }
        },
        visibleChange(visible) {
            if(visible) {
                this.getActions()
            }
        }
    }
}
</script>