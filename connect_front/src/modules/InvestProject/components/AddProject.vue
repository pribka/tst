<template>
    <a-drawer
        ref="addInvestProjectDrawer"
        :title="isEdit ? $t('invest.form.edit_invest_p') : $t('invest.form.add_invest_p')"
        placement="right"
        :width="drawerWidth"
        :visible="visible"
        destroyOnClose
        :afterVisibleChange="afterVisibleChange"
        @close="visible = false">
        <a-spin :spinning="formDataLoading">
            <a-form-model
                ref="investForm"
                class="invest_form"
                :model="form"
                :rules="rules">
                <div class="form_block">
                    <div class="form_block__header">
                        <h3>{{ $t('invest.main_info') }}</h3>
                        <div class="st">{{ $t('invest.form.step', { step: 1 }) }}</div>
                    </div>
                    <div class="grid gap-0 md:gap-6 grid-cols-1 md:grid-cols-2">
                        <a-form-model-item ref="project_name" :label="$t('invest.form.project_name')" prop="project_name">
                            <a-input
                                v-model="form.project_name"
                                :placeholder="$t('invest.form.enter_project_name')"
                                size="large" />
                        </a-form-model-item>
                        <a-form-model-item ref="organization" :label="$t('invest.form.organization')" prop="organization">
                            <a-select
                                v-model="form.organization"
                                :placeholder="$t('invest.form.organization')"
                                size="large"
                                class="w-full"
                                :loading="orgLoading"
                                :default-active-first-option="false"
                                :filter-option="false"
                                :not-found-content="null">
                                <a-select-option 
                                    v-for="org in organization.results" 
                                    :key="org.id" 
                                    :value="org.id">
                                    {{ org.name }}
                                </a-select-option>
                            </a-select>
                        </a-form-model-item>
                    </div>
                    <a-form-model-item ref="location" :label="$t('invest.form.location')" prop="location">
                        <div v-if="locationLabel" class="name">{{ locationLabel }}</div>
                        <div v-else class="name text-gray-300">{{ $t('invest.form.not_specified') }}</div>
                    </a-form-model-item>
                    <div class="grid gap-x-0 gap-y-0 md:gap-x-6 md:gap-y-0 grid-cols-1 md:grid-cols-2">
                        <a-form-model-item ref="location_region" :label="$t('invest.form.region')" prop="location_region">
                            <a-select
                                v-model="locationRegion"
                                allowClear
                                :placeholder="$t('invest.form.select_project_region')"
                                size="large"
                                class="w-full"
                                :loading="locationRegionLoading"
                                :default-active-first-option="false"
                                :filter-option="false"
                                :not-found-content="null"
                                @dropdownVisibleChange="locationRegionOpenSelect"
                                @change="locationRegionChange">
                                <a-select-option 
                                    v-for="region in locationRegionList" 
                                    :key="region.id" 
                                    :value="region.id">
                                    {{ region.code }} - {{ region.name }}
                                </a-select-option>
                            </a-select>
                        </a-form-model-item>
                        <a-form-model-item ref="location_district" :label="$t('invest.form.district')" prop="location_district">
                            <a-select
                                v-model="locationDistrict"
                                allowClear
                                :disabled="locationRegion ? false : true"
                                :placeholder="$t('invest.form.select_district')"
                                size="large"
                                class="w-full"
                                :loading="locationDistrictLoading"
                                :default-active-first-option="false"
                                :filter-option="false"
                                :not-found-content="null"
                                @dropdownVisibleChange="locationDistrictOpenSelect"
                                @change="locationDistrictChange">
                                <a-select-option 
                                    v-for="district in locationDistrictList" 
                                    :key="district.id" 
                                    :value="district.id">
                                    {{ district.code }} - {{ district.name }}
                                </a-select-option>
                            </a-select>
                        </a-form-model-item>
                        <a-form-model-item ref="location_akimat" :label="$t('invest.form.akimat')" prop="location_akimat">
                            <a-select
                                v-model="locationAkimat"
                                allowClear
                                :disabled="locationDistrict ? false : true"
                                :placeholder="$t('invest.form.select_akimat')"
                                size="large"
                                class="w-full"
                                :loading="locationAkimatLoading"
                                :default-active-first-option="false"
                                :filter-option="false"
                                :not-found-content="null"
                                @dropdownVisibleChange="locationAkimatOpenSelect"
                                @change="locationAkimatChange">
                                <a-select-option 
                                    v-for="akimat in locationAkimatList" 
                                    :key="akimat.id" 
                                    :value="akimat.id">
                                    {{ akimat.code }} - {{ akimat.name }}
                                </a-select-option>
                            </a-select>
                        </a-form-model-item>
                        <a-form-model-item ref="location_settlement" :label="$t('invest.form.settlement')" prop="location_settlement">
                            <a-select
                                v-model="locationSettlement"
                                allowClear
                                :disabled="locationAkimat ? false : true"
                                :placeholder="$t('invest.form.select_settlement')"
                                size="large"
                                class="w-full"
                                :loading="locationSettlementLoading"
                                :default-active-first-option="false"
                                :filter-option="false"
                                :not-found-content="null"
                                @dropdownVisibleChange="locationSettlementOpenSelect"
                                @change="locationSettlementChange">
                                <a-select-option 
                                    v-for="settlement in locationSettlementList" 
                                    :key="settlement.id" 
                                    :value="settlement.id">
                                    {{ settlement.code }} - {{ settlement.name }}
                                </a-select-option>
                            </a-select>
                        </a-form-model-item>
                        <a-form-model-item ref="location_settlement_2" :label="$t('invest.form.village')" prop="location_settlement_2">
                            <a-select
                                v-model="locationVillage"
                                allowClear
                                :disabled="locationSettlement ? false : true"
                                :placeholder="$t('invest.form.select_village')"
                                size="large"
                                class="w-full"
                                :loading="locationVillageLoading"
                                :default-active-first-option="false"
                                :filter-option="false"
                                :not-found-content="null"
                                @dropdownVisibleChange="locationVillageOpenSelect"
                                @change="locationVillageChange">
                                <a-select-option 
                                    v-for="village in locationVillageList" 
                                    :key="village.id" 
                                    :value="village.id">
                                    {{ village.code }} - {{ village.name }}
                                </a-select-option>
                            </a-select>
                        </a-form-model-item>
                    </div>
                    <div class="grid gap-0 md:gap-6 grid-cols-1 md:grid-cols-2">
                        <a-form-model-item ref="company_bin" :label="$t('invest.form.company_bin')" prop="company_bin">
                            <a-input
                                v-model="form.company_bin"
                                :placeholder="$t('invest.form.enter_company_bin')"
                                :maxLength="12"
                                size="large"
                                @change="binChange">
                                <template v-if="binLoading" slot="suffix">
                                    <a-spin size="small" />
                                </template>
                            </a-input>
                        </a-form-model-item>
                        <a-form-model-item ref="company_name" :label="$t('invest.form.company_name')" prop="company_name">
                            <a-input
                                v-model="form.company_name"
                                :placeholder="$t('invest.form.enter_company_name')"
                                size="large" />
                        </a-form-model-item>
                    </div>
                    <div class="grid gap-0 md:gap-6 grid-cols-1 md:grid-cols-2">
                        <a-form-model-item ref="category" :label="$t('invest.form.category')" prop="category">
                            <a-select 
                                v-model="form.category"
                                :placeholder="$t('invest.form.select_category')"
                                size="large" 
                                class="w-full"
                                :default-active-first-option="false"
                                :not-found-content="null"
                                :loading="categoryLoading"
                                @change="categoryChange">
                                <a-select-option 
                                    v-for="category in categoryList.results" 
                                    :key="category.id" 
                                    :value="category.id">
                                    {{ category.string_view }}
                                </a-select-option>
                            </a-select>
                        </a-form-model-item>
                        <a-form-model-item ref="subcategory" :label="$t('invest.form.subcategory')" prop="subcategory">
                            <a-select 
                                v-model="form.subcategory"
                                :disabled="form.category ? false : true"
                                :placeholder="$t('invest.form.select_subcategory')"
                                size="large" 
                                class="w-full"
                                :default-active-first-option="false"
                                :not-found-content="null"
                                :loading="subcategoryLoading">
                                <a-select-option 
                                    v-for="subcategory in subcategoryList.results" 
                                    :key="subcategory.id" 
                                    :value="subcategory.id">
                                    {{ subcategory.string_view }}
                                </a-select-option>
                            </a-select>
                        </a-form-model-item>
                    </div>
                    <div class="grid gap-0 md:gap-6 grid-cols-1">
                        <a-form-model-item ref="comment" :label="$t('invest.form.comment')" prop="comment">
                            <a-textarea
                                v-model="form.comment"
                                :maxLength="1000"
                                :auto-size="{ minRows: 3, maxRows: 8 }"
                                :placeholder="$t('invest.form.add_comment')"
                                size="large" />
                        </a-form-model-item>
                    </div>
                    <div class="grid gap-0 md:gap-6 grid-cols-1 md:grid-cols-2">
                        <a-form-model-item ref="company_director_name" :label="$t('invest.form.company_director_name')" prop="company_director_name">
                            <a-input
                                v-model="form.company_director_name"
                                :placeholder="$t('invest.form.company_director_name')"
                                size="large" />
                        </a-form-model-item>
                        <a-form-model-item ref="company_phone" :label="$t('invest.form.contact_phone_number')" prop="company_phone">
                            <a-input
                                v-model="form.company_phone"
                                :placeholder="$t('invest.form.contact_phone_number')"
                                size="large" />
                        </a-form-model-item>
                        <a-form-model-item ref="stage" :label="$t('invest.form.project_stage')" prop="stage">
                            <a-select 
                                v-model="form.stage"
                                :placeholder="$t('invest.form.specify_project_stage')"
                                size="large" 
                                class="w-full"
                                :default-active-first-option="false"
                                :not-found-content="null"
                                :loading="stageLoading"
                                @dropdownVisibleChange="stageOpenSelect">
                                <a-select-option 
                                    v-for="stage in stageList.results" 
                                    :key="stage.id" 
                                    :value="stage.id">
                                    {{ stage.string_view }}
                                </a-select-option>
                            </a-select>
                        </a-form-model-item>
                    </div>
                    <div class="grid gap-0 md:gap-6 grid-cols-1">
                        <a-form-model-item ref="foreign_investor_info" :label="$t('invest.form.foreign_investor')" prop="foreign_investor_info">
                            <a-textarea
                                v-model="form.foreign_investor_info"
                                :maxLength="1000"
                                :auto-size="{ minRows: 3, maxRows: 8 }"
                                :placeholder="$t('invest.form.specify_foreign_investor')"
                                size="large" />
                        </a-form-model-item>
                    </div>
                    <div class="grid gap-0 md:gap-6 grid-cols-1 md:grid-cols-2">
                        <a-form-model-item ref="project_capacity" :label="$t('invest.form.project_capacity')" prop="project_capacity">
                            <a-input-number
                                v-model="form.project_capacity"
                                :step="0.01"
                                class="w-full"
                                :placeholder="$t('invest.form.specify_project_capacity')"
                                size="large" />
                        </a-form-model-item>
                        <a-form-model-item ref="measure_unit" :label="$t('invest.form.measure_unit')" prop="measure_unit">
                            <a-select 
                                v-model="form.measure_unit"
                                :placeholder="$t('invest.form.measure_unit')"
                                size="large" 
                                class="w-full"
                                :default-active-first-option="false"
                                :not-found-content="null"
                                :loading="measureUnitLoading">
                                <a-select-option 
                                    v-for="unit in measureUnitList.results" 
                                    :key="unit.id" 
                                    :value="unit.code">
                                    {{ unit.string_view }}
                                </a-select-option>
                            </a-select>
                        </a-form-model-item>
                    </div>
                    <div class="grid gap-0 md:gap-6 grid-cols-1 md:grid-cols-2">
                        <a-form-model-item ref="date_start" :label="$t('invest.form.project_start_date')" prop="date_start">
                            <a-date-picker v-model="form.date_start" valueFormat="YYYY-MM-DD" :showToday="false" size="large" :placeholder="$t('invest.form.project_start_date')" class="w-full" />
                        </a-form-model-item>
                        <a-form-model-item ref="dead_line" :label="$t('invest.form.planned_completion_date')" prop="dead_line">
                            <a-date-picker v-model="form.dead_line" valueFormat="YYYY-MM-DD" :showToday="false" size="large" :placeholder="$t('invest.form.planned_completion_date_p')" class="w-full" />
                        </a-form-model-item>
                    </div>
                </div>
                <div class="form_block">
                    <div class="form_block__header">
                        <h3>{{ $t('invest.form.project_cost') }}</h3>
                        <div class="st">{{ $t('invest.form.step', { step: 2 }) }}</div>
                    </div>
                    <div class="grid gap-0 md:gap-6 grid-cols-1 md:grid-cols-2">
                        <a-form-model-item ref="funds" :label="$t('invest.form.total_project_cost')" prop="funds">
                            <a-input-number
                                v-model="form.funds"
                                :step="0.01"
                                class="w-full"
                                :placeholder="$t('invest.form.total_project_cost_p')"
                                size="large" />
                        </a-form-model-item>
                    </div>
                    <div class="funding_sources_list" :class="form.funding_sources.length && 'mb-5'">
                        <div 
                            v-for="(source, index) in form.funding_sources" 
                            :key="source.key"
                            class="equipment_list__item">
                            <div class="grid gap-0 md:gap-6 grid-cols-1 md:grid-cols-2">
                                <a-form-model-item 
                                    :label="$t('invest.form.funding_source')"
                                    :prop="'funding_sources.' + index + '.funding_source'"
                                    :rules="{
                                        required: true,
                                        message: $t('wgr.field_require'),
                                        trigger: 'blur',
                                    }">
                                    <a-select 
                                        v-model="source.funding_source" 
                                        :placeholder="$t('invest.form.select_funding_source')"
                                        size="large" 
                                        class="w-full"
                                        :default-active-first-option="false"
                                        :not-found-content="null"
                                        show-search
                                        :filter-option="filterOption"
                                        :loading="sourceLoading"
                                        @dropdownVisibleChange="sourceOpenSelect">
                                        <a-select-option 
                                            v-for="iSource in fundingSourceList.results" 
                                            :key="iSource.id" 
                                            :value="iSource.id">
                                            {{ iSource.string_view }}
                                        </a-select-option>
                                    </a-select>
                                </a-form-model-item>
                                <a-form-model-item 
                                    :prop="'funding_sources.' + index + '.amount'" 
                                    :label="$t('invest.form.funding_volume')"
                                    :rules="{
                                        required: true,
                                        message: $t('wgr.field_require'),
                                        trigger: 'blur',
                                    }">
                                    <a-input-number
                                        v-model="source.amount"
                                        :step="0.01"
                                        class="w-full"
                                        :placeholder="$t('invest.form.enter_funding_volume')"
                                        size="large" />
                                </a-form-model-item>
                            </div>
                            <div class="grid gap-0 md:gap-6 grid-cols-1">
                                <a-form-model-item 
                                    :prop="'funding_sources.' + index + '.comment'"  
                                    :label="$t('invest.form.comment')"
                                    :rules="{
                                        required: false,
                                        message: $t('wgr.field_require'),
                                        trigger: 'blur',
                                    }">
                                    <a-textarea
                                        v-model="source.comment"
                                        :maxLength="1000"
                                        :auto-size="{ minRows: 3, maxRows: 8 }"
                                        :placeholder="$t('invest.form.add_comment_2')"
                                        size="large" />
                                </a-form-model-item>
                            </div>
                            <div v-if="form.funding_sources.length > 1" style="margin-top: -10px;">
                                <a-button type="link" size="small" @click="removeSource(index)">
                                    {{ $t('invest.form.remove') }}
                                </a-button>
                            </div>
                        </div>
                    </div>
                    <a-button 
                        type="primary" 
                        ghost 
                        block 
                        size="large"
                        @click="addSource()">
                        {{ $t('invest.form.add_funding_source') }}
                    </a-button>
                </div>
                <div class="form_block">
                    <div class="form_block__header">
                        <h3>{{ $t('invest.form.implementation_stage') }}</h3>
                        <div class="st">{{ $t('invest.form.step', { step: 3 }) }}</div>
                    </div>
                    <div class="grid gap-0 md:gap-6 grid-cols-1 md:grid-cols-2">
                        <a-form-model-item ref="has_documentation" :label="$t('invest.form.psd')" prop="has_documentation">
                            <a-select v-model="form.has_documentation" size="large" class="w-full">
                                <a-select-option value="true">
                                    {{ $t('invest.form.developed') }}
                                </a-select-option>
                                <a-select-option value="false">
                                    {{ $t('invest.form.not_developed') }}
                                </a-select-option>
                            </a-select>
                        </a-form-model-item>
                        <a-form-model-item ref="installation_stage" :label="$t('invest.form.construction_stage')" prop="installation_stage">
                            <a-input-number
                                v-model="form.installation_stage"
                                class="w-full"
                                :min="0"
                                :max="100"
                                :placeholder="$t('invest.form.construction_stage_placeholder')"
                                size="large" />
                        </a-form-model-item>
                    </div>
                    <div class="grid gap-0 md:gap-6 grid-cols-1">
                        <a-form-model-item ref="infrastructure_info" :label="$t('invest.form.infrastructure_info')" prop="infrastructure_info">
                            <a-textarea
                                v-model="form.infrastructure_info"
                                :maxLength="1000"
                                :auto-size="{ minRows: 3, maxRows: 8 }"
                                :placeholder="$t('invest.form.describe_infrastructure')"
                                size="large" />
                        </a-form-model-item>
                    </div>
                </div>
                <div class="form_block">
                    <div class="form_block__header">
                        <h3>{{ $t('invest.form.additional_info') }}</h3>
                        <div class="st">{{ $t('invest.form.step', { step: 4 }) }}</div>
                    </div>
                    <div class="grid gap-0 md:gap-6 grid-cols-1 md:grid-cols-2">
                        <a-form-model-item ref="jobs_temporary" :label="$t('invest.form.temporary_jobs')" prop="jobs_temporary">
                            <a-input-number
                                v-model="form.jobs_temporary"
                                class="w-full"
                                :placeholder="$t('invest.form.enter_temporary_jobs')"
                                size="large" />
                        </a-form-model-item>
                        <a-form-model-item ref="jobs_permanent" :label="$t('invest.form.permanent_jobs')" prop="jobs_permanent">
                            <a-input-number
                                v-model="form.jobs_permanent"
                                class="w-full"
                                :placeholder="$t('invest.form.enter_permanent_jobs')"
                                size="large" />
                        </a-form-model-item>
                    </div>
                    <div class="grid gap-0 md:gap-6 grid-cols-1 md:grid-cols-2">
                        <a-form-model-item ref="land_plot_is_allocated" :label="$t('invest.form.land_plot_allocated')" prop="land_plot_is_allocated">
                            <a-switch
                                :checked="form.land_plot_is_allocated"
                                size="large"
                                @change="onChange"/>
                        </a-form-model-item>
                        <a-form-model-item ref="land_plot" :label="$t('invest.form.land_plot_area')" prop="land_plot">
                            <a-input-number
                                v-model="form.land_plot"
                                class="w-full"
                                :step="0.01"
                                :placeholder="$t('invest.form.enter_land_plot_area')"
                                size="large" />
                        </a-form-model-item>
                        <a-form-model-item ref="cadaster" :label="$t('invest.form.cadaster_number')" prop="cadaster">
                            <a-input
                                v-model="form.cadaster"
                                :placeholder="$t('invest.form.enter_cadaster_number')"
                                size="large" />
                        </a-form-model-item>
                    </div>
                </div>
                <div class="form_block">
                    <div class="form_block__header">
                        <h3>{{ $t('invest.form.project_documents') }}</h3>
                        <div class="st">{{ $t('invest.form.step', { step: 5 }) }}</div>
                    </div>
                    <div class="form_block__attachments">
                        <a-button
                            class="mt-auto"
                            type="primary"
                            block
                            ghost
                            size="large"
                            @click="openFileModal">
                            {{ $t('invest.form.attach_documents') }}
                        </a-button>
                        <FileAttach 
                            ref="fileAttach"
                            :zIndex="1100"
                            :attachmentFiles="form.attachments"
                            :maxMBSize="50"
                            createFounder
                            :showDeviceUpload="true"
                            :class="form.attachments.length && 'mt-2 mb-5'"
                            class="ml-2" />
                    </div>
                </div>
                <div class="footer_buttons">
                    <a-button type="primary" size="large" :loading="loading" @click="formSubmit()">
                        {{ isEdit ? $t('invest.form.save_invest_project') : $t('invest.form.create_invest_project') }}
                    </a-button>
                    <a-button type="ui" size="large" @click="visible = false">
                        {{ $t('invest.form.cancel') }}
                    </a-button>
                </div>
            </a-form-model>
        </a-spin>
    </a-drawer>
