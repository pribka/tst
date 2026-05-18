<template>
    <a-dropdown :trigger="['click']" :getPopupContainer="trigger => trigger.parentNode">
        <a-menu slot="overlay">
            <a-menu-item
                v-if="isAuthor && meeting.status === 'ended' && !meeting.is_external"
                class="text-green-400 flex items-center"
                key="6"
                @click="restartConference()">
                <i class="fi fi-rr-refresh mr-2"></i>
                {{ $t('meeting.restartConference') }}
            </a-menu-item>
            <a-menu-item 
                v-if="isAuthor && meeting.status !== 'ended' && !meeting.is_external"
                class="text-green-400 flex items-center"
                key="4"
                @click="closeConference()">
                <i class="fi fi-rr-badge-check mr-2"></i>
                {{ $t('meeting.endConference') }}
            </a-menu-item>
            <a-menu-item 
                v-if="meeting.invite_link && !meeting.is_external"
                key="2" 
                class="flex items-center"
                @click="inviteLink()">
                <i class="fi fi-rr-copy-alt mr-2"></i>
                {{ $t('meeting.inviteLink') }}
            </a-menu-item>
            <a-menu-item 
                key="3" 
                class="flex items-center"
                @click="share()">
                <i class="fi fi-rr-share mr-2"></i>
                {{ $t('meeting.share') }}
            </a-menu-item>
            <template v-if="isAuthor">
                <a-menu-divider />
                <a-menu-item 
                    class="text-red-500 flex items-center"
                    key="1"
                    @click="deleteConference()">
                    <i class="fi fi-rr-trash mr-2"></i>
                    {{ $t('meeting.delete') }}
                </a-menu-item>
            </template>
        </a-menu>
        <a-button 
            icon="fi-rr-menu-dots-vertical" 
            flaticon
            ghost
            :loading="actionLoading"
            shape="circle"
            type="ui" /> 
    </a-dropdown>
</template>

<script>
export default {
    props: {
        actionLoading: {
            type: Boolean,
            requered: false
        },
        isAuthor: {
            type: Boolean,
            requered: true
        },
        meeting: {
            type: Object,
            requered: true
        },
        closeConference: {
            type: Function,
            requered: true
        },
        inviteLink: {
            type: Function,
            default: () => {}
        },
        share: {
            type: Function,
            requered: true
        },
        deleteConference: {
            type: Function,
            requered: true
        },
        openEditDrawer: {
            type: Function,
            requered: true
        },
        restartConference: {
            type: Function,
            default: () => {}
        }
    },
}
</script>
