<template>
    <a-modal
        :width="677"
        @afterVisibleChange="afterVisibleChange"
        destroyOnClose
        :visible="visible"
        @cancel="visible = false">
        <template #title>
            <a-form-model
                v-if="!formLoading"
                ref="nameForm"
                :model="form"
                class="name_form"
                :rules="nameRules">
                <a-form-model-item 
                    ref="name" 
                    prop="name" 
                    class="mb-0 name_row">
                    <div class="flex items-center justify-between">
                        <a-input 
                            v-model="form.name"
                            ref="nameInput"
                            inputType="ghost"
                            :placeholder="$t('project.title_project')" 
                            size="large"
                            @pressEnter="onSubmit()" />
                        <HelpButton partCode="projects" class="ml-2" />
                    </div>
                </a-form-model-item>
            </a-form-model>
            <a-skeleton v-else active :paragraph="{rows: 0}" />
        </template>
        <a-form-model
            v-if="!formLoading"
            ref="ruleForm"
            :model="form"
            class="mini_form"
            :label-col="{ span: 7, style: { textAlign: 'left' } }"
            :wrapper-col="{ span: 17 }"
            :rules="rules">
            <a-form-model-item :wrapper-col="{ span: 24 }" ref="description" prop="description">
                <a-textarea
                    v-model="form.description"
                    :placeholder="$t('project.description')"
                    inputType="ghost"
                    :auto-size="{ minRows: 1, maxRows: 10 }" />
            </a-form-model-item>
            <a-form-model-item v-if="!edit" :label="$t('project.project_founder')" class="flex items-center h-9" ref="founder" prop="founder">
                <UserDrawer
                    :id="`${defaultUserSelectId}_founder`"
                    v-model="form.founder"
                    inputType="ghost"
                    class="w-full"
                    :title="$t('project.project_founder')" />
            </a-form-model-item>
            <a-form-model-item :label="$t('Organization')" ref="organization" prop="organization">
                <DSelect
                    v-model="form.organization"
                    apiUrl="/contractor_permissions/organizations/"
                    class="w-full"
                    oneSelect
                    size="default"
                    inputType="ghost"
                    :params="{ permission_type: 'create_workgroup' }"
                    showPlaceholder
                    labelKey="name"
                    :placeholder="$t('Organization')"
                    :listObject="false"
                    :default-active-first-option="false"
                    :filter-option="false"
                    :not-found-content="null"
                    @change="organizationChange" />
            </a-form-model-item>
            <a-form-model-item
                :label="$t('project.work_directions')"
                ref="work_directions"
                prop="work_directions">
                <WorkDirectionsSelect
                    v-model="form.work_directions"
                    :organization="form.organization" />
            </a-form-model-item>
            <a-form-model-item v-if="visible" class="h-9" :label="$t('sports.provide_address')" ref="location_point" prop="location_point">
                <component
                    v-if="AddressSelectAsync"
                    :is="AddressSelectAsync"
                    v-model="form.location_point"
                    inputType="ghost"
                    class="form_address_select"
                    :placeholder="$t('sports.provide_address')"
                    ref="addressSelect" />
            </a-form-model-item>
            <a-form-model-item class="flex items-center h-9 date_select" :label="$t('project.date_start_plan')" ref="date_start_plan" prop="date_start_plan">
                <a-date-picker
                    ref="startPicker"
                    class="w-full"
                    inputType="ghost"
                    iconPosition="left"
                    :show-time="true"
                    :placeholder="$t('project.date_start_plan')"
                    :showTime="{ defaultValue: $moment('09:00:00', 'HH:mm'), format: 'HH:mm' }"
                    @change="changeStartDate"
                    dropdownClassName="project_start"
                    :disabled-time="disabledDateTime"
                    :disabled-date="disabledDate"
                    :inputReadOnly="false" 
                    :getCalendarContainer="getCalendarContainer"
                    format="DD.MM.YYYY HH:mm"
                    v-model="form.date_start_plan"/>
            </a-form-model-item>

            <a-form-model-item class="flex items-center h-9 date_select" :label="$t('project.deadline_project')" ref="dead_line" prop="dead_line">
                <a-date-picker
                    ref="endPicker"
                    inputType="ghost"
                    iconPosition="left"
                    :placeholder="$t('project.deadline_project')"
                    :disabled="fromTemplate"
                    class="w-full"
                    :getCalendarContainer="getCalendarContainer"
                    :show-time="true"
                    :inputReadOnly="false" 
                    dropdownClassName="project_end"
                    :disabled-date="disabledDateFrom"
                    :showTime="{ defaultValue: $moment('18:00:00', 'HH:mm'), format: 'HH:mm' }"
                    :showToday="false"
                    format="DD.MM.YYYY HH:mm"
                    v-model="form.dead_line">
                    <template #renderExtraFooter>
                        <div class="dp-shortcuts mt-1" style="display:flex;flex-wrap:wrap;gap:6px;">
                            <a-button
                                v-for="item in quickShortcuts"
                                :key="item.key"
                                size="small"
                                type="ui"
                                :title="item.title"
                                :disabled="item.disabled"
                                @click="applyShortcut(item.key)">
                                {{ item.label }}
                            </a-button>
                        </div>
                    </template>
                </a-date-picker>
            </a-form-model-item>
            <div class="modal_divider"></div>
            <div class="flex items-center gap-2 flex-wrap">
                <Upload
                    objectType
                    croper
                    class="min-w-0"
                    v-model="form.workgroup_logo">
                    <template v-slot:button>
                        <div type="button" class="ant-btn ant-btn-flat flex items-center">
                            <div v-if="form.workgroup_logo && form.workgroup_logo.path" class="flex items-center gap-1">
                                <span>{{ $t("project.avatar_project") }}:</span>
                                <div>
                                    <a-avatar
                                        class="shrink-0"
                                        :size="20"
                                        :src="
                                            form.workgroup_logo && form.workgroup_logo.path
                                                ? form.workgroup_logo.path
                                                : null
                                        "
                                        :key="
                                            form.workgroup_logo && form.workgroup_logo.path
                                                ? form.workgroup_logo.path
                                                : null
                                        "
                                        flaticon
                                        icon="fi-rr-users-alt"/>
                                </div>
                            </div>
                            <div v-else class="flex items-center">
                                <i class="fi fi-rr-clip mr-2" />
                                {{ $t("project.avatar_project") }}
                            </div>
                        </div>
                    </template>
                </Upload>
                <TemplateSelect 
                    v-model="form.template"
                    @change="templateChange" />
                <div>
                    <a-popover
                        placement="bottomLeft"
                        trigger="click"
                        transitionName=""
                        v-model="budgetVisible"
                        :destroyTooltipOnHide="true"
                        @visibleChange="budgetVisibleChange"
                        overlayClassName="project_popover"
                        
                        :getPopupContainer="getCalendarContainer">
                        <a-button type="flat">
                            <div v-if="form.funds">
                                {{ $t('project.project_budget') }}: {{ form.funds }} {{ currentCurrency && currentCurrency.string_view }}
                            </div>
                            <div v-else class="flex items-center">
                                <i class="fi fi-rr-folder mr-2" />
                                {{ $t('project.project_budget') }}
                            </div>
                        </a-button>
                        <template #content>
                            <a-form-model-item
                                ref="funds"
                                class="mb-0"
                                :label-col="{ span: 24 }"
                                :wrapper-col="{ span: 24 }"
                                :label="$t('project.project_budget')"
                                prop="funds">
                                <div class="md:flex items-center mb-2">
                                    <a-input-number
                                        v-model="form.funds"
                                        class="w-full"
                                        ref="budgetInput"
                                        :placeholder="$t('project.project_budget')"
                                        size="large"/>
                                    <DSelect
                                        v-model="form.funds_currency"
                                        size="large"
                                        apiUrl="/app_info/filtered_select_list/"
                                        class="w-full mt-2 md:mt-0 md:ml-2 currency_select"
                                        oneSelect
                                        firstSelected
                                        defaultSelectCode="643"
                                        showSearch
                                        searchKey="text"
                                        valueKey="code"
                                        listObject="filteredSelectList"
                                        :params="{ model: 'catalogs.CurrencyModel' }"
                                        :default-active-first-option="false"
                                        :filter-option="false"
                                        :not-found-content="null"/>
                                </div>
                                <a-button type="primary" ghost block @click="budgetVisible = false">
                                    {{ $t('close') }}
                                </a-button>
                            </a-form-model-item>
                        </template>
                    </a-popover>
                </div>
                <UserDrawer
                    v-if="!edit"
                    :id="defaultUserSelectId"
                    v-model="form.members.profile_id"
                    :metadata="{ key: 'profile_id', value: form.metadata }"
                    :changeMetadata="changeMetadata"
                    multiple
                    buttonNew
                    :buttonText="$t('project.participants')"
                    buttonIcon="fi-rr-user-add"
                    :title="$t('project.participants')"/>
            </div>
        </a-form-model>
        <template v-else>
            <div class="mb-5">
                <a-skeleton active :paragraph="{ rows: 0 }" :title="{width: '100%'}" style="width: 70%;" /> 
            </div>
            <div class="flex items-center w-full gap-4 mb-6">
                <div style="width: 30%;">
                    <a-skeleton active :paragraph="{ rows: 0 }" :title="{width: '100%'}" style="width: 60%;" /> 
                </div>
                <div style="width: 70%;">
                    <a-skeleton active :paragraph="{ rows: 0 }" :title="{width: '100%'}" style="width: 70%;" /> 
                </div>
            </div>
            <div class="flex items-center w-full gap-4 mb-6">
                <div style="width: 30%;">
                    <a-skeleton active :paragraph="{ rows: 0 }" :title="{width: '100%'}" style="width: 70%;" /> 
                </div>
                <div style="width: 40%;">
                    <a-skeleton active :paragraph="{ rows: 0 }" :title="{width: '100%'}" style="width: 60%;" /> 
                </div>
            </div>
            <div class="flex items-center w-full gap-4 mb-6">
                <div style="width: 30%;">
                    <a-skeleton active :paragraph="{ rows: 0 }" :title="{width: '100%'}" style="width: 40%;" /> 
                </div>
                <div style="width: 70%;">
                    <a-skeleton active :paragraph="{ rows: 0 }" :title="{width: '100%'}" style="width: 60%;" /> 
                </div>
            </div>
            <div class="flex items-center w-full gap-4 mb-6">
                <div style="width: 30%;">
                    <a-skeleton active :paragraph="{ rows: 0 }" :title="{width: '100%'}" style="width: 80%;" /> 
                </div>
                <div style="width: 40%;">
                    <a-skeleton active :paragraph="{ rows: 0 }" :title="{width: '100%'}" style="width: 70%;" /> 
                </div>
            </div>
            <div class="modal_divider" />
            <div class="flex items-center gap-2 flex-wrap form_footer_btn mb-2">
                <a-skeleton active :paragraph="{ rows: 0 }" :title="{width: '100%'}" style="width: 100px;" /> 
                <a-skeleton active :paragraph="{ rows: 0 }" :title="{width: '100%'}" style="width: 100px;" /> 
                <a-skeleton active :paragraph="{ rows: 0 }" :title="{width: '100%'}" style="width: 100px;" /> 
                <a-skeleton active :paragraph="{ rows: 0 }" :title="{width: '100%'}" style="width: 100px;" /> 
            </div>
        </template>
        <template #footer>
            <div v-if="!formLoading" class="flex items-center justify-between w-full">
                <div class="flex gap-1 items-center">
                    <a-button type="primary" size="large" :loading="loading" @click="onSubmit()">
                        {{ submitButtonText }}
                    </a-button>
                    <a-button type="ui_ghost" ghost size="large" @click="visible = false">
                        {{ $t("project.close") }}
                    </a-button>
                </div>
                <!--<a-button type="ui_ghost" ghost size="large" @click="openFullForm()">
                    {{ $t('open_full_form') }}
                </a-button>-->
            </div>
            <a-skeleton v-else active :paragraph="{rows: 0}" />
        </template>
    </a-modal>
