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

        <a-form-model-item v-if="formInfo.lecturer" label="Лектор" :rules="formInfo.lecturer.rules" prop="lecturer">
            <DrawerSelectUser v-model="form.lecturer" />
        </a-form-model-item>
        <a-form-model-item v-if="formInfo.lecturer_full_name" :rules="formInfo.lecturer_full_name.rules" label="Лектор" prop="lecturer_full_name">
            <a-input v-model="form.lecturer_full_name" size="large" placeholder="Лектор" />
        </a-form-model-item>

        <div class="grid grid-cols-1 md:grid-cols-2 md:gap-4">
            <a-form-model-item v-if="formInfo.partition" label="Раздел" :rules="formInfo.partition.rules" prop="partition">
                <DrawerSelectPartition v-model="form.partition" />
            </a-form-model-item>

            <a-form-model-item v-if="formInfo.contentType" :label="formInfo.contentType.title" :rules="formInfo.contentType.rules" prop="contentType">
                <a-select v-model="form.contentType" size="large" :getPopupContainer="getPopupContainer" placeholder="Тип">
                    <a-select-option v-for="item in contentTypes" :key="item.id" :value="item.id">{{ item.title }}</a-select-option>
                </a-select>
            </a-form-model-item>
        </div>

        <a-form-model-item v-if="formInfo.tags" label="Теги" :rules="formInfo.tags.rules" prop="tags">
            <DrawerSelectTag v-model="form.tags" :multiple="true" />
        </a-form-model-item>

        <a-form-model-item v-if="formInfo.planned_date" :rules="formInfo.planned_date.rules" :label="formInfo.planned_date.title" prop="planned_date">
            <a-date-picker
                v-model="form.planned_date"
                :allowClear="false"
                size="large"
                placeholder="Выбрать дату"
                format="DD.MM.YYYY"
                valueFormat="YYYY-MM-DD"
                :getCalendarContainer="getPopupContainer"
                :locale="locale"
                class="w-full"
                :showToday="false"/>
        </a-form-model-item>

        <div class="grid grid-cols-1 md:grid-cols-2 md:gap-4">
            <a-form-model-item v-if="formInfo.start_live_time" :rules="formInfo.start_live_time.rules" :label="formInfo.start_live_time.title" prop="start_live_time">
                <a-time-picker v-model="form.start_live_time" :allowClear="false" format="HH:mm" valueFormat="HH:mm" :getPopupContainer="getPopupContainer" :minuteStep="5" size="large" class="time_picker w-full" placeholder="Время" />
            </a-form-model-item>

            <a-form-model-item v-if="formInfo.end_live_time" :rules="formInfo.end_live_time.rules" :label="formInfo.end_live_time.title" prop="end_live_time">
                <a-time-picker v-model="form.end_live_time" :allowClear="false" format="HH:mm" valueFormat="HH:mm" :getPopupContainer="getPopupContainer" :minuteStep="5" size="large" class="time_picker w-full" placeholder="Время" />
            </a-form-model-item>
        </div>

        <a-form-model-item v-if="formInfo.youtube_url" :rules="formInfo.youtube_url.rules" label="Ссылка (YouTube)" prop="youtube_url">
            <a-input v-model="form.youtube_url" size="large" placeholder="Ссылка (YouTube)" />
        </a-form-model-item>

        <a-form-model-item v-if="formInfo.broadcast" :rules="formInfo.broadcast.rules" label="Ссылка на трансляцию" prop="broadcast">
            <a-input v-model="form.broadcast" size="large" placeholder="Ссылка на трансляцию" />
        </a-form-model-item>

        <!-- Содержание: RU/KK -->
        <a-tabs size="large" animated>
            <a-tab-pane key="ru-body" tab="Содержание (ru)">
                <a-form-model-item v-if="formInfo.body" label="Содержание (ru)" :rules="formInfo.body.rules" prop="body">
                    <component :showTextDecorations="true" :uploadFieldKey="uploadFieldKey" :uploadUrl="uploadUrl" :is="ckEditor" v-model="form.body" :key="'body-ru-' + `${form.id || 'new'}-${editorRev}`" />
                </a-form-model-item>
            </a-tab-pane>

            <a-tab-pane key="kk-body" tab="Содержание (kk)">
                <a-form-model-item v-if="formInfo.body" label="Содержание (kk)" prop="body_kk">
                    <component :showTextDecorations="true" :uploadFieldKey="uploadFieldKey" :uploadUrl="uploadUrl" :is="ckEditor" v-model="form.body_kk" :key="'body-kk-' + `${form.id || 'new'}-${editorRev}`" />
                </a-form-model-item>
            </a-tab-pane>
        </a-tabs>

        <a-form-model-item prop="spend">
            <a-radio-group v-model="form.spend">
                <a-radio :value="true">Проведён</a-radio>
                <a-radio :value="false">Не проведён</a-radio>
            </a-radio-group>
        </a-form-model-item>

        <a-form-model-item prop="draft">
            <a-radio-group v-model="form.draft">
                <a-radio :value="false">Готово к публикации</a-radio>
                <a-radio :value="true">Черновик</a-radio>
            </a-radio-group>
        </a-form-model-item>

        <a-form-model-item prop="webinar_active">
            <a-radio-group v-model="form.webinar_active">
                <a-radio :value="false">Не активный</a-radio>
                <a-radio :value="true">Активный</a-radio>
            </a-radio-group>
        </a-form-model-item>

        <a-form-model-item prop="free">
            <a-checkbox v-model="form.free">Бесплатный</a-checkbox>
        </a-form-model-item>

    </a-form-model>
