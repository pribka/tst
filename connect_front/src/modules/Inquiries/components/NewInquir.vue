<template>
    <DrawerTemplate
        v-model="visible"
        class="de_drawer"
        @close="visible = false"
        destroyOnClose
        :zIndex="zIndex"
        :width="drawerWidth"
        @afterVisibleChange="afterVisibleChange"
        placement="right">
        <template #title>
            <div class="drawer_title">
                {{ edit ? $t('inquiries.resEdit') : $t('inquiries.resAdd') }}
            </div>
        </template>
        <template #rightHeader>
            <HelpButton partCode="inquiries" />
        </template>
        <div class="forma">
            <a-form-model
                v-if="visible"
                ref="riskAssessmentForm"
                :model="form"
                :rules="rules">
                <template v-if="isMobile">
                    <div class="mobile-drawer-body w-full" ref="riskAssessmentAddBody">
                        <div class="user mb-2">
                            <div class="label">{{ $t('inquiries.responsible') }}</div>
                            <Profiler class="pt-2" :user="user" />
                        </div>
                        <div class="issue_date">
                            <a-form-model-item ref="issue_date" :label="$t('inquiries.issueDate')" prop="issue.issue_date">
                                <a-date-picker
                                    v-model="form.issue.issue_date"
                                    :getPopupContainer="trigger => trigger.parentElement"
                                    :placeholder="$t('inquiries.datePlaceholder')"
                                    class="w-full"
                                    format="DD.MM.YYYY"
                                    size="large" />
                            </a-form-model-item>
                        </div>
                        <div class="organization truncate">
                            <template v-if="edit">
                                <div class="">{{ $t('inquiries.organization') }}:</div>
                                <div class="organization_edit flex items-center pt-2">
                                    <span :key="form?.organization?.logo" class="pr-2">
                                        <a-avatar 
                                            :size="30"
                                            :src="form?.organization?.logo"
                                            icon="fi-rr-users-alt" 
                                            flaticon />
                                    </span>
                                    <a-tooltip placement="topLeft" :title="form?.organization?.name">
                                        <span class="break-all truncate">
                                            {{ form?.organization?.name }}
                                        </span>
                                    </a-tooltip>
                                </div>
                            </template>
                            <template v-else>
                                <a-form-model-item ref="organization" :label="$t('inquiries.organization')" prop="organization">
                                    <a-select
                                        v-model="form.organization"
                                        size="large"
                                        :getPopupContainer="getPopupContainer"
                                        :loading="myOrganizationsLoading"
                                        :placeholder="$t('inquiries.orgSelect')">
                                        <a-select-option v-for="org in myOrganizations" :key="org.id" :value="org.id">
                                            <div class="truncate">{{ org.name }}</div>
                                        </a-select-option>
                                    </a-select>
                                </a-form-model-item>
                            </template>
                        </div>
                        <a-form-model-item ref="location_points" :label="$t('inquiries.provide_address')" prop="location_points">
                            <AddressSelect 
                                ref="addressSelect"
                                placeholder="inquiries.map_select"
                                @change="addressChange" />
                        </a-form-model-item>
                        <div v-if="form.location_points && form.location_points.length" style="grid-column: span 2;">
                            <div v-for="(point, index) in form.location_points" :key="point.id" class="address_item">
                                <span>
                                    {{ point.address }}    
                                </span>
                                <div class="flex items-center pl-2">
                                    <a-button 
                                        icon="fi-rr-edit" 
                                        flaticon
                                        @click="addressEdit(point)" />
                                    <a-button 
                                        type="danger"
                                        class="ml-1"
                                        icon="fi-rr-trash" 
                                        flaticon
                                        @click="addressDelete(index)" />
                                </div>
                            </div>
                        </div>
                        <div class="number">
                            <a-form-model-item ref="number" :label="$t('inquiries.resNumber')" prop="issue.number">
                                <a-input
                                    size="large"
                                    v-model="form.issue.number"
                                    :placeholder="$t('inquiries.resNumberPlaceholder')" />
                            </a-form-model-item>
                        </div>
                        <div class="issue_type">
                            <a-form-model-item ref="issue_type" :label="$t('inquiries.resType')" prop="issue.issue_type">
                                <a-select
                                    size="large"
                                    :getPopupContainer="trigger => trigger.parentElement"
                                    :loading="issueTypesLoading"
                                    v-model="form.issue.issue_type"
                                    :placeholder="$t('inquiries.resTypePlaceholder')" >
                                    <a-select-option v-for="item in issueTypes" :value="item.code" :key="item.id">
                                        {{ item.string_view }}
                                    </a-select-option>
                                </a-select>
                            </a-form-model-item>
                        </div>
                        <div class="summary">
                            <a-form-model-item ref="issue_category" :label="`${$t('inquiries.issue_category')}:`" prop="issue.issue_category">
                                <TreeSelect
                                    v-model="form.issue.issue_category"
                                    useSearch
                                    apiUrl="/app_info/select_list/"
                                    titleKey="string_view"
                                    isLeafKey="isLeaf"
                                    parentIdKey="id"
                                    valueKey="id"
                                    pidKey="id"
                                    idKey="id"
                                    :params="{
                                        model: 'risk_assessment.IssueCategoryModel', 
                                        parent: 'root'
                                    }"
                                    :onLoadParams="{
                                        model: 'risk_assessment.IssueCategoryModel'
                                    }"
                                    :searchParams="{
                                        model: 'risk_assessment.IssueCategoryModel'
                                    }"
                                    :dropdownStyle="{
                                        maxHeight: '300px', 
                                        overflowY: 'auto'
                                    }"
                                    :treeDefaultExpandedKeys="treeDefaultExpandedKeys"
                                    @initLoading="issueCategoryInitLoading"
                                    @change="changeTree" />
                            </a-form-model-item>
                        </div>
                        <div class="sent_for">
                            <a-form-model-item ref="sent_for" :label="$t('inquiries.resSt')" prop="sent_for">
                                <a-radio-group v-model="form.sent_for" :default-value="0" size="large">
                                    <a-radio :value="0">
                                        {{ $t('inquiries.main_leader_or_deputies') }}
                                    </a-radio>
                                    <a-radio :value="1" class="mt-3">
                                        {{ $t('inquiries.head_of_apparatus') }}
                                    </a-radio>
                                </a-radio-group>
                            </a-form-model-item>
                        </div>
                        <div class="issue_text">
                            <a-form-model-item ref="text" :label="$t('inquiries.resText')" prop="issue.text" class="mb-2">
                                <a-textarea
                                    v-model="form.issue.text"
                                    allowClear
                                    :placeholder="$t('inquiries.inquiryText')"
                                    :auto-size="{ minRows: 10, maxRows: 10 }" />
                            </a-form-model-item>
                        </div>
                        <div class="risk_assessment">
                            <div class="risk_assessment_list">
                                <div class="mb-3">{{ $t('inquiries.resCr') }}</div>
                                <a-spin :spinning="riskAssessmentCriteriaLoading" class="mb-3">
                                    <div
                                        v-for="item in form.risk_assessment_criteria"
                                        :key="item.id"
                                        class="ra_list_item cursor_pointer select-none"
                                        :class="item?.value && 'bg-blue-200'"
                                        @click="clickHandler(item)">
                                        {{ item.string_view }}
                                    </div>
                                </a-spin>
                                <div class="ra_total_item w-full" :class="backgroundColorClass()">{{ $t('inquiries.resTotal') }} {{ total }}</div>
                            </div>
                        </div>
                    </div>
                </template>
                <template v-else>
                    <div class="drawer_body w-full" ref="riskAssessmentAddBody">
                        <div class="grid gap-4 grid-cols-[250px,1fr] md:grid-cols-[300px,1fr] lg:grid-cols-[400px,1fr]">
                            <div class="risk_assessment">
                                <div class="risk_assessment_list">
                                    <div class="label">{{ $t('inquiries.resCr') }}</div>
                                    <a-spin :spinning="riskAssessmentCriteriaLoading">
                                        <div v-for="item in form.risk_assessment_criteria" :key="item.id">
                                            <a-tooltip placement="right" :overlayStyle="{zIndex: 1100}">
                                                <template slot="title">
                                                    <span>{{ $t('inquiries.touch') }}</span>
                                                </template>
                                                <div
                                                    class="ra_list_item cursor_pointer select-none"
                                                    :class="item?.value && 'bg-blue-200'"
                                                    @click="clickHandler(item)">
                                                    {{ item.string_view }}
                                                </div>
                                            </a-tooltip>
                                        </div>
                                    </a-spin>
                                    <div class="ra_total_item label w-full" :class="backgroundColorClass()">{{ $t('inquiries.resTotal') }} {{ total }}</div>
                                </div>
                            </div>
                            <div>
                                <div class="grid gap-2 grid-cols-1 xl:grid-cols-3" style="grid-column: span 2;">
                                    <div>
                                        <div class="responsible">{{ $t('inquiries.responsible') }}:</div>
                                        <Profiler class="" :user="user" />
                                    </div>
                                    <div class="organization truncate">
                                        <template v-if="edit">
                                            <div class="responsible">{{ $t('inquiries.organization') }}:</div>
                                            <div class="organization_edit flex items-center pt-2">
                                                <span :key="form?.organization?.logo" class="pr-2">
                                                    <a-avatar 
                                                        :size="30"
                                                        :src="form?.organization?.logo"
                                                        icon="fi-rr-users-alt" 
                                                        flaticon />
                                                </span>
                                                <a-tooltip placement="topLeft" :title="form?.organization?.name">
                                                    <span class="break-all truncate">
                                                        {{ form?.organization?.name }}
                                                    </span>
                                                </a-tooltip>
                                            </div>
                                        </template>
                                        <template v-else>
                                            <a-form-model-item ref="organization" :label="$t('inquiries.organization')" prop="organization">
                                                <a-select
                                                    v-model="form.organization"
                                                    size="large"
                                                    :getPopupContainer="getPopupContainer"
                                                    :loading="myOrganizationsLoading"
                                                    :placeholder="$t('inquiries.orgSelect')">
                                                    <a-select-option v-for="org in myOrganizations" :key="org.id" :value="org.id">
                                                        <div class="truncate">{{ org.name }}</div>
                                                    </a-select-option>
                                                </a-select>
                                            </a-form-model-item>
                                        </template>
                                    </div>
                                    <a-form-model-item ref="location_points" :label="$t('inquiries.provide_address')" prop="location_points">
                                        <AddressSelect 
                                            ref="addressSelect"
                                            placeholder="inquiries.map_select"
                                            :addressList="form.location_points"
                                            :addressDelete="addressDelete"
                                            @change="addressChange" />
                                    </a-form-model-item>
                                </div>
                                <div v-if="form.location_points && form.location_points.length" style="grid-column: span 2;">
                                    <div v-for="(point, index) in form.location_points" :key="point.id" class="address_item">
                                        <span>
                                            {{ point.address }}    
                                        </span>
                                        <div class="flex items-center pl-2">
                                            <a-button 
                                                icon="fi-rr-edit" 
                                                flaticon
                                                @click="addressEdit(point)" />
                                            <a-button 
                                                type="danger"
                                                class="ml-1"
                                                icon="fi-rr-trash" 
                                                flaticon
                                                @click="addressDelete(index)" />
                                        </div>
                                    </div>
                                </div>
                                <div class="grid gap-2 grid-cols-1 xl:grid-cols-3" style="grid-column: span 2;">
                                    <div class="issue_date">
                                        <a-form-model-item ref="issue_date" :label="$t('inquiries.issueDate')" prop="issue.issue_date">
                                            <a-date-picker
                                                v-model="form.issue.issue_date"
                                                :getPopupContainer="trigger => trigger.parentElement"
                                                :placeholder="$t('inquiries.datePlaceholder')"
                                                class="w-full"
                                                format="DD.MM.YYYY"
                                                size="large" />
                                        </a-form-model-item>
                                    </div>
                                    <div class="number">
                                        <a-form-model-item ref="number" :label="$t('inquiries.resNumber')" prop="issue.number">
                                            <a-input
                                                size="large"
                                                v-model="form.issue.number"
                                                :placeholder="$t('inquiries.resNumberPlaceholder')" />
                                        </a-form-model-item>
                                    </div>
                                    <div class="issue_type">
                                        <a-form-model-item ref="issue_type" :label="$t('inquiries.resType')" prop="issue.issue_type">
                                            <a-select
                                                size="large"
                                                :getPopupContainer="trigger => trigger.parentElement"
                                                :loading="issueTypesLoading"
                                                v-model="form.issue.issue_type"
                                                :placeholder="$t('inquiries.resTypePlaceholder')" >
                                                <a-select-option v-for="item in issueTypes" :value="item.code" :key="item.id">
                                                    {{ item.string_view }}
                                                </a-select-option>
                                            </a-select>
                                        </a-form-model-item>
                                    </div>
                                </div>
                                <div class="summary">
                                    <a-form-model-item ref="issue_category" :label="`${$t('inquiries.issue_category')}:`" prop="issue.issue_category">
                                        <TreeSelect
                                            v-model="form.issue.issue_category"
                                            useSearch
                                            apiUrl="/risk_assessment/issue_categories/"
                                            titleKey="name"
                                            isLeafKey="is_leaf"
                                            parentIdKey="id"
                                            valueKey="id"
                                            pidKey="id"
                                            idKey="id"
                                            :params="{
                                                parent: 'root'
                                            }"
                                            :dropdownStyle="{
                                                maxHeight: '300px', 
                                                overflowY: 'auto'
                                            }"
                                            :treeDefaultExpandedKeys="treeDefaultExpandedKeys"
                                            @initLoading="issueCategoryInitLoading"
                                            @change="changeTree" />
                                    </a-form-model-item>
                                </div>
                                <div class="extra">
                                    <WidgetsSwitch 
                                        v-for="(item, index) in extra"
                                        :key="item.key || index"
                                        :item="item"
                                        :form="form"
                                        :categoryDetails="categoryDetails"
                                        :deleteExtraKeys="deleteExtraKeys" />
                                </div>
                                <div class="sent_for">
                                    <a-form-model-item ref="sent_for" :label="$t('inquiries.resSt')" prop="sent_for">
                                        <a-radio-group v-model="form.sent_for" :default-value="0" button-style="solid" size="large">
                                            <a-radio-button :value="0">
                                                {{ $t('inquiries.main_leader') }}
                                            </a-radio-button>
                                            <a-radio-button :value="2">
                                                {{ $t('inquiries.deputies') }}
                                            </a-radio-button>
                                            <a-radio-button :value="1">
                                                {{ $t('inquiries.head_of_apparatus') }}
                                            </a-radio-button>
                                        </a-radio-group>
                                    </a-form-model-item>
                                </div>
                                <div class="issue_text">
                                    <a-form-model-item ref="text" :label="$t('inquiries.resText')" prop="issue.text">
                                        <a-textarea
                                            v-model="form.issue.text"
                                            allowClear
                                            :placeholder="$t('inquiries.inquiry_text')"
                                            :auto-size="{ minRows: 10, maxRows: 10 }" />
                                    </a-form-model-item>
                                </div>
                            </div>
                        </div>
                    </div>
                </template>
            </a-form-model>
        </div>
        <template #footer>
            <div class="flex items-center">
                <a-button 
                    type="primary"
                    size="large"
                    :loading="loading"
                    @click="formSubmit()">
                    {{ submitButtonText }}
                </a-button>
                <a-button 
                    type="ui"
                    class="ml-2"
                    size="large"
                    :loading="loading"
                    @click="visible = false">
                    {{ $t('inquiries.cancel') }}
                </a-button>
            </div>
        </template>
    </DrawerTemplate>
