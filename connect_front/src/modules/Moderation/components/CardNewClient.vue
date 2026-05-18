<template>
    <div class="card">
        <div class="mb-2">
            <Profiler :avatarSize="28" :user="item.user" />
        </div>
        <div 
            v-if="item.contractor"
            class="flex items-center mb-2">
            <div class="pr-2">
                <a-avatar 
                    :size="28" 
                    icon="team" 
                    :src="item.contractor.logo ? item.contractor.logo : null" />
            </div>
            <span class="group_name truncate">
                {{ item.contractor.name }}
            </span>
        </div>
        <div v-if="tarrifs" class="mb-2">
            <span class="gray">Тариф:</span> {{ tarrifs }}
        </div>
        <div class="mb-2">
            <span class="gray">Дата создания:</span> {{ $moment(item.created_at).format('DD.MM.YYYY HH:mm') }}
        </div>
        <div v-if="item.user && item.user.last_activity" class="mb-3">
            <span class="gray">Дата активности:</span> {{ $moment(item.user.last_activity).format('DD.MM.YYYY HH:mm') }}
        </div>
        <div v-if="item.user">
            <a-button 
                type="primary" 
                flaticon
                block
                icon="fi-rr-comment"
                @click="sendMessage">
                Написать в чат
            </a-button>
        </div>
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
        isMobile() {
            return this.$store.state.isMobile
        },
        tarrifs() {
            if(this.item.tariffs?.length)
                return null
            return this.item.tariffs.join(', ')
        },
        user() {
            return this.$store.state.user?.user || null
        }
    },
    data() {
        return {
            loading: false
        }
    },
    methods: {
        goToChat() {
            const chatId = this.item.support_chat
            const route = {
                name: this.isMobile ? 'chat-body' : 'chat', 
                query: {
                    [this.isMobile ? 'id' : 'chat_id']: chatId
                }
            }
            this.$router.push(route)  
        },
        
        sendMessage() {
            if (this.item.is_chat_welcome_sent) {
                return this.goToChat()
            }
            this.sendWelcomeMessage()
            return this.goToChat()
        },
        sendWelcomeMessage() {
            const payload = this.getWelcomeMessagePayload()
            this.$socket.client.emit("message", payload)
            const url = `users/new_user_info/${this.item.id}/`

            const userPayload = {
                "is_chat_welcome_sent": true
            }
            this.$http.put(url, userPayload)
                .catch(error => {
                    console.error(error)
                })
        },

        getWelcomeMessagePayload() {
            const message = `Здравствуйте, меня зовут ${this.user?.first_name}! 😊
                Добро пожаловать на нашу платформу!
                Если потребуется помощь с настройкой профиля, 
                доступом или первыми шагами в работе — напишите прямо здесь, 
                я помогу разобраться и подскажу, с чего лучше начать.`
            const messageParams = {
                text: message,
                chat: this.item.support_chat
            }
            return messageParams
        }
    }
}
</script>

<style lang="scss" scoped>
.card{
    padding: 12px;
    background: #ffffff;
    border-radius: var(--borderRadius);
    .group_selected{
        &::v-deep{
            .flex.flex-wrap,
            .ant-tag{
                width: 100%!important;
                max-width: 100%!important;
            }
        }
    }
}
</style>