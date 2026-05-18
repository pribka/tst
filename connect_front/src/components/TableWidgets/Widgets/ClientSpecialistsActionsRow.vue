<template>
    <a-dropdown 
        :trigger="['click']" 
        :disabled="!canChange"
        :getPopupContainer="getPopupContainer">
        <a-button 
            type="ui"
            ghost 
            shape="circle"
            flaticon
            :disabled="!canChange"
            size="small"
            icon="fi-rr-menu-dots-vertical" />
        <a-menu slot="overlay">
            <a-menu-item
                v-if="record.action_info?.can_move_up"
                key="priority-up"
                @click="movePriority('up')">
                {{ $t('directories.move_specialist_up') }}
            </a-menu-item>
            <a-menu-item
                v-if="record.action_info?.can_move_down"
                key="priority-down"
                @click="movePriority('down')">
                {{ $t('directories.move_specialist_down') }}
            </a-menu-item>
            <a-menu-item key="0" @click="editSpec()">
                {{ $t('directories.edit_specialist') }}
            </a-menu-item>
            <a-menu-item key="1" @click="deleteSpec()">
                {{ $t('directories.delete_specialist') }}
            </a-menu-item>
        </a-menu>
    </a-dropdown>
</template>

<script>
import eventBus from '@/utils/eventBus'
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
        colParams: {
            type: Object,
            default: () => null
        }
    },
    data() {
        return {
            model: "models.CustomerSupportSpecialistModel",
            pageName: `client_specialists_list_by_${this.colParams.client.id}`,
            mainModel: "help_desk.customercardmodel",
            mainPageName: "list_help_desk.customercardmodel",
        }
    },
    computed: {
        canChange() {
            return this.colParams.actions?.edit_specialist?.availability
        }
    },
    methods: {
        emitUpdates() {
            eventBus.$emit(`update_filter_${this.model}_${this.pageName}`)
            eventBus.$emit(`update_filter_${this.model}_${this.pageName}_aggregate`)
            eventBus.$emit(`update_filter_${this.mainModel}_${this.mainPageName}`)
        },
        async movePriority(direction) {
            try {
                await this.$http.put(`/help_desk/customer_cards/${this.colParams.client.id}/specialists/${direction}/`, { id: this.record.id })
                this.$message.success(
                    direction === 'up'
                        ? this.$t('directories.specialist_priority_increased')
                        : this.$t('directories.specialist_priority_decreased')
                )
                this.emitUpdates()
            } catch (error) {
                errorHandler({error})
            }
        },
        deleteSpec() {
            this.$confirm({
                title: this.$t('directories.confirm_delete_specialist'),
                content: '',
                okText: this.$t('directories.delete'),
                okType: 'danger',
                closable: true,
                maskClosable: true,
                cancelText: this.$t('directories.close'),
                onOk: () => {
                    return new Promise((resolve, reject) => {
                        this.$http.post(`/help_desk/customer_cards/${this.colParams.client.id}/specialists/remove/`, {specialists: [this.record.id]})
                            .then(() => {
                                this.$message.success(this.$t('directories.specialist_deleted'))
                                this.emitUpdates()
                                resolve()
                            })
                            .catch(error => {
                                errorHandler({error})
                                reject(error)
                            })
                    })
                }
            })
        },
        editSpec() {
            eventBus.$emit('edit_specialist_modal', this.record)
        },
        getPopupContainer() {
            return this.colParams.getPopupContainer()
        }
    }
}
</script>