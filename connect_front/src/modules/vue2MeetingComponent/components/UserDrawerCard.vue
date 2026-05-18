<template>
    <div class="cursor-pointer flex items-center user_card_drawer justify-between">
        <Profiler
            :avatarSize="28"
            nameClass="text-sm"
            :popoverText="$t('meeting.author2')"
            initStatus
            :user="user" />
        <div v-if="checkAuthor" class="flex items-center gap-1">
            <a-switch 
                @click="memberType(user)"
                :defaultChecked="user.is_moderator"
                :checked-children="$t('meeting.moderator')" 
                :un-checked-children="$t('meeting.participant')" />
            <a-button 
                @click="memberDelete(user)"
                type="ui"
                flaticon
                ghost 
                icon="fi-rr-delete-user" />
        </div>
    </div>
</template>

<script>
export default {
    name: "MeetingUserDrawerCard",
    props: {
        user: {
            type: Object,
            required: true
        },
        memberDelete: {
            type: Function,
            default: () => {}
        },
        memberType: {
            type: Function,
            default: () => {}
        },
        form: {
            type: Object,
            default: () => null
        },
        edit: {
            type: Boolean,
            default: false
        }
    },
    computed: {
        checkAuthor() {
            if(this.edit && this.form?.author?.id === this.user?.id)
                return false
            return true
        },
    }
}
</script>

<style lang="scss" scoped>
.user_card_drawer{
    padding: 5px;
}
</style>