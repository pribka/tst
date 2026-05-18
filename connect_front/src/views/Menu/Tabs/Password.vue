<template>
    <div style="max-width: 450px;">
        <a-form-model
            ref="changePasswordForm"
            :model="form"
            class="change_pass_form"
            layout="vertical"
            autocomplete="off"
            :rules="rules">
            <a-form-model-item
                has-feedback 
                ref="oldPassword"
                label="Введите текущий пароль"
                prop="oldPassword">
                       
                <a-input-password
                    v-model="form.oldPassword"
                         
                    size="large"/>
            </a-form-model-item>
            <a-form-model-item
                has-feedback 
                ref="password"
                label="Введите новый пароль"
                prop="password">
                       
                <a-input-password
                    v-model="form.password"
                         
                    size="large"/>
            </a-form-model-item>
            <a-form-model-item
                has-feedback 
                ref="passwordConfirm"
                label="Повторите новый пароль"
                prop="passwordConfirm">
                       
                <a-input-password
                    v-model="form.passwordConfirm"
                    size="large"/>
            </a-form-model-item>
            <a-form-model-item label="Надежность Пароля"> 
                <password
                    v-model="form.password" 
                    :strength-meter-only="true"/>
            </a-form-model-item>
            <a-button
                type="primary"
                :loading="loading"
                class="px-10"
                size="large"
                @click="formSubmit()">
                Сменить пароль
            </a-button>
        </a-form-model>
    </div>
</template>

<script>
import Password from 'vue-password-strength-meter'
export default {
    components: {
        Password
    },
    data(){
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
            form: {
                oldPassword: "",
                password: "",
                passwordConfirm: ""
            },
            loading: false,
            rules: {
                oldPassword: [
                    { required: true, message: this.$t('field_required'), trigger: 'change' },
                    
                ],
                password: [
                    { required: true, message: this.$t('field_required'), trigger: 'change' },
                    { min: 8, message: this.$t('required_sym', { sym: 8 }), trigger: 'change' }
                ],
                passwordConfirm: [
                    { validator: validatePass, trigger: 'change' },
                    { required: true, message: this.$t('field_required'), trigger: 'change' },
                    { min: 8, message: this.$t('required_sym', { sym: 8 }), trigger: 'change' }
                ],

            }
        }
    },
    methods: {
        formSubmit(){
            this.$refs.changePasswordForm.validate(async valid => {
                if (valid) {
                    try {
                        this.loading = true
                        await this.$http.post('/users/change_password/', this.form)
                        this.$message.success('Пароль успешно изменен')
                    }
                    catch(e){
                        if(e.non_field_errors){
                            this.$message.error(String(e.non_field_errors), 4)
                        } else {
                            this.$message.error('Ошибка')
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
        }
    }

}
</script>

<style lang="scss">
.change_pass_form{
    .Password{
        margin: 0px;
    }
}
</style>