</template>

<script>
import locale from 'ant-design-vue/es/date-picker/locale/ru_RU'
import moment from 'moment'
import mixins from '@/modules/GOS24/mixins/mixins'

const formModel = () => ({
    // RU базовые
    title: '',
    body: '',

    // KK переводные
    title_kk: '',
    body_kk: '',

    youtube_url: '',
    broadcast: '',
    lecturer_full_name: '',
    lecturer: undefined,
    partition: undefined,
    contentType: undefined,
    tags: [],

    planned_date: null,       // 'YYYY-MM-DD'
    start_live_time: null,    // 'HH:mm'
    end_live_time: null,      // 'HH:mm'

    spend: false,
    draft: true,
    webinar_active: true,
    free: true
})

// длина текстовой версии (без HTML/сущностей)
function textLength (html) {
    if (!html) return 0
    const noTags = String(html).replace(/<[^>]+>/g, '')
    const ta = document.createElement('textarea')
    ta.innerHTML = noTags
    return ta.value.trim().length
}

export default {
    name: 'WebinarForm',
    components: {
        DrawerSelectPartition: () => import('@/modules/GOS24/components/DrawerSelectPartition.vue'),
        DrawerSelectUser: () => import('@apps/Directories/Team/components/Drawers/DrawerSelectUser.vue'),
        DrawerSelectTag: () => import('@apps/GOS24/components/DrawerSelectTag.vue')
    },
    props: { visible: { type: Boolean, default: false } },
    mixins: [mixins],
    data () {
        return {
            form: formModel(),
            locale,
            formInfo: {
                title: { rules: { required: true } },
                lecturer: { rules: { required: false } },
                lecturer_full_name: { rules: { required: false } },
                selectedSection: { title: 'Раздел', rules: { required: true } },
                contentType: { title: 'Тип', rules: { required: true } },
                planned_date: { title: 'Дата проведения', rules: { required: true } },
                start_live_time: { title: 'Время начала', rules: { required: true } },
                end_live_time: { title: 'Время окончания', rules: { required: false } },
                youtube_url: { rules: { required: false } },
                broadcast: { rules: { required: false } },
                body: { rules: { required: true } },
                partition: { title: 'Раздел', rules: { required: true } },
                tags: { title: 'Теги', rules: { required: true } }
            },
            contentTypes: [
                { id: 0, title: 'Вебинары' },
                { id: 1, title: 'Мастер-классы' },
                { id: 2, title: 'Курсы' }
            ],
            editorRev: 0,
        }
    },
    computed: {
        rules () {
            return {
                // Требуем только RU; KK — опционально
                title: [{ required: true, message: 'Заполните название (ru)', trigger: 'blur' }],
                lecturer: [{ required: false, message: 'Выберите лектора', trigger: 'change' }],
                lecturer_full_name: [{ required: false, message: 'Укажите ФИО лектора', trigger: 'change' }],
                partition: [{ required: true, message: 'Выберите раздел', trigger: 'change' }],
                contentType: [{ required: true, message: 'Выберите тип', trigger: 'change' }],
                planned_date: [{ required: true, message: 'Выберите дату проведения', trigger: 'change' }],
                start_live_time: [{ required: true, message: 'Укажите время начала', trigger: 'change' }],
                end_live_time: [{ required: false, message: 'Укажите время окончания', trigger: 'change' }],
                broadcast: [{ required: false, message: 'Заполните ссылку на трансляцию', trigger: 'blur' }],
                body: [{ required: true, message: 'Заполните содержание (ru)', trigger: 'blur' }],
                tags: [{ required: true, message: 'Выберите теги', trigger: 'change' }]
            }
        },
        ckEditor () { return this.visible ? () => import('@apps/CKEditor') : null }
    },
    methods: {
        reset () {
            this.form = formModel()
            this.editorRev += 1
        },

        setData (data) {
            const toHHmm = (v) => {
                if (!v) return null
                const m = moment(v)
                return m.isValid() ? m.format('HH:mm') : v
            }

            this.form = {
                ...formModel(),

                // RU: падаем назад на базовые поля, если *_ru нет
                title: data.title_ru ?? data.title ?? '',
                body: data.body_ru ?? data.body ?? '',

                // KK
                title_kk: data.title_kk ?? '',
                body_kk: data.body_kk ?? '',

                youtube_url: data.youtube_url || '',
                broadcast: data.broadcast || '',
                lecturer: data.lecturer,
                lecturer_full_name: data.lecturer_full_name,
                partition: data.partition,
                contentType: Number(data.content_type),
                tags: data.tags || [],

                planned_date: data.planned_date || null,
                start_live_time: toHHmm(data.start_live_time),
                end_live_time: toHHmm(data.end_live_time),

                spend: !!data.spend,
                draft: !!data.draft,
                webinar_active: !!data.webinar_active,
                free: !data.only_subscribed
            }
            this.editorRev += 1
        },

        getPopupContainer (trigger) {
            return (trigger && trigger.parentNode) ? trigger.parentNode : document.body
        },

        submit () {
            return new Promise((resolve) => {
                this.$refs.formRef.validate((valid) => {
                    if (!valid) return resolve({ valid: false })

                    const planned_date = this.form.planned_date
                        ? (moment.isMoment(this.form.planned_date) ? this.form.planned_date.format('YYYY-MM-DD') : this.form.planned_date)
                        : null

                    const toISODateTime = (dateStr, timeStr) => {
                        if (!dateStr || !timeStr) return null
                        return moment(`${dateStr} ${timeStr}`, 'YYYY-MM-DD HH:mm')
                            .seconds(0)
                            .milliseconds(0)
                            .toISOString()
                    }

                    const start_live_time = toISODateTime(planned_date, this.form.start_live_time)
                    const end_live_time = toISODateTime(planned_date, this.form.end_live_time)

                    const payload = {
                        kind: 'webinar',

                        // RU
                        title: this.form.title,
                        body: this.form.body,

                        // KK
                        title_kk: this.form.title_kk,
                        body_kk: this.form.body_kk,

                        youtube_url: this.form.youtube_url || null,
                        broadcast: this.form.broadcast || null,
                        lecturer_full_name: this.form.lecturer_full_name || null,
                        lecturer: this.form.lecturer && this.form.lecturer.id ? this.form.lecturer.id : null,
                        partition: this.form.partition && this.form.partition.id ? this.form.partition.id : null,
                        content_type: this.form.contentType,
                        tags: (this.form.tags || []).map(t => t.id),

                        planned_date,        // 'YYYY-MM-DD'
                        start_live_time,     // ISO datetime
                        end_live_time,       // ISO datetime

                        spend: !!this.form.spend,
                        draft: !!this.form.draft,
                        only_subscribed: !this.form.free,
                        webinar_active: !!this.form.webinar_active,

                        // можно положить и на фронте, но на бэке всё равно принудительно сбрасываем:
                        sent_gos: false
                    }

                    resolve({ valid: true, payload })
                })
            })
        }
    }
}
</script>
