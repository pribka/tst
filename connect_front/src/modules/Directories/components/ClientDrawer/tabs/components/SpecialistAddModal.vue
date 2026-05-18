<template>
    <a-modal
        :title="edit ? $t('directories.edit_specialist') : $t('directories.add_specialist')"
        destroyOnClose
        :width="600"
        :visible="visible"
        @cancel="visible = false"
        @afterVisibleChange="afterVisibleChange">
        <a-form-model
            ref="ruleForm"
            :model="form"
            class="mini_form"
            :rules="rules">
            <a-form-model-item prop="comment">
                <a-textarea 
                    v-model="form.comment" 
                    ref="commentInput"
                    inputType="ghost" 
                    :auto-size="{ minRows: 1, maxRows: 6 }"
                    :placeholder="$t('directories.enter_comment')" />
            </a-form-model-item>

            <a-form-model-item prop="user">
                <UserMiniSelect 
                    v-model="form.user"
                    inputType="input"
                    placement="bottomLeft"
                    :contractor="client.org_admin.id"
                    :placeholder="$t('directories.select_support_employee')" />
            </a-form-model-item>

            <a-form-model-item prop="start_date">
                <a-date-picker 
                    v-model="form.start_date"
                    inputType="ghost"
                    allowClear
                    class="w-full"
                    :placeholder="$t('directories.select_start_period')"
                    format="DD.MM.YYYY"
                    :getCalendarContainer="getPopupContainer"
                    iconPosition="left"
                    :disabledDate="disabledStartDate" />
            </a-form-model-item>

            <a-form-model-item prop="end_date">
                <a-date-picker 
                    v-model="form.end_date"
                    inputType="ghost"
                    allowClear
                    class="w-full"
                    :placeholder="$t('directories.select_end_period')"
                    format="DD.MM.YYYY"
                    :getCalendarContainer="getPopupContainer"
                    iconPosition="left"
                    :disabledDate="disabledEndDate" />
            </a-form-model-item>

            <a-form-model-item prop="duration_plan">
                <div class="number_input flex items-center">
                    <div class="number_input__icon mr-5">
                        <i class="fi fi-rr-clock" />
                    </div>
                    <a-input-number 
                        v-model="form.duration_plan" 
                        :min="1" 
                        :placeholder="$t('directories.enter_hours_plan')"
                        class="w-full" />
                </div>
            </a-form-model-item>

            <a-form-model-item prop="is_reserve">
                <a-checkbox v-model="form.is_reserve">
                    {{ $t('directories.is_reserve') }}
                </a-checkbox>
            </a-form-model-item>

            <a-form-model-item prop="accepts_calls">
                <div class="flex items-center justify-between mb-2">
                    <span class="cursor-pointer" @click="form.accepts_calls = !form.accepts_calls">
                        {{ $t('directories.accepts_calls') }}
                    </span>
                    <a-switch v-model="form.accepts_calls" />
                </div>
                <a-alert :message="$t('directories.accepts_calls_hint')" type="info" show-icon />
            </a-form-model-item>

            <div class="mb-3">{{ $t('directories.vacation_dates') }}</div>
            <div class="form_block">
                <a-form-model-item 
                    v-for="(vacation, index) in form.vacation_dates" 
                    :key="vacation.key" 
                    class="mb-0"
                    :prop="'vacation_dates.' + index + '.date'">
                    <div class="flex items-center">
                        <div class="mr-5">
                            <i class="fi fi-rr-calendar-day" />
                        </div>
                        <a-range-picker 
                            v-model="vacation.date" 
                            :locale="locale"
                            format="DD.MM.YYYY"
                            class="w-full"
                            :mask="{ mask: '00.00.0000', lazy: true, autofix: true }"
                            inputType="ghost" 
                            :allowClear="false"
                            :getCalendarContainer="getPopupContainer" />
                        <a-button 
                            v-if="form.vacation_dates.length > 1"
                            type="flat_danger" 
                            icon="fi-rr-trash"
                            flaticon
                            size="small"
                            class="ml-2"
                            shape="circle"
                            @click="vacationDelete(index)" />
                    </div>
                </a-form-model-item>
                <a-button type="link" size="small" flaticon icon="fi-rr-plus-small" class="ml-0 pl-0 mb-2" @click="vacationAdd()">
                    {{ $t('directories.add_more') }}
                </a-button>
            </div>
        </a-form-model>
        <template #footer>
            <div class="flex items-center gap-1 w-full">
                <a-button type="primary" size="large" :loading="loading" @click="onSubmit()">{{ edit ? $t('directories.save') : $t('directories.add') }}</a-button>
                <a-button type="ui_ghost" ghost size="large" @click="visible = false">
                    {{ $t("task.close") }}
                </a-button>
            </div>
        </template>
    </a-modal>
</template>

