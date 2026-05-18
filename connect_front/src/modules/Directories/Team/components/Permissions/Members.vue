<template>
    <div class="flex items-center">
        <div 
            v-for="user in memberVisible" 
            :key="user.id"
            class="member flex items-center">
            <Profiler
                :avatarSize="22"
                nameClass="text-sm"
                :popoverText="user.is_author ? $t('team.founder') : '' || user.role_code === 'MODERATOR' ? $t('team.moderator') : ''"
                :showUserName="false"
                :user="user" />
        </div>
        <div 
            v-if="memberHidden" 
            class="member">
            <a-avatar 
                :size="22" 
                style="backgroundColor:#87d068">
                +{{ memberHidden.length }}
            </a-avatar>
        </div>
    </div>
</template>

<script>
export default {
    props: {
        item: {
            type: Object,
            required: true
        },
        visibleCount: {
            type: Number,
            default: 3
        }
    },
    computed: {
        members() {
            return this.item.users
        },
        memberVisible() {
            if(this.members?.length > this.visibleCount)
                return this.members.slice(0, this.visibleCount)
            return this.members
        },
        memberHidden() {
            if(this.members?.length > this.visibleCount)
                return this.members.slice(this.visibleCount, this.members.length)
            return false
        }
    }
}
</script>

<style lang="scss" scoped>
.member{
    &:not(:last-child){
        margin-right: 3px;
    }
}
</style>