<template>
    <div>
        <ActivityDrawer v-model="visible">
            <template v-if="actionsLoading">
                <ActivityItem 
                    key="menu_loader"
                    class="flex justify-center">
                    <a-spin size="small"/>
                </ActivityItem>
            </template>
            <template v-if="permissions?.actions?.edit?.availability">
                <ActivityItem 
                    key="edit"
                    @click="openConnectDrawer('edit')">
                    <div class="text-blue-500">
                        <i class="fi fi-rr-edit mr-2"></i>
                        Редактировать
                    </div>                 
                </ActivityItem>
            </template>
            <template  v-if="permissions?.actions?.set_status?.availability">
                <ActivityItem
                    @click="setStatus(true)"
                    key="approve">
                    <div class="text-green-500">
                        <i class="fi fi-rr-check mr-2 "></i>
                        Одобрить
                    </div>
                    
                </ActivityItem>
                <ActivityItem 
                    @click="setStatus(false)"
                    key="reject">
                    <div class="text-red-500">
                        <i class="fi fi-rr-cross-circle text_red mr-2"></i>
                        Отклонить  
                    </div>
                </ActivityItem>
            </template>
            <ActivityItem 
                @click="shareHandler"
                key="share"
                class="flex items-center">
                <i class="fi fi-rr-share mr-2"></i>
                Поделиться
            </ActivityItem>
        </ActivityDrawer>
    </div>
</template>

<script>
import { ActivityItem, ActivityDrawer } from '@/components/ActivitySelect'
import eventBus from '@/utils/eventBus'
import { mapActions, mapState } from 'vuex'

export default {
    components: {
        ActivityItem, 
        ActivityDrawer,
    },
    props: {
        record: {
            type: Object,
            erequird: true
        }
    },
    data() {
        return {
            visible: false,
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
        openDrawer() {
            this.visible = true
            this.visibleChange(this.visible)
        },
        openConnectDrawer(mode) {
            eventBus.$emit('OPEN_MY_BASES_DRAWER', { ticket: this.record, mode: mode })
        },
        async setStatus(isApproved) {
            await this.setTicketStatus({ticketId: this.record.id, isApproved: isApproved})
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