</template>

<script>
import eventBus from '@/utils/eventBus'
import { mapState } from 'vuex'
export default {
    name: 'NewInquir',
    components: {
        AddressSelect: () => import('@apps/DrawerSelect/AddressSelect.vue'),
        TreeSelect: () => import('@apps/DrawerSelect/TreeSelect.vue'),
        WidgetsSwitch: () => import('./extraComponents/WidgetsSwicth.vue'),
        DrawerTemplate: () => import('@/components/DrawerTemplate.vue'),
        HelpButton: () => import('@apps/Support/components/HelpButton.vue')
    },
    props: {
        zIndex: {
            type: Number,
            default: 1050
        },
        pageName: {
            type: String,
            default: null
        }
    },
    computed: {
        windowWidth() {
            return this.$store.state.windowWidth
        },
        isMobile() {
            return this.$store.state.isMobile
        },
        drawerWidth() {
            if(this.isMobile) {
                return '100%'
            } else if(this.windowWidth > 1400) {
                return 1400
            } else {
                return '95%'
            }
        },
        ...mapState({
            user: state => state.user.user,
        }),
        submitButtonText() {
            return this.edit ? this.$t('inquiries.save') : this.$t('inquiries.create')
        }
    },
    data() {
        return {
            edit: false,
            loading: false,
            myOrganizations: [],
            myOrganizationsLoading: false,
            summariesLoading: false,
            riskAssessmentCriteriaLoading: false,
            visible: false,
            issueTypesLoading: false,
            issueTypes: [],
            total: 0,
            editAddress: null,
            treeDefaultExpandedKeys: [],
            extra: [],
            categoryDetails: {},
            form: {
                organization: null,
                assessment_type: 'initial',
                location_points: [],
                issue: {
                    issue_type: null,
                    number: "",
                    summary: "",
                    issue_category: null,
                    text: "",
                    issue_date: null
                },
                risk_assessment_criteria: [],
                sent_for: 0, // Направлено для рассмотрения.
                //              Значения: 0 - Первый руководитель,
                //                        1 - Руководитель аппарата,
                //                        2 - Заместители первого руководителя
            },
            rules: {
                organization: [
                    { required: true, message: this.$t('inquiries.field_required'), trigger: 'blur' }
                ],
                "issue.issue_date": [
                    { required: true, message: this.$t('inquiries.field_required'), trigger: 'blur' }
                ],
                "issue.number": [
                    { required: true, message: this.$t('inquiries.field_required'), trigger: 'blur' }
                ],
                "issue.issue_type": [
                    { required: true, message: this.$t('inquiries.field_required'), trigger: 'blur' }
                ],
                "issue.issue_category": [
                    { required: true, message: this.$t('inquiries.field_required'), trigger: 'blur' }
                ],
                // "location_points": [
                //     { required: true, message: this.$t('inquiries.field_required'), trigger: 'blur' }
                // ]
            },
        }
    },
    created() {
        eventBus.$on('new_inquir', () => {
            this.visible = true
        })
        eventBus.$on('edit_inquir', async (id) => {
            this.edit = true
            await this.getAssessment(id)
            this.visible = true
        })
    },
    methods: {
        setExtraKeysValues(extra) {
            if(this.form.issue[extra.key]) {
                this.form[extra.key] = this.form.issue[extra.key]
            }
        },
        addExtraKeys(extra) {
            this.$set(this.form, extra.key, extra.options)
            Object.keys(extra.rules).forEach(key => {
                this.$set(this.rules, key, extra.rules[key])
            })
        },
        deleteExtraKeys(componentName) {
            this.$delete(this.form, componentName)
            Object.keys(this.rules).forEach(key => {
                if(key.startsWith(componentName))
                    this.$delete(this.rules, key)
            })
        },
        changeTree(val) {
            this.treeDefaultExpandedKeys = []
            this.extra = []
            this.categoryDetails = {}
            this.getCategory(val)
        },
        async getCategory(categoryID) {
            this.loading = true
            try {
                const { data } = await this.$http.get(`/risk_assessment/issue_categories/${categoryID}/`)
                if(data) {
                    this.categoryDetails = data
                    this.setExtra(data.metadata)
                }
            } catch(e) {
                console.log(e)
            } finally {
                this.loading = false
            }
        },
        setExtra(metadata) {
            if(Object.hasOwn(metadata, 'extra')) {
                if(metadata.extra.length) {
                    metadata.extra.forEach(item => {
                        this.addExtraKeys(item)
                        if(this.edit) this.setExtraKeysValues(item)
                    })
                }
                this.$nextTick(() => {
                    this.extra = metadata.extra
                })
            }
        },
        renderCustomTitle({ title, value }) {
            return `<span class="custom-class" data-value="${value}">${title}</span>`
        },
        addressEdit(point) {
            this.$nextTick(() => {
                this.$refs.addressSelect.editAddress(point)
            })
        },
        addressChange(point) {
            const index = this.form.location_points.findIndex(f => f.key === point.key)
            if(index !== -1) {
                this.$set(this.form.location_points, index, point)
            } else {
                this.form.location_points.unshift({
                    ...point,
                    key: Date.now()
                })
            }
        },
        addressDelete(index) {
            this.form.location_points.splice(index, 1)
        },
        backgroundColorClass() {
            if (this.total >= 1 && this.total <= 2) {
                return 'bg-yellow'
            } else if (this.total >= 3 && this.total <= 5) {
                return 'bg-orange'
            } else if (this.total >= 5) {
                return 'bg-red'
            } else {
                return ''
            }
        },
        getTotal() {
            this.total = 0
            this.form.risk_assessment_criteria.forEach(each => {
                if(each.value === 1)
                    this.total += 1
            })
        },
        async getAssessment(id) {
            if(!this.assessmentLoading) {
                try {
                    this.myOrganizationsLoading = true
                    this.summariesLoading = true
                    this.riskAssessmentCriteriaLoading = true
                    const { data } = await this.$http.get(`risk_assessment/${id}/`)
                    if(data) {
                        this.form = {...data}
                        this.form.editCategory = this.form.issue.issue_category
                        if(this.form.issue.issue_category?.id)
                            this.form.issue.issue_category = this.form.issue.issue_category?.id
                        if(!this.form.location_points?.length)
                            this.form.location_points = []
                        if(this.form.issue.issue_type?.code)
                            this.form.issue.issue_type = this.form.issue.issue_type?.code
                        if(Object.hasOwn(this.form.issue, 'personal_reception')) {
                            this.form.issue.personal_reception.social_status = this.form.issue.personal_reception.social_status.code
                            this.form.issue.personal_reception.status = this.form.issue.personal_reception.status.code
                        }
                        if(data.risk_assessment_criteria.length) {
                            this.form.risk_assessment_criteria = data.risk_assessment_criteria.map(item => {
                                return {
                                    "criteria": item.criteria.id,
                                    "code.criteria": item.code,
                                    "string_view": item.criteria.name,
                                    "value": item.value
                                }
                            })
                            this.getTotal()
                        }
                    }
                } catch(e) {
                    console.log(e)
                } finally {
                    this.myOrganizationsLoading = false
                    this.summariesLoading = false
                    this.riskAssessmentCriteriaLoading = false
                }
            }
        },
        clickHandler(item) {
            const index = this.form.risk_assessment_criteria.findIndex(each => each.criteria === item.criteria)
            if(index !== -1) {
                if(this.form.risk_assessment_criteria[index]['value'] === 1)
                    this.form.risk_assessment_criteria[index]['value'] = 0
                else
                    this.form.risk_assessment_criteria[index]['value'] = 1
                
                this.getTotal()
            }
        },
        async getRiskAssessmentCriteriaList() {
            if(!this.riskAssessmentCriteriaLoading) {
                try {
                    this.riskAssessmentCriteriaLoading = true
                    const { data } = await this.$http.get('app_info/select_list/', {
                        params: {
                            model: 'risk_assessment.AssessmentCriteriaModel'
                        }
                    })
                    if(data.selectList.length) {
                        this.form.risk_assessment_criteria = data.selectList.map(item => {
                            return {
                                "criteria": item.id,
                                "code": item.code,
                                "string_view": item.string_view,
                                "value": 0
                            }
                        })
                    }
                } catch(e) {
                    console.log(e)
                } finally {
                    this.riskAssessmentCriteriaLoading = false
                }
            }
        },
        async getIssueTypes() {
            if(!this.issueTypesLoading) {
                try {
                    this.issueTypesLoading = true
                    const { data } = await this.$http.get('app_info/select_list/?model=risk_assessment.IssueTypeModel')
                    if(data.selectList.length) {
                        this.issueTypes = data.selectList
                        if(!this.edit && data.selectList.length === 1)
                            this.form.issue_type = data.selectList[0].id
                    }
                } catch(e) {
                    console.log(e)
                } finally {
                    this.issueTypesLoading = false
                }
            }
        },
        issueCategoryInitLoading(onLoadData) {
            if(this.edit) {
                if(this.form.editCategory?.id) {
                    if(this.form.editCategory.issue_category?.id) {
                        onLoadData({
                            dataRef: {
                                id: this.form.editCategory.issue_category.id,
                                loaded: false
                            }
                        })
                        this.treeDefaultExpandedKeys.push(this.form.editCategory.issue_category.id)
                    }
                    this.setExtra(this.form.editCategory.metadata)
                }
            }
        },
        async getMyOrganizations() {
            if(!this.myOrganizationsLoading) {
                const params = {
                    permission_type: 'create_risk_assessment'
                }
                try {
                    this.myOrganizationsLoading = true
                    const { data } = await this.$http.get(`/contractor_permissions/organizations/`, {
                        params: params
                    })
                    if(data.length) {
                        this.myOrganizations = data
                        if(!this.edit && data.length === 1)
                            this.form.organization = data[0].id
                    }
                } catch(e) {
                    console.log(e)
                } finally {
                    this.myOrganizationsLoading = false
                }
            }
        },
        async formSubmit() {
            this.$refs.riskAssessmentForm.validate(async valid => {
                if (valid) {
                    try {
                        this.loading = true
                        const formData = JSON.parse(JSON.stringify(this.form))
                        if(formData.issue.issue_date)
                            formData.issue.issue_date = this.$moment(formData.issue.issue_date).format('YYYY-MM-DD')
                        if(this.edit) {
                            const { data } = await this.$http.put(`/risk_assessment/${formData.id}/`, formData)
                            if(data) {
                                this.visible = false
                                eventBus.$emit('update_assessment_in_list', data)
                                this.$message.info(this.$t('inquiries.resUpdated'))
    
                            }
                        } else {
                            const { data } = await this.$http.post('/risk_assessment/', formData)
                            if(data) {
                                this.visible = false
                                eventBus.$emit('assessment_list_reload')
                                this.$message.info(this.$t('inquiries.resCreated'))  
                            }

                        }
                    } catch(e) {
                        console.log(e)
                        this.$message.error(e[0] ? e[0] : this.$t('inquiries.resError'))
                    } finally {
                        this.loading = false
                    }
                } else {
                    this.$message.error(this.$t('inquiries.dataError'))
                    return false
                }
            })
        },
        getPopupContainer() {
            return this.$refs['riskAssessmentAddBody']
        },
        async afterVisibleChange(vis) {
            if(vis) {
                this.getMyOrganizations()
                this.getIssueTypes()
                if(!this.edit) {
                    this.getRiskAssessmentCriteriaList()
                }
            } else {
                this.treeDefaultExpandedKeys = []
                this.myOrganizations = []
                this.issueTypes = []
                this.form = {
                    organization: null,
                    assessment_type: 'initial',
                    location_points: [],
                    issue: {
                        issue_type: null,
                        number: "",
                        summary: "",
                        issue_category: null,
                        text: "",
                        issue_date: null
                    },
                    risk_assessment_criteria: [],
                    sent_for: 0
                },
                this.edit = false
                this.total = 0
                this.extra = []
                this.categoryDetails = {}
            }
        },
    },
    beforeDestroy() {
        eventBus.$off('new_inquir')
        eventBus.$off('edit_inquir')
    }
}
</script>

