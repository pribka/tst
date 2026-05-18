<template>
    <div class="flex items-center">
        <div 
            v-for="user, index in memberVisible" 
            :key="`${user.id}_${index}`"
            class="member flex items-center">
            <Profiler
                :avatarSize="26"
                nameClass="text-sm"
                :popoverText="user.is_author ? 'Основатель' : '' || user.role_code === 'MODERATOR' ? 'Модератор' : ''"
                :showUserName="false"
                :user="user" />
        </div>
        <div v-if="memberHidden" class="ml-2">
            <a-avatar 
                :size="26" 
                class="count_avatar">
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
            if(this.item.users) {
                return this.item.users
            }
            if(this.item.members) {
                return this.item.members
            }

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
.count_avatar{
    background: transparent!important;
    color: var(--text)!important;
    font-size: 14px!important;
}
.member{
    &:not(:first-child){
        margin-left: -10px;
    }
}
</style>