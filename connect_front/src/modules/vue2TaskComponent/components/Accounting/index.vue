<template>
    <div class="accounting_wrapper flex flex-col" :class="tableFullHeight && 'h-full'" ref="accountingRef">
        <template v-if="pageConfig">
            <div v-if="actions && actions.create_accounting && actions.create_accounting.availability" class="mb-2 flex items-center gap-2">
                <a-button 
                    flaticon
                    icon="fi-rr-plus-small"
                    :type="addBtnType"
                    :block="isMobile"
                    @click="visible = true">
                    {{ $t('task.add') }}
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
                :excludeCol="excludeCol"
                :isModerator="isModerator"
                :task="task" />

            <a-modal
                v-if="checkActions && pageConfig"
                :title="$t('task.add')"
                :zIndex="9999999"
                destroyOnClose
                width="520px"
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
                    <a-form-model-item
                        v-if="pageConfig.form.measure_unit"
                        class="mb-0"
                        prop="measure_unit">
                        <div class="measure_unit_select">
                            <span class="mr-2">{{ $t('task.unit_measurement_short') }}:</span>
                            <a-select 
                                v-model="form.measure_unit"
                                :loading="edListLoading"
                                defaultActiveFirstOption
                                :getPopupContainer="trigger => trigger.parentNode"
                                @change="measureUnitChange">
                                <a-select-option 
                                    v-for="item in edList" 
                                    :key="item.id" 
                                    :value="item.code">
                                    {{ item.string_view }}
                                </a-select-option>
                            </a-select>
                        </div>
                    </a-form-model-item>
                    <a-form-model-item v-if="form.measure_unit === 'hours'" class="mb-2">
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
                    <template v-else>
                        <a-form-model-item
                            v-if="pageConfig.form.hours"
                            :label="$t('task.count')"
                            prop="hours">
                            <a-input-number 
                                v-model="form.hours" 
                                ref="firstInput"
                                :min="0.1"
                                :step="0.1"
                                class="w-full"
                                @pressEnter="formSubmit()"
                                size="large"
                                :max="99" />
                        </a-form-model-item>
                    </template>
                    <a-form-model-item
                        v-if="pageConfig.form.description"
                        class="mb-2"
                        prop="description">
                        <div class="textarea_wrapper">
                            <a-textarea
                                v-model="form.description"
                                ref="descriptionTextArea"
                                class="textarea_input"
                                :maxLength="descriptionMaxCount"
                                :placeholder="$t('task.work_desc')"
                                @input="adjustHeight" />
                            <div class="description_length">
                                {{form.description.length}}/{{ descriptionMaxCount }}
                            </div>
                        </div>
                    </a-form-model-item>
                    <div class="grid grid-cols-1 md:grid-cols-2 gap-2">
                        <a-form-model-item
                            v-if="pageConfig.form.date"
                            :label="$t('task.date')"
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
                        <a-form-model-item
                            v-if="pageConfig.form.work_type"
                            :label="$t('task.work_type')"
                            class="mb-0"
                            prop="work_type">
                            <a-select 
                                v-model="form.work_type"
                                :loading="typeListLoading"
                                defaultActiveFirstOption
                                :getPopupContainer="trigger => trigger.parentNode"
                                size="large">
                                <a-select-option 
                                    v-for="item in typeList" 
                                    :key="item.id" 
                                    :value="item.code">
                                    {{ item.string_view }}
                                </a-select-option>
                            </a-select>
                        </a-form-model-item>
                    </div>
                    <div v-if="isModerator">
                        <a-form-model-item
                            :label="$t('task.user')"
                            class="mb-0"
                            prop="user">
                            <UserMiniSelect 
                                :showSearch="false"
                                v-model="form.user" 
                                :showIcon="false"
                                size="large"
                                :placeholder="$t('task.user')"
                                :showRecent="false"
                                :apiUrl="`/tasks/task_members/?task=${task.id}`"
                                inputType="bordered_input" />
                        </a-form-model-item>
                    </div>
                </a-form-model>
                <template slot="footer">
                    <div class="footer">
                        <div class="add-cancel flex items-center gap-2">
                            <a-button
                                v-if="pageConfig.modalConfig.okButton"
                                :block="isMobile"
                                :size="pageConfig.modalConfig.okButton.size"
                                :type="pageConfig.modalConfig.okButton.type"
                                :loading="loading"
                                @click="formSubmit()">
                                {{ edit ? $t('task.save') : $t('task.add') }}
                            </a-button>
                            <a-button 
                                v-if="pageConfig.modalConfig.cancelButton"
                                :block="isMobile"
                                :size="pageConfig.modalConfig.cancelButton.size"
                                type="ui_ghost"
                                @click="closeModal()">
                                {{ pageConfig.modalConfig.cancelButton.text }}
                            </a-button>
                        </div>
                        <a-checkbox v-model="form.is_result" class="is-results">
                            {{ $t('task.is_results') }}
                        </a-checkbox>
                    </div>
                </template>
            </a-modal>
        </template>
        <div v-else class="flex justify-center">
            <a-spin size="small" />
        </div>
    </div>
