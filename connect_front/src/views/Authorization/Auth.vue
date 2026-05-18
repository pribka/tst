<template>
    <div class="auth">
        <a-form-model
            ref="authForm"
            :model="form"
            :rules="authRules"
            layout="vertical"
            class="form">
            <div class="form_inner">
                <a-form-model-item
                    class="mb-2"
                    prop="email"
                    label="E-mail">
                    <a-input 
                        v-model="form.email"
                        size="large"
                        @pressEnter="captchaCheck()"/>
                </a-form-model-item>
                <a-form-model-item
                    class="mb-2"
                    prop="password"
                    label="Пароль">
                    <a-input-password 
                        v-model="form.password"
                        size="large"
                        @pressEnter="captchaCheck()" />
                </a-form-model-item>
                <a-button
                    type="primary"
                    :loading="loading"
                    class="mb-2"
                    size="large"
                    ghost
                    block
                    @click="captchaCheck()">
                    Войти
                </a-button>
            </div>
        </a-form-model>
    </div>
</template>

<script>
import { mapState } from 'vuex'
const regexEmail = /^[a-zA-Z0-9.!#$%&'*+/=?^_`{|}~-]+@[a-zA-Z0-9-]+(?:\.[a-zA-Z0-9-]+)*$/;

export default {
    computed: {
        ...mapState({
            windowWidth: state => state.windowWidth
        }),
        drawerWidth() {
            if (this.windowWidth > 1024) 
                return 936
            if (this.windowWidth > 828)
                return 828
            return this.windowWidth
        },
        authConfig() {
            return this.$store.state.user.authConfig
        },

    },
    data() {
        return {
            loading: false,
            form: {
                typeInput: '',
                password: ''
            },

            authRules: {
                email: [
                    { required: true, message: this.$t('auth.field_required'), trigger: 'change' },
                    { type: 'email', message: this.$t('auth.enter_valid_email'), trigger: 'change' },
                    { max: 255, message: this.$t('auth.required_sym', { sym: 255 }), trigger: 'change' },
                ],
                password: [
                    { required: true, message: this.$t('auth.field_required'), trigger: 'change' },
                    { min: 6, message: this.$t('auth.required_sym', { sym: 6 }), trigger: 'change' }
                ]
            },
        }
    },
    methods: {
        captchaCheck() {
            if (this.authConfig.reCAPTCHASiteKey) {
                grecaptcha.ready(() => {
                    this.loading = true
                    grecaptcha.execute(this.authConfig.reCAPTCHASiteKey, { action: 'login' }).then((token) => {
                        this.formSubmit(token)
                    })
                })
            } else {
                this.formSubmit()
            }
        },
        formSubmit(captcha = null) {
            this.$refs.authForm.validate(async valid => {
                if (valid) {
                    try {
                        this.loading = true
                        const target = regexEmail.test(this.form.typeInput) ? 'email' : 'phone'
                        let login = JSON.parse(JSON.stringify(this.form.typeInput)).trim()
                        let formData = JSON.parse(JSON.stringify(this.form))

                        if (target === 'email') {
                            formData.email = login
                        }
                        if (target === 'phone') {
                            formData.phone = login
                        }

                        if (captcha)
                            formData.captcha = captcha
                        else
                            formData.captcha = 'captcha'

                        if (target === 'phone' && !login.includes('+')) {
                            const fLetter = login.charAt(0)
                            if (fLetter !== '8') {
                                formData.phone = `+${login}`
                            } else {
                                login = login.substring(1)
                                formData.phone = `+7${login}`
                            }
                        }

                        const data = await this.$store.dispatch('user/login', formData)
                        if (data) {
                            localStorage.setItem('is_show_offer', data.user_previous_login === null)
                            await this.$store.dispatch('loginConfigInit')
                            // await this.$store.dispatch('navigation/routeInit')
                            // await this.$store.dispatch('loginAppInit')
                            location.reload()
                            // this.$router.push({ name: 'meetings' })
                        }
                    } catch (error) {
                        if (error?.data?.status) {
                            this.$message.error(error?.data.status, 5)
                        } else {
                            if (error?.data?.message) {
                                this.$message.error(error?.data.message, 5)
                            } else {
                                this.$message.error(this.$t('auth.authorisation_error'))
                            }
                        }
                        console.log(error)
                    } finally {
                        this.loading = false
                    }
                } else {
                    this.loading = false
                    return false
                }
            })
        },

    }
}
</script>

<style lang="scss" scoped>
$breakpoint-1: 1279px;
$breakpoint-2: 1024px;
.auth {
    height: 100%;
    display: flex;
    justify-content: space-between;
    align-items: flex-start;    
    &::v-deep {
        .ant-input,
        .ant-btn {
            height: 50px;
        }
    }
    @media (max-width: $breakpoint-1) {
        flex-direction: column;
    }
}
.form {
    padding: 30px 40px;
    background: #ffffffb2;
    border-radius: 20px;
    margin-top: auto;
    backdrop-filter: blur(10px);
    -webkit-backdrop-filter: blur(10px);
    
    @media (max-width: $breakpoint-1) {
        max-width: 716px;
        width: 100%;
        margin: 0 auto;
        margin-bottom: 50px;
    }

    @media (max-width: $breakpoint-2) {
        padding: 30px 30px;

        max-width: auto;
        width: 100%;
    }
}
.form_inner {
    width: 500px;
    margin: 0 auto;
    @media (max-width: $breakpoint-2) {
        max-width: auto;
        width: 100%;
    }

}
</style>
