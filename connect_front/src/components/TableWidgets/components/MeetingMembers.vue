<template>
    <div class="flex items-center">
        <Profiler
            :avatarSize="22"
            nameClass="text-sm"
            popoverText="Автор"
            :showUserName="false"
            :user="item.author" />
        <span 
            v-if="memberCount > 1" 
            class="ml-1">
            <a-avatar 
                :size="22"
                style="backgroundColor:#87d068">
                +{{ memberCount }}
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
        memberCount() {
            return this.item.members_count - 1
        }
    }
}
</script>