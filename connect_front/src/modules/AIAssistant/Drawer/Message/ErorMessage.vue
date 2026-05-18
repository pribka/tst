<template>
    <a-alert :message="message.text || $t('ai_assistant.error_generic')" banner />
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
    }
}
</script>