</template>

<script>
import eventBus from '@/utils/eventBus'
import { mapState } from 'vuex'

let binTimer;
const formData = {
    add_project: false,
    attachments: new Array(),
    cadaster: "",
    category: null,
    comment: '',
    company_bin: "",
    company_director_name: "",
    company_name: "",
    company_phone: "",
    country: null,
    date_start: null,
    dead_line: null,
    foreign_investor_info: "",
    funding_source: null,
    funds: "",
    has_documentation: null,
    infrastructure_info: "",
    installation_stage: "",
    jobs_permanent: 0,
    jobs_temporary: 0,
    land_plot: 0,
    land_plot_is_allocated: false,
    location: null,
    measure_unit: null,
    organization: null,
    project: null,
    pasture_quantity: 0,
    plowed_field_quantity: 0,
    project_capacity: "",
    project_name: "",
    questions: "",
    stage: "",
    srok: "",
    subcategory: null,
    work_experience: "",
    funding_sources: [
        {
            key: Date.now(),
            funding_source: null,
            amount: null,
            comment: ''
        }
    ]
}

export default {
    name: 'AddProject',
    components: {
        FileAttach: () => import('@apps/vue2Files/components/FileAttach')
    },
    computed: {
        ...mapState({
            windowWidth: state => state.windowWidth
        }),
        drawerWidth() {
            if(this.windowWidth > 1100)
                return 1100
            else {
                return '100%'
            }
        }
    },
    data() {
        return {
            isEdit: false,
            visible: false,
            rules: {
                category: [{ required: true, message: this.$t('wgr.field_require'), trigger: 'blur' }],
                company_bin: [{ min: 12, max: 12, message: 'Введите 12 символов', trigger: 'blur' }],
                country: [{ required: true, message: this.$t('wgr.field_require'), trigger: 'blur' }],
                date_start: [{ required: true, message: this.$t('wgr.field_require'), trigger: 'change' }],
                dead_line: [{ required: true, message: this.$t('wgr.field_require'), trigger: 'change' }],
                funds: [{ required: true, message: this.$t('wgr.field_require'), trigger: 'blur' }],
                has_documentation: [{ required: true, message: this.$t('wgr.field_require'), trigger: 'blur' }],
                installation_stage: [{ required: true, message: this.$t('wgr.field_require'), trigger: 'blur' }],
                location: [{ required: true, message: this.$t('wgr.field_require'), trigger: 'change' }],
                measure_unit: [{ required: true, message: this.$t('wgr.field_require'), trigger: 'blur' }],
                organization: [{ required: true, message: this.$t('wgr.field_require'), trigger: 'blur' }],
                p_name_equipment: [{ required: true, message: this.$t('wgr.field_require'), trigger: 'blur' }],
                project_capacity: [{ required: true, message: this.$t('wgr.field_require'), trigger: 'blur' }],
                project_name: [{ required: true, message: this.$t('wgr.field_require'), trigger: 'blur' }],
                srok: [{ required: true, message: this.$t('wgr.field_require'), trigger: 'blur' }]
            },
            form: {...formData},
            locationLabel: '',
            locationRegion: null,
            locationRegionList: [],
            locationRegionLoading: false,
            locationDistrict: null,
            locationDistrictList: [],
            locationDistrictLoading: false,
            locationAkimat: null,
            locationAkimatList: [],
            locationAkimatLoading: false,
            locationSettlement: null,
            locationSettlementList: [],
            locationSettlementLoading: false,
            locationVillage: null,
            locationVillageList: [],
            locationVillageLoading: false,
            stageLoading: false,
            organization: {
                results: []
            },
            regionLoading: false,
            orgLoading: false,
            districtLoading: false,
            countryLoading: false,
            sourceLoading: false,
            categoryLoading: false,
            subcategoryLoading: false,
            measureUnitLoading: false,
            loading: false,
            formDataLoading: false,
            binLoading: false,
            fundingSourceList: {
                results: []
            },
            categoryList: {
                results: []
            },
            measureUnitList: {
                results: []
            },
            subcategoryList: {
                results: []
            },
            stageList: {
                results: []
            }
        }
    },
    methods: {
        openFileModal() {
            this.$nextTick(() => {
                this.$refs.fileAttach.openFileModal()
            })
        },
        onChange(checked) {
            this.form.land_plot_is_allocated = checked
        },
        async getSubcategory() {
            if(!this.subcategoryList.results.length) {
                try {
                    this.subcategoryLoading = true
                    const params = {
                        model: "invest_projects_info.InvestProjectSubcategoryModel",
                        filters: {
                            category: this.form.category
                        }
                    }
                    const { data } = await this.$http.get('/app_info/select_list/', {
                        params
                    })
                    if(data?.selectList?.length) {
                        this.subcategoryList.results = data.selectList
                    }
                } catch(e) {
                    console.log(e)
                } finally {
                    this.subcategoryLoading = false
                }
            }
        },
        async getMeasureUnit() {
            if(!this.measureUnitList.results.length) {
                try {
                    this.measureUnitLoading = true
                    const params = {
                        model: "invest_projects_info.InvestProjectMeasureUnitModel"
                    }
                    const { data } = await this.$http.get('/app_info/select_list/', {
                        params
                    })
                    if(data?.selectList?.length) {
                        this.measureUnitList.results = data.selectList
                        if(!this.isEdit)
                            this.form.measure_unit = data.selectList[0].code
                    }
                } catch(e) {
                    console.log(e)
                } finally {
                    this.measureUnitLoading = false
                }
            } else
                this.form.measure_unit = this.measureUnitList.results[0].code
        },
        async getOrganization() {
            if(!this.organization.results.length) {
                try {
                    this.orgLoading = true
                    const params = {
                        permission_type: "create_invest_projects_info"
                    }
                    const { data } = await this.$http.get('/contractor_permissions/organizations', {
                        params
                    })
                    if(data?.length) {
                        this.organization.results = data
                        if(!this.isEdit)
                            this.form.organization = data[0].id
                    }
                } catch(e) {
                    console.log(e)
                } finally {
                    this.orgLoading = false
                }
            }
        },
        async getCategory() {
            if(!this.categoryList.results.length) {
                try {
                    this.categoryLoading = true
                    const params = {
                        model: "invest_projects_info.InvestProjectCategoryModel"
                    }
                    const { data } = await this.$http.get('/app_info/select_list/', {
                        params
                    })
                    if(data?.selectList?.length) {
                        this.categoryList.results = data.selectList
                    }
                } catch(e) {
                    console.log(e)
                } finally {
                    this.categoryLoading = false
                }
            }
        },
        filterOption(input, option) {
            return (
                option.componentOptions.children[0].text.toLowerCase().indexOf(input.toLowerCase()) >= 0
            )
        },
        formSubmit() {
            this.$refs['investForm'].validate(async valid => {
                if (valid) {
                    try {
                        this.loading = true
                        const formData = {...this.form}
                        formData.has_documentation = formData.has_documentation === 'true'
                        if(formData.attachments.length) {
                            formData.attachments = formData.attachments.map(each => each.id)
                        }
                        if(this.isEdit) {
                            delete formData.author
                            const { data } = await this.$http.put(`/invest_projects_info/${formData.id}/`, formData)
                            if(data) {
                                this.visible = false
                                this.$message.success(this.$t('invest.form_submit.success_message'))
                                eventBus.$emit('update_invest_full_project', data)
                                eventBus.$emit('update_actualization_form', data)
                                eventBus.$emit('update_price_chart')
                            }
                        } else {
                            const { data } = await this.$http.post('/invest_projects_info/', formData)
                            if(data) {
                                this.visible = false
                                this.$message.success(this.$t('invest.form_submit.success_created'))
                                eventBus.$emit('update_invest_list')
                                eventBus.$emit('update_invest_project_statistic')
                            }
                        }
                    } catch(error) {
                        console.log(error)
                        this.$message.error(this.$t('invest.form_submit.error_message'))
                    } finally{
                        this.loading = false
                    }
                } else
                    return false
            })
        },
        removeSource(index) {
            this.form.funding_sources.splice(index, 1)
        },
        addSource() {
            this.form.funding_sources.push({
                key: Date.now(),
                funding_source: null,
                amount: null,
                comment: ''
            })
        },
        binChange(e) {
            clearTimeout(binTimer)
            binTimer = setTimeout(async () => {
                const bin = e.target.value
                if(bin.length === 12) {
                    try {
                        this.binLoading = true
                        const { data } = await this.$http.get('/catalogs/contractor_from_egov/', {
                            params: {
                                bin
                            }
                        })
                        if(data?.success && data.obj) {
                            if(data.obj.fio)
                                this.form.company_director_name = data.obj.fio
                            if(data.obj.name)
                                this.form.company_name = data.obj.name
                        }
                    } catch(e) {
                        console.log(e)
                    } finally {
                        this.binLoading = false
                    }
                }
            }, 300)
        },
        afterVisibleChange(vis) {
            if(!vis) {
                this.form = {...formData}
                this.form.attachments = new Array()
                this.form.funding_sources = [
                    {
                        key: Date.now(),
                        funding_source: null,
                        amount: null,
                        comment: ''
                    }
                ]
                this.organization.results = []
                this.categoryList.results = []
                this.measureUnitList.results = []
                this.subcategoryList.results = []
                this.stageList.results = []
                this.locationLabel = ''
                this.locationRegion = null
                this.locationRegionList = []
                this.locationDistrict = null
                this.locationDistrictList = []
                this.locationAkimat = null
                this.locationAkimatList = []
                this.locationSettlement = null
                this.locationSettlementList = []
                this.locationVillage = null
                this.locationVillageList = []
                this.fundingSourceList.results = []
                this.isEdit = false
            } else {
                this.getCategory()
                this.getOrganization()
                this.getMeasureUnit()
            }
        },
        categoryChange() {
            this.form.subcategory = null
            this.subcategoryList = {
                results: []
            }
            this.getSubcategory()
        },
        locationRegionOpenSelect(vis) {
            if(vis)
                this.getLocationRegions()
        },
        stageOpenSelect(vis) {
            if(vis)
                this.getProjectStages()
        },
        locationRegionChange() {
            this.form.location = this.locationRegion
            this.setLocationLabel('region')
            this.locationDistrict = null
            this.locationDistrictList = []
            this.locationAkimat = null
            this.locationAkimatList = []
            this.locationSettlement = null
            this.locationSettlementList = []
            this.locationVillage = null
            this.locationVillageList = []
        },
        locationDistrictOpenSelect(vis) {
            if(vis)
                this.getLocationDistricts()
        },
        locationDistrictChange(val) {
            val ? this.setLocationLabel('district') : this.setLocationLabel('region')
            this.form.location = this.locationDistrict
            this.locationAkimat = null
            this.locationAkimatList = []
            this.locationSettlement = null
            this.locationSettlementList = []
            this.locationVillage = null
            this.locationVillageList = []
        },
        locationAkimatOpenSelect(vis) {
            if(vis)
                this.getLocationAkimats()
        },
        locationAkimatChange(val) {
            val ? this.setLocationLabel('akimat') : this.setLocationLabel('district')
            this.form.location = this.locationAkimat
            this.locationSettlement = null
            this.locationSettlementList = []
            this.locationVillage = null
            this.locationVillageList = []
        },
        locationSettlementOpenSelect(vis) {
            if(vis)
                this.getLocationSettlements()
        },
        locationSettlementChange(val) {
            val ? this.setLocationLabel('settlement') : this.setLocationLabel('akimat')
            this.form.location = this.locationSettlement
            this.locationVillage = null
            this.locationVillageList = []
        },
        locationVillageOpenSelect(vis) {
            if(vis)
                this.getLocationVillages()
        },
        locationVillageChange(val) {
            val ? this.setLocationLabel('village') : this.setLocationLabel('settlement')
            this.form.location = this.locationVillage
        },
        setLocationLabel(location) {
            let loc = null
            switch(location) {
            case 'region':
                loc = this.locationRegionList.find(item => item.id === this.locationRegion)
                break
            case 'district':
                loc = this.locationDistrictList.find(item => item.id === this.locationDistrict)
                break
            case 'akimat':
                loc = this.locationAkimatList.find(item => item.id === this.locationAkimat)
                break
            case 'settlement':
                loc = this.locationSettlementList.find(item => item.id === this.locationSettlement)
                break
            case 'village':
                loc = this.locationVillageList.find(item => item.id === this.locationVillage)
                break
            }
            this.locationLabel = loc ? `${loc.code} - ${loc.full_name}` : ''
        },
        sourceOpenSelect(vis) {
            if(vis)
                this.getFundingSourcesList()
        },
        async getProjectStages() {
            if(!this.stageList.results.length) {
                try {
                    this.stageLoading = true
                    const params = {
                        model: "invest_projects_info.InvestProjectStageModel"
                    }
                    const { data } = await this.$http.get('/app_info/select_list/', {
                        params
                    })
                    if(data?.selectList?.length) {
                        this.stageList.results = data.selectList
                    }
                } catch(e) {
                    console.log(e)
                } finally {
                    this.stageLoading = false
                }
            }
        },
        async getLocations(parent) {
            try {
                const { data } = await this.$http.get('/accounting_catalogs/locations/', { params: { parent: parent } })
                if(data) {
                    return data
                }
            } catch(error) {
                console.log(error)
            }
        },
        async getLocationRegions() {
            if(this.locationRegionList.length !== 0 && !this.isEdit) 
                return
            this.locationRegionLoading = true
            try {
                const { data } = await this.$http.get('/accounting_catalogs/locations/', { params: { parent: 'root' } })
                if(data.length !== 0) {
                    this.locationRegionList = data
                }
            } catch(error) {
                console.log(error)
            } finally {
                this.locationRegionLoading = false
            }
        },
        async getLocationDistricts() {
            if(this.locationDistrictList.length !== 0 && !this.isEdit) 
                return
            this.locationDistrictLoading = true
            try {
                const response = await this.getLocations(this.locationRegion)
                if(response.length !== 0) {
                    this.locationDistrictList = response
                }
            } catch(error) {
                console.log(error)
            } finally {
                this.locationDistrictLoading = false
            }
        },
        async getLocationAkimats() {
            if(this.locationAkimatList.length !== 0 && !this.isEdit) 
                return
            this.locationAkimatLoading = true
            try {
                const response = await this.getLocations(this.locationDistrict)
                if(response.length !== 0) {
                    this.locationAkimatList = response
                }
            } catch(error) {
                console.log(error)
            } finally {
                this.locationAkimatLoading = false
            }
        },
        async getLocationSettlements() {
            if(this.locationSettlementList.length !== 0 && !this.isEdit) 
                return
            this.locationSettlementLoading = true
            try {
                const response = await this.getLocations(this.locationAkimat)
                if(response.length !== 0) {
                    this.locationSettlementList = response
                }
            } catch(error) {
                console.log(error)
            } finally {
                this.locationSettlementLoading = false
            }
        },
        async getLocationVillages() {
            if(this.locationVillageList.length !== 0 && !this.isEdit) 
                return
            this.locationVillageLoading = true
            try {
                const response = await this.getLocations(this.locationSettlement)
                if(response.length !== 0) {
                    this.locationVillageList = response
                }
            } catch(error) {
                console.log(error)
            } finally {
                this.locationVillageLoading = false
            }
        },
        async getFundingSourcesList() {
            if(!this.fundingSourceList.results.length) {
                try {
                    this.sourceLoading = true
                    const params = {
                        model: "invest_projects_info.InvestProjectFundingSourceModel"
                    }
                    const { data } = await this.$http.get('/app_info/select_list/', {
                        params
                    })
                    if(data?.selectList?.length) {
                        this.fundingSourceList.results = data.selectList
                    }
                } catch(e) {
                    console.log(e)
                } finally {
                    this.sourceLoading = false
                }
            }
        },
        async getLocationStructure(location) {
            try {
                const { data } = await this.$http.get('/invest_projects_info/location_structure', {
                    params: {
                        location: location
                    }
                })
                if(data) {
                    return data
                }
            } catch(error) {
                console.log(error)
            }
        },
        async fillFormFields(injectProject) {
            this.formDataLoading = true
            try {
                const {
                    id,
                    author,
                    category,
                    funding_sources,
                    has_documentation,
                    location,
                    measure_unit,
                    organization,
                    stage,
                    status,
                    subcategory,
                    ...formData
                } = injectProject
                if(id)
                    this.form.id = id
                for (let key in formData) {
                    if (this.form.hasOwnProperty(key)) {
                        this.form[key] = formData[key]
                    }
                }
                if(category && category.id) {
                    this.form.category = category.id
                    await this.categoryChange()
                    if(subcategory && subcategory.id) {
                        this.form.subcategory = subcategory.id
                    }
                }
                if(funding_sources.length) {
                    this.getFundingSourcesList()
                    this.form.funding_sources = funding_sources.map(item => {
                        return {
                            key: item.id,
                            funding_source: item.funding_source.id,
                            amount: item.amount,
                            comment: item.comment
                        }
                    })
                }
                this.form.has_documentation = String(has_documentation)
                if(location && location.id) {
                    const locationStructure = await this.getLocationStructure(location.id)
                    if(locationStructure) {
                        if('region' in locationStructure) {
                            this.locationRegionList.push(locationStructure['region'])
                            this.locationRegion = locationStructure['region'].id
                            this.form.location = locationStructure['region'].id
                            this.setLocationLabel('region')
                        }
                        if('district' in locationStructure) {
                            this.locationDistrictList.push(locationStructure['district'])
                            this.locationDistrict = locationStructure['district'].id
                            this.form.location = locationStructure['district'].id
                            this.setLocationLabel('district')
                        }
                        if('akimat' in locationStructure) {
                            this.locationAkimatList.push(locationStructure['akimat'])
                            this.locationAkimat = locationStructure['akimat'].id
                            this.form.location = locationStructure['akimat'].id
                            this.setLocationLabel('akimat')
                        }
                        if('settlement' in locationStructure) {
                            this.locationSettlementList.push(locationStructure['settlement'])
                            this.locationSettlement = locationStructure['settlement'].id
                            this.form.location = locationStructure['settlement'].id
                            this.setLocationLabel('settlement')
                        }
                        if('village' in locationStructure) {
                            this.locationVillageList.push(locationStructure['village'])
                            this.locationVillage = locationStructure['village'].id
                            this.form.location = locationStructure['village'].id
                            this.setLocationLabel('village')
                        }
                    }
                }
                if(measure_unit && measure_unit.code) {
                    this.form.measure_unit = measure_unit.code
                }
                if(organization && organization.id)
                    this.form.organization = organization.id
                
                if(stage && stage.id) {
                    await this.getProjectStages()
                    this.form.stage = stage.id
                }
            } catch(error) {
                console.log(error)
            } finally {
                this.formDataLoading = false
            }
        }
    },
    mounted(){
        eventBus.$on('add_invest_project', async (injectProject=null) => {
            if(injectProject) {
                this.isEdit = true
                this.fillFormFields(injectProject)
            }
            this.visible = true
        })
    },
    beforeDestroy() {
        eventBus.$off('add_invest_project')
    }
}
</script>

