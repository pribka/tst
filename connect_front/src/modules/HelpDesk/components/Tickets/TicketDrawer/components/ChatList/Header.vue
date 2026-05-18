<!-- Header.vue -->
<template>
    <div class="chat_header flex items-center justify-between">
        <div class="flex items-center">
            <div v-if="infoRouter['key'] ==='ticketView'">
                <div v-if="ticket.contact_person" style="font-size: 12px;">{{ ticket.contact_person.name }}</div>
                <div style="font-size: 12px;opacity: 0.6;">{{ $t('helpdesk.contact_person') }}</div>
            </div>
            <div>
                <div v-if="ticket.org_admin" style="font-size: 12px;">{{ ticket.org_admin.name }}</div>
                <div style="font-size: 12px;opacity: 0.6;">{{ $t('helpdesk.organization') }}</div>
            </div>
        </div>
        <div class="flex items-center gap-2">
            <a-button
                type="ui"
                flaticon
                ghost
                shape="circle"
                icon="fi-rr-cross"
                @click="changeShowChat(false)" />
        </div>
    </div>
</template>

<script>
export default {
    props: {
        ticket: {
            type: Object,
            required: true
        },
        infoRouter: {
            type: Object,
            required: false
        },
        showAside: {
            type: Boolean,
            default: false
        },
        changeShowAside: {
            type: Function,
            default: () => {}
        },
        useAside: {
            type: Boolean,
            default: false
        },
        showChat: {
            type: Boolean,
            default: true
        },
        changeShowChat: {
            type: Function,
            default: () => {}
        }
    }
}
</script>

<style lang="scss" scoped>
.chat_header{
    border-radius: 12px 12px 0 0;
    background: #e8ecfa;
    padding: 10px 20px;
}
</style>
