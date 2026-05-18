<template>
    <a-modal
        :visible="visible"
        :width="width"
        destroyOnClose
        wrapClassName="add-key-result-modal"
        @afterVisibleChange="afterVisibleChange"
        @cancel="onClose()">
        <template slot="title">
            <div class="modal-title">
                <a-form-model
                    ref="KRDescriptionForm"
                    class="description"
                    :model="form"
                    :rules="descriptionRules">
                    <a-form-model-item ref="description" prop="description" class="mb-0">
                        <a-input
                            v-model="form.description"
                            :disabled="loading"
                            ref="KRDescriptionInput"
                            class="w-full"
                            inputType="ghost"
                            :placeholder="$t('okr.nameOfKeyResult')"
                            size="large" />
                    </a-form-model-item>
                </a-form-model>
                <a-tag
                    v-if="showHelpLink"
                    color="#FFF8EB"
                    class="info-tag">
                    <div class="icon">
                        <i class="fi fi-rr-info"></i>
                    </div>
                    <div class="label">
                        {{ $t('okr.howItWorks') }}
                    </div>
                </a-tag>
            </div>
        </template>
        <a-spin :spinning="loading">
            <a-form-model
                :model="form"
                :rules="rules"
                ref="krForm"
                class="form">
                <a-form-model-item ref="operator" label="" prop="operator" class="mb-0">
                    <DSelect
                        v-model="form.operator"
                        size="default"
                        apiUrl="/contractor_permissions/app_sections/okr/members/"
                        :page_size="7"
                        :params="{
                            contractor: currentContractor.id,
                            first: inject?.operator?.id ?? currentUser.id
                        }"
                        class="w-full"
                        inputType="ghost"
                        showSearch
                        useSearchApi
                        searchKey="text"
                        :firstSelected="!edit"
                        oneSelect
                        showPlaceholder
                        infinity
                        labelKey="full_name"
                        :placeholder="$t('okr.selectAssignee')">
                        <template #prefixIcon>
                            <i class="fi fi-rr-user mr-3" v-tippy="{
                                inertia: true,
                                duration: [300, 200],
                                content: $t('okr.operator')
                            }" />
                        </template>
                    </DSelect>
                </a-form-model-item>
                <div class="form-field">
                    <div class="prefix mr-3">
                        <i class="fi fi-rr-ruler-combined" v-tippy="{
                            inertia: true,
                            duration: [300, 200],
                            content: $t('okr.metric')
                        }" />
                    </div>
                    <div class="field" >
                        <div class="metrics-select-wrapper" ref="metricsSelectWrapper">
                            <a-form-model-item ref="metrics" class="mb-0" prop="metrics" >
                                <a-select
                                    :placeholder="$t('okr.selectMetric')"
                                    size="default"
                                    :loading="loading"
                                    inputType="ghost"
                                    :disabled="loading"
                                    :getPopupContainer="getPopupContainer"
                                    dropdownMatchSelectWidth
                                    dropdownClassName="metrics-dropdown-menu"
                                    v-model="form.metrics"
                                    allow-clear
                                    :filter-option="false"
                                    showSearch
                                    @search="searchHandler"
                                    @change="onMetricChange">
                                    <a-select-option
                                        v-if="filteredMetrics.length === 0"
                                        class="add-metric"
                                        key="addMetric"
                                        value="addMetric">
                                        {{ `${$t('okr.createNewMetric')} "${search}"` }}
                                    </a-select-option>
                                    <a-select-option
                                        v-for="metric in filteredMetrics"
                                        :disabled="loading"
                                        :key="metric.id"
                                        :value="metric.id">
                                        <div class="metrics-option" v-tippy="{ content: metric.name, delay: [500, 0] }" >
                                            {{ metric.name }}
                                        </div>
                                    </a-select-option>
                                </a-select>
                            </a-form-model-item>
                        </div>
                    </div>
                    <div class="suffix">
                        <MetricsLibrary
                            ghost
                            @selectMetric="selectMetric" />
                    </div>
                </div>
                <div class="form-field">
                    <div class="prefix mr-3">
                        <i class="fi fi-rr-file-chart-line" v-tippy="{
                            inertia: true,
                            duration: [300, 200],
                            content: $t('okr.baseValue')
                        }" />
                    </div>
                    <div class="field">
                        <a-form-model-item ref="base" class="mb-0" prop="base">
                            <a-input-number
                                class="w-full"
                                :placeholder="$t('okr.baseValue')"
                                v-model="form.base" />
                        </a-form-model-item>
                    </div>
                    <div class="suffix">
                        <i class="fi fi-rr-pencil"></i>
                    </div>
                </div>
                <div class="form-field">
                    <div class="prefix mr-3">
                        <i class="fi fi-rr-file-chart-line" v-tippy="{
                            inertia: true,
                            duration: [300, 200],
                            content: $t('okr.planValue')
                        }" />
                    </div>
                    <div class="field">
                        <a-form-model-item ref="plan" class="mb-0" prop="plan">
                            <a-input-number
                                class="w-full"
                                :placeholder="$t('okr.planValue')"
                                v-model="form.plan" />
                        </a-form-model-item>
                    </div>
                    <div class="suffix">
                        <i class="fi fi-rr-pencil"></i>
                    </div>
                </div>
                <div class="form-field">
                    <div class="prefix mr-3">
                        <i class="fi fi-rr-file-chart-line" v-tippy="{
                            inertia: true,
                            duration: [300, 200],
                            content: $t('okr.factValue')
                        }" />
                    </div>
                    <div class="field">
                        <a-form-model-item ref="fact" class="mb-0" prop="fact">
                            <a-input-number
                                class="w-full"
                                :placeholder="$t('okr.factValue')"
                                v-model="form.fact" />
                        </a-form-model-item>
                    </div>
                    <div class="suffix">
                        <i class="fi fi-rr-pencil"></i>
                    </div>
                </div>
                <div class="form-field">
                    <div class="prefix mr-3">
                        <i class="fi fi-rr-calendar" v-tippy="{
                            inertia: true,
                            duration: [300, 200],
                            content: $t('okr.period')
                        }" />
                    </div>
                    <a-form-model-item class="mb-0 w-full" ref="period" prop="period">
                        <a-range-picker
                            class="w-full"
                            inputType="ghost"
                            :getCalendarContainer="trigger => trigger.parentElement"
                            :locale="locale"
                            :ranges="ranges"
                            v-model="form.period"
                            :placeholder="[$t('okr.startDate'), $t('okr.endDate')]"
                            :valueFormat="dateFormat"
                            format="DD.MM.YYYY">
                            <i slot="suffixIcon" class="fi fi-rr-calendar"></i>
                        </a-range-picker>
                    </a-form-model-item>
                </div>
            </a-form-model>
        </a-spin>
        <template #footer>
            <div class="w-full flex justify-between">
                <div class="flex gap-1 items-center">
                    <a-button type="primary" size="large" :loading="loading" @click="submit">
                        {{ saveButtonText }}
                    </a-button>
                    <a-button type="ui_ghost" ghost size="large" @click="onClose()">
                        {{ $t('okr.cancel') }}
                    </a-button>
                </div>
                <div v-if="inject">
                    <template v-if="inject?.actions?.delete">
                        <a-popconfirm
                            prefixCls="delete-kr-confirm ant-popover"
                            :title="$t('okr.deleteKeyResultConfirm')"
                            :ok-text="$t('okr.delete')"
                            :cancel-text="$t('okr.cancel')"
                            :getPopupContainer="trigger => trigger.parentElement"
                            placement="topRight"
                            @confirm="deleteKR">
                            <a-button
                                :disabled="!inject?.actions?.delete"
                                v-tippy="{ content: $t('okr.delete') }"
                                class="delete-button"
                                type="ui"
                                ghost
                                icon="fi-rr-trash"
                                flaticon />
                        </a-popconfirm>
                    </template>
                    <template v-else>
                        <a-button
                            disabled
                            v-tippy="{ content: $t('okr.delete') }"
                            class="delete-button"
                            type="ui"
                            ghost
                            icon="fi-rr-trash"
                            flaticon />
                    </template>
                </div>
            </div>
        </template>
    </a-modal>