</template>

<script>
import eventBus from '@/utils/eventBus'
import { formModel } from './utils.js'
import createdMethods from "./mixins/createdMethods"
import { mapState } from 'vuex'
import { errorHandler } from '@/utils/index.js'
export default {
    mixins: [createdMethods],
    components: {
        DSelect: () => import('@apps/DrawerSelect/Select.vue'),
        TemplateSelect: () => import('./components/TemplateSelect.vue'),
        WorkDirectionsSelect: () => import('./components/WorkDirectionsSelect.vue'),
        Upload: () => import("@apps/Upload"),
        UserDrawer: () => import("@apps/DrawerSelect/index.vue"),
        HelpButton: () => import('@apps/Support/components/HelpButton.vue')
    },
    props: {
        pageName: {
            type: String,
            default: "page_list_projects.WorkgroupModel",
        },
        model: {
            type: String,
            default: "workgroups.WorkgroupModel",
        }
    },
    computed: {
        ...mapState({
            user: state => state.user.user
        }),
        submitButtonText() {
            return this.edit ? this.$t('project.update') : this.$t('project.add_project')
        },
        quickShortcuts() {
            const now = this.$moment()
            const items = [
                { key: 'end_week',  label: 'В конце недели',   make: () => now.clone().endOf('isoWeek') },
                { key: 'plus_week', label: 'Через неделю',     make: () => now.clone().add(1, 'week') },
                { key: 'end_month', label: 'В конце месяца',   make: () => now.clone().endOf('month') },
                { key: 'plus_month', label: 'Через месяц',    make: () => now.clone().add(1, 'month') },
            ]

            return items.map(it => {
                const m = this.applyDefaultTime(it.make())                // выставляем 18:00:00
                const title = this.tooltipFormat(m)                       // тултип с точной датой
                // дизейблим кнопку, если дата раньше стартовой (учитываем твой disabledDateFrom)
                const disabled = this.form.date_start_plan ? !!this.disabledDateFrom(m) : false
                return { ...it, moment: m, title, disabled }
            })
        },
        fromTemplate() {
            return this.form.use_template;
        },
        currentCurrency() {
            if(this.form.funds_currency) {
                const find = this.currencyList.find(f => f.code === this.form.funds_currency)
                return find || null
            }
            return null
        },
        rules() {
            return {
                founder: [
                    {
                        required: !this.edit,
                        message: this.$t("project.field_require"),
                        trigger: "change",
                    },
                ],
                organization: [
                    {
                        required: true,
                        message: this.$t("project.field_require"),
                        trigger: "blur",
                    },
                ],
                dead_line: [
                    {
                        required: !this.fromTemplate,
                        message: this.$t("project.field_require"),
                        trigger: "change",
                    },
                ],
                date_start_plan: [
                    {
                        required: this.fromTemplate,
                        message: this.$t("project.field_require"),
                        trigger: "change",
                    },
                ],
                template: [
                    {
                        required: this.fromTemplate,
                        message: this.$t("project.field_require"),
                        trigger: "blur",
                    },
                ]
            }
        }
    },
    data() {
        return {
            AddressSelectAsync: null,
            sLinks: [],
            listLinks: [],
            valueFormat: '',
            defaultUserSelectId: 'project',
            budgetVisible: false,
            dateFormat: 'DD.MM.YYYY HH:mm', 
            loading: false,
            formLoading: true,
            visible: false,
            edit: false,
            editProjectId: null,
            form: {...formModel},
            currencyList: [],
            nameRules: {
                name: [
                    { required: true, message: '', trigger: 'blur' }
                ]
            }
        }
    },
    methods: {
        applyShortcut(key) {
            const item = this.quickShortcuts.find(i => i.key === key)
            if (!item || item.disabled) return

            this.form.dead_line = item.moment
        },

        applyDefaultTime(baseMoment) {
            const m = this.$moment(baseMoment).clone()
            return m.hour(18).minute(0).second(0)
        },

        tooltipFormat(m) {
            return this.$moment(m).format('DD.MM.YYYY HH:mm')
        },
        changeMetadata({ key, value }) {
            this.$set(this.form.metadata, key, value);
        },
        organizationChange() {
            this.form.work_directions = []
        },
        budgetVisibleChange(vis) {
            if(vis) {
                this.$nextTick(() => {
                    requestAnimationFrame(() => {
                        const el = this.$refs.budgetInput
                        if (el) el.focus()
                    })
                })
            }
        },
        templateChange(value) {
            if(value) {
                this.form.use_template = true
            } else {
                this.form.use_template = false
            }
            this.form.dead_line = null
        },
        normalizeEditForm(res) {
            const formData = {
                ...JSON.parse(JSON.stringify(formModel)),
                ...res
            }

            if (!formData.members || typeof formData.members !== 'object') {
                formData.members = { profile_id: [] }
            }
            if (!Array.isArray(formData.members.profile_id)) {
                formData.members.profile_id = []
            }

            if (!formData.metadata || typeof formData.metadata !== 'object') {
                formData.metadata = { profile_id: [] }
            }
            if (!Array.isArray(formData.metadata.profile_id)) {
                formData.metadata.profile_id = []
            }

            if (formData?.founder?.member) {
                formData.founder = formData.founder.member
            }

            if (formData?.organization?.id) {
                formData.organization = formData.organization.id
            }
            if (formData?.funds_currency?.code) {
                formData.funds_currency = formData.funds_currency.code
            }
            if (Array.isArray(formData.work_directions)) {
                formData.work_directions = formData.work_directions.map(item => item?.id || item)
            }

            return formData
        },
        async getCurrency() {
            try {
                const { data } = await this.$http.get('/app_info/filtered_select_list/?model=catalogs.CurrencyModel', {
                    params: {
                        model: 'catalogs.CurrencyModel'
                    }
                })
                if(data?.filteredSelectList?.length) {
                    this.currencyList = data.filteredSelectList
                    if (!this.form.funds_currency) {
                        this.form.funds_currency = data.filteredSelectList[0].code
                    }
                }
            } catch(error) {
                errorHandler({error, show: false})
            }
        },
        getCalendarContainer(trigger) {
            return trigger.parentNode
        },
        disabledDateFrom(current) {
            if (this.form.date_start_plan) {
                if (
                    this.$moment(this.form.date_start_plan).isSame(
                        current.format(),
                        "day"
                    )
                ) {
                    return false;
                } else
                    return (
                        current &&
            current < this.$moment(this.form.date_start_plan).endOf("day")
                    );
            } else return null;
        },
        async loadAddressSelect() {
            const m = await import(/* webpackChunkName: "address-select", webpackPrefetch: false, webpackPreload: false */ '@apps/DrawerSelect/AddressSelect')
            this.AddressSelectAsync = m.default || m
        },
        async openCreateModal(payload = {}) {
            const organizationId = payload?.organization?.id || null

            if (this.visible) {
                this.clearForm()
            }

            this.edit = false
            this.editProjectId = null
            if (organizationId) {
                this.form.organization = organizationId
            }
            this.visible = true

            if (this.visible && this.$refs.ruleForm) {
                this.initializeModal()
            }
        },
        async openEditModal({ id } = {}) {
            if (!id) return

            if (this.visible) {
                this.clearForm()
            }

            this.edit = true
            this.editProjectId = id
            this.visible = true

            if (this.visible && this.$refs.ruleForm) {
                this.initializeModal()
            }
        },
        async initializeModal() {
            try {
                this.formLoading = true
                const [, editResponse] = await Promise.all([
                    this.getCurrency(),
                    this.edit && this.editProjectId ? this.getInfo(this.editProjectId) : Promise.resolve(),
                    this.AddressSelectAsync ? Promise.resolve() : this.loadAddressSelect()
                ])

                if (this.edit && editResponse) {
                    this.form = this.normalizeEditForm(editResponse)
                    this.initFormDefaults()
                    this.sLinks = Array.isArray(this.form.social_links)
                        ? this.form.social_links.map((item) => ({
                            content: item.social_link,
                            type: item.social_web_type.id,
                            key: Date.now() + Math.random()
                        }))
                        : []
                } else {
                    this.initFormDefaults()
                }

                await this.$nextTick()
                requestAnimationFrame(() => {
                    this.$refs?.nameInput?.focus?.()
                })
            } catch (error) {
                errorHandler({ error })
                this.visible = false
            } finally {
                this.formLoading = false
            }
        },
        afterVisibleChange(vis) {
            if (vis) {
                this.initializeModal()
            } else {
                this.formLoading = true
                this.clearForm()
            }
        },
        range(start, end) {
            const result = [];
            for (let i = start; i < end; i++) {
                result.push(i);
            }
            return result;
        },
        disabledDateTime() {
            if (this.form.dead_line) {
                return {
                    disabledHours: () =>
                        this.range(
                            this.$moment(this.form.dead_line)
                                .subtract({ hours: 1 })
                                .format("HH"),
                            24
                        ),
                };
            } else return null;
        },
        disabledDate(current) {
            if (this.form.dead_line)
                return (
                    current && current > this.$moment(this.form.dead_line).endOf("day")
                );
            else return null;
        },
        changeStartDate(date) {
            if (this.form.dead_line && this.$moment(this.form.dead_line).isSameOrBefore(date)) {
                this.form.date_start_plan = this.$moment(date).subtract({ hours: 1 });
            }
        },
        openFullForm() {
            const query = {...this.$route.query}
            if(!query.create_project) {
                query.create_project = true
                this.$router.push({query})
            }
            const injectForm = {...this.form}
            if(injectForm.template)
                injectForm.template = injectForm.template.id
            this.$store.commit('projects/SET_FORM_INJECT', injectForm)
            this.visible = false
        },
        initFormDefaults() {
            if (!this.user || this.edit) return

            if (!this.form.founder?.id) {
                this.form.founder = this.user
            }
        },
        clearForm() {
            this.sLinks = []
            this.listLinks = []
            this.edit = false
            this.editProjectId = null
            this.form = JSON.parse(JSON.stringify(formModel))
            this.form.members.profile_id = []
            this.form.metadata.profile_id = []
        },
        prepareCommonPayload(form) {
            const payload = {
                is_project: true,
                name: form.name,
                description: form.description,
                organization: form.organization,
                work_directions: Array.isArray(form.work_directions)
                    ? form.work_directions.map(item => item?.id || item)
                    : [],
                location_point: form.location_point,
                date_start_plan: form.date_start_plan,
                dead_line: form.dead_line,
                template: form.template,
                use_template: form.use_template,
                funds: typeof form.funds === 'number' ? form.funds : 0,
                funds_currency: form.funds_currency,
                social_links: form.social_links
            }

            if (!payload.funds) {
                delete payload.funds_currency
            }
            if (payload.template?.id) {
                payload.template = payload.template.id
            }
            if (!payload.template) {
                payload.template = ""
            }

            if (form.workgroup_logo?.id) {
                payload.workgroup_logo = form.workgroup_logo.id
            } else {
                payload.workgroup_logo = null
            }

            return payload
        },
        prepareCreatePayload(form) {
            const payload = this.prepareCommonPayload(form)

            if (form?.founder?.id) {
                payload.founder = form.founder.id
            } else {
                payload.founder = null
            }

            payload.members = {
                profile_id: form.members.profile_id?.length
                    ? form.members.profile_id
                        .map(item => item.id)
                        .filter(id => id !== this.user.id)
                    : []
            }

            return payload
        },
        prepareUpdatePayload(form) {
            return this.prepareCommonPayload(form)
        },
        onSubmit() {
            this.$refs.ruleForm.validate((valid) => {
                this.$refs.nameForm.validate(async valid2 => {
                    if (valid && valid2) {
                        try {
                            if(!this.form.name) {
                                this.$message.error(this.$t("project.fill_all_fields"))
                                return false
                            }

                            this.loading = true;
                            //await this.uploadSocLink();

                            const form = JSON.parse(JSON.stringify(this.form))
                            let res

                            if (this.edit && this.editProjectId) {
                                const payload = this.prepareUpdatePayload(form)
                                payload.name_ru = payload.name
                                res = await this.updateGroupS({ data: payload, id: this.editProjectId })
                                this.$message.success(this.$t("project.information_edited"))
                                eventBus.$emit('project_updated', res.id)
                            } else {
                                const payload = this.prepareCreatePayload(form)
                                res = await this.createGroupS(payload)

                                const openProject = () => {
                                    const query = {...this.$route.query}
                                    if(!query.viewProject) {
                                        query.viewProject = res.id;
                                        this.$router.push({ query });
                                    }
                                }

                                this.$message.info(
                                    this.$createElement("span", {}, [
                                    `${this.$t("project.project_created")}. `,
                                    this.$createElement(
                                        "span",
                                        {
                                            class: "link cursor-pointer blue_color",
                                            on: {
                                                click: () => {
                                                    openProject();
                                                },
                                            },
                                        },
                                        this.$t('project.open_project')
                                    ),
                                    ]),
                                    5
                                );
                            }

                            this.sLinks = [];
                            eventBus.$emit("update_list_project");
                            eventBus.$emit(`update_filter_${this.model}_${this.pageName}`)
                            this.visible = false
                        } catch (error) {
                            errorHandler({error})
                        } finally {
                            this.loading = false;
                        }
                    } else {
                        this.$message.error(this.$t("project.fill_all_fields"));
                        return false
                    }
                })
            });
        }
    },
    mounted() {
        eventBus.$on('add_proejct_modal', this.openCreateModal)
        eventBus.$on('edit_project_modal', this.openEditModal)
    },
    beforeDestroy() {
        eventBus.$off('add_proejct_modal', this.openCreateModal)
        eventBus.$off('edit_project_modal', this.openEditModal)
    }
}
</script>

<style lang="scss" scoped>
.form_address_select{
    &::v-deep{
        .address_select_ghost{
            height: 30px;
            .select_placeholder{
                .mr-5{
                    margin-right: 10px;
                }
            }
        }
    }
}
.date_select{
    &::v-deep{
        .ant-calendar-picker-ghost.ant-calendar-picker-icon-left .ant-calendar-picker-input{
            padding-left: 25px;
        }
    }
}
.name_form{
    margin-bottom: -15px;
}
.name_row{
    &::v-deep{
        .has-error{
            .ant-input.ant-input-ghost{
                color: #ff5d5d!important;
                &::placeholder{
                    color: #ff5d5d!important;
                }
            }
            .ant-form-explain{
                display: none;
            }
        }
    }
}
</style>
