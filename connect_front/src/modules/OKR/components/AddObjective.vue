<template>
    <a-modal
        :afterClose="afterClose"
        :visible="visible"
        :width="width"
        destroyOnClose
        wrapClassName="add-objective-modal"
        @cancel="onClose()">
        <template slot="title">
            <div class="modal-title">
                <a-form-model
                    ref="objectiveNameForm"
                    class="objective"
                    :model="form"
                    :rules="objectiveRules">
                    <a-form-model-item ref="objective" prop="objective" class="mb-0">
                        <div class="flex items-center justify-between">
                            <a-input 
                                v-model="form.objective"
                                :disabled="loading"
                                ref="objectiveNameInput"
                                class="w-full"
                                inputType="ghost"
                                :placeholder="$t('okr.newObjective')" 
                                size="large" />
                            <HelpButton partCode="okr" class="ml-2" />
                        </div>
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
                ref="objectiveForm"
                :model="form"
                :rules="rules"
                class="content">
                <div class="obj-organization">
                    <i class="fi fi-rr-sitemap" v-tippy="{
                        inertia: true,
                        duration: [300, 200],
                        content: $t('okr.organization')
                    }" />
                    <div v-if="currentContractor">{{ currentContractor.name }}</div>
                    <div v-else class='text-gray-300'>
                        {{ $t('okr.organizationNotSpecified') }}
                    </div>
                    
                </div>
                <a-form-model-item ref="department" label="" prop="department" class="mb-0">
                    <DSelect
                        v-model="form.department"
                        :initOptionList="departments"
                        allowClear
                        class="w-full"
                        oneSelect
                        infinity
                        size="default"
                        inputType="ghost"
                        :useOptionFlex="false"
                        useSearchApi
                        showPlaceholder
                        :placeholder="$t('okr.selectDepartment')"
                        searchKey="text"
                        labelKey="name"
                        :listObject="false"
                        :default-active-first-option="false"
                        :filter-option="false"
                        :not-found-content="null"
                        @change="onDepartmentChange">
                        <template #prefixIcon>
                            <i class="fi fi-rr-sitemap" v-tippy="{
                                inertia: true,
                                duration: [300, 200],
                                content: $t('okr.department')
                            }" />
                        </template>
                    </DSelect>
                </a-form-model-item>
                <a-form-model-item ref="value_efforts" label="" prop="value_efforts" class="mb-0">
                    <DSelect
                        v-model="form.value_efforts"
                        :initOptionList="valueEfforts"
                        useOptionsBadge
                        class="w-full"
                        oneSelect
                        infinity
                        size="default"
                        inputType="ghost"
                        allowClear
                        :useOptionFlex="false"
                        useSearchApi
                        showPlaceholder
                        :placeholder="$t('okr.selectPriority')"
                        searchKey="text"
                        labelKey="name"
                        valueKey="code"
                        :listObject="false"
                        :default-active-first-option="false"
                        :filter-option="false"
                        :not-found-content="null">
                        <template #prefixIcon>
                            <i class="fi fi-rr-rectangle-list" v-tippy="{
                                inertia: true,
                                duration: [300, 200],
                                content: $t('okr.priority')
                            }" />
                        </template>
                    </DSelect>
                </a-form-model-item>
                <a-form-model-item ref="notification" label="" prop="notification" class="mb-0">
                    <DSelect
                        v-model="form.notification"
                        :initOptionList="reminders"
                        useOptionsBadge
                        class="w-full"
                        oneSelect
                        infinity
                        size="default"
                        inputType="ghost"
                        allowClear
                        :useOptionFlex="false"
                        useSearchApi
                        showPlaceholder
                        :placeholder="$t('okr.setReminder')"
                        searchKey="text"
                        labelKey="name"
                        valueKey="code"
                        :listObject="false"
                        :default-active-first-option="false"
                        :filter-option="false"
                        :not-found-content="null">
                        <template #prefixIcon>
                            <i class="fi fi-rr-bell" v-tippy="{
                                inertia: true,
                                duration: [300, 200],
                                content: $t('okr.remind')
                            }" />
                        </template>
                    </DSelect>
                </a-form-model-item>
                <a-form-model-item ref="owner" label="" prop="owner" class="mb-0">
                    <DSelect
                        v-model="form.owner"
                        size="default"
                        apiUrl="/contractor_permissions/app_sections/okr/members/"
                        :page_size="7"
                        :params="{
                            contractor: currentContractor.id,
                            first: objectiveDetail?.owner?.id ?? currentUser.id
                        }"
                        class="w-full"
                        inputType="ghost"
                        showSearch
                        useSearchApi
                        searchKey="text"
                        :firstSelected="!isEdit"
                        oneSelect
                        showPlaceholder
                        infinity
                        labelKey="full_name"
                        :placeholder="$t('okr.selectAuthor')">
                        <template #prefixIcon>
                            <i class="fi fi-rr-user" v-tippy="{
                                inertia: true,
                                duration: [300, 200],
                                content: $t('okr.owner')
                            }" />
                        </template>
                    </DSelect>
                </a-form-model-item>
                <a-form-model-item ref="operator" label="" prop="operator" class="mb-0">
                    <DSelect
                        v-model="form.operator"
                        size="default"
                        apiUrl="/contractor_permissions/app_sections/okr/members/"
                        :page_size="7"
                        :params="{
                            contractor: currentContractor.id,
                            first: objectiveDetail?.operator?.id ?? currentUser.id
                        }"
                        class="w-full"
                        inputType="ghost"
                        showSearch
                        useSearchApi
                        searchKey="text"
                        :firstSelected="!isEdit"
                        oneSelect
                        showPlaceholder
                        infinity
                        labelKey="full_name"
                        :placeholder="$t('okr.selectAssignee')">
                        <template #prefixIcon>
                            <i class="fi fi-rr-user" v-tippy="{
                                inertia: true,
                                duration: [300, 200],
                                content: $t('okr.operator')
                            }" />
                        </template>
                    </DSelect>
                </a-form-model-item>
                <div class="form-row">
                    <i class="fi fi-rr-calendar"
                       v-tippy="{
                           inertia: true,
                           duration: [300, 200],
                           content: $t('okr.period')
                       }"></i>
                    <a-form-model-item ref="period" prop="period" class="form-item">
                        <a-range-picker
                            class="w-full"
                            inputType="ghost"
                            allowClear
                            :getCalendarContainer="trigger => trigger.parentElement"
                            :ranges="ranges"
                            :mask="{ mask: '00.00.0000', lazy: true, autofix: true }"
                            v-model="form.period"
                            :placeholder="[$t('okr.startDate'), $t('okr.endDate')]"
                            :valueFormat="dateFormat"
                            format="DD.MM.YYYY" />
                    </a-form-model-item>
                </div>
                <div class="form-row">
                    <i class="fi fi-rr-eye"
                       v-tippy="{
                           inertia: true,
                           duration: [300, 200],
                           content: $t('okr.privacy')
                       }"></i>
                    <a-form-model-item ref="is_public" prop="is_public" class="form-item">
                        <div class="public_picker">
                            <div 
                                v-for="(item, index) in publicOptions" 
                                :key="index" 
                                :class="item.value === form.is_public && 'active'"
                                class="public_picker__item cursor-pointer flex items-center justify-center text-base" 
                                @click="form.is_public = item.value">
                                {{ item.name }}
                            </div>
                        </div> 
                    </a-form-model-item>
                </div>
                <a-form-model-item v-if="form.is_public === 'withVisors'" ref="visors" label="" prop="visors" class="mb-0">
                    <UserDrawer
                        :id="form.id || ''"
                        :taskId="form.id ? form.id : null"
                        class="w-full"
                        v-model="form.visors"
                        :title="$t('okr.selectWatchers')"
                        :inputPlaceholder="$t('okr.selectWatchers')"
                        multiple
                        useIco
                        inputType="ghost"
                        :metadata="{ key: 'visors', value: form.metadata }"
                        :changeMetadata="changeMetadata" />
                </a-form-model-item>
            </a-form-model>
        </a-spin>
        <template #footer>
            <div class="footer">
                <div class="flex gap-1 items-center">
                    <a-button type="primary" size="large" :loading="loading" @click="save()">
                        {{ saveButtonText }}
                    </a-button>
                    <a-button type="ui_ghost" ghost size="large" @click="onClose()">
                        {{ $t('okr.cancel') }}
                    </a-button>
                </div>
                <div class="obj-delete">
                    <a-button
                        v-if="isEdit"
                        type="ui_ghost"
                        class="text_red"
                        ghost
                        flaticon
                        icon="fi-rr-trash"
                        @click="deleteHandler" />
                </div>
            </div>
        </template>
    </a-modal>