</template>
<script>
import { mapState, mapMutations, mapActions } from 'vuex'
import DSelect from '@apps/DrawerSelect/Select.vue'
import MetricsLibrary from '@/modules/OKR/components/MetricsLibrary'
import locale from 'ant-design-vue/es/date-picker/locale/ru_RU'
import ranges from '@apps/OKR/mixins/ranges'

export default {
    name: 'AddKeyResult',
    components: {
        DSelect,
        MetricsLibrary
    },
    mixins: [
        ranges
    ],
    data() {
        return {
            form: {
                description: '',
                operator: undefined,
                metrics: undefined,
                base: 0,
                plan: 0,
                fact: 0,
                period: []
            },
            showFormError: false,
            dateFormat: 'YYYY-MM-DD',
            locale,
            loading: false,
            search: '',
            inject: undefined,
            edit: false,
            metricsInitOptionList: [],
            rules: {
                operator: [
                    { required: true, message: this.$t('okr.requiredField'), trigger: 'blur' },
                ],
                base: [
                    { required: true, message: this.$t('okr.requiredField'), trigger: 'blur' },
                ],
                plan: [
                    { required: true, message: this.$t('okr.requiredField'), trigger: 'blur' },
                ],
                fact: [
                    { required: true, message: this.$t('okr.requiredField'), trigger: 'blur' },
                ],
                period: [
                    { validator: this.validatePeriod, message: 'Не соответствует периоду цели', trigger: ['change', 'blur'] }
                ],
            },
            descriptionRules: {
                description: [
                    { required: true, message: this.$t('okr.requiredField'), trigger: 'blur' },
                ],
            },
        }
    },
    computed: {
        ...mapState({
            metrics: state => state.okr.metrics,
            objective: state => state.okr.objectiveDetail,
            visible: state => state.okr.addKeyResultModalVisible,
            currentContractor: state => state.user.user.current_contractor || null,
            currentUser: state => state.user.user || null,
        }),
        showHelpLink() {
            // Показать кода будет страница помощи на которую будет вести ссылка
            return false
        },
        saveButtonText() {
            return `${this.edit ? this.$t('okr.saveKeyResult') : this.$t('okr.addKeyResult')}`
        },
        windowWidth() {
            return this.$store.state.windowWidth
        },
        width() {
            return this.windowWidth < 750 ? '100%' : '677px'
        },
        refsCOMP() {
            return this.$refs.metricsDSelect
        },
        filteredMetrics() {
            return this.metrics.filter(metric =>
                metric.name.toLowerCase().includes(this.search.toLowerCase())
            )
        },
    },
    methods: {
        ...mapMutations({
            UNSHIFT_KEY_RESULT: 'okr/UNSHIFT_KEY_RESULT',
            UPDATE_KEY_RESULT: 'okr/UPDATE_KEY_RESULT',
            REMOVE_REY_RESULT_FROM_LIST: 'okr/REMOVE_REY_RESULT_FROM_LIST',
            SET_ADD_KEY_RESULT_MODAL_VISIBLE: 'okr/SET_ADD_KEY_RESULT_MODAL_VISIBLE'
        }),
        ...mapActions({
            addMetric: 'okr/addMetric'
        }),
        afterVisibleChange(vis) {
            if (vis) {
                this.$nextTick(() => {
                    this.$refs?.KRDescriptionInput.focus()
                })
            } else {
                this.$nextTick(() => {
                    this.resetForm()
                    this.inject = undefined
                    this.edit = false
                    this.metricsInitOptionList.splice(0)
                })
            }
        },
        getPopupContainer() {
            return this.$refs.metricsSelectWrapper
        },
        getCalendarContainer() {
            return this.$refs.KRRangePicker
        },
        onClose() {
            this.SET_ADD_KEY_RESULT_MODAL_VISIBLE(false)
        },
        searchHandler(value) {
            this.search = value
        },
        onMetricChange(value) {
            if (value === 'addMetric') {
                this.loading = true
                this.addMetric({ name: this.search, description: '' })
                    .then((newMetric) => {
                        this.form.metrics = newMetric.id
                        this.$message.success(`${this.$t('okr.newMetricAdded')} "${newMetric.name}"`)
                        this.search = ''
                    })
                    .catch(e => {
                        console.log(e)
                        this.$message.error(this.$t('okr.failedToCreateMetric'))
                    })
                    .finally(() => {
                        this.loading = false
                    })
            }
        },
        selectMetric(metricID) {
            this.form.metrics = metricID
        },
        validatePeriod (rule, value, callback) {
            if (!value.length)
                callback()

            const objStart = this.$moment(this.objective.date_start)
            const objEnd = this.$moment(this.objective.date_end)
            const krStart = this.$moment(value[0])
            const krEnd = this.$moment(value[1])

            if (objStart.isSameOrBefore(krStart) && krEnd.isSameOrBefore(objEnd)) {
                callback()
            } else {
                callback(new Error(this.$t('okr.invalidPeriod')))
            }
        },
        fillForm() {
            this.form.description = this.inject.description
            this.form.operator = this.inject.operator.id
            this.form.metrics = this.inject.metrics?.id ? this.inject.metrics.id : null
            this.form.base = this.inject.base
            this.form.plan = this.inject.plan
            this.form.fact = this.inject.fact
            this.form.period = (this.inject.date_start && this.inject.date_end) ? [this.inject.date_start, this.inject.date_end] : []
        },
        resetForm() {
            this.form = {
                description: '',
                operator: undefined,
                metrics: undefined,
                base: 0,
                plan: 0,
                fact: 0,
                period: []
            }
        },
        async deleteKR() {
            this.loading = true
            const payload = [{
                id: this.inject.id,
                is_active: false
            }]
            try {
                await this.$http.post('/table_actions/update_is_active/', payload)
                this.REMOVE_REY_RESULT_FROM_LIST(this.inject.id)
                this.$message.info(this.$t('okr.keyResultDeleted'))
                this.onClose()
            } catch(e) {
                console.log(e)
                this.$message.error(this.$t('okr.error'))
            } finally {
                this.loading = false
            }
        },
        submit() {
            this.$refs.krForm.validate(KRFormValid => {
                this.$refs.KRDescriptionForm.validate(async KRDescription => {
                    if (KRFormValid && KRDescription) {
                        this.loading = true
                        const payload = {
                            objective: this.objective.id,
                            description: this.form.description,
                            operator: this.form.operator,
                            metrics: this.form.metrics,
                            base: this.form.base,
                            plan: this.form.plan,
                            fact: this.form.fact,
                            date_start: null,
                            date_end: null
                        }
                        if (this.form.period.length === 2) {
                            payload.date_start = this.form.period[0],
                            payload.date_end = this.form.period[1]
                        }
                        try {
                            if (this.edit) {
                                const { data } = await this.$http.put(`/okr/key_results/${this.inject.id}/`, payload)
                                if (data) {
                                    this.UPDATE_KEY_RESULT(data)
                                    this.$message.success(this.$t('okr.keyResultUpdated'))
                                    this.onClose()
                                    this.$emit('reloadObjective')
                                }
                            } else {
                                const { data } = await this.$http.post('/okr/key_results/', payload)
                                if (data) {
                                    this.UNSHIFT_KEY_RESULT(data)
                                    this.$message.success(this.$t('okr.keyResultAdded'))
                                    this.onClose()
                                }
                            }
                        } catch(e) {
                            console.log(e)
                            this.$message.error(this.$t('okr.error'))
                        } finally {
                            this.loading = false
                        }
                    } else {
                        this.$message.error(this.$t('okr.checkFormFields'))
                    }
                })
            })
        }
    }
}
</script>
<style lang="scss" scoped>
.form-field {
    display: flex;
    align-items: center;
    .suffix {
        width: 36px;
        margin-left: 8px;
        text-align: center;
    }
    .field {
        flex: 1;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
        .metrics-select-wrapper {
            height: 32px;
            margin-left: 11px;
        }
    }
    &::v-deep {
        .ant-select {
            width: 100%;
        }
        .ant-input-number-handler-wrap {
            display: none;
        }
        .ant-input-number {
            border-color: #fff;
        }
    }
}
</style>
<style lang="scss">
.add-key-result-modal {
    .modal-title {
        display: flex;
        justify-content: space-between;
        gap: 8px;
        width: 100%;
        .title {
            font-weight: 600;
            font-style: SemiBold;
            font-size: 16px;
            line-height: 24px;
            color: #888888;
        }
        .info-tag {
            display: flex;
            gap: 8px;
            height: 28px;
            cursor: pointer;
            .icon {
                color: #FF9A01;
            }
            .label {
                color: #2D2D2D;
            }
        }
        .description {
            margin-bottom: 0;
            flex: 1;
        }
    }
    .delete-button {
        height: 32px;
        width: 32px;
        color: red;
    }
    .metrics-dropdown-menu {
        .add-metric {
            font-weight: 400;
            font-size: 14px;
            color: #1D65C0;
        }
    }
}
</style>