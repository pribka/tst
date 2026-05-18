<template>
    <a-form-model ref="formRef" class="task_form_wrap" :model="form" :rules="rules">
        <a-form-model-item
            v-if="formInfo.title"
            :rules="formInfo.title.rules"
            label="Название (ru)"
            prop="title">
            <a-input v-model="form.title" size="large" placeholder="Название на русском" />
        </a-form-model-item>

        <!-- Дополнительное поле без табов -->
        <a-form-model-item
            v-if="formInfo.title"
            :rules="formInfo.title_kk.rules"
            label="Название (kk)"
            prop="title_kk">
            <a-input v-model="form.title_kk" size="large" placeholder="Атауы (қазақша)" />
        </a-form-model-item>
    </a-form-model>
</template>

<script>
export default {
    name: 'OrganForm',
    props: { visible: { type: Boolean, default: false } },
    data () {
        const formModel = () => ({
            id: null,
            // RU обязательное поле (базовое)
            title: '',
            // KK опциональное
            title_kk: ''
        })

        return {
            form: formModel(),
            formInfo: {
                title: { rules: [{ required: true, message: 'Введите заголовок (ru)', trigger: 'blur' }] },
                title_kk: { rules: [] }
            }
        }
    },
    computed: {
        rules () {
            return {
                title: this.formInfo.title.rules,
                title_kk: this.formInfo.title_kk.rules
            }
        }
    },
    methods: {
        reset () {
            this.form = { id: null, title: '', title_kk: '' }
        },

        setData (item) {
            this.form = {
                id: item.id ?? null,
                // падение назад на старое поле title, если нет title_ru
                title: item.title_ru ?? item.title ?? '',
                title_kk: item.title_kk ?? ''
            }
        },

        submit () {
            return new Promise((resolve) => {
                this.$refs.formRef.validate((valid) => {
                    if (!valid) return resolve({ valid: false })
                    const payload = {
                        // RU
                        title: this.form.title,
                        // KK (опционально)
                        title_kk: this.form.title_kk || null
                    }
                    resolve({ valid: true, id: this.form.id, payload })
                })
            })
        }
    }
}
</script>

<style scoped>
/* стили при необходимости */
</style>
