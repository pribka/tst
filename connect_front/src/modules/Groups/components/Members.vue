<template>
    <div class="flex items-center">
        <div 
            v-for="user in memberVisible" 
            :key="user.id"
            class="member flex items-center">
            <Profiler
                :avatarSize="22"
                nameClass="text-sm"
                :popoverText="user.is_author ? $t('wgr.director') : '' || user.role_code === 'MODERATOR' ? $t('wgr.moderator') : ''"
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
            default: 4
        }
    },
    computed: {
        members() {
            const { workgroup_members, founder } = this.item
            let onlyMember = workgroup_members.filter(f => f.id !== founder.id)
            onlyMember.unshift(founder)
            return onlyMember.map(user => {
                return {
                    ...user.member,
                    is_author: user.id === founder.id ? true : false,
                    role_code: user.membership_role?.code || null
                }
            })
        },
        memberVisible() {
            if(this.members?.length > this.visibleCount)
                return this.members.slice(0, this.visibleCount)
            else
                return this.members
        },
        memberHidden() {
            if(this.members?.length > this.visibleCount)
                return this.members.slice(this.visibleCount, this.members.length)
            else
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