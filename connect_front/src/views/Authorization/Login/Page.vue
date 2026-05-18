<template>
    <div>
        
    </div>
    <!-- <div class="page_wrapper">
        <div class="page_labels mb-7">
            <h1 class="mb-2">
                Авторизация на портале
            </h1>
            <p v-if="authConfig && authConfig.register">
                {{ $t('reg_text') }}
                <router-link v-if="joinUser" :to="{name: 'joinUser', query: $route.query}">
                    {{ $t('reg') }}
                </router-link>
                <router-link v-else :to="{name: 'registration'}">
                    {{ $t('reg') }}
                </router-link>
            </p>
        </div>
        <a-form-model
            ref="authForm"
            :model="form"
            layout="vertical"
            autocomplete="off"
            :rules="rules">
            <a-form-model-item
                ref="typeInput"
                class="mb-3"
                prop="typeInput">
                <div class="flex items-center email_input">
                    <a-input
                        v-model="form.typeInput"
                        ref="loginEmail"
                        :placeholder="regTypePlaceholder"
                        size="large"
                        @pressEnter="captchaCheck()" />
                </div>
            </a-form-model-item>
            <a-form-model-item
                ref="password"
                prop="password">
                <a-input-password
                    v-model="form.password"
                    ref="loginPassword"
                    :placeholder="$t('your_password')"
                    size="large"
                    @pressEnter="captchaCheck()" />
            </a-form-model-item>
            <div>
                <a-button
                    type="primary"
                    :loading="loading"
                    class="form_buttom mb-2"
                    size="large"
                    block
                    @click="captchaCheck()">
                    {{ $t('sing_in') }}
                </a-button>
                <div class="flex items-center justify-between">
                    <router-link
                        v-if="authConfig && authConfig.forgotPassword"
                        :to="{name: 'forgotPassword'}"
                        class="text_current block py-4">
                        {{ $t('forgot_your_password') }}
                    </router-link>
                    <a-button
                        v-if="help_text"
                        type="link"
                        size="large"
                        style="font-size: 14px;"
                        class="text_current px-0"
                        :loading="helpLoader"
                        @click="registerHelp">
                        Помощь
                    </a-button>
                </div>
            </div>
        </a-form-model>
        <a-modal 
            v-model="visible"
            :title="help_title"
            :width="width"
            on-ok="handleOk">
            <template slot="footer">
                <a-button key="submit" type="primary" @click="handleOk">
                    Закрыть
                </a-button>
            </template>
            <div class="help__text">
                {{ help_text }}
            </div>
        </a-modal>
    </div> -->
</template>

