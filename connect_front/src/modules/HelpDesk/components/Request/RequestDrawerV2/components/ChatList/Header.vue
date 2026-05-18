<template>
    <div class="chat_header flex items-center justify-between" :class="isMobile && 'mobile_header'">
        <div class="flex items-center">
            <div>
                <div v-if="ticket.org_admin" style="font-size: 12px;">{{ ticket.org_admin.name }}</div>
                <div style="font-size: 12px;opacity: 0.6;">{{ $t('helpdesk.organization') }}</div>
            </div>
        </div>
        <div v-if="!isMobile" class="flex items-center gap-2">
            <a-button 
                v-if="useAside"
                type="ui" 
                flaticon
                ghost
                :class="showAside && 'active'"
                shape="circle"
                icon="fi-rr-sidebar"
                @click="changeShowAside(!showAside)" />
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
        }
    },
    computed: {
        isMobile() { 
            return this.$store.state.isMobile
        },
    }
}
</script>

<style lang="scss" scoped>
.chat_header{
    background: #e8ecfa;
    padding: 5px 15px;
    &:not(.mobile_header){
        border-radius: 12px 12px 0 0;
        padding: 10px 20px;
    }
}
</style>