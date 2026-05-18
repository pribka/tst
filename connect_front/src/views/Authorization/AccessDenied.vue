<template>
    <div class="auth_layout pt-8">
        <header class="header">
            <div class="container">
                <div class="header_inner">
                    <div class="auth_logo">
                        <router-link :to="{name: 'login'}">
                            <!-- <LogoBlock /> -->
                            <img 
                                class="logo"
                                src="@/assets/images/logo_white_text.svg" 
                                alt="logo">
                        </router-link>
                    </div>
                </div>
            </div>
        </header>
        <main class="main">
            <div class="container flex-grow flex flex-col">
                <div class="panel">
                    <h1 class="panel__title">
                        {{ $t('Access is denied') }}
                    </h1>
                    <p class="panel__text">
                        {{ $t('Unfortunately, your data plan has expired. To continue working, you need to renew your subscription or select a new tariff') }}
                    </p>
                    <template v-if="false">
                        <div class="flex flex-col items-center">
                            <a-button
                                class="mb-2.5 max-w-[300px]"
                                block
                                type="primary"
                                size="large">
                                {{ $t('Extend the tariff plan')}}
                            </a-button>
                            <a-button
                                class="max-w-[300px]"
                                block
                                type="ui"
                                ghost
                                size="large">
                                {{ $t('Contact support')}}
                            </a-button>
                        </div>
                    </template>
                </div>
            </div>
        </main>
    </div>
</template>

<script>
import { mapState } from 'vuex'
import eventBus from '@/utils/eventBus'
import { langList, loadedLanguages } from '@/config/i18n-setup'
export default {
    components: {
    },
    computed: {
        ...mapState({
            windowWidth: state => state.windowWidth
        }),
        register() {
            return this.$route?.name === 'registration' ? true : false
        },
        authConfig() {
            return this.$store.state.user.authConfig
        },
        locales() {
            return this.$i18n.availableLocales.filter(f => f !== this.$i18n.locale)
        }
    },
    metaInfo() {
        return {
            title: `${this.$t('Access is denied')} | Gos24.КОННЕКТ`
        }
    },
    data() {
        return {
            langList,
            loadedLanguages,
            loading: false,
            formInfo: null,
            show: false
        }
    },
    created() {
        this.getInfo()
    },
    methods: {
        changeLang(lang) {
            try {
                localStorage.setItem('lang', lang)
                location.reload()
            } catch(e) {
                console.log(e)
            }
        },
        openRegistration() {
            eventBus.$emit('open_registration')
        },
        changeLocale(locale) {
            this.$i18n.locale = locale
            this.$router.push({params: { lang: locale }})
        },
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

<style lang="scss" scoped>
.panel {
    max-width: 670px;
    margin: 0 auto;
    padding: 45px;
    padding-bottom: 35px;
    padding: 30px 40px;

    background-color: rgba(#FFFFFFB2, 0.7);
    border-radius: 20px;
    backdrop-filter: blur(14px);

    @media (max-width: 900px) {
        padding: 30px 30px;
    }
}

.panel__title {
    line-height: 1.1;
    margin-bottom: 20px;
    font-size: 32px;
    text-align: center;
}


.panel__text {
    margin-bottom: 30px;
    font-size: 18px;
    text-align: center;
}


.logo {
    height: 76px;
}
.container {
    $padding-x: 30px;
    max-width: calc(1600px - $padding-x);
    padding: 0 $padding-x;
    margin: 0 auto;
    height: 100%;
    @media (max-width: 680px) {
        padding: 0 16px;
    }
}
.lang_btn_wrapp{
    padding-left: 15px;
    padding-right: 15px;
    display: block;
    margin-top: 20px;
    @media (min-width: 600px) {
        display: none;
    }
}
.header {
    margin-bottom: 2rem;
}
.lang_btn{
    cursor: pointer;
    margin-bottom: 5px;
    font-size: 16px;
    line-height: 50px;
    background: rgba(255, 255, 255, 0.6980392157);
    border-radius: 8px;
    height: 50px;
    padding: 0 20px;
    white-space: nowrap;
    text-align: center;
    @media (min-width: 600px) {
        margin-right: 15px;
        margin-bottom: 0px;
        text-align: left;
    }
}
.header_inner {
    display: flex;
    align-items: center;
    justify-content: space-between;
    height: 120px;
    .ant-btn::v-deep {
        height: 50px;
        padding: 0 50px;
    }
    @media (min-width: 600px) {
        .register_button {
            display: flex;
            align-items: center;
            padding-left: 20px;
        }
    }
    @media (max-width: 600px) {
        height: auto;
        flex-direction: column;
        justify-content: center;
        // mb
        .auth_logo {
            margin-bottom: 3rem;
        }
        .register_button {
            width: 100%;
            .ant-btn::v-deep {
                width: 100%;
            }
            .lang_btn{
               display: none; 
            }
        }
    }
}

::v-deep{
    .lang_switch__popup{
        max-width: 150px;
    }
}
.auth_route{
    transition: all 0.5s cubic-bezier(0.645, 0.045, 0.355, 1);
    visibility: hidden;
    opacity: 0;
    &.show{
        opacity: 1;
        visibility: visible;
    }
}
.translate-enter-active,
  .translate-leave-active {
    transition: all 0.5s ease;
  }
  .translate-enter-from,
  .translate-leave-to {
    opacity: 0;
    transform: translateX(30px);
  }
.auth_layout{
    font-family: 'Rubik', sans-serif;

    display: flex;
    flex-direction: column;

    height: 100vh;
    width: 100vw;
    padding-bottom: 200px;

    overflow-y: auto;;
    
    background-image: url("~@/assets/images/auth_bg.jpg");
    background-size: cover;

}
.main {
    flex-grow: 1;
    display: flex;
    flex-direction: column;
}
</style>

<style lang="scss">
.grecaptcha-badge{
    bottom: 10px;
}
</style>