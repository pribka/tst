<template>
    <div class="action_btn">
        <a-popover v-model="visible" destroyTooltipOnHide @visibleChange="visibleChange">
            <a-button 
                type="link" 
                class="text-current"
                icon="cloud-download" />
            <div 
                slot="content" 
                class="pwa_popup">
                <p>{{$t('install_prompt')}}</p>
                <a-button 
                    size="small" 
                    type="primary"
                    @click="installApp()">
                    {{$t('install')}}
                </a-button>
            </div>
        </a-popover>
    </div>
</template>

<script>
export default {
    name: 'HeaderPWABanner',
    data() {
        return {
            visible: false
        }
    },
    computed: {
        deferredPrompt() {
            return this.$store.state.deferredPrompt
        }
    },
    created() {
        if(this.deferredPrompt) {
            const banner = localStorage.getItem('pwa_banner')
            if(!banner) {
                setTimeout(() => {
                    localStorage.setItem('pwa_banner', true)
                    this.visible = true
                }, 5000)
            }
        }
    },
    methods: {
        visibleChange(vis) {
            if(!vis) {
                const banner = localStorage.getItem('pwa_banner')
                if(!banner)
                    localStorage.setItem('pwa_banner', true)
            }
        },
        async installApp() {
            this.visible = false
            this.deferredPrompt.prompt()
            const { outcome } = await this.deferredPrompt.userChoice
            this.$store.commit('SET_PWA_POPUP', null)
        }
    },
    mounted() {
        window.addEventListener('appinstalled', () => {
            this.visible = false
            this.$store.commit('SET_PWA_POPUP', null)
        })
    }
}
</script>


<style lang="scss" scoped>
.pwa_popup{
    text-align: center;
    p{
        margin-bottom: 10px;
        max-width: 180px;
        font-size: 15px;
        line-height: 20px;
    }
}
</style>