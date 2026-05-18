<template>
    <div v-if="tgBotLink">
        <a-button 
            v-if="isMobile"
            type="ui" 
            ghost
            style="max-width: 38px;max-height: 36px;padding: 0px;"
            shape="circle"
            size="large" 
            class="flex items-center justify-center ant-btn-icon-only"
            @click="openLink()">
            <img src="@/assets/images/telegram.svg" style="max-width: 16px;min-width: 16px;" />
        </a-button>
        <a-popover
            v-else
            :mouseLeaveDelay="0.5"
            v-model="popupVisible"
            transitionName=""
            :getPopupContainer="trigger => trigger.parentNode"
            placement="bottom">
            <a-button 
                type="ui" 
                ghost
                style="max-width: 38px;max-height: 36px;padding: 0px;"
                shape="circle"
                size="large" 
                class="flex items-center justify-center ant-btn-icon-only"
                @click="openLink()">
                <img src="@/assets/images/telegram.svg" style="max-width: 16px;min-width: 16px;" />
            </a-button>
            <template v-slot:content>
                <div class="mb-2 font-semibold">
                    {{ $t('noty.telegramNotifications') }}
                </div>
                <qr-code :size="210" :text="tgBotLink" />
            </template>
        </a-popover>
    </div>
</template>

<script>
export default {
    components: {
        QrCode: () => import('vue-qrcode-component')
    },
    computed: {
        tgBotURL() {
            return this.$store?.state?.config?.config?.tg_bot_settings?.url
        },
        user() {
            return this.$store.state.user.user
        },
        tgBotLink() {
            if(this.user)
                return `${this.tgBotURL}?start=${this.user.telegram_connect_token}`
            return null
        },
        isMobile() {
            return this.$store.state.isMobile
        },
    },
    data() {
        return {
            popupVisible: false
        }
    },
    methods: {
        openLink() {
            window.open(this.tgBotLink, '_blank')
        }
    }
}
</script>