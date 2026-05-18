<template>
    <a-modal
        :visible="visible"
        :width="635"
        :title="modalTitle"
        destroyOnClose
        @afterVisibleChange="afterVisibleChange"
        @cancel="visible = false">
        <a-spin :spinning="detailLoading" class="w-full" size="small">
            <a-form-model ref="formRef" :model="form" :rules="rules">
                <div class="mt-2">
                    <a-form-model-item :label="$t('workplan.day_pulse_note_content_label')" prop="content" class="mb-3 text_block">
                        <component
                            v-if="ckEditor && editorGate"
                            :is="ckEditor"
                            initFocus
                            :value="form.content"
                            :key="`${visible}_${isEditMode}`"
                            @input="onContentInput"
                            @change="onContentInput"
                            :placeholder="$t('workplan.day_pulse_note_content_placeholder')" />
                    </a-form-model-item>
                    <a-form-model-item :label="$t('workplan.day_pulse_note_category_label')" prop="category" class="mb-3">
                        <div class="category_picker flex items-center gap-x-1 gap-y-1 flex-wrap">
                            <div
                                v-for="item in categories"
                                :key="item.code"
                                class="category_picker__item cursor-pointer select-none"
                                :class="{ active: item.code === form.category }"
                                :title="item.name"
                                @click="setCategory(item.code)">
                                <i class="fi" :class="item.icon" :style="{ color: item.hex_color || '#000000' }" />
                                <span>{{ item.name }}</span>
                            </div>
                        </div>
                    </a-form-model-item>
                    <a-form-model-item :label="$t('workplan.day_pulse_note_date_label')" prop="date">
                        <a-date-picker
                            v-model="form.date"
                            class="w-full"
                            size="large"
                            format="DD.MM.YYYY"
                            :allowClear="false"
                            :getCalendarContainer="getCalendarContainer" />
                    </a-form-model-item>
                </div>
            </a-form-model>
        </a-spin>

        <template #footer>
            <div class="w-full flex items-center justify-end gap-2">
                <a-button size="large" :block="isMobile" type="ui_ghost" @click="close">{{ $t('cancel') }}</a-button>
                <a-button type="primary" :block="isMobile" size="large" :loading="submitLoading || categoriesLoading || detailLoading" :disabled="categoriesLoading || detailLoading" @click="submit">{{ $t('workplan.day_pulse_note_save_btn') }}</a-button>
            </div>
        </template>
    </a-modal>
</template>

<script>
import { errorHandler } from '@/utils/index.js'
const list = 'dayPulseList'
export default {
    props: {
        value: {
            type: Boolean,
            default: false
        },
        editNote: {
            type: Object,
            default: null
        },
        selectedDate: {
            type: String,
            default: null
        },
        storeKey: {
            type: String,
            required: true
        }
    },
    data() {
        return {
            form: {
                date: null,
                content: '',
                category: null
            },
            editorGate: false,
            isEditMode: false,
            submitLoading: false,
            detailLoading: false
        }
    },
    computed: {
        visible: {
            get() {
                return this.value
            },
            set(val) {
                this.$emit('input', val)
            }
        },
        modalTitle() {
            return this.isEditMode
                ? this.$t('workplan.day_pulse_note_modal_title_edit')
                : this.$t('workplan.day_pulse_note_modal_title_create')
        },
        mainDate() {
            return this.$store.state.workplan.mainDate?.[this.storeKey] || []
        },
        isSingleDayRange() {
            const start = this.mainDate?.[0]
            const end = this.mainDate?.[1]
            if (!start || !end) return false
            return this.$moment(start).isSame(this.$moment(end), 'day')
        },
        ckEditor() {
            if (this.visible) return () => import('@apps/CKEditor')
            return null
        },
        categories() {
            return this.$store.state.workplan.dayPulseCategories?.results || []
        },
        categoriesLoading() {
            return this.$store.state.workplan.dayPulseCategories?.loading || false
        },
        isMobile() { 
            return this.$store.state.isMobile
        },
        rules() {
            return {
                category: [
                    {
                        required: true,
                        message: this.$t('field_required'),
                        trigger: ['change', 'blur']
                    }
                ],
                date: [
                    {
                        required: true,
                        message: this.$t('field_required'),
                        trigger: ['change', 'blur']
                    }
                ]
            }
        }
    },
    watch: {
        value: {
            immediate: true,
            handler(vis) {
                if(vis) {
                    this.setModeByProps()
                }
            }
        },
        editNote() {
            if(this.visible) {
                this.setModeByProps()
            }
        }
    },
    methods: {
        getPlainTextFromHtml(value) {
            const source = typeof value === 'string' ? value : ''
            return source
                .replace(/<[^>]*>/g, ' ')
                .replace(/&nbsp;/gi, ' ')
                .replace(/\s+/g, ' ')
                .trim()
        },
        resolveEditorValue(payload) {
            if (typeof payload === 'string')
                return payload
            if (payload && typeof payload === 'object') {
                if (typeof payload.value === 'string')
                    return payload.value
                if (typeof payload.html === 'string')
                    return payload.html
                if (typeof payload.data === 'string')
                    return payload.data
                if (typeof payload.target?.value === 'string')
                    return payload.target.value
            }
            return ''
        },
        onContentInput(payload) {
            const value = this.resolveEditorValue(payload)
            this.$set(this.form, 'content', value)
        },
        getDefaultCreateDate() {
            if (this.isSingleDayRange && this.mainDate?.[0]) {
                return this.$moment(this.mainDate[0])
            }
            if (this.selectedDate) {
                return this.$moment(this.selectedDate)
            }
            return this.$moment()
        },
        getItemKey(item) {
            if (!item || typeof item !== 'object') return null
            return item.id ?? item.pk ?? item.uuid ?? null
        },
        getCategoryCode(note) {
            if(!note) return null
            if(typeof note.category === 'string') return note.category
            if(note.category && typeof note.category === 'object') return note.category.code || null
            return note.category_code || null
        },
        async loadCategories(load = false) {
            try {
                if(load)
                    this.detailLoading = true
                const results = await this.$store.dispatch('workplan/getDayPulseCategories')
                if(!this.isEditMode && !this.form.category && results.length)
                    this.form.category = results[0].code
            } catch(error) {
                errorHandler({ error, show: false })
            } finally {
                if(load)
                    this.detailLoading = false
            }
        },
        setCategory(code) {
            this.form.category = code
        },
        async loadDetail() {
            if(!this.form.id) return
            this.detailLoading = true
            try {
                const { data } = await this.$http.get(`/day_summary/note/${this.form.id}/`)
                if(data) {
                    this.form.content = data.content || ''
                    this.form.category = this.getCategoryCode(data)
                    this.form.date = data.date ? this.$moment(data.date) : this.$moment()
                    await this.loadCategories()
                }
            } catch(error) {
                errorHandler({ error })
            } finally {
                this.detailLoading = false
            }
        },
        setModeByProps() {
            const key = this.getItemKey(this.editNote)
            this.isEditMode = key !== null && key !== undefined
            this.form.id = key
            this.form.content = ''
            this.form.category = null
            this.form.date = this.getDefaultCreateDate()
        },
        resetFormState() {
            this.form = {
                content: '',
                date: null,
                category: null
            }
            this.isEditMode = false
        },
        async afterVisibleChange(vis) {
            if (vis) {
                this.editorGate = false
                if (this.isEditMode)
                    await this.loadDetail()
                else {
                    await this.loadCategories(true)
                    this.form.date = this.getDefaultCreateDate()
                }
                await this.$nextTick()
                await new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve)))
                this.editorGate = true
            } else {
                this.editorGate = false
                this.resetFormState()
            }
        },
        getCalendarContainer(trigger) {
            return trigger.parentNode
        },
        close() {
            this.visible = false
        },
        async submit() {
            if (!this.getPlainTextFromHtml(this.form?.content)) {
                this.$message.error(this.$t('workplan.day_pulse_note_content_required'))
                return
            }
            this.$refs.formRef.validate(async valid => {
                if (!valid) return
                try {
                    this.submitLoading = true

                    const note = JSON.parse(JSON.stringify(this.form))
                    if(note.date)
                        note.date = this.$moment(note.date).format('YYYY-MM-DD')
                    if(this.isEditMode)
                        note.is_ai_summary = false

                    await this.$store.dispatch('workplan/saveDayPulseNote', {
                        storeKey: this.storeKey,
                        list,
                        note,
                        edit: this.isEditMode
                    })
                    this.$message.success(
                        this.isEditMode
                            ? this.$t('workplan.day_pulse_note_updated')
                            : this.$t('workplan.day_pulse_note_created')
                    )
                    this.close()
                } catch(error) {
                    errorHandler({ error })
                } finally {
                    this.submitLoading = false
                }
            })
        }
    },
}
</script>

<style scoped lang="scss">
.text_block::v-deep .ck-content.ck-editor__editable,
.text_block::v-deep .ck-content.ck-editor__editable_inline {
    min-height: 100px;
}
.category_picker{
    &__item{
        display: inline-flex;
        align-items: center;
        gap: 8px;
        min-height: 30px;
        padding: 3px 12px;
        border: 1px solid var(--borderColor);
        border-radius: 20px;
        color: #4a4a4a;
        transition: all 0.3s cubic-bezier(0.645, 0.045, 0.355, 1);
        span{
            font-size: 14px;
            line-height: 1;
            white-space: nowrap;
            text-transform: capitalize;
        }
        &:hover{
            background: #f5f7fb;
        }
        &.active{
            background: #e8ecfa;
            border-color: var(--borderColor);
            color: var(--blue);
        }
    }
}
</style>
