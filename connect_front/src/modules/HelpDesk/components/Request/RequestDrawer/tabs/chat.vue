<template>
    <ChatList 
        ref="chatList"
        :ticket="ticket"
        edit
        :actions="actions" />
</template>

<script>
export default {
    components: {
        ChatList: () => import('../components/ChatList/index.vue')
    },
    props: {
        ticket: {
            type: Object,
            required: true
        },
        actions: {
            type: Object,
            default: () => null
        }
    },
}
</script>