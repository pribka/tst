<template>
    <a-button
        v-if="canShowButton"
        icon="fi-rr-computer"
        type="flat_primary"
        v-tippy
        shape="circle"
        :content="$t('remote.remote_access')"
        flaticon
        @click="requestRemoteAccess" />
</template>

<script>
import { mapState } from 'vuex'
import eventBus from '@/utils/eventBus'
import { REMOTE_ACCESS_AGENT_STATUSES } from '@/utils/remoteAccess'
export default {
    name: 'RemoteAccessButton',
    computed: {
        ...mapState({
            user: state => state.user.user,
            agentStatus: state => state.remoteAccess.agentStatus,
            isMobile: state => state.isMobile,
            activeChat: state => state.chat.activeChat
        }),
        canShowButton() {
            return !this.isMobile
                && !this.activeChat?.is_public
                && this.user?.is_helpdesk_support
                && this.agentStatus === REMOTE_ACCESS_AGENT_STATUSES.CONNECTED
        }
    },
    methods: {
        requestRemoteAccess() {
            eventBus.$emit('send_remote_access_request')
        }
    }
}
</script>
