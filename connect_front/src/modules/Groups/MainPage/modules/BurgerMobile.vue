<template>
    <div>
        <a-button 
            size="default"
            class="open_button"
            type="ui"
            shape="circle"
            ghost
            flaticon
            icon="fi-rr-menu-dots-vertical"
            :loading="loading" 
            @click="visible = true" />
        <ActivityDrawer v-model="visible">
            <!--<template v-if="actions && actions.project_finish">
                <ActivityItem
                    v-show="isFounder" 
                    v-if="is_project && requestData.finished"
                    @click="$emit('finishProject', true)">
                    <i class="fi fi-rr-play-alt mr-2"></i>
                    {{$t('wgr.resume_project')}}
                </ActivityItem>
                <ActivityItem
                    v-show="isFounder"
                    v-if="is_project && !requestData.finished"
                    @click="$emit('finishProject', false)">
                    <i class="fi fi-rr-comment-check mr-2"></i>
                    {{$t('wgr.finished_project')}}
                </ActivityItem>
            </template>-->
            <!--<ActivityItem
                v-if="actions && actions.create_chat && !requestData.with_chat"
                :loading="createChatLoading"
                @click="$emit('createChat')">
                <i class="fi fi-rr-comment-medical mr-2"></i>
                {{ $t('wgr.create_chat')  }}
            </ActivityItem>
            <ActivityItem
                v-if="requestData.with_chat && this.requestData.linked_chat"
                @click="$emit('openChat')">
                <i class="fi fi-rr-comment mr-2"></i>
                {{ $t('wgr.open_chat') }}
            </ActivityItem>-->
            <ActivityItem
                v-if="!isStudent && !requestData.public_or_private"
                :disabled="disableJoinClub"
                :loading="loadingJoin"
                @click="$emit('joinGroup')">
                <i class="fi fi-rr-users-medical mr-2"></i>
                {{ disableJoinClub ? $t("wgr.request_posted") : $t('wgr.join_group') }}
            </ActivityItem>
            <ActivityItem
                v-if="isStudent && !isFounder"
                @click="$emit('leaveGroup')"
                :loading="loadingExit">
                <i class="fi fi-rr-remove-user"></i>
                {{ $t("wgr.exit") }}
            </ActivityItem>
            <ActivityItem
                v-if="actions && actions.edit"
                @click="$emit('goToEdit')">
                <i class="fi fi-rr-edit"></i>
                {{ $t('wgr.edit') }}
            </ActivityItem>
            <ActivityItem
                @click="$emit('shareToChat')">
                <i class="fi fi-rr-share"></i>
                {{ $t('wgr.share') }}
            </ActivityItem>
            <ActivityItem 
                v-if="actions && actions.delete"
                @click="$emit('deleteGroup')">
                <div class="text-red-500 flex items-center">
                    <i class="fi fi-rr-trash"></i>
                    {{ $t('wgr.delete') }}
                </div>
            </ActivityItem>
        </ActivityDrawer>
    </div>
</template>

<script>

import { ActivityItem, ActivityDrawer } from '@/components/ActivitySelect'

export default {
    props: {
        requestData: {
            type: Object,
            requered: true
        },
        is_project: {
            type: Boolean,
            requered: true
        },
        isFounder: {
            type: Boolean,
            requered: true
        },
        isStudent: {
            type: Boolean,
            requered: true
        },
        loadingExit: {
            type: Boolean,
            requered: true
        },
        loadingJoin: {
            type: Boolean,
            requered: true
        },
        disableJoinClub: {
            type: Boolean,
            requered: true
        },
        createChatLoading: {
            type: Boolean,
            requered: true
        },
        actions: {
            type: Object,
            default: () => null
        }
    },
    components: {
        ActivityItem, 
        ActivityDrawer
    },
    data() {
        return {
            loading: false,
            visible: false,
        }
    },
}
</script>

<style scoped>
.open_button {
    display: flex;
    justify-content: center;
    align-items: center;

    line-height: 100%;
}
.active_option {
    color: var(--blue);
}
</style>