<template>
    <a-modal
        title="Установить пароль"
        :zIndex="5000"
        :visible="visible"
        class="set_pass_modal"
        :confirm-loading="confirmLoading"
        :footer="null"
        @cancel="handleCancel">
        <a-alert 
            message="Установите надежный пароль для доступа к личному кабинету" 
            class="mb-4"
            banner
            type="info" 
            show-icon />
        <a-form-model
            ref="setPassForm"
            :model="form"
            layout="vertical"
            autocomplete="off"
            :rules="rules">
            <a-form-model-item
                has-feedback 
                class="mb-2"
                ref="password"
                label="Введите пароль"
                prop="password">
                <a-input-password
                    v-model="form.password"    
                    size="large"/>
            </a-form-model-item>
            <a-form-model-item
                has-feedback 
                class="mb-2"
                ref="passwordConfirm"
                label="Повторите пароль"
                prop="passwordConfirm"> 
                <a-input-password
                    v-model="form.passwordConfirm"
                    size="large"/>
            </a-form-model-item>
            <a-button
                type="primary"
                :loading="loading"
                :disabled="disabled"
                class="px-10"
                size="large"
                @click="formSubmit()">
                Установить пароль
            </a-button>
        </a-form-model>
    </a-modal>
</template>

<script>
export default {
    name: 'PasswordSet',
    data() {
        let validatePass = (rule, value, callback) => {
            if (value === '') {
                callback(new Error(this.$t('field_required')));
            } else if (value !== this.form.password) {
                callback(new Error("Пароли не совпадают"));
            } else {
                callback();
            }
        }
        return {
            confirmLoading: false,
            rules: {
                password: [
                    { required: true, message: this.$t('field_required'), trigger: 'change' },
                    { min: 8, message: this.$t('required_sym', { sym: 8 }), trigger: 'change' }
                ],
                passwordConfirm: [
                    { validator: validatePass, trigger: 'change' },
                    { required: true, message: this.$t('field_required'), trigger: 'change' },
                    { min: 8, message: this.$t('required_sym', { sym: 8 }), trigger: 'change' }
                ],
            },
            visible: false,
            loading: false,
            disabled: false,
            form: {
                password: '',
                passwordConfirm: ''
            }
        }
    },
    created() {
        setTimeout(() => {
            this.visible = true
        }, 500)
    },
    methods: {
        formSubmit() {
            this.$refs.setPassForm.validate(async valid => {
                if (valid) {
                    try {
                        this.loading = true
                        await this.$store.dispatch('user/setPassword', this.form)
                        this.visible = false
                    }
                    catch(e){
                        if(e.non_field_errors){
                            this.$message.error(String(e.non_field_errors), 4)
                        }
                        console.error(e)
                    }
                    finally{
                        this.loading = false
                    }
                }
                else {
                    this.$message.warning("Проверьте правильность введенных данных")
                    return false
                }
            })
        },
        async handleCancel() {
            try {
                this.confirmLoading = true
                this.disabled = true

                await this.$store.dispatch('user/skipPassword')
                this.visible = false
            } catch(e) {
                console.log(e)
            } finally {
                this.confirmLoading = false
                this.disabled = false
            }
        }
    }
}
</script>

<style lang="scss">
.set_pass_modal{
    .Password{
        margin: 0px;
    }
}
</style>