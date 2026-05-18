<template>
    <div class="flex justify-end">
        <a-dropdown :trigger="['click']">
            <a-button
                icon="fi-rr-menu-dots-vertical"
                flaticon
                shape="circle"
                style="color: var(--text);background: transparent!important;box-shadow: initial!important;border-color: transparent!important;"
                type="ui" /> 
            <a-menu slot="overlay">
                <a-menu-item
                    v-if="item.status !== 'ended'"
                    class="flex"
                    key="connect"
                    type="link">
                    <a  
                        class="flex-grow"
                        :href="item.target" 
                        target="_blank">
                        <i class="fi fi-rr-sign-in-alt icon mr-2"></i>
                        {{ $t('meeting.connect') }}
                    </a>
                </a-menu-item>
                <a-menu-item
                    v-if="item.has_record"
                    class="flex items-center"
                    key="open_records"
                    @click="openRec()">
                    <i class="fi fi-rr-file-video icon mr-2"></i>
                    {{ $t('meeting.viewRecords') }}
                </a-menu-item>
                <a-menu-item
                    v-if="isAuthor && item.status === 'ended'"
                    class="text-green-400 flex items-center"
                    key="6"
                    @click="restartConference()">
                    <i class="fi fi-rr-refresh mr-2"></i>
                    {{ $t('meeting.restartConference') }}
                </a-menu-item>
                <a-menu-item
                    v-if="isAuthor && item.status !== 'ended'"
                    class="text-green-400 flex items-center"
                    key="5"
                    @click="closeConference()">
                    <i class="fi fi-rr-badge-check mr-2"></i>
                    {{ $t('meeting.endConference') }}
                </a-menu-item>
                <a-menu-item
                    v-if="item.invite_link"
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
                <a-menu-item
                    v-if="isAuthor"
                    key="1"
                    class="flex items-center"
                    @click="openEdit()">
                    <i class="fi fi-rr-edit mr-2"></i>
                    {{ $t('meeting.edit') }}
                </a-menu-item>
                <template v-if="isAuthor">
                    <a-menu-divider />
                    <a-menu-item
                        class="text-red-500 flex items-center"
                        key="4"
                        @click="deleteConference()">
                        <i class="fi fi-rr-trash mr-2"></i>
                        {{ $t('meeting.delete') }}
                    </a-menu-item>
                </template>
            </a-menu>
        </a-dropdown>
    </div>
</template>

<script>
export default {
    props: {
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