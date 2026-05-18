<template>
    <div class="lang_message">
        <div class="lang_message__title">{{ $t('notice_browser_language', { lang: $t(browserLang) }) }}</div>
        <div class="lang_message__text">{{ $t('change_site_language', { lang: $t(browserLang) }) }}</div>
        <a-button type="primary" block size="large" class="mb-2" @click="setLang()">
            {{ $t('change_language', { lang: $t(browserLang) }) }}
        </a-button>
        <a-button block size="large" @click="closeMessage()">
            {{ $t('keep_current_language') }}
        </a-button>
    </div>
</template>

<script>
import {mapState} from 'vuex'

export default {
    computed: {
        ...mapState({
            browserLang: state => state.browserLang
        })
    },
    methods: {
        closeMessage() {
            localStorage.setItem('langInit', true)
            this.$store.commit('SET_SHOW_LANG_MESSAGE', true)
            this.$store.commit('SET_BROWSER_LANG', null)
        },
        setLang() {
            try {
                localStorage.setItem('lang', this.browserLang || 'ru')
                this.closeMessage()
                location.reload()
            } catch(e) {
                console.log(e)
            }
        }
    }
}
</script>

<style lang="scss" scoped>
.lang_message{
    position: fixed;
    top: 60px;
    right: 20px;
    z-index: 100;
    padding: 20px 30px;
    border-radius: 10px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
    max-width: 490px;
    -webkit-backdrop-filter: blur(15px);
    backdrop-filter: blur(15px);
    background: #f1f5fbb3;
    &__title{
        font-weight: 600;
        font-size: 16px;
        margin-bottom: 10px;
    }
    &__text{
        margin-bottom: 15px;
        font-size: 15px;
        line-height: 24px;
    }
    &::v-deep{
        .ant-btn{
            &:not(.ant-btn-primary){
                background: transparent;
            }
        }
    }
}
</style>