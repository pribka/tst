<template>
    <div class="user_card flex items-center justify-between" :style="!isMobile && 'padding-left: 15px;padding-right: 15px;'">
        <Profiler 
            initStatus
            :user="user" />
        <div class="flex items-center justify-between" :style="!isMobile && 'min-width: 150px;'">
            <div :style="!isMobile && 'min-width: 101px;'">
                <a-tag 
                    v-if="isAuthorUser" 
                    class="mr-0"
                    :style="isMobile && 'font-size: 12px;'"
                    color="green">
                    {{ $t('meeting.author2') }}
                </a-tag>
                <a-tag
                    v-else-if="isModerator"
                    :style="isMobile && 'font-size: 12px;'"
                    color="blue">
                    {{ $t('meeting.moderator') }}
                </a-tag>
                <a-tag v-else :style="isMobile && 'font-size: 12px;'">
                    {{ $t('meeting.participant_table') }}
                </a-tag>
            </div>

            <a-button
                v-if="canShowModeratorBtn"
                type="ui"
                ghost
                flaticon
                shape="circle"
                v-tippy
                :content="isModerator ? $t('meeting.removeModerator') : $t('meeting.setModerator')"
                :icon="isModerator ? 'fi-rr-delete-user' : 'fi-rr-user-add'"
                @click="onToggleModerator" />
        </div>
    </div>
</template>

<script>
export default {
    name: "MeetingShowDrawerUserCard",
    props: {
        user: {
            type: Object,
            required: true
        },
        meeting: {
            type: Object,
            required: true
        },
        isModerator: {
            type: Boolean,
            default: false
        },
        canEditModerators: {
            type: Boolean,
            default: false
        },
        toggleModerator: {
            type: Function,
            default: () => {}
        }
    },
    computed: {
        isMobile() {
            return this.$store.state.isMobile
        },
        isAuthorUser() {
            return Boolean(this.user?.id && this.meeting?.author?.id && this.user.id === this.meeting.author.id)
        },
        canShowModeratorBtn() {
            if (!this.canEditModerators) return false
            if (!this.user?.id) return false
            if (this.isAuthorUser) return false
            return true
        }
    },
    methods: {
        onToggleModerator() {
            this.toggleModerator({
                userId: this.user.id,
                value: !this.isModerator
            })
        }
    }
}
</script>