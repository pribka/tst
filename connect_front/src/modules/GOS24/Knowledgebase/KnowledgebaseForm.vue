<template>
    <a-form-model ref="formRef" class="task_form_wrap" :model="form" :rules="rules">
        <div class="row mb-2">
            <a-radio-group v-model="form.content_type">
                <a-radio v-for="opt in pageTypes" :key="opt.id" :value="String(opt.id)">{{ opt.title }}</a-radio>
            </a-radio-group>
        </div>

        <div class="flex justify-between gap-2">
            <a-form-model-item label="Пособие" prop="tutorial_id" class="w-full">
                <a-select
                    v-model="form.tutorial_id"
                    :disabled="Number(form.content_type) === 1"
                    placeholder="Выберите пособие"
                    :allowClear="true">
                    <a-select-option v-for="t in tutorials" :key="t.id" :value="t.id">{{ t.title }}</a-select-option>
                </a-select>
            </a-form-model-item>

            <a-form-model-item label="Раздел" prop="section_id" class="w-full">
                <a-select
                    v-model="form.section_id"
                    :disabled="Number(form.content_type) !== 3 || !form.tutorial_id"
                    placeholder="Выберите раздел"
                    :allowClear="true">
                    <a-select-option v-for="s in sections" :key="s.id" :value="s.id">{{ s.title }}</a-select-option>
                </a-select>
            </a-form-model-item>
        </div>

        <!-- Заголовок: RU/KK -->
        <a-tabs size="large" animated>
            <a-tab-pane key="ru-title" tab="Заголовок (ru)">
                <a-form-model-item label="Заголовок (ru)" prop="title">
                    <a-input v-model="form.title" placeholder="Заголовок на русском"/>
                </a-form-model-item>
            </a-tab-pane>
            <a-tab-pane key="kk-title" tab="Заголовок (kk)">
                <a-form-model-item label="Заголовок (kk)" prop="title_kk">
                    <a-input v-model="form.title_kk" placeholder="Тақырып (қазақша)"/>
                </a-form-model-item>
            </a-tab-pane>
        </a-tabs>

        <!-- Содержание страницы: RU/KK -->
        <a-tabs size="large" animated>
            <a-tab-pane key="ru-body" tab="Содержание (ru)">
                <a-form-model-item label="Содержание (ru)" prop="body">
                    <component :showTextDecorations="true" :uploadFieldKey="uploadFieldKey" :uploadUrl="uploadUrl" :is="ckEditor" v-model="form.body" :key="'body-ru-' + `${form.id || 'new'}-${editorRev}`"/>
                </a-form-model-item>
            </a-tab-pane>
            <a-tab-pane key="kk-body" tab="Содержание (kk)">
                <a-form-model-item label="Содержание (kk)" prop="body_kk">
                    <component :showTextDecorations="true" :uploadFieldKey="uploadFieldKey" :uploadUrl="uploadUrl" :is="ckEditor" v-model="form.body_kk" :key="'body-kk-' + `${form.id || 'new'}-${editorRev}`"/>
                </a-form-model-item>
            </a-tab-pane>
        </a-tabs>

        <a-form-model-item label="Youtube URL" prop="youtube_url">
            <a-input v-model="form.youtube_url" placeholder="https://youtube.com/..."/>
        </a-form-model-item>

        <a-form-model-item label="Якорная ссылка" prop="anchor_links">
            <a-radio-group v-model="form.anchor_links">
                <a-radio :value="true">Показать якорную ссылку</a-radio>
                <a-radio :value="false">Скрыть якорную ссылку</a-radio>
            </a-radio-group>
        </a-form-model-item>
    </a-form-model>
</template>

<script>
import axios from '@/config/axios'
import mixins from "@/modules/GOS24/mixins/mixins";

