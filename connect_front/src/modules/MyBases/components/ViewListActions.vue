<template>
    <a-dropdown 
        :destroyPopupOnHide="true"
        @visibleChange="visibleChange">
        <a-button 
            icon="menu" 
            type="link" />
        <a-menu slot="overlay">
            <template v-if="actionsLoading">
                <a-menu-item 
                    key="menu_loader"
                    class="flex justify-center">
                    <a-spin size="small" />
                </a-menu-item>
            </template>
            <template v-else>
                <template v-if="permissions?.actions?.edit?.availability">
                    <a-menu-item 
                        key="edit"
                        class="flex items-center blue_color"
                        @click="openConnectDrawer('edit')">
                        <i class="fi fi-rr-edit mr-1"></i>
                        Редактировать
                    </a-menu-item>
                </template>
                <template  v-if="permissions?.actions?.set_status?.availability">
                    <a-menu-item 
                        @click="setStatus(true)"
                        key="approve"
                        class="flex items-center text_green">
                        <i class="fi fi-rr-check mr-1"></i>
                        Одобрить
                    </a-menu-item>
                    <a-menu-item 
                        @click="setStatus(false)"
                        key="reject"
                        class="flex items-center text_red">
                        <i class="fi fi-rr-cross-circle mr-1"></i>
                        Отклонить
                    </a-menu-item>
                </template>
                <template>
                    <a-menu-item 
                        @click="shareHandler"
                        key="share"
                        class="flex items-center">
                        <i class="fi fi-rr-share mr-1"></i>
                        Поделиться
                    </a-menu-item>
                </template>
            </template>
        </a-menu>
    </a-dropdown>
</template>

<script>
import eventBus from '@/utils/eventBus'
import { mapActions, mapState } from 'vuex'

export default {
    props: {
        record: {
            type: Object,
            required: true
        },
        pageName: {
            type: String,
            default: 'IncomingServiceTicketModel'
        }
    },
    data() {
        return {
            actionsLoading: true,
            permissions: []
        }
    },
    computed: {
        ...mapState({
            user: state => state.user.user
        }),
        userId() {
            return this.user.id
        }
    },
    methods: {
        ...mapActions({
            setTicketStatus: 'mybases/setTicketStatus'
        }),
        async visibleChange(visible) {
            if(visible) {
                this.actionsLoading = true
                await this.$http(`tickets/ticket/${this.record.id}/action_info/`)
                    .then(({ data }) => {
                        this.permissions = data
                    })
                    .catch(error => console.error(error))
                this.actionsLoading = false
            }
            
        },
        openConnectDrawer(mode) {
            eventBus.$emit('OPEN_MY_BASES_DRAWER', { ticket: this.record, mode: mode })
        },
        async setStatus(isApproved) {
            const responseTicket = await this.setTicketStatus({ticketId: this.record.id, isApproved: isApproved})
            eventBus.$emit(`table_row_${this.pageName}`, {
                action: 'update',
                row: responseTicket
            })
        },
        shareHandler() {
            this.$store.commit('share/SET_SHARE_PARAMS', {
                model: 'tickets.TicketModel',
                shareId: this.record.id,
                object: this.record,
                shareUrl: `${window.location.origin}/my-bases?ticket=${this.record.id}`,
                shareTitle: this.record.name
            })
        },
    }
}
</script>