<template>
    <div>
        <ChatComponent :dealerChat="true" style="max-height: 85vh"/>
    </div>
</template>

<script>
export default {
    components: {
        ChatComponent: () => import("@apps/vue2ChatComponent/ChatComponent")
    },
       

    created(){
        let query = Object.assign({}, this.$route.query)
        query['chat_id'] = this.$store.state.user.user.default_chat
        this.$router.replace({query})
    }

}
</script>