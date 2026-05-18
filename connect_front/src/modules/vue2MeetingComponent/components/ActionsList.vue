<template>
    <ActivityDrawer 
        :vis="activity" 
        useVis
        :cDrawer="closeDrawer">
        <ActivityItem v-if="item.status !== 'ended'" @click="conferenceLink()">
            <i class="fi fi-rr-sign-in-alt icon"></i> {{ $t('meeting.connect') }}
        </ActivityItem>
        <ActivityItem v-if="item.has_record" @click="openRec()">
            <i class="fi fi-rr-play-alt icon"></i> {{ $t('meeting.records') }}
        </ActivityItem>
        <ActivityItem v-if="isAuthor && item.status === 'ended'" @click="restartConference()">
            <i class="fi fi-rr-refresh icon"></i> {{ $t('meeting.restartConference') }}
        </ActivityItem>
        <ActivityItem v-if="item.invite_link" @click="inviteLink()">
            <i class="fi fi-rr-copy-alt icon"></i> {{ $t('meeting.inviteLink') }}
        </ActivityItem>
        <ActivityItem @click="share()">
            <i class="fi fi-rr-share icon"></i> {{ $t('meeting.share') }}
        </ActivityItem>
        <ActivityItem v-if="isAuthor" @click="openEdit()">
            <i class="fi fi-rr-edit icon"></i> {{ $t('meeting.edit') }}
        </ActivityItem>
        <ActivityItem v-if="isAuthor && item.status !== 'ended'" @click="closeConference()">
            <div class="text-green-600 flex items-center">
                <i class="fi fi-rr-badge-check icon"></i> {{ $t('meeting.endConference') }}
            </div>
        </ActivityItem>
        <ActivityItem v-if="isAuthor" @click="deleteConference()">
            <div class="text-red-500 flex items-center">
                <i class="fi fi-rr-trash icon"></i> {{ $t('meeting.delete') }}
            </div>
        </ActivityItem>
    </ActivityDrawer>
</template>

<script>
import { ActivityItem, ActivityDrawer } from '@/components/ActivitySelect'
export default {
    components: {
        ActivityItem,
        ActivityDrawer
    },
    props: {
        conferenceLink: {
            type: Function,
            default: () => {}
        },
        activity: {
            type: Boolean,
            default: false
        },
        closeDrawer: {
            type: Function,
            default: () => {}
        },
        item: {
            type: Object,
            required: true
        },
        isAuthor: {
            type: Boolean,
            default: false
        },
        recordLoading: {
            type: Boolean,
            default: false
        },
        restartConference: {
            type: Function,
            default: () => {}
        },
        closeConference: {
            type: Function,
            default: () => {}
        },
        inviteLink: {
            type: Function,
            default: () => {}
        },
        share: {
            type: Function,
            default: () => {}
        },
        deleteConference: {
            type: Function,
            default: () => {}
        },
        openEdit: {
            type: Function,
            default: () => {}
        },
        openRec: {
            type: Function,
            default: () => {}
        }
    }
}
</script>