</template>

<script>
import { errorHandler } from '@/utils/index.js'
import eventBus from "@/utils/eventBus"
import { mapState } from 'vuex'
export default {
    components: {
        Datepicker: () => import('@apps/Datepicker'),
        UserMiniSelect: () => import('@apps/DrawerSelect/UserMiniSelect.vue'),
        SettingsButton: () => import('@/components/TableWidgets/SettingsButton'),
    },
    props: {
        task: {
            type: Object,
            required: true
        },
        injectActions: {
            type: Object,
            default: () => null
        },
        addBtnType: {
            type: String,
            default: 'flat_primary'
        },
        pageModel: {
            type: String,
            default: 'tasks.TaskExecutionTimeModel'
        },
        tableFullHeight: {
            type: Boolean,
            default: false
        },
        minHeight: {
            type: Number,
            default: 300
        },
        taskType: {
            type: String,
            default: 'task'
        }
    },
    computed: {
        ...mapState({
            user: state => state.user.user,
        }),
        isComponent() {
            if(this.isMobile)
                return () => import('./List.vue')
            return () => import('./Table.vue')
        },
        pageName() {
            return `tasks.TaskExecutionTimeModel_${this.task.id}`
        },
        workTimeSettings() {
            return this.$store.state.task.workTimeSettings
        },
        pageConfig() {
            if(this.workTimeSettings?.[this.task.task_type])
                return this.workTimeSettings[this.task.task_type]
            else
                return null
        },
        isModerator() {
            return true //this.actions?.create_accounting?.edit_user || false
        },
        excludeCol() {
            return this.isModerator ? [] : ['user']
        },
        isMobile() { 
            return this.$store.state.isMobile
        },
        checkActions() {
            if(this.actions?.create_accounting?.availability || this.actions?.edit_accounting?.availability)
                return true
            return false
        },
        actions() {
            if(this.injectActions)
                return this.injectActions
            return this.task.actions || null 
        }
    },
    data() {
        return {
            descriptionMaxCount: 4000,
            visible: false,
            edit: false,
            loading: false,
            edListLoading: false,
            typeListLoading: false,
            edList: [],
            typeList: [],
            mainLoading: false,
            rules: {
                work_type: [
                    { 
                        required: true,
                        message: this.$t('field_required'), 
                        trigger: 'change' 
                    }
                ],
                hours: [
                    { 
                        required: true,
                        message: this.$t('field_required'), 
                        trigger: 'change',
                        type: 'number'
                    }
                ],
                description: [
                    { 
                        max: this.descriptionMaxCount,
                        message: this.$t('auth.required_sym', { sym: this.descriptionMaxCount }), 
                        trigger: 'change'
                    }
                ],
                measure_unit: [
                    { 
                        required: true,
                        message: this.$t('field_required'), 
                        trigger: 'change'
                    }
                ]
            },
            form: {
                task: this.task.id,
                work_type: null,
                description: '',
                date: null,
                hours: 1.0,
                measure_unit: this.pageConfig?.defaultValue?.measure_unit ? this.pageConfig.defaultValue.measure_unit : "hours",
                is_result: false,
                duration_h: null,
                duration_m: null,
                duration_s: null
            },
        }
    },
    created() {
        this.getSettings()
        if(this.isModerator) {
            this.$set(this.form, 'user', null)
        }
    },
    methods: {
        hmsToSeconds(h, m, s) {
            const hh = Number(h || 0)
            const mm = Number(m || 0)
            const ss = Number(s || 0)
            return hh * 3600 + mm * 60 + ss
        },
        getPopupContainer() {
            return this.$refs.accountingRef
        },
        measureUnitChange() {
            this.$nextTick(() => {
                if(this.$refs.firstInput)
                    this.$refs.firstInput.focus()
            })
            this.form.hours = 1.0
        },
        async getSettings() {
            try {
                this.mainLoading = true
                await this.$store.dispatch('task/getWorkTimeSettings', {
                    task_type: this.task.task_type
                })
            } catch(error) {
                errorHandler({error})
            } finally {
                this.mainLoading = false
            }
        },
        deleteHandler(item) {
            this.$emit('change', item)
        },
        secondsToHMS(total) {
            const t = Number(total || 0)
            const h = Math.floor(t / 3600)
            const m = Math.floor((t % 3600) / 60)
            const s = t % 60
            return { h, m, s }
        },
        editTime(item) {
            this.edit = true
            const editData = {
                work_type: item.work_type.code,
                description: item.description,
                hours: Number(item.hours),
                date: item.date ? this.$moment(item.date) : null,
                id: item.id,
                is_result: item.is_result,
                measure_unit: item.measure_unit?.code || "hours"
            }
            if(editData.measure_unit === 'hours') {
                const parts = this.secondsToHMS(item.duration)
                editData.duration_h = parts.h
                editData.duration_m = parts.m
                editData.duration_s = parts.s
            } else {
                editData.duration_h = null
                editData.duration_m = null
                editData.duration_s = null
            }
            this.form = JSON.parse(JSON.stringify(editData))
            if(this.isModerator) {
                if(item.user)
                    this.$set(this.form, 'user', item.user)
            }
            this.visible = true
        },
        formSubmit() {
            this.$refs.workTimeForm.validate(async valid => {
                if (valid) {
                    try {
                        this.loading = true
                        const form = JSON.parse(JSON.stringify(this.form))
                        const total = this.hmsToSeconds(this.form.duration_h || 0, this.form.duration_m || 0, this.form.duration_s || 0)

                        if(form.date)
                            form.date = this.$moment(form.date).format('YYYY-MM-DD')
                        if(form.user?.id)
                            form.user = form.user.id
                        if(form.measure_unit === 'hours') {
                            form.duration = total
                            delete form.hours
                            delete form.duration_h
                            delete form.duration_m
                            delete form.duration_s

                            if(!total) {
                                this.$message.warning(this.$t('task.worktime_required'))
                                return;
                            }
                        }

                        if(this.edit) {
                            const { data } = await this.$http.put(`/tasks/time_tracking/${this.form.id}/`, form)
                            if(data) {
                                if (this.$store.hasModule('workplan')) {
                                    this.$store.dispatch('workplan/updateItem', {
                                        item: this.task,
                                        list: 'taskList'
                                    })
                                }
                                this.$message.success(this.$t('task.item_updated'))
                                eventBus.$emit(`update_filter_${this.pageModel}_${this.pageName}`)
                                this.$emit('change', data)
                                this.closeModal()
                            }
                        } else {
                            const { data } = await this.$http.post('/tasks/time_tracking/', form) 
                            if(data) {
                                if (this.$store.hasModule('workplan')) {
                                    this.$store.dispatch('workplan/updateItem', {
                                        item: this.task,
                                        list: 'taskList'
                                    })
                                }
                                this.$message.success(this.$t('task.item_added'))
                                eventBus.$emit(`update_filter_${this.pageModel}_${this.pageName}`)
                                this.$emit('change', data)
                                this.closeModal()
                                if(data?.status) {
                                    const status = data.status
                                    this.$store.dispatch('task/updateStatus', {
                                        task: this.task, 
                                        status
                                    })
                                }
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
        async getTypeList() {
            try {
                this.typeListLoading = true
                const { data } = await this.$http.get('/app_info/select_list/', {
                    params: {
                        model: 'tasks.TaskWorkTypeModel',
                        filters: {
                            work_type_task_type__task_type_id: this.task?.task_type ? this.task.task_type : this.taskType
                        }
                    }
                })
                if(data?.selectList?.length) {
                    this.typeList = data.selectList
                }
            } catch(error) {
                errorHandler({error, show: false})
            } finally {
                this.typeListLoading = false
            }
        },
        async getEdList() {
            try {
                this.edListLoading = true
                const { data } = await this.$http.get('/app_info/select_list/', {
                    params: {
                        model: 'catalogs.MeasureUnitModel'
                    }
                })
                if(data?.selectList?.length) {
                    this.edList = data.selectList
                    if(!this.form.measure_unit && this.pageConfig?.defaultValue?.measure_unit) {
                        this.form.measure_unit = this.pageConfig.defaultValue.measure_unit
                    }
                }
            } catch(error) {
                errorHandler({error, show: false})
            } finally {
                this.edListLoading = false
            }
        },
        afterVisibleChange(vis) {
            if (vis) {
                const textarea = this.$refs['descriptionTextArea']?.$el;
                if (textarea) {
                    textarea.style.height = 'auto';
                    const maxHeight = window.innerHeight - 100;
                    textarea.style.height = `${Math.min(textarea.scrollHeight, maxHeight)}px`
                }
                if(!this.typeList?.length) {
                    this.getTypeList()
                    this.getEdList()
                }
                if(this.isModerator && this.user && !this.edit) {
                    const selectedUser = {
                        ...this.user,
                        full_name: `${this.user.last_name} ${this.user.first_name}`
                    }
                    this.$set(this.form, 'user', selectedUser)
                }

                if(!this.edit)
                    this.form.date = this.$moment()
                this.$nextTick(() => {
                    if(this.$refs.firstInput)
                        this.$refs.firstInput.focus()
                })
            } else {
                this.edit = false
            }
        },
        closeModal() {
            this.visible = false
            this.edit = false
            this.form = {
                task: this.task.id,
                work_type: null,
                description: '',
                is_result: false,
                date: null,
                hours: 1.0,
                duration_h: null,
                duration_m: null,
                duration_s: null,
                measure_unit: this.pageConfig?.defaultValue?.measure_unit ? this.pageConfig.defaultValue.measure_unit : "hours"
            }
        }
    }
}
</script>

<style lang="scss" scoped>
.measure_unit_select{
    display: flex;
    align-items: center;
    margin-bottom: 5px;
    &::v-deep{
        .ant-select{
            display: flex;
            width: auto;
            min-width: 200px;
            .ant-selectant-select-arrow{
                opacity: 0.6;
            }
            .ant-select-selection{
                height: auto;
                border: initial;
                background-color: initial;
                outline: none!important;
                box-shadow: none!important;
                .ant-select-selection__rendered{
                    margin-left: 0px;
                    line-height: initial;
                    .ant-select-selection-selected-value{
                        padding-right: 0px;
                        color: var(--blue);
                        border-bottom: 1px dashed;
                    }
                }
            }
        }
    }
}
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
</style>

<style lang="scss">
.table_wrapper{
    position: relative;
    overflow: hidden;
    display: flex;
    flex-direction: column;
}
.footer {
    width: 100%;
    display: grid;
    grid-template-columns: auto 1fr;
    grid-template-areas: 'addCancel is-results';
    align-items: center;
    @media (max-width: 450px) {
        grid-template-columns: 1fr;
        grid-template-areas: 'is-results' 'addCancel';
        row-gap: 1.5rem;
        .is-results {
            justify-self: start !important;
        }
    }
    .add-cancel {
        grid-area: addCancel;
    }
    .is-results {
        grid-area: is-results;
        justify-self: end;
    }
}
.task-work-time-modal {
    textarea.ant-input {
        min-height: 75px;
        max-height: calc(100vh - 465px);
    }
}
</style>