<template>
    <component 
        :is="messageWidget" 
        :messageIndex="messageIndex"
        :message="message" />
</template>

<script>
export default {
    props: {
        message: {
            type: Object,
            required: true
        },
        messageIndex: {
            type: Number,
            default: 0
        }
    },
    computed: {
        messageWidget() {
            if(this.message.is_bot) {
                if(this.message.is_error || this.message.status === 'failed' || this.message.stream_state === 'error')
                    return () => import('./ErorMessage.vue')
                else
                    return () => import('./BotMessage.vue')
            } else
                return () => import('./UserMessage.vue')
        }
    }
}
</script>

<style lang="scss" scoped>
.message_text{
    font-size: 14px;
    word-break: break-word;
    line-height: 22px;
}
.chat_message{
    &.user_message{
        display: flex;
    }
    &.user_message{
        justify-content: flex-end;
    }
    &__bubble{
        background: #fff;
        border-radius: 8px;
        padding: 12px;
        max-width: 400px;
        .message_header{
            margin-bottom: 5px;
            color: #888888;
            font-size: 12px;
            line-height: 16px;
        }
    }
}
</style>
