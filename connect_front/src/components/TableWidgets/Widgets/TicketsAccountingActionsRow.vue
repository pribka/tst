<template>
    <div class="worklog_actions">
        <!-- ✅ MOBILE: показываем кнопки как "в первой версии" -->
        <div v-if="isMobile" class="item_field w-full flex items-center gap-2 mt-4">
            <a-button
                class="w-full"
                v-if="actions?.edit?.availability"
                :loading="actionsLoading"
                type="flat_primary"
                @click="editAccouting()">
                {{ $t('edit') }}
            </a-button>

            <a-button
                class="w-full"
                v-if="actions?.delete?.availability"
                :loading="actionsLoading"
                type="flat_danger"
                @click="deleteAccouting()">
                {{ $t('Delete') }}
            </a-button>
        </div>

        <!-- ✅ DESKTOP: оставляем ⋮ dropdown -->
        <a-dropdown
            v-else
            :trigger="['click']"
            :destroyPopupOnHide="false"
            @visibleChange="visibleChange"
            :getPopupContainer="getPopupContainer">
            <a-button
                icon="fi-rr-menu-dots-vertical"
                flaticon
                shape="circle"
                :loading="actionsLoading"
                ghost
                size="small"
                type="ui" />
            <a-menu slot="overlay">
                <a-menu-item
                    v-if="actions?.edit?.availability"
                    class="flex items-center"
                    key="edit"
                    @click="editAccouting()">
                    <i class="fi fi-rr-edit mr-2" />
                    {{ $t('edit') }}
                </a-menu-item>

                <a-menu-item
                    v-if="actions?.delete?.availability"
                    class="text-red-500 flex items-center"
                    key="delete"
                    @click="deleteAccouting()">
                    <i class="fi fi-rr-trash mr-2" />
                    {{ $t('Delete') }}
                </a-menu-item>

                <a-menu-item
                    v-if="!actionsLoading && disabledButton"
                    class="text-muted flex items-center"
                    key="no_action">
                    {{ $t('no_actions') }}
                </a-menu-item>
            </a-menu>
        </a-dropdown>
    </div>
</template>

<script>
import eventBus from '@/utils/eventBus'
import { mapState } from 'vuex'

export default {
    props: {
        record: { type: Object, required: true },
        colParams: { type: Object, default: () => null }
    },
    data() {
        return {
            listModel: 'help_desk.HelpDeskTicketWorkLogModel',
            listPageName: `work_log_${this.colParams?.id || 'new'}`,
            actions: null,
            actionsLoading: false
        }
    },
    computed: {
        ...mapState({
            user: state => state.user.user
        }),
        isMobile() {
            return this.$store.state.isMobile
        },
        disabledButton() {
            return !(this.actions?.delete?.availability || this.actions?.edit?.availability)
        },
        isAuthor() {
            return this.record.user?.id === this.user?.id
        }
    },
    methods: {
        getActionInfo() {
            const url = `/help_desk/tickets/work_log/${this.record.id}/action_info/`
            this.actionsLoading = true
            this.actions = null
            this.$http.get(url)
                .then(({ data }) => {
                    this.actions = data.actions
                })
                .catch((error) => {
                    console.error(error)
                })
                .finally(() => {
                    this.actionsLoading = false
                })
        },
        visibleChange(visible) {
            if (!visible) return
            this.getActionInfo()
        },
        editAccouting() {
            eventBus.$emit(`edit_accounting_${this.colParams?.id || 'new'}`, this.record)
        },
        deleteAccouting() {
            if (!this.colParams?.id) return

            this.$confirm({
                title: 'Вы действительно хотите удалить трудозатрату?',
                content: '',
                okText: this.$t('remove'),
                okType: 'danger',
                zIndex: 2000,
                closable: true,
                maskClosable: true,
                cancelText: this.$t('Close'),
                onOk: () => {
                    return new Promise((resolve, reject) => {
                        this.$http.post(`/help_desk/tickets/${this.colParams.id}/work_log/delete/`, { id: this.record.id })
                            .then(() => {
                                this.$message.success('Трудозатрата удалена')
                                eventBus.$emit(`update_filter_${this.listModel}_${this.listPageName}`)
                                this.colParams.getTimer && this.colParams.getTimer()
                                resolve()
                            })
                            .catch(e => reject(e))
                    })
                }
            })
        },
        getPopupContainer() {
            return this.colParams?.getPopupContainer ? this.colParams.getPopupContainer() : document.body
        }
    },
    mounted() {
        // ✅ на мобилке сразу подгружаем действия, чтобы кнопки корректно показались/скрылись
        if (this.isMobile) this.getActionInfo()
    },
    watch: {
        // ✅ если карточка переиспользуется и record меняется — обновляем availability
        'record.id': function () {
            if (this.isMobile) this.getActionInfo()
        }
    }
}
</script>

<style scoped>
.inline_actions{
    display: flex;
    align-items: center;
    gap: 8px;
    flex-wrap: wrap;
}
</style>
