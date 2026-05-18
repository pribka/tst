<template>
    <div class="chat_message user_message">
        <div class="chat_message__bubble">
            <div class="message_header">
                {{ formattedDate }}
            </div>
            <div v-if="message.text" class="message_text" v-html="message.text" />
        </div>
    </div>
</template>

<script>
export default {
    props: {
        message: {
            type: Object,
            required: true
        }
    },
    computed: {
        formattedDate() {
            const date = this.$moment(this.message.created_at)
            return date.isSame(this.$moment(), 'day')
                ? date.format('HH:mm')
                : date.format('DD.MM.YYYY HH:mm')
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
    display: flex;
    &:not(:last-child) {
        margin-bottom: 15px;
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