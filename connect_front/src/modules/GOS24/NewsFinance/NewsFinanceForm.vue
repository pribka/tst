<template>
    <a-form-model ref="formRef" class="task_form_wrap" :model="form" :rules="rules">
        <a-form-model-item label="Обложка" prop="image">
            <div class="flex items-center gap-3">
                <a-upload
                    :beforeUpload="beforeImageUpload"
                    :customRequest="uploadImage"
                    :showUploadList="false"
                    accept="image/png,image/jpeg,image/webp,image/gif">
                    <a-button icon="upload">Загрузить изображение</a-button>
                </a-upload>
                <a-button v-if="form.image" type="link" @click="form.image = ''">Удалить</a-button>
            </div>

            <div v-if="form.image" class="mt-3">
                <img :src="form.image" alt="cover" style="max-width:320px;max-height:200px;object-fit:cover;border-radius:6px;" />
            </div>
        </a-form-model-item>

        <!-- Заголовок: RU/KK -->
        <a-tabs size="large" animated>
            <a-tab-pane key="ru-title" tab="Заголовок (ru)">
                <a-form-model-item v-if="formInfo.title" :rules="formInfo.title.rules" :label="'Заголовок (ru)'" prop="title">
                    <a-input v-model="form.title" size="large" placeholder="Заголовок на русском" />
                </a-form-model-item>
            </a-tab-pane>
            <a-tab-pane key="kk-title" tab="Заголовок (kk)">
                <a-form-model-item v-if="formInfo.title" :label="'Заголовок (kk)'" prop="title_kk">
                    <a-input v-model="form.title_kk" size="large" placeholder="Тақырып (қазақша)" />
                </a-form-model-item>
            </a-tab-pane>
        </a-tabs>

        <div class="grid grid-cols-1 md:grid-cols-2 md:gap-4">
            <a-form-model-item v-if="formInfo.publication_date" :rules="rules.publication_date" :label="formInfo.publication_date.title" prop="publication_date">
                <DatePicker
                    v-model="form.publication_date"
                    size="large"
                    allowClear
                    :disabledAfter="disabledStartDateAfter"
                    :disabledBefore="disabledStartDateBefore"
                    :getCalendarContainer="getPopupContainer"
                    :disabled="isMilestone"
                    :show-time="{ format: 'HH:mm' }"
                    @change="dateStartChange"/>
            </a-form-model-item>

            <a-form-model-item v-if="formInfo.partition" label="Раздел" :rules="formInfo.partition.rules" prop="partition">
                <DrawerSelectPartition v-model="form.partition" />
            </a-form-model-item>
        </div>

        <a-form-model-item v-if="formInfo.tags" label="Теги" :rules="formInfo.tags.rules" prop="tags">
            <DrawerSelectTag v-model="form.tags" :multiple="true" />
        </a-form-model-item>

        <!-- Содержание: RU/KK -->
        <a-tabs size="large" animated>
            <a-tab-pane key="ru-body" tab="Содержание (ru)">
                <a-form-model-item v-if="formInfo.body" label="Содержание (ru)" :rules="formInfo.body.rules" prop="body">
                    <component
                        :showTextDecorations="true"
                        :uploadFieldKey="uploadFieldKey"
                        :uploadUrl="uploadUrl"
                        :is="ckEditor"
                        :taskId="form.id"
                        :key="'body-ru-' + `${form.id || 'new'}-${editorRev}`"
                        v-model="form.body"/>
                </a-form-model-item>
            </a-tab-pane>
            <a-tab-pane key="kk-body" tab="Содержание (kk)">
                <a-form-model-item v-if="formInfo.body" label="Содержание (kk)" prop="body_kk">
                    <component
                        :showTextDecorations="true"
                        :uploadFieldKey="uploadFieldKey"
                        :uploadUrl="uploadUrl"
                        :is="ckEditor"
                        :taskId="form.id"
                        :key="'body-kk-' + `${form.id || 'new'}-${editorRev}`"
                        v-model="form.body_kk"/>
                </a-form-model-item>
            </a-tab-pane>
        </a-tabs>

        <!-- Описание: RU/KK -->
        <a-tabs size="large" animated>
            <a-tab-pane key="ru-desc" :tab="`Описание (ru: ${descriptionLengthRu})`">
                <a-form-model-item v-if="formInfo.description" :label="`Описание (ru: ${descriptionLengthRu})`" :rules="formInfo.description.rules" prop="description">
                    <component
                        :showTextDecorations="true"
                        :uploadFieldKey="uploadFieldKey"
                        :uploadUrl="uploadUrl"
                        :is="ckEditor"
                        :taskId="form.id"
                        :key="'desc-ru-' + `${form.id || 'new'}-${editorRev}`"
                        v-model="form.description"
                        @input="syncRuDescription"/>
                </a-form-model-item>
            </a-tab-pane>
            <a-tab-pane key="kk-desc" :tab="`Описание (kk: ${descriptionLengthKk})`">
                <a-form-model-item v-if="formInfo.description" :label="`Описание (kk: ${descriptionLengthKk})`" prop="description_kk">
                    <component
                        :showTextDecorations="true"
                        :uploadFieldKey="uploadFieldKey"
                        :uploadUrl="uploadUrl"
                        :is="ckEditor"
                        :taskId="form.id"
                        :key="'desc-kk-' + `${form.id || 'new'}-${editorRev}`"
                        v-model="form.description_kk"/>
                </a-form-model-item>
            </a-tab-pane>
        </a-tabs>

        <a-form-model-item prop="anchor_links">
            <a-radio-group v-model="form.anchor_links">
                <a-radio :value="true">Показать якорную ссылку</a-radio>
                <a-radio :value="false">Скрыть якорную ссылку</a-radio>
            </a-radio-group>
        </a-form-model-item>
        <a-form-model-item prop="draft">
            <a-radio-group v-model="form.draft">
                <a-radio :value="false">Готово к публикации</a-radio>
                <a-radio :value="true">Черновик</a-radio>
            </a-radio-group>
        </a-form-model-item>

        <a-form-model-item prop="main_in_week">
            <a-checkbox v-model="form.main_in_week">Главное за неделю</a-checkbox>
        </a-form-model-item>

        <a-form-model-item prop="only_subscribed">
            <a-checkbox v-model="form.only_subscribed">По подписке</a-checkbox>
        </a-form-model-item>
    </a-form-model>
