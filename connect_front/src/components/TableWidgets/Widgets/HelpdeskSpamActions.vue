<template>
    <a-dropdown :trigger="['click']">
        <a-button 
            type="ui" 
            ghost 
            flaticon 
            :loading="loading"
            size="small"
            icon="fi-rr-menu-dots-vertical"
            :destroyPopupOnHide="false" />
        <a-menu slot="overlay">
            <a-menu-item key="open" class="flex items-center" @click="unmarkAsSpam">
                <i class="fi fi-rr-link-alt mr-2" />
                {{ $t('helpdesk.no_spam') }}
            </a-menu-item>
        </a-menu>
    </a-dropdown>
</template>

<script>
import eventBus from '@/utils/eventBus'

export default {
    props: {
        record: {
            type: Object,
            required: true
        },
        expanded: {
            type: Number,
        },
        pageName: {
            type: String,
            default: ''
        }
    },
    data() {
        return {
            loading: false,
            listModel: "help_desk.ContactPersonModel",
        }
    },
    methods: {
        unmarkAsSpam() {
            const url = `help_desk/contact_persons/${this.record.id}/unmark_as_spam/`
            this.loading = true
            this.$http.post(url)
                .then(({ data }) => {
                    if(data) {
                        this.$message.success('Контактное лицо помечено как не спам')
                        eventBus.$emit(`update_filter_${this.listModel}_${this.pageName}`)
                    }
                })
                .catch((error) => {
                    this.$message.error('Ошибка')
                    console.error(error)
                })
                .finally(() => {
                    this.loading = false
                })
        },
    }
}
</script>