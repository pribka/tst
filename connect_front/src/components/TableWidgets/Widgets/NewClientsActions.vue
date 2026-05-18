<template>
    <div>
        <a-button :key="record.user.id" type="ui" @click="sendMessage">
            Написать в чат
        </a-button>
    </div>
</template>

<script>
export default {
    props: {
        text: {
            type: [String, Number, Boolean, Object, Array]
        },
        record: {
            type: Object
        },
    },
    computed: {
        user() {
            return this.$store.state.user.user
        }
    },
    methods: {
        goToChat() {
            const chatId = this.record.support_chat
            const route = {
                name: this.isMobile ? 'chat-body' : 'chat', 
                query: {
                    [this.isMobile ? 'id' : 'chat_id']: chatId
                }
            }
            this.$router.push(route)  
        },
        
        sendMessage() {
            if (this.record.is_chat_welcome_sent) {
                return this.goToChat()
            }
            this.sendWelcomeMessage()
            return this.goToChat()
        },
        sendWelcomeMessage() {
            const payload = this.getWelcomeMessagePayload()
            this.$socket.client.emit("message", payload)
            const url = `users/new_user_info/${this.record.id}/`

            const userPayload = {
                "is_chat_welcome_sent": true
            }
            this.$http.put(url, userPayload)
                .catch(error => {
                    console.error(error)
                })
        },

        getWelcomeMessagePayload() {
            const message = `Здравствуйте, меня зовут ${this.user.first_name}! 😊
                Добро пожаловать на нашу платформу!
                Если потребуется помощь с настройкой профиля, 
                доступом или первыми шагами в работе — напишите прямо здесь, 
                я помогу разобраться и подскажу, с чего лучше начать.`
            const messageParams = {
                text: message,
                chat: this.record.support_chat
            }
            return messageParams
        },
    }
}
</script>