<style lang="scss" scoped>
.address_item{
    margin-bottom: 15px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    border: 1px solid #e1e7ec;
    padding: 15px;
    border-radius: 8px;
}
.de_drawer{
    &::v-deep{
        .forma {
            height: inherit;
            overflow-y: auto;
        }
        .mobile-drawer-body{
            .issue_text {
                display: flex;
                flex-direction: column;
                width: 100%;
                min-width: 0;
                .ck-editor {
                    display: flex; 
                    flex-direction: column;
                    flex-grow: 1;
                    min-height: 0;
                }
                .ck-editor__main {
                    min-height: 0;
                    flex-grow: 1;
                }
                .ck-editor__editable_inline {
                    height: 100%;
                }
                .text-label{
                    line-height: 26px;
                    color: rgba(0, 0, 0, 0.85);
                    padding-bottom: 8px;
                }
            }
            .risk_assessment {
                grid-row: span 5;
                .risk_assessment_list{
                    width: 100%;
                    display: grid;
                    grid-template-columns: 1fr;
                    align-content: space-between;
                    height: 100%;
                    .ra_list_item {
                        border-radius: var(--borderRadius);
                        border: 1px solid var(--border1);
                        margin-top: 1px;
                        padding: 5px;
                        cursor: pointer;
                    }
                    .ra_total_item {
                        border-radius: var(--borderRadius);
                        border: 1px solid var(--border1);
                        margin-top: 1px;
                        padding: 10px;
                        align-self: end;
                    }
                        .bg-yellow {
                        background-color: yellow;
                    }
                        .bg-orange {
                        background-color: orange;
                    }
                        .bg-red {
                        background-color: red;
                    }
                }
            }
        }
        .drawer_body{
            .label {
                font-weight: 600;
                line-height: 26px;
            }
            .risk_assessment {
                .risk_assessment_list{
                    width: 100%;
                    align-content: space-between;
                    height: 100%;
                    .ra_list_item {
                        border-radius: var(--borderRadius);
                        border: 1px solid var(--border1);
                        margin-top: 1px;
                        padding: 5px;
                        cursor: pointer;
                    }
                    .ra_total_item {
                        border-radius: var(--borderRadius);
                        border: 1px solid var(--border1);
                        margin-top: 1px;
                        padding: 10px;
                        align-self: end;
                    }
                        .bg-yellow {
                        background-color: yellow;
                    }
                        .bg-orange {
                        background-color: orange;
                    }
                        .bg-red {
                        background-color: red;
                    }
                }
            }
            .three_items {
                grid-column: span 2;
                display: grid;
                grid-template-columns: 1fr 1.7fr 1fr;
                gap: 20px;
                .responsible{
                    line-height: 26px;
                }
                .organization {
                    width: 100%;
                }
                .issue_date {
                    width: 100%;
                }
                .organization_edit {
                    display: grid;
                    grid-template-columns: max-content 1fr;
                }
            }
            .responsible {
            }
            .number {
                width: 100%;
            }
            .issue_type {
                width: 100%;
            }
            .summary {
                grid-column: span 2;
            }
            .sent_for {
                grid-column: span 2;
            }
            .issue_text {
                grid-column: span 2;
            }
            .submt_button {
                grid-column: span 2;
            }
        }
    }
}
</style>