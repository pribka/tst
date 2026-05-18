<template>
    <div class="flex items-center">
        <Profiler
            :avatarSize="22"
            nameClass="text-sm"
            :popoverText="$t('meeting.author2')"
            :showUserName="false"
            :user="item.author" />
        <span 
            v-if="membersCount" 
            class="ml-1">
            <a-avatar 
                :size="22"
                style="backgroundColor:#87d068">
                +{{ membersCount }}
            </a-avatar>
        </span>
        
    </div>
</template>

<script>
export default {
    props: {
        item: {
            type: Object,
            required: true
        }
    },
    computed: {
        membersCount() {
            if(this.item.members_count > 1)
                return this.item.members_count - 1
            else
                return false
        }
    }
}
</script>