<style lang="scss" scoped>
.equipment_list{
    &__item{
        &:not(:last-child){
            margin-bottom: 20px;
            padding-bottom: 20px;
            border-bottom: 1px solid var(--border2);
        }
    }
}
.funding_sources_list{
    &__item{
        &:not(:last-child){
            margin-bottom: 20px;
            padding-bottom: 20px;
            border-bottom: 1px solid var(--border2);
        }
    }
}
.invest_form{
    .form_block{
        padding: 15px;
        border: 1px solid var(--border2);
        border-radius: var(--borderRadius);
        margin-bottom: 20px;
        @media (min-width: 768px) {
            padding: 30px;
        }
        &__header{
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 20px;
            h3{
                font-size: 20px;
                color: #000000;
                font-weight: 400;
                margin: 0px;
            }
            .st{
                color: #000000;
                font-size: 18px;
                opacity: 0.3;
                padding-left: 15px;
                text-wrap: nowrap;
            }
        }
        &__attachments{
            margin-bottom: 20px;
        }
    }
    .footer_buttons{
        display: flex;
        align-items: center;
        &::v-deep{
            .ant-btn{
                &:not(:last-child){
                    margin-right: 10px;
                }
                &.ant-btn-lg{
                    height: 50px;
                    padding: 0 25px;
                }
            }
        }
    }
}
</style>