</template>
<script>
import { mapMutations, mapState, mapActions, mapGetters } from 'vuex'
import DeleteObjective from '@apps/OKR/mixins/DeleteObjective'
import eventBus from '@/utils/eventBus'
import ranges from '@apps/OKR/mixins/ranges'
import { errorHandler } from '@/utils/index.js'
export default {
    name: 'AddObjective',
    components: {
        DSelect: () => import('@apps/DrawerSelect/Select.vue'),
        UserDrawer: () => import('@apps/DrawerSelect/index.vue'),
        HelpButton: () => import('@apps/Support/components/HelpButton.vue')
    },
    mixins: [
        ranges,
        DeleteObjective
    ],
    data() {
        return {
            form: {
                department: undefined,
                is_public: 'isPublic',
                key_results: [],
                metadata: {
                    visors: []
                },
                notification: 'never',
                objective: undefined,
                operator: undefined, 
                organization: undefined,
                owner: undefined,
                parent: undefined,
                period: undefined,
                value_efforts: undefined,
                visors: [],
            },
            publicOptions: [
                {
                    name: this.$t('okr.visibleToAll'),
                    value: 'isPublic',
                },
                {
                    name: this.$t('okr.visibleToMe'),
                    value: 'onlyOwner',
                },
                {
                    name: this.$t('okr.addWatchers'),
                    value: 'withVisors',
                },
            ],
            rules: {
                owner: [
                    { required: true, message: this.$t('okr.requiredField'), trigger: 'change' },
                ],
                operator: [
                    { required: true, message: this.$t('okr.requiredField'), trigger: 'change' },
                ],
                period: [
                    { required: true, message: this.$t('okr.requiredField'), trigger: 'change' },
                ],
                is_public: [
                    { required: true, message: this.$t('okr.requiredField'), trigger: 'change' },
                ]
            },
            objectiveRules: {
                objective: [
                    { required: true, message: this.$t('okr.requiredField'), trigger: 'change' },
                ],
            },
            kr_form: {
                description: '',
                operator: null,
                metrics: undefined,
                base: null,
                plan: null,
                fact: null,
                period: []
            },
            dateFormat: 'YYYY-MM-DD',
            isEdit: false,
            pLoading: false,
            metricsLoading: false,
        }
    },
    watch: {
        'form.visors.length': {
            handler(newValue, oldValue) {
                if (newValue > 0) {
                    this.form.is_public = 'withVisors'
                }
                if (newValue === 0 && oldValue > newValue) {
                    this.form.is_public = undefined
                }
            }
        },
        'form.is_public': {
            handler(newValue, oldValue) {
                if (newValue !== 'withVisors') {
                    this.form.visors = []
                    this.changeMetadata({
                        key: 'visors',
                        value: [] 
                    })
                }
            }
        }
    },
    computed: {
        ...mapState({
            addMetricLoading: state => state.okr.addMetricLoading,
            currentContractor: state => state.user.user.current_contractor || null,
            currentUser: state => state.user.user || null,
            departments: state => state.okr.departments,
            metrics: state => state.okr.metrics,
            objectiveDetail: state => state.okr.objectiveDetail,
            reminders: state => state.okr.reminders,
            stakeholders: state => state.okr.stakeholders,
            stakeholdersLoading: state => state.okr.stakeholdersLoading,
            valueEfforts: state => state.okr.valueEfforts,
            visible: state => state.okr.addObjectiveModalVisible
        }),
        ...mapGetters({
            loading: 'okr/anyLoading'
            
        }),
        showHelpLink() {
            // Показать кода будет страница помощи на которую будет вести ссылка
            return false
        },
        windowWidth() {
            return this.$store.state.windowWidth
        },
        saveButtonText() {
            return this.isEdit ? this.$t('okr.save') : this.$t('okr.createObjective')
        },
        width() {
            return this.windowWidth < 750 ? '100%' : '677px'
        },
        isPrivacySelectDisabled() {
            return this.form.visors.length > 0
        }
    },
    mounted(){
        eventBus.$on('add_objective', () => {
            const promises = []
            if (!this.departments.length)
                promises.push(this.fetchDepartments())
            if (!this.valueEfforts.length)
                promises.push(this.fetchValueEfforts())
            if (!this.reminders.length)
                promises.push(this.fetchReminders())
            Promise.all(promises)
                .then(() => {
                    this.form.organization = this.currentContractor.id
                    this.SET_ADD_OBJECTIVE_MODAL_VISIBLE(true)
                    this.$nextTick(() => {
                        this.$refs?.objectiveNameInput.focus()
                    })
                })
        })
        eventBus.$on('edit_objective', async (objectiveID) => {
            await this.fetchValueEfforts()
            if (!this.reminders.length)
                this.fetchReminders()
            this.isEdit = true
            this.SET_OBJECTIVE_DETAIL_LOADING(true)
            this.fetchDetails(objectiveID)
                .then(() => {
                    this.fillForm()
                    this.SET_ADD_OBJECTIVE_MODAL_VISIBLE(true)
                    this.$nextTick(() => {
                        this.$refs?.objectiveNameInput.focus()
                    })
                })
                .catch((e) => {
                    this.$message.error(this.$t('okr.fetchDataFailed'))
                    console.log(e)
                })
                .finally(() => {
                    this.SET_OBJECTIVE_DETAIL_LOADING(false)
                })
        })
    },
    beforeDestroy(){
        eventBus.$off('add_objective')
        eventBus.$off('edit_objective')
    },
    methods: {
        ...mapMutations({
            REMOVE_OBJECTIVE: 'okr/REMOVE_OBJECTIVE',
            REMOVE_OBJECTIVE_DETAIL: 'okr/REMOVE_OBJECTIVE_DETAIL',
            SET_ADD_OBJECTIVE_MODAL_VISIBLE: 'okr/SET_ADD_OBJECTIVE_MODAL_VISIBLE',
            SET_LOADING: 'okr/SET_LOADING',
            SET_OBJECTIVE_DETAIL_LOADING: 'okr/SET_OBJECTIVE_DETAIL_LOADING'
        }),
        ...mapActions({
            fetchDepartments: 'okr/fetchDepartments',
            fetchDetails: 'okr/fetchObjectiveDetail',
            fetchReminders: 'okr/fetchReminders',
            fetchStakeholders: 'okr/fetchStakeholders',
            fetchValueEfforts: 'okr/fetchValueEfforts'
        }),
        deleteHandler() {
            if (!this.isEdit || !this.objectiveDetail.id)
                return
            this.deleteObjective(this.objectiveDetail.id)
                .then(async () => {
                    this.REMOVE_OBJECTIVE(this.objectiveDetail)
                    this.onClose()
                })
        },
        changeMetadata({ key, value }) {
            this.$set(this.form.metadata, key, value)
        },
        onDepartmentChange(val, option) {
            if (!val) {
                this.form.parent = undefined
            }
        },
        afterClose() {
            this.resetForm()
            this.REMOVE_OBJECTIVE_DETAIL()
            this.isEdit = false
        },
        fillForm() {
            this.form.department = this.objectiveDetail?.department?.id || null
            this.form.key_results = this.objectiveDetail.key_results || []
            this.form.objective = this.objectiveDetail.objective
            this.form.operator = this.objectiveDetail.operator.id || null
            this.form.organization = this.objectiveDetail.organization.id
            this.form.owner = this.objectiveDetail.owner.id || null
            this.form.parent = this.objectiveDetail?.parent?.id || null
            this.form.notification = this.objectiveDetail?.notification?.code || null
            this.form.period = [
                this.$moment(this.objectiveDetail.date_start).format('YYYY-MM-DD'),
                this.$moment(this.objectiveDetail.date_end).format('YYYY-MM-DD')
            ]
            this.form.value_efforts = this.objectiveDetail?.value_efforts?.code || null
            this.form.visors = this.objectiveDetail.visors
            this.form.metadata = this.objectiveDetail.metadata
            this.form.is_public = String(this.objectiveDetail.is_public)
            if (this.objectiveDetail.is_public) {
                this.form.is_public = 'isPublic'
            } else if (this.form.visors.length) {
                this.form.is_public = 'withVisors'
            } else {
                this.form.is_public = 'onlyOwner'
            }
            this.form.key_results.forEach(kr => {
                if (kr?.operator?.id) {
                    kr.operator = kr.operator.id
                }
                if (kr?.metrics?.id) {
                    kr.metrics = kr.metrics.id
                }
                kr.period = this.$set(kr, 'period', [kr.date_start, kr.date_end])
                delete kr.date_start
                delete kr.date_end
                kr.base = Number(kr.base)
                kr.plan = Number(kr.plan)
                kr.fact = Number(kr.fact)
            })          
        },
        resetForm() {
            this.form = {
                department: undefined,
                is_public: 'isPublic',
                key_results: [],
                metadata: {
                    visors: []
                },
                notification: 'never',
                objective: undefined,
                operator: undefined, 
                organization: undefined,
                owner: undefined,
                parent: undefined,
                period: undefined,
                value_efforts: undefined,
                visors: []
            }
        },
        onClose() {
            this.SET_ADD_OBJECTIVE_MODAL_VISIBLE(false)
        },
        itemDelete(index) {
            this.form.key_results.splice(index, 1)
        },
        addKeyResult() {
            const newKR = JSON.parse(JSON.stringify(this.kr_form))
            if (this.stakeholders.length) {
                newKR.operator = this.form.operator ? this.form.operator : this.stakeholders[0].id
            }
            if (this.form.period) {
                newKR.period = this.form.period
            }
            this.form.key_results.push(newKR)
        },
        async saveObjective() {
            this.SET_LOADING(true)
            const payload = JSON.parse(JSON.stringify(this.form))
            payload.date_start = this.form.period[0]
            payload.date_end = this.form.period[1]
            delete payload.period
            payload.key_results.forEach(each => {
                each.date_start = each.period[0]
                each.date_end = each.period[1]
                delete each.period
            })
            payload.visors = payload.visors.map(visor => visor.id)
            payload.is_public = String(payload.is_public === 'isPublic')
            try {
                if (this.isEdit) {
                    await this.$http.put(`okr/objectives/${this.objectiveDetail.id}/`, payload)
                    let query = Object.assign({}, this.$route.query)
                    if(!!query.objective && query.objective === this.objectiveDetail.id) {
                        eventBus.$emit('reload_objective_details')
                    }
                } else {
                    await this.$http.post('okr/objectives/', payload)
                }
                this.SET_ADD_OBJECTIVE_MODAL_VISIBLE(false)
                this.$message.success(`${this.isEdit ? this.$t('okr.objectiveUpdated') : this.$t('okr.objectiveCreated')}`)
                eventBus.$emit('reload_okr_dashboard')
            }
            catch(error){
                errorHandler({error})
            }
            finally{
                this.SET_LOADING(false)
            }
        },
        scrollToError() {
            const el = document.getElementsByClassName('has-error')[0]
            if (el) el.scrollIntoView({ behavior: "smooth" })
        },
        validatePeriod (rule, value, callback) {
            const objStart = this.$moment(this.form.period[0])
            const objEnd = this.$moment(this.form.period[1])
            const krStart = this.$moment(value[0])
            const krEnd = this.$moment(value[1])

            if (objStart.isSameOrBefore(krStart) && krEnd.isSameOrBefore(objEnd)) {
                callback()
            } else {
                callback(new Error(this.$t('okr.invalidPeriod')))
            }
        },
        save() {
            this.$refs.objectiveForm.validate(formValid => {
                this.$refs.objectiveNameForm.validate(async objectiveNameValid => {
                    if (formValid && objectiveNameValid) {
                        this.saveObjective()
                    } else {
                        this.$nextTick(() => {
                            this.scrollToError()
                        })
                        this.$message.warning(this.$t('okr.checkFormFields'))
                        return
                    }
                })
            })
        }
    },
}
</script>

<style lang="scss">
.add-objective-modal {
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
    .content {
        display: flex;
        flex-direction: column;
        gap: 8px;
        .obj-organization {
            width: 100%;
            display: flex;
            align-items: center;
            gap: 0.75rem;
            color: #2D2D2D;
        }
    }
    .objective {
        margin-bottom: 0;
        flex: 1;
    }
    .form-row {
        display: flex;
        gap: 0.75rem;
        align-items: center;
        .form-item {
            flex: 1;
            margin-bottom: 0;
        }
    }
    .public_picker{
        display: flex;
        align-items: center;
        gap: 10px;
        &__item{
            transition: all 0.3s cubic-bezier(0.645, 0.045, 0.355, 1);
            border-radius: 8px;
            padding: 4px 8px;
            color: #2D2D2D;
            &:hover{
                background: #E8EDFA;
                color: #4777FF;
            }
            &.active{
                background: #E8EDFA;
                color: #4777FF;
            }
        }
    }
    .footer {
        width: 100%;
        display: flex;
        justify-content: space-between;
        .obj-delete {
            &::v-deep{
                .ant-btn{
                    width: 36px;
                    height: 36px;
                    border: 0px;
                    box-shadow: initial;
                }
            }
        }
    }
}
</style>