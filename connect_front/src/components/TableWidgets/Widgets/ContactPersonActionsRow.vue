<template>
    <a-dropdown 
        :trigger="['click']" 
        :disabled="disabledButton"
        :getPopupContainer="getPopupContainer">
        <a-button 
            type="ui" 
            ghost
            shape="circle"
            :disabled="disabledButton"
            flaticon 
            :loading="listLoading"
            size="small"
            icon="fi-rr-menu-dots-vertical"
            :destroyPopupOnHide="false" />
        <a-menu slot="overlay">
            <template>
                <a-menu-item 
                    v-if="actions?.edit_contact_person?.availability"
                    key="0" 
                    @click="editSpec()">
                    {{ $t('edit') }}
                </a-menu-item>
                <a-menu-item
                    v-if="actions?.delete_contact_person?.availability" 
                    key="1" 
                    @click="deleteSpec()">
                    {{ $t('Delete') }}
                </a-menu-item>
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
    computed: {
        disabledButton() {
            return !(this.actions?.delete_contact_person?.availability && this.actions?.edit_contact_person?.availability)
        },
        actions() {
            return this.colParams.actions
        }
    },
    data() {
        return {
            model: "help_desk.ContactPersonModel",
            pageName: `helpdesk_contact_person_by_${this.record.customer_card.id}`,
            listLoading: false,
            // mainModel: "help_desk.customercardmodel",
            // mainPageName: "list_help_desk.customercardmodel",
        }
    },
    methods: {
        deleteSpec() {
            this.$confirm({
                title: this.$t('helpdesk.contact_person_delete_text'),
                content: '',
                okText: this.$t('Delete'),
                okType: 'danger',
                closable: true,
                maskClosable: true,
                cancelText: this.$t('Close'),
                onOk: () => {
                    return new Promise((resolve, reject) => {
                        const url = `/help_desk/customer_cards/${this.record.customer_card.id}/contact_persons/remove/`
                        const payload = {
                            contact_person: this.record.id
                        }
                        this.$http.post(url, payload)
                            .then(() => {
                                this.$message.success('Контактное лицо успешно удалено')
                                eventBus.$emit(`update_filter_${this.model}_${this.pageName}`)
                                eventBus.$emit(`update_filter_${this.model}`)
                                resolve()
                            })
                            .catch(error => {
                                errorHandler({error})
                            })
                    })
                }
            })
        },
        editSpec() {
            eventBus.$emit('edit_contact_person_modal', { client: this.record.customer_card, contactPerson: this.record })
        },
        getPopupContainer() {
            return this.colParams.getPopupContainer()
        }
    }
}
</script>