<script>
import eventBus from '@/utils/eventBus'
import locale from 'ant-design-vue/es/date-picker/locale/ru_RU'
import { errorHandler } from '@/utils/index.js'
export default {
    props: {
        client: {
            type: Object,
            required: true
        }
    },
    components: {
        UserMiniSelect: () => import('@apps/DrawerSelect/UserMiniSelect.vue')
    },
    data() {
        return {
            model: "models.CustomerSupportSpecialistModel", 
            pageName: `client_specialists_list_by_${this.client.id}`,
            mainModel: "help_desk.CustomerCardModel",
            mainPageName: "list_help_desk.CustomerCardModel",
            locale: {
                lang: {
                    ...locale.lang,
                    rangePlaceholder: [this.$t('directories.vacation_from'), this.$t('directories.vacation_to')]
                },
                timePickerLocale: locale.timePickerLocale
            },
            visible: false,
            edit: false,
            rules: {
                user: [{ required: true, message: this.$t("field_required"), trigger: "change" }]
            },
            loading: false,
            form: {
                user: null,
                is_reserve: false,
                accepts_calls: true,
                start_date: null,
                end_date: null,
                comment: "",
                duration_plan: null,
                vacation_dates: [
                    { key: Date.now(), date: [null, null] }
                ]
            }
        }
    },
    methods: {
        disabledStartDate(date) {
            if (!this.form.end_date) return false
            const end = this.$moment(this.form.end_date).endOf('day')
            return date && date.isAfter(end)
        },
        disabledEndDate(date) {
            if (!this.form.start_date) return false
            const start = this.$moment(this.form.start_date).startOf('day')
            return date && date.isBefore(start)
        },
        vacationDelete(index) {
            this.form.vacation_dates.splice(index, 1)
        },
        vacationAdd() {
            this.form.vacation_dates.push({
                key: Date.now(),
                date: [null, null]
            })
        },
        onSubmit() {
            this.$refs.ruleForm.validate(async valid => {
                if (!valid) return false
                try {
                    this.loading = true
                    const queryData = JSON.parse(JSON.stringify(this.form))
                    if (queryData.user?.id) queryData.user = queryData.user.id
                    if (queryData.start_date) queryData.start_date = this.$moment(queryData.start_date).format('YYYY-MM-DD')
                    if (queryData.end_date) queryData.end_date = this.$moment(queryData.end_date).format('YYYY-MM-DD')
                    if (queryData.vacation_dates?.length) {
                        queryData.vacation_dates = queryData.vacation_dates
                            .filter(f => f.date[0] && f.date[1])
                            .map(item => ({ start_date: this.$moment(item.date[0]).format('YYYY-MM-DD'), end_date: this.$moment(item.date[1]).format('YYYY-MM-DD') }))
                    }
                    if(this.edit) {
                        const { data } = await this.$http.put(`/help_desk/customer_cards/${this.client.id}/specialists/update/`, queryData)
                        if(data) {
                            this.$message.success(this.$t('directories.specialist_updated'))
                            eventBus.$emit(`update_filter_${this.model}_${this.pageName}`)
                            eventBus.$emit(`update_filter_${this.model}_${this.pageName}_aggregate`)
                            eventBus.$emit(`update_filter_${this.mainModel}_${this.mainPageName}`)
                            this.visible = false
                        }
                    } else {
                        const { data } = await this.$http.post(`/help_desk/customer_cards/${this.client.id}/specialists/add/`, [queryData])
                        if(data) {
                            this.$message.success(this.$t('directories.specialist_added'))
                            eventBus.$emit(`update_filter_${this.model}_${this.pageName}`)
                            eventBus.$emit(`update_filter_${this.model}_${this.pageName}_aggregate`)
                            eventBus.$emit(`update_filter_${this.mainModel}_${this.mainPageName}`)
                            this.visible = false
                        }
                    }
                } catch (error) {
                    errorHandler({error})
                } finally {
                    this.loading = false
                }
            })
        },
        getPopupContainer(trigger) {
            return trigger.parentNode
        },
        afterVisibleChange(vis) {
            if (vis) {
                this.$nextTick(() => {
                    if (this.$refs?.commentInput) this.$refs.commentInput.focus()
                })
            } else {
                this.edit = false
                this.form = {
                    user: null,
                    is_reserve: false,
                    accepts_calls: true,
                    start_date: null,
                    end_date: null,
                    comment: "",
                    duration_plan: null,
                    vacation_dates: [
                        { key: Date.now(), date: [null, null] }
                    ]
                }
            }
        }
    },
    mounted() {
        eventBus.$on('edit_specialist_modal', record => {
            this.edit = true
            this.visible = true
            const formData = JSON.parse(JSON.stringify(record))
            if(formData.user)
                formData.user = formData.user
            if(formData.is_reserve)
                formData.is_reserve = formData.is_reserve
            if(typeof formData.accepts_calls !== 'boolean')
                formData.accepts_calls = true
            if(formData.start_date)
                formData.start_date = this.$moment(formData.start_date)
            if(formData.end_date)
                formData.end_date = this.$moment(formData.end_date)
            if(formData.duration_plan === 0)
                formData.duration_plan = null
            if(formData.vacation_dates?.length) {
                formData.vacation_dates = formData.vacation_dates.map((item, index) => {
                    return {
                        key: Date.now() + '_' + index,
                        date: [this.$moment(item.start_date), this.$moment(item.end_date)]
                    }
                })
            } else {
                formData.vacation_dates = [
                    { key: Date.now(), date: [null, null] }
                ]
            }
            this.form = formData
        })
        eventBus.$on('add_specialist_modal', () => {
            this.visible = true
        })
    },
    beforeDestroy() {
        eventBus.$off('edit_specialist_modal')
        eventBus.$off('add_specialist_modal')
    }
}
</script>

<style lang="scss" scoped>
.form_block{
    background: #f7f9fc;
    padding: 5px 15px;
    border-radius: 8px;
}
.number_input{
    &::v-deep{
        .ant-input-number{
            border-color: transparent;
            box-shadow: initial!important;
        }
        .ant-input-number-handler-wrap{
            display: none;
        }
        .ant-input-number-input{
            padding: 0px;
            &::placeholder{
                color: #888888;
            }
        }
    }
}
</style>
