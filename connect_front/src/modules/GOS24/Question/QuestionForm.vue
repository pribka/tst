<template>
    <a-form-model ref="formRef" class="task_form_wrap" :model="form" :rules="rules">
        <!-- Заголовок: RU/KK -->
        <a-tabs size="large" animated>
            <a-tab-pane key="ru-title" tab="Заголовок (ru)">
                <a-form-model-item
                    v-if="formInfo.title"
                    :rules="formInfo.title.rules"
                    label="Заголовок (ru)"
                    prop="title">
                    <a-input v-model="form.title" size="large" placeholder="Заголовок на русском" />
                </a-form-model-item>
            </a-tab-pane>

            <a-tab-pane key="kk-title" tab="Заголовок (kk)">
                <a-form-model-item
                    v-if="formInfo.title"
                    label="Заголовок (kk)"
                    prop="title_kk">
                    <a-input v-model="form.title_kk" size="large" placeholder="Тақырып (қазақша)" />
                </a-form-model-item>
            </a-tab-pane>
        </a-tabs>

        <a-form-model-item v-if="formInfo.partition" label="Раздел" :rules="formInfo.partition.rules" prop="partition">
            <DrawerSelectPartition v-model="form.partition" />
        </a-form-model-item>

        <a-form-model-item v-if="formInfo.tags" label="Теги" :rules="formInfo.tags.rules" prop="tags">
            <DrawerSelectTag v-model="form.tags" :multiple="true" />
        </a-form-model-item>

        <!-- Вопрос: RU/KK -->
        <a-tabs size="large" animated>
            <a-tab-pane key="ru-question" tab="Вопрос (ru)">
                <a-form-model-item v-if="formInfo.question_html" label="Вопрос (ru)" :rules="formInfo.question_html.rules" prop="question_html">
                    <component
                        :showTextDecorations="true"
                        :uploadFieldKey="uploadFieldKey"
                        :uploadUrl="uploadUrl"
                        :is="ckEditor"
                        :taskId="form.id"
                        :key="'q-ru-' + `${form.id || 'new'}-${editorRev}`"
                        v-model="form.question_html"/>
                </a-form-model-item>
            </a-tab-pane>

            <a-tab-pane key="kk-question" tab="Вопрос (kk)">
                <a-form-model-item v-if="formInfo.question_html" label="Вопрос (kk)" prop="question_html_kk">
                    <component
                        :showTextDecorations="true"
                        :uploadFieldKey="uploadFieldKey"
                        :uploadUrl="uploadUrl"
                        :is="ckEditor"
                        :taskId="form.id"
                        :key="'q-kk-' + `${form.id || 'new'}-${editorRev}`"
                        v-model="form.question_html_kk"/>
                </a-form-model-item>
            </a-tab-pane>
        </a-tabs>

        <!-- Ответ: RU/KK -->
        <a-tabs size="large" animated>
            <a-tab-pane key="ru-answer" tab="Ответ (ru)">
                <a-form-model-item v-if="formInfo.answer_html" label="Ответ (ru)" :rules="formInfo.answer_html.rules" prop="answer_html">
                    <component
                        :showTextDecorations="true"
                        :uploadFieldKey="uploadFieldKey"
                        :uploadUrl="uploadUrl"
                        :is="ckEditor"
                        :taskId="form.id"
                        :key="'a-ru-' + `${form.id || 'new'}-${editorRev}`"
                        v-model="form.answer_html"/>
                </a-form-model-item>
            </a-tab-pane>

            <a-tab-pane key="kk-answer" tab="Ответ (kk)">
                <a-form-model-item v-if="formInfo.answer_html" label="Ответ (kk)" prop="answer_html_kk">
                    <component
                        :showTextDecorations="true"
                        :uploadFieldKey="uploadFieldKey"
                        :uploadUrl="uploadUrl"
                        :is="ckEditor"
                        :taskId="form.id"
                        :key="'a-kk-' + `${form.id || 'new'}-${editorRev}`"
                        v-model="form.answer_html_kk"/>
                </a-form-model-item>
            </a-tab-pane>
        </a-tabs>

        <a-form-model-item prop="draft">
            <a-radio-group v-model="form.draft">
                <a-radio :value="false">Готово к публикации</a-radio>
                <a-radio :value="true">Черновик</a-radio>
            </a-radio-group>
        </a-form-model-item>

        <a-form-model-item prop="main_in_week">
            <a-checkbox v-model="form.main_in_week">Главное за неделю</a-checkbox>
        </a-form-model-item>
    </a-form-model>
</template>

<script>
import mixins from '@/modules/GOS24/mixins/mixins'

const mkForm = () => ({
    id: null,
    kind: 'qa',

    // RU обязательные
    title: '',
    question_html: '',
    answer_html: '',

    // KK опциональные
    title_kk: '',
    question_html_kk: '',
    answer_html_kk: '',

    partition: undefined,
    tags: [],
    main_in_week: false,
    draft: false
})

export default {
    name: 'QuestionForm',
    components: {
        DrawerSelectPartition: () => import('@apps/GOS24/components/DrawerSelectPartition.vue'),
        DrawerSelectTag: () => import('@apps/GOS24/components/DrawerSelectTag.vue')
    },
    props: { visible: { type: Boolean, default: false } },
    mixins: [mixins],
    data () {
        return {
            form: mkForm(),
            formInfo: {
                title: { rules: [{ required: true, message: 'Введите заголовок (ru)', trigger: 'blur' }] },
                partition: { rules: [{ required: true, message: 'Выберите раздел', trigger: 'change' }] },
                tags: { rules: [{ required: true, message: 'Выберите теги', trigger: 'change' }] },
                question_html: { rules: [{ required: true, message: 'Введите вопрос (ru)', trigger: 'change' }] },
                answer_html: { rules: [{ required: true, message: 'Введите ответ (ru)', trigger: 'change' }] }
            },
            editorRev: 0,
        }
    },
    computed: {
        rules () {
            return {
                title: this.formInfo.title.rules,
                partition: this.formInfo.partition.rules,
                tags: this.formInfo.tags.rules,
                question_html: this.formInfo.question_html.rules,
                answer_html: this.formInfo.answer_html.rules
            }
        },
        ckEditor () {
            return this.visible ? () => import('@apps/CKEditor') : null
        }
    },
    methods: {
        reset () { this.form = mkForm() },
        setData (item) {
            this.form = {
                ...mkForm(),
                id: item.id ?? null,
                kind: 'qa',

                // RU (фолбэк на базовые поля, если *_ru нет)
                title: item.title_ru ?? item.title ?? '',
                question_html: item.question_html_ru ?? item.question_html ?? '',
                answer_html: item.answer_html_ru ?? item.answer_html ?? '',

                // KK
                title_kk: item.title_kk ?? '',
                question_html_kk: item.question_html_kk ?? '',
                answer_html_kk: item.answer_html_kk ?? '',

                partition: item.partition ?? undefined,
                tags: item.tags || [],
                main_in_week: !!item.main_in_week,
                draft: !!item.draft
            }
            this.editorRev += 1
        },
        submit () {
            return new Promise((resolve) => {
                this.$refs.formRef.validate((valid) => {
                    if (!valid) return resolve({ valid: false })
                    const payload = {
                        kind: 'qa',

                        // RU
                        title: this.form.title,
                        question_html: this.form.question_html,
                        answer_html: this.form.answer_html,

                        // KK
                        title_kk: this.form.title_kk,
                        question_html_kk: this.form.question_html_kk,
                        answer_html_kk: this.form.answer_html_kk,

                        partition: this.form.partition ? this.form.partition.id : null,
                        tags: (this.form.tags || []).map(t => t.id),
                        main_in_week: this.form.main_in_week,
                        draft: this.form.draft,

                        // можно положить с фронта, но источником истины будет бэк:
                        sent_gos: false
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