export default {
    name: 'KnowledgebaseForm',
    props: { visible: { type: Boolean, default: false } },
    data () {
        return {
            loading: { tutorials: false, sections: false },
            tutorials: [],
            sections: [],
            pageTypes: [
                { id: 1, title: 'Пособие' },
                { id: 2, title: 'Раздел' },
                { id: 3, title: 'Страница' }
            ],
            form: {
                content_type: '1',   // '1' | '2' | '3'
                tutorial_id: null,
                section_id: null,

                // RU обязательные
                title: '',
                body: '',

                // KK опциональные
                title_kk: '',
                body_kk: '',

                youtube_url: '',
                kind: 'knowledgebase',
                anchor_links: false
            },
            editorRev: 0,
        }
    },
    mixins: [mixins],
    computed: {
        ckEditor () {
            return () => import('@apps/CKEditor')
        },
        rules () {
            const requiredMsg = 'Обязательное поле'
            return {
                title: [{ required: true, message: requiredMsg, trigger: 'blur' }],
                tutorial_id: [{ validator: this.validateTutorial, trigger: 'change' }],
                section_id: [{ validator: this.validateSection, trigger: 'change' }],
                body: [{ required: true, message: requiredMsg, trigger: 'change' }],
                youtube_url: [{ validator: this.validateYoutube, trigger: 'blur' }]
            }
        }
    },
    watch: {
        'form.content_type': {
            immediate: true,
            handler (val) {
                const t = Number(val)
                if (t === 1) {
                    this.form.tutorial_id = null
                    this.form.section_id = null
                    this.sections = []
                } else if (t === 2) {
                    this.form.section_id = null
                    this.sections = []
                    this.fetchTutorials()
                } else if (t === 3) {
                    this.fetchTutorials()
                }
            }
        },
        'form.tutorial_id' (id) {
            if (Number(this.form.content_type) === 3) {
                this.form.section_id = null
                this.sections = []
                if (id) this.fetchSections()
            }
        }
    },
    methods: {
        reset () {
            this.form = {
                content_type: '1',
                tutorial_id: null,
                section_id: null,

                title: '',
                body: '',
                title_kk: '',
                body_kk: '',

                youtube_url: '',
                kind: 'knowledgebase',
                anchor_links: false
            }
            this.tutorials = []
            this.sections = []
            this.editorRev += 1
        },
        async setData (data) {
            this.form.content_type = String(data.content_type ?? '1')

            // RU с фолбэком на базовые поля при отсутствии *_ru
            this.form.title = data.title_ru ?? data.title ?? ''
            this.form.body = data.body_ru ?? data.body ?? ''

            // KK
            this.form.title_kk = data.title_kk ?? ''
            this.form.body_kk = data.body_kk ?? ''

            this.form.youtube_url = data.youtube_url ?? ''
            this.form.anchor_links = Boolean(data.anchor_links)

            if (Number(this.form.content_type) >= 2) {
                await this.fetchTutorials()
                this.form.tutorial_id = data.tutorial_id ?? null
            }
            if (Number(this.form.content_type) === 3 && this.form.tutorial_id) {
                await this.fetchSections()
                this.form.section_id = data.section_id ?? null
            }
            this.editorRev += 1
        },
        submit () {
            return new Promise((resolve) => {
                this.$refs.formRef.validate((valid) => {
                    if (!valid) return resolve({ valid: false, payload: null })
                    const payload = {
                        content_type: Number(this.form.content_type),
                        tutorial_id: this.form.tutorial_id,
                        section_id: this.form.section_id,

                        // RU
                        title: this.form.title,
                        body: this.form.body,

                        // KK
                        title_kk: this.form.title_kk,
                        body_kk: this.form.body_kk,

                        youtube_url: this.form.youtube_url || null,
                        kind: 'knowledgebase',
                        anchor_links: !!this.form.anchor_links,

                        // фронт тоже проставит, но источник истины — на бэке
                        sent_gos: false
                    }
                    return resolve({ valid: true, payload })
                })
            })
        },

        // ===== Validators
        validateTutorial (rule, value, cb) {
            const need = Number(this.form.content_type) >= 2
            if (need && !this.form.tutorial_id) return cb(new Error('Обязательное поле'))
            cb()
        },
        validateSection (rule, value, cb) {
            const need = Number(this.form.content_type) === 3
            if (need && !this.form.section_id) return cb(new Error('Обязательное поле'))
            cb()
        },
        validateYoutube (rule, value, cb) {
            if (!value) return cb()
            const ok = /^(https?:\/\/)?(www\.)?(youtube\.com|youtu\.be)\/.+$/i.test(value)
            if (!ok) return cb(new Error('Введите корректную ссылку YouTube.'))
            cb()
        },

        // ===== Fetches
        async fetchTutorials () {
            if (this.loading.tutorials) return
            this.loading.tutorials = true
            try {
                const { data } = await axios.get('content_item_gos24/knowledgebase/pages/', {
                    params: { type_page: 1, tutorial_id: 0 }
                })
                this.tutorials = Array.isArray(data) ? data : []
            } catch (e) {
                // eslint-disable-next-line no-console
                console.log('fetchTutorials error', e)
            } finally {
                this.loading.tutorials = false
            }
        },
        async fetchSections () {
            if (!this.form.tutorial_id || this.loading.sections) return
            this.loading.sections = true
            try {
                const { data } = await axios.get('content_item_gos24/knowledgebase/pages/', {
                    params: { type_page: 2, tutorial_id: this.form.tutorial_id }
                })
                this.sections = Array.isArray(data) ? data : []
            } catch (e) {
                // eslint-disable-next-line no-console
                console.log('fetchSections error', e)
            } finally {
                this.loading.sections = false
            }
        }
    }
}
</script>