<script>
import { mapState, mapActions } from 'vuex'
const regexEmail = /^[a-zA-Z0-9.!#$%&'*+/=?^_`{|}~-]+@[a-zA-Z0-9-]+(?:\.[a-zA-Z0-9-]+)*$/;
export default {
    computed: {
        ...mapState({
            usersAuth: state => state.user.usersAuth
        }),
        loginEmail() {
            return this.$refs['loginEmail']
        },
        loginPassword() {
            return this.$refs['loginPassword']
        },
        authConfig() {
            return this.$store.state.user.authConfig
        },
        regTypePlaceholder() {
            if(this.authConfig?.registerType === 'all')
                return 'Ваш телефон или e-mail'
            if(this.authConfig?.registerType === 'phone')
                return 'Ваш телефон'
            return 'Ваш e-mail'
        },
        joinUser() {
            return this.$route.query?.token ? true : false
        }
    },
    data() {
        const validateMailOrPhone = (rule, value, callback) => {
            const regex = /^([a-zA-Z0-9_\.\-])+\@(([a-zA-Z0-9\-])+\.)+([a-zA-Z0-9]{2,4})|([0-9]{10})+$/;
            if (value === '') {
                callback(new Error(this.$t('field_required')))
            } else if (!regex.test(value)) {
                callback(new Error('Заполнено не верно'))
            } else {
                callback()
            }
        };
        return {
            selected: [],
            loading: false,
            helpLoader: false,
            visible: false,
            help_text: '',
            help_title: '',
            width: '80%',
            form: {
                typeInput: '',
                password: ''
            },
            rules: {
                typeInput: [
                    { validator: validateMailOrPhone, trigger: 'change' },
                    { required: true, message: this.$t('field_required'), trigger: 'change' },
                    { max: 255, message: this.$t('required_sym', { sym: 255 }), trigger: 'change' },
                ],
                password: [
                    { required: true, message: this.$t('field_required'), trigger: 'change' },
                    { min: 6, message: this.$t('required_sym', { sym: 6 }), trigger: 'change' }
                ]
            }
        }
    },
    metaInfo() {
        return {
            title: `Авторизация на портале | Gos24.КОННЕКТ`
        }
    },
    beforeCreate() {
        const user = localStorage.getItem('user')
        if(user) {
            // location.reload()
        }
    },
    created() {
        this.getHelpText()
    },
    methods: {
        ...mapActions({
            init: 'user/init'
        }),
        captchaCheck() {
            if(this.authConfig.reCAPTCHASiteKey) {
                grecaptcha.ready(() => {
                    this.loading = true
                    grecaptcha.execute(this.authConfig.reCAPTCHASiteKey, {action: 'login'}).then((token) => {
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

                        if(target === 'email') {
                            formData.email = login
                        }
                        if(target === 'phone') {
                            formData.phone = login
                        }

                        if(captcha)
                            formData.captcha = captcha
                        else
                            formData.captcha = 'captcha'

                        if(target === 'phone' && !login.includes('+')) {
                            const fLetter = login.charAt(0)
                            if(fLetter !== '8') {
                                formData.phone = `+${login}`
                            } else {
                                login = login.substring(1)
                                formData.phone = `+7${login}`
                            }
                        }

                        const data = await this.$store.dispatch('user/login', formData)
                        if(data) {
                            localStorage.setItem('is_show_offer', data.user_previous_login === null)
                            await this.$store.dispatch('loginConfigInit')
                            // await this.$store.dispatch('navigation/routeInit')
                            // await this.$store.dispatch('loginAppInit')
                            location.reload()
                            // this.$router.push({ name: 'meetings' })
                        }
                    } catch(error) {
                        if(error?.status) {
                            this.$message.error(error.status, 5)
                        } else {
                            if(error?.message) {
                                this.$message.error(error.message, 5)
                            } else {
                                this.$message.error(this.$t('authorisation_error'))
                            }
                        }
                        console.log(error)
                    } finally {
                        this.loading = false
                    }
                } else {
                    return false
                }
            })
        },
        registerHelp() {
            this.visible = true
        },
        async getHelpText () {
            try {
                this.helpLoader = true
                await this.$http.get('/catalogs/register_help/')
                    .then((data) => {
                        if (data?.data) {
                            if (data.data.help_text && data.data.name) {
                                this.help_text = data.data.help_text
                                this.help_title = data.data.name
                            }
                        }
                    })
            } catch(e) {
                console.log(e)
            } finally {
                this.helpLoader = false
            }
        },
        handleOk() {
            this.visible = false
        }
    }
}
</script>

<style lang="scss" scoped>
.login_button{
    height: 50px;
}
</style>

<style lang="scss">
.auth_layout{
    .email_input{
        .ant-btn{
            &.ant-dropdown-trigger{
                height: 65px;
                border-radius: 0px var(--borderRadius) var(--borderRadius) 0px;
                border-left: 0px;
            }
        }
        &.email_drop{
            .ant-input{
                border-radius: var(--borderRadius) 0px 0px var(--borderRadius);
            }
        }
    }
}

.help{
    &__text{
        white-space: pre-line;
        height: 50vh;
        overflow-y: auto;
    }
}
</style>