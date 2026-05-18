<template>
    <div 
        class="cursor-pointer reply_message truncate w-full mt-2 mb-2 pt-1 lg:pt-3 pb-1 lg:pb-3 pr-2" 
        @click="openSprint()">
        <div class="label truncate">
            {{ $t('chat.sprint') }}: {{ messageItem.share.name }}
        </div>
    </div>
</template>

<script>
export default {
    props: {
        messageItem: {
            type: Object,
            required: true
        }
    },
    methods: {
        openSprint() {
            this.$router.push({query: {sprint: this.messageItem.share.id}})
            this.$store.commit('task/CHANGE_SPRINT_SHOW', true)
        }
    }
}
</script>