<template>
    <div>
        <a-button
            class="ml-1"
            type="link"
            icon="more"
            @click="visible = true" />
        <ActivityDrawer v-model="visible">
            <ActivityItem 
                v-if="activeChat.is_public"
                icon="fi-rr-info"
                @click="openChatInfo()">
                {{ $t('chat.chat_information') }}
            </ActivityItem>
            <ActivityItem 
                v-if="activeChat.workgroup"
                icon="fi-rr-users"
                @click="openWorkgroup()">
                {{ activeChat.workgroup.is_project ? $t("chat.project") :  $t("chat.workgroup")}}
            </ActivityItem>
            <ActivityItem 
                v-if="isAdmin" 
                redLink
                icon="fi-rr-trash"
                @click="showDeleteModal()">
                {{ $t('chat.remove') }}
            </ActivityItem>
        </ActivityDrawer>
    </div>
</template>

<script>
import { ActivityItem, ActivityDrawer } from '@/components/ActivitySelect'
export default {
    components: {
        ActivityItem,
        ActivityDrawer
    },
    props: {
        activeChat: {
            type: Object,
            default: () => null
        },
        openChatInfo: {
            type: Function,
            default: () => {}
        },
        openWorkgroup: {
            type: Function,
            default: () => {}
        },
        showDeleteModal: {
            type: Function,
            default: () => {}
        },
        isAdmin: {
            type: Boolean,
            default: false
        }
    },
    data() {
        return {
            visible: false
        }
    }
}
</script>