<template>
    <div>
        <a-button 
            size="default"
            type="ui"
            ghost
            shape="circle"
            flaticon
            icon="fi-rr-menu-dots-vertical" 
            :loading="loading" 
            @click="openDrawer" />
        <ActivityDrawer v-model="visible">
            <ActivityItem 
                v-if="isAuthor && meeting.status === 'ended' && !meeting.is_external"
                @click="restartConference()">
                <div class="flex items-center">
                    <i class="fi fi-rr-refresh mr-2"></i>
                    {{ $t('meeting.restartConference') }}
                </div>
            </ActivityItem>
            <ActivityItem 
                v-if="isAuthor && meeting.status !== 'ended' && !meeting.is_external"
                @click="closeConference()">
                <div class="flex items-center">
                    <i class="fi fi-rr-badge-check mr-2"></i>
                    {{ $t('meeting.endConference') }}
                </div>
            </ActivityItem>
            <ActivityItem 
                v-if="meeting.invite_link && !meeting.is_external"
                @click="inviteLink()">
                <i class="fi fi-rr-copy-alt mr-2"></i>
                {{ $t('meeting.inviteLink') }}
            </ActivityItem>
            <ActivityItem 
                @click="share()">
                <i class="fi fi-rr-share mr-2"></i>
                {{ $t('meeting.share') }}
            </ActivityItem>
            <template v-if="isAuthor">
                <ActivityItem 
                    key="1"
                    @click="deleteConference()">
                    <div class="text-red-500 flex items-center">
                        <i class="fi fi-rr-trash mr-2"></i>
                        {{ $t('meeting.delete') }}
                    </div>
                </ActivityItem>
            </template>

        </ActivityDrawer>
    </div>
</template>

<script>
import { ActivityItem, ActivityDrawer } from '@/components/ActivitySelect'

export default {
    props: {
        loading: {
            type: Boolean,
            default: false
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
        onlyMoreButton: {
            type: Boolean,
            requered: true
        },
        restartConference: {
            type: Function,
            default: () => {}
        }
    },
    data() {
        return {
            visible: false,
        }
    },
    components: {
        ActivityItem, 
        ActivityDrawer
    },
    methods: {
        openDrawer() {
            this.visible = true
        }
    }
}
</script>
