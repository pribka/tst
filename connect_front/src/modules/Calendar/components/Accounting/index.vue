<template>
    <div class="accounting_wrapper flex flex-col" :class="tableFullHeight && 'h-full'" ref="accountingRef">
        <div v-if="checkActions" class="mb-2 flex items-center gap-2">
            <a-button 
                flaticon
                icon="fi-rr-plus-small"
                :block="isMobile"
                :type="addBtnType"
                @click="visible = true">
                {{ $t('calendar.add') }}
            </a-button>
            <SettingsButton
                v-if="!isMobile"
                :pageName="pageName" />
        </div>

        <component 
            :is="isComponent" 
            :pageModel="pageModel"
            :pageName="pageName"
            :actions="actions"
            :editTime="editTime"
            :deleteHandler="deleteHandler"
            :getPopupContainer="getPopupContainer"
            :tableFullHeight="tableFullHeight"
            :minHeight="minHeight"
            :event="event" />

        <a-modal
            v-if="checkActions"
            :title="edit ? $t('calendar.edit') : $t('calendar.add')"
            destroyOnClose
            width="580px"
            :maskClosable="false"
            dialogClass="task-work-time-modal"
            :visible="visible"
            @afterVisibleChange="afterVisibleChange"
            @cancel="closeModal()">
            <a-form-model
                ref="workTimeForm"
                class="work_time_form"
                :model="form"
                :rules="rules">
                <a-form-model-item class="mb-2">
                    <div class="time_block">
                        <div class="time_block__label">{{ $t('task.time_spent_short') }}</div>
                        <div class="grid grid-cols-3 gap-2">
                            <div class="item_block">
                                <div class="item_block__label">
                                    {{ $t('task.hour') }}
                                </div>
                                <a-input-number v-model="form.duration_h" ref="firstInput" size="large" class="w-full" :min="0" :precision="0" :placeholder="$t('task.hour')" />
                            </div>
                            <div class="item_block">
                                <div class="item_block__label">
                                    {{ $t('task.minuts') }}
                                </div>
                                <a-input-number v-model="form.duration_m" size="large" class="w-full" :min="0" :max="59" :precision="0" :placeholder="$t('task.minuts')" />
                            </div>
                            <div class="item_block">
                                <div class="item_block__label">
                                    {{ $t('task.seconds') }}
                                </div>
                                <a-input-number v-model="form.duration_s" size="large" class="w-full" :min="0" :max="59" :precision="0" :placeholder="$t('task.seconds')" />
                            </div>
                        </div>
                    </div>
                </a-form-model-item>
                <a-form-model-item
                    class="mb-2"
                    prop="description">
                    <div class="textarea_wrapper">
                        <a-textarea
                            v-model="form.description"
                            ref="descriptionTextArea"
                            class="textarea_input"
                            :maxLength="descriptionMaxCount"
                            :placeholder="$t('calendar.desc')"
                            @input="adjustHeight" />
                        <div class="description_length">
                            {{form.description.length}}/{{ descriptionMaxCount }}
                        </div>
                    </div>
                </a-form-model-item>
                <a-form-model-item
                    v-if="!related_object && !edit"
                    :label="$t('calendar.related_task')"
                    class="mb-2"
                    :rules="{
                        required: true,
                        message: this.$t('field_required'), 
                        trigger: 'change' 
                    }"
                    prop="task">
                    <TaskSelectDrawer 
                        v-model="form.task" 
                        placeholder="Выбрать задачу"
                        :toogleTaskEdit="toogleTaskEdit" />
                </a-form-model-item>
                <a-form-model-item
                    v-if="!related_object && edit && form.task"
                    :label="$t('calendar.related_task')"
                    class="mb-2">
                    <span class="related_task_link" @click="openTask(form.task)">
                        #{{ form.task.counter }} {{ form.task.name }}
                    </span>
                </a-form-model-item>
                <a-form-model-item
                    :label="$t('calendar.date')"
                    class="mb-0"
                    :rules="{
                        required: true,
                        message: this.$t('field_required'), 
                        trigger: 'change' 
                    }"
                    prop="date">
                    <Datepicker 
                        v-model="form.date" 
                        size="large"
                        mask="00.00.0000"
                        :showTime="false"
                        dateFormat="DD.MM.YYYY"
                        :getCalendarContainer="trigger => trigger.parentNode" />
                </a-form-model-item>
            </a-form-model>
            <template #footer>
                <div class="flex items-center gap-2" :class="isMobile && 'w-full'">
                    <a-button 
                        type="primary" 
                        :loading="loading" 
                        :block="isMobile" 
                        @click="formSubmit()">
                        {{ edit ? $t('calendar.save') : $t('calendar.add') }}
                    </a-button>
                    <a-button 
                        :block="isMobile"
                        type="ui_ghost"
                        :disabled="loading"
                        @click="closeModal()">
                        {{ $t('close') }}
                    </a-button>
                </div>
            </template>
        </a-modal>
    </div>
</template>

<script>
import { errorHandler } from '@/utils/index.js'
import eventBus from "@/utils/eventBus"
export default {
    components: {
        Datepicker: () => import('@apps/Datepicker'),
        UniversalTable: () => import('@/components/TableWidgets/UniversalTable'),
        TaskSelectDrawer: () => import('@apps/DrawerSelect/TaskSelectDrawer'),
        SettingsButton: () => import('@/components/TableWidgets/SettingsButton'),
    },
    props: {
        event: {
            type: Object,
            required: true
        },
        actions: {
            type: Object,
            default: () => null
        },
        addBtnType: {
            type: String,
            default: 'flat_primary'
        },
        pageModel: {
            type: String,
            default: 'event_calendar.EventExecutionTimeModel'
        },
        tableFullHeight: {
            type: Boolean,
            default: false
        },
        minHeight: {
            type: Number,
            default: 300
        }
    },
    computed: {
        pageName() {
            return `event_calendar.EventExecutionTimeModel_${this.event.id}`
        },
        isMobile() { 
            return this.$store.state.isMobile
        },
        checkActions() {
            return this.actions?.create_accounting?.availability || false
        },
        related_object() {
            if(this.event.calendar?.calendar_group?.id === 'task' && this.event.calendar?.related_object?.id)
                return this.event.calendar.related_object.id
            if(this.event.related_object && this.event.related_object.type === 'tasks.TaskModel')
                return this.event.related_object.id
            return false
        },
        isComponent() {
            if(this.isMobile)
                return () => import('./List.vue')
            return () => import('./Table.vue')
        }
    },
    data() {
        return {
            descriptionMaxCount: 4000,
            visible: false,
            edit: false,
            loading: false,
            rules: {},
            taskEdit: false,
            form: {
                event_calendar: null,
                task: null,
                date: null,
                hours: 1,
                description: "",
                duration_h: null,
                duration_m: null,
                duration_s: null
            }
        }
    },
    methods: {
        getPopupContainer() {
            return this.$refs.accountingRef
        },
        toogleTaskEdit(value) {
            this.taskEdit = value
        },
        deleteHandler(item) {
            this.$emit('change', item)
        },
        async openTask(task) {
            if(!task?.id)
                return
            const query = Object.assign({}, this.$route.query, { task: task.id })
            if(this.$route.query.task !== task.id)
                this.$router.push({ query })
        },
        editTime(item) {
            this.edit = true
            const editData = {
                description: item.description,
                hours: Number(item.hours),
                date: item.date ? this.$moment(item.date) : null,
                task: item.task || null,
                id: item.id
            }
            const parts = this.secondsToHMS(item.duration)
            editData.duration_h = parts.h
            editData.duration_m = parts.m
            editData.duration_s = parts.s

            this.form = JSON.parse(JSON.stringify(editData))
            this.visible = true
        },
        hmsToSeconds(h, m, s) {
            const hh = Number(h || 0)
            const mm = Number(m || 0)
            const ss = Number(s || 0)
            return hh * 3600 + mm * 60 + ss
        },
        secondsToHMS(total) {
            const t = Number(total || 0)
            const h = Math.floor(t / 3600)
            const m = Math.floor((t % 3600) / 60)
            const s = t % 60
            return { h, m, s }
        },
        formSubmit() {
            this.$refs.workTimeForm.validate(async valid => {
                if (valid) {
                    try {
                        this.loading = true
                        const form = JSON.parse(JSON.stringify(this.form))
                        form.event_calendar = this.event.id
                        form.duration = this.hmsToSeconds(this.form.duration_h || 0, this.form.duration_m || 0, this.form.duration_s || 0)

                        if(!form.duration) {
                            this.$message.warning(this.$t('task.worktime_required'))
                            return;
                        }

                        delete form.hours
                        delete form.duration_h
                        delete form.duration_m
                        delete form.duration_s

                        if(form.date)
                            form.date = this.$moment(form.date).format('YYYY-MM-DD')
                        if(this.edit) {
                            if(form.task && typeof form.task === 'object')
                                form.task = form.task.id
                            const { data } = await this.$http.put(`/tasks/time_tracking/${form.id}/`, form)
                            if(data) {
                                this.$message.success(this.$t('calendar.item_updated'))
                                if (this.$store.hasModule('workplan')) {
                                    this.$store.dispatch('workplan/updateItem', {
                                        item: this.event,
                                        list: 'eventList'
                                    })
                                    if(form.task) {
                                        this.$store.dispatch('workplan/updateItem', {
                                            item: {id: form.task},
                                            list: 'taskList'
                                        })
                                    }
                                }
                                eventBus.$emit(`update_filter_${this.pageModel}_${this.pageName}`)
                                this.$emit('change', data)
                                this.closeModal()
                            }
                        } else {
                            if(this.related_object)
                                this.$set(form, 'task', this.related_object)
                            else {
                                if(form.task)
                                    this.$set(form, 'task', form.task.id)
                            }
                            const { data } = await this.$http.post('/tasks/time_tracking/', form) 
                            if(data) {
                                this.$message.success(this.$t('calendar.item_created'))
                                if (this.$store.hasModule('workplan')) {
                                    this.$store.dispatch('workplan/updateItem', {
                                        item: this.event,
                                        list: 'eventList'
                                    })
                                    if(form.task) {
                                        this.$store.dispatch('workplan/updateItem', {
                                            item: {id: form.task},
                                            list: 'taskList'
                                        })
                                    }
                                }
                                eventBus.$emit(`update_filter_${this.pageModel}_${this.pageName}`)
                                this.$emit('change', data)
                                this.closeModal()
                            }
                        }
                    } catch (error) {
                        errorHandler({error})
                    } finally {
                        this.loading = false
                    }
                } else {
                    this.$message.warning(this.$t('fill_required_fields'))
                    return false
                }
            })
        },
        adjustHeight(event) {
            const textarea = event.target;
            textarea.style.height = 'auto'
            const maxHeight = window.innerHeight - 100
            textarea.style.height = `${Math.min(textarea.scrollHeight, maxHeight)}px`
        },
        afterVisibleChange(vis) {
            if(vis) {
                if(!this.edit)
                    this.form.date = this.$moment()
                this.$nextTick(() => {
                    if(this.$refs.firstInput && !this.isMobile)
                        this.$refs.firstInput.focus()
                })
            } else {
                this.edit = false
                this.clearForm()
            }
        },
        clearForm() {
            this.form = {
                event_calendar: null,
                task: null,
                date: null,
                hours: 1,
                description: "",
                duration_h: null,
                duration_m: null,
                duration_s: null
            }
        },
        closeModal() {
            this.visible = false
        }
    }
}
</script>

<style lang="scss" scoped>
.time_block{
    background: #f7f9fc;
    border-radius: 12px;
    padding: 10px;
    @media (min-width: 768px) {
        padding: 15px;
    }
    &__label{
        margin-bottom: 10px;
        line-height: 16px;
    }
    .item_block{
        &__label{
            color: #888888;
            line-height: 16px;
            margin-bottom: 5px;
        }
    }
}
.textarea_wrapper{
    position: relative;
    .description_length{
        position: absolute;
        bottom: 10px;
        right: 10px;
        z-index: 5;
        color: #888;
        font-size: 13px;
        line-height: 13px;
    }
    .textarea_input{
        margin-bottom: 0px!important;
        padding-bottom: 25px;
    }
}
.related_task_link{
    display: block;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    color: var(--blue);
    cursor: pointer;
}
</style>