</template>

<script>
import moment from 'moment'
import mixins from '../mixins/mixins.js'

const formModel = () => ({
    id: null,
    title: '',
    description: '',
    body: '',
    // KK — переводные
    title_kk: '',
    description_kk: '',
    body_kk: '',
    kind: 'news_finance',
    publication_date: null,
    main_in_week: false,
    anchor_links: false,
    draft: false,
    only_subscribed: false,
    tags: [],
    partition: undefined,
    image: ''
})

function toBackendIsoWithOffset (m, offset) {
    if (!m || !moment.isMoment(m) || !m.isValid()) return null
    const mm = m.clone().utcOffset(offset, true)
    const base = mm.format('YYYY-MM-DD[T]HH:mm:ss.SSS')
    const z = mm.format('Z')
    return `${base}000${z}`
}

function plainLength (html) {
    if (!html) return 0
    let plainText = String(html).replace(/<[^>]+>/g, '')
    const textarea = document.createElement('textarea')
    textarea.innerHTML = plainText
    plainText = textarea.value
    return plainText.trim().length
}

export default {
    name: 'NewsForm',
    components: {
        DrawerSelectPartition: () => import('@apps/GOS24/components/DrawerSelectPartition.vue'),
        DatePicker: () => import('@apps/Datepicker'),
        DrawerSelectTag: () => import('@apps/GOS24/components/DrawerSelectTag.vue')
    },
    props: {
        visible: { type: Boolean, default: false },
        timezoneOffset: { type: String, default: '+03:00' }
    },
    mixins: [mixins],
    data () {
        return {
            form: formModel(),
            formInfo: {
                title: { rules: { required: true } },
                description: { rules: { required: true } },
                tags: { title: 'Теги', rules: { required: false } },
                body: { rules: { required: true } },
                publication_date: { title: 'Дата публикации', rules: { required: true } },
                partition: { title: 'Раздел', rules: { required: true } }
            },
            editorRev: 0,
        }
    },
    computed: {
        rules () {
            return {
                publication_date: [{ required: true, message: 'Укажите дату публикации', trigger: 'change' }],
                title: [{ required: true, message: 'Заполните название (ru)', trigger: 'blur' }],
                description: [{ required: true, message: 'Заполните описание (ru)', trigger: 'blur' }],
                body: [{ required: true, message: 'Введите содержание (ru)', trigger: 'change' }],
                partition: [{ required: true, message: 'Выберите раздел', trigger: 'change' }]
            }
        },
        ckEditor () { return this.visible ? () => import('@apps/CKEditor') : null },
        isMilestone () { return false },
        disabledStartDateBefore () { return null },
        disabledStartDateAfter () { return null },
        descriptionLengthRu () { return plainLength(this.form.description) },
        descriptionLengthKk () { return plainLength(this.form.description_kk) }
    },
    methods: {
        reset () {
            this.form = formModel()
            this.editorRev += 1
        },
        setData (item) {
            const m = item.publication_date ? moment(item.publication_date) : null
            this.form = {
                ...formModel(),
                id: item.id ?? null,
                // RU — откат на базовые поля, если *_ru нет
                title: item.title_ru ?? item.title ?? '',
                description: item.description_ru ?? item.description ?? '',
                body: item.body_ru ?? item.body ?? '',
                // KK
                title_kk: item.title_kk ?? '',
                description_kk: item.description_kk ?? '',
                body_kk: item.body_kk ?? '',
                publication_date: m ? m.utcOffset(this.timezoneOffset, true) : null,
                main_in_week: !!item.main_in_week,
                anchor_links: !!item.anchor_links,
                draft: !!item.draft,
                tags: item.tags || [],
                only_subscribed: !!item.only_subscribed,
                partition: item.partition,
                image: item.image || ''
            }
            if (typeof this.updateDescriptionCount === 'function') {
                this.updateDescriptionCount(this.form.description)
            }
            this.editorRev += 1
        },
        dateStartChange (v) {
            this.form.publication_date = (v && v._isAMomentObject) ? v : (v ? moment(v) : null)
        },
        getPopupContainer (trigger) {
            return (trigger && trigger.parentNode) ? trigger.parentNode : document.body
        },
        beforeImageUpload (file) {
            const okType = ['image/jpeg', 'image/png', 'image/webp', 'image/gif'].includes(file.type)
            if (!okType) this.$message.error('Поддерживаются JPG, PNG, WEBP, GIF')
            const okSize = file.size <= 5 * 1024 * 1024
            if (!okSize) this.$message.error('Файл до 5 МБ')
            return okType && okSize
        },
        async uploadImage({ file, onSuccess, onError, onProgress }) {
            try {
                const data = await this.$uploadFile({
                    file,
                    url: 'https://gos24.kz/api/v2/common/upload/',
                    fieldName: 'file',
                    fileName: file.name,
                    withCredentials: false,
                    onProgress
                })
                const url = data?.url || data?.default || data?.location || data?.path || ''
                if (!url)
                    throw new Error('Upload URL not found')
                this.form.image = url
                this.$message.success('Изображение загружено')
                onSuccess && onSuccess(data)
                
            } catch (e) {
                // eslint-disable-next-line no-console
                console.log('e', e)
                onError && onError(e)
            }
        },
        syncRuDescription (val) { this.form.description = val },
        submit () {
            return new Promise((resolve) => {
                this.$refs.formRef.validate((valid) => {
                    if (!valid) return resolve({ valid: false })
                    const isoDate = toBackendIsoWithOffset(this.form.publication_date, this.timezoneOffset)
                    const payload = {
                        title: this.form.title,
                        body: this.form.body,
                        description: this.form.description,
                        title_kk: this.form.title_kk,
                        body_kk: this.form.body_kk,
                        description_kk: this.form.description_kk,
                        publication_date: isoDate,
                        main_in_week: this.form.main_in_week,
                        anchor_links: this.form.anchor_links,
                        draft: this.form.draft,
                        only_subscribed: this.form.only_subscribed,
                        partition: this.form.partition ? this.form.partition.id : null,
                        tags: (this.form.tags || []).map((el) => el.id),
                        kind: 'news_finance',
                        image: this.form.image || null
                    }
                    resolve({ valid: true, id: this.form.id, payload })
                })
            })
        }
    }
}
</script>

<style scoped>
/* свои стили при необходимости */
</style>
