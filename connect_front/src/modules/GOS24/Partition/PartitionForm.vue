<template>
    <a-form-model ref="formRef" class="task_form_wrap" :model="form" :rules="rules">
        <a-form-model-item
            v-if="formInfo.name"
            :rules="formInfo.name.rules"
            label="Название (ru)"
            prop="name">
            <a-input v-model="form.name" size="large" placeholder="Название на русском" />
        </a-form-model-item>

        <a-form-model-item
            v-if="formInfo.name_kk"
            :rules="formInfo.name_kk.rules"
            label="Название (kk)"
            prop="name_kk">
            <a-input v-model="form.name_kk" size="large" placeholder="Атауы (қазақша)" />
        </a-form-model-item>
        <a-form-model-item v-if="formInfo.code" :rules="formInfo.code.rules" label="Код" prop="code">
            <a-input v-model="form.code" size="large" placeholder="Код (необязательно)" />
        </a-form-model-item>
    </a-form-model>
</template>

<script>
export default {
    name: 'PartitionForm',
    props: { visible: { type: Boolean, default: false } },
    data () {
        const formModel = () => ({
            id: null,
            // RU (базовое, обязательное)
            name: '',
            // KK (опционально)
            name_kk: '',
            code: '' // если нужен — оставил место
        })

        return {
            form: formModel(),
            formInfo: {
                name: { rules: [{ required: true, message: 'Введите название (ru)', trigger: 'blur' }] },
                name_kk: { rules: [] },
                code: { rules: [] },
            }
        }
    },
    computed: {
        rules () {
            return {
                name: this.formInfo.name.rules,
                name_kk: this.formInfo.name_kk.rules,
                code: this.formInfo.code.rules,
            }
        }
    },
    methods: {
        reset () {
            this.form = { id: null, name: '', name_kk: '', code: '' }
        },

        setData (item) {
            this.form = {
                id: item.id ?? null,
                // падение назад на старое поле name, если нет name_ru
                name: item.name_ru ?? item.name ?? '',
                name_kk: item.name_kk ?? '',
                code: item.code ?? ''
            }
        },

        submit () {
            return new Promise((resolve) => {
                this.$refs.formRef.validate((valid) => {
                    if (!valid) return resolve({ valid: false })
                    const payload = {
                        // RU
                        name: this.form.name,
                        // KK (опционально, отправляем null если пусто)
                        name_kk: this.form.name_kk || null,
                        code: this.form.code || null
                    }
                    resolve({ valid: true, id: this.form.id, payload })
                })
            })
        }
    }
}
</script>

<style scoped>
/* при необходимости — свои стили */
</style>
