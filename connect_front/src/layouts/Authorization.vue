<template>
    <div class="flex justify-center pt-8">
        <router-view v-if="authConfig" />
    </div>
</template>

<script>
export default {
    computed: {
        authConfig() {
            return this.$store.state.user.authConfig
        }
    },
    data() {
        return {
            loading: false,
            formInfo: null
        }
    },
    created() {
        this.getInfo()
    },
    methods: {
        async getInfo() {
            try {
                this.loading = true
                await this.$store.dispatch('user/getAuthConfig')
                if(this.authConfig.reCAPTCHASiteKey) {
                    this.capGenerate()
                }
            } catch(e) {
                console.log(e)
            } finally {
                this.loading = false
            }
        },
        capGenerate() {
            const script = document.createElement('script')
            script.async = true
            script.src = `https://www.google.com/recaptcha/api.js?trustedtypes=true&render=${this.authConfig.reCAPTCHASiteKey}`
            script.onload = () => {}
            script.onerror = () => {
                console.log('%c Error occurred while loading script', 'color: #bf1432')
            }
            document.body.appendChild(script)
        }
    }
}
</script>