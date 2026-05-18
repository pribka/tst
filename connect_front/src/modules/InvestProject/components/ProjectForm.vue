<template>
    <div class="project_form">
        <div class="project_form__wrapper">
            <div class="top">
                <h2>{{ $t('invest.data_update.title') }}</h2>
                <div class="status" :style="`background-color: ${project.status.hex_color}`">
                    {{ $t('invest.status') }}: {{ project.status.name }}
                </div>
            </div>
            <a-form-model
                v-if="actionInfo || viewMode"
                ref="investForm"
                :model="form">
                <div class="form_block">
                    <div class="form_block__header">
                        <h3>{{ $t('invest.main_info2') }}</h3>
                    </div>
                    <div class="grid gap-4 xl:gap-6 grid-cols-1 xl:grid-cols-2">
                        <a-form-model-item 
                            v-if="actionInfo?.stage || viewMode" 
                            ref="stage" 
                            :label="$t('invest.project_stage')" 
                            :rules="{
                                required: false,
                                message: $t('wgr.field_require'),
                                trigger: 'blur',
                            }"
                            prop="stage">
                            <a-select 
                                v-model="form.stage"
                                :placeholder="$t('invest.construction_stage')" 
                                size="large" 
                                class="w-full"
                                :disabled="viewMode"
                                :default-active-first-option="false"
                                :not-found-content="null"
                                :loading="stageLoading">
                                <a-select-option 
                                    v-for="stage in stageList.results" 
                                    :key="stage.id" 
                                    :value="stage.id">
                                    {{ stage?.string_view }}
                                </a-select-option>
                            </a-select>
                        </a-form-model-item>
                        <a-form-model-item  
                            v-if="actionInfo?.installation_stage || viewMode" 
                            ref="installation_stage" 
                            :label="$t('invest.installation_stage')" 
                            :rules="{
                                required: true,
                                message: $t('wgr.field_require'),
                                trigger: 'blur',
                            }"
                            prop="installation_stage">
                            <a-input-number
                                v-model="form.installation_stage"
                                :disabled="viewMode"
                                class="w-full"
                                :min="0"
                                :max="100"
                                :placeholder="$t('invest.installation_stage')" 
                                size="large" />
                        </a-form-model-item>
                    </div>
                    <div class="grid gap-4 xl:gap-6 grid-cols-1 xl:grid-cols-2">
                        <a-form-model-item 
                            v-if="actionInfo?.project_capacity || viewMode" 
                            ref="project_capacity" 
                            :label="$t('invest.project_capacity')" 
                            :rules="{
                                required: true,
                                message: $t('wgr.field_require'),
                                trigger: 'blur',
                            }"
                            prop="project_capacity">
                            <a-input-number
                                v-model="form.project_capacity"
                                :disabled="viewMode"
                                :step="0.01"
                                class="w-full"
                                :placeholder="$t('invest.project_capacity_placeholder')" 
                                size="large" />
                        </a-form-model-item>
                        <a-form-model-item 
                            v-if="actionInfo?.measure_unit || viewMode" 
                            ref="measure_unit" 
                            :label="$t('invest.measure_unit')" 
                            :rules="{
                                required: true,
                                message: $t('wgr.field_require'),
                                trigger: 'blur',
                            }"
                            prop="measure_unit">
                            <a-select 
                                v-model="form.measure_unit"
                                :disabled="viewMode"
                                :placeholder="$t('invest.measure_unit')" 
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
                </div>
                <div class="form_block">
                    <div class="form_block__header">
                        <h3>{{ $t('invest.project_cost') }}</h3>
                    </div>
                    <div class="grid gap-4 xl:gap-6 grid-cols-1 xl:grid-cols-2">
                        <a-form-model-item 
                            v-if="actionInfo?.funds || viewMode" 
                            ref="funds" 
                            :label="$t('invest.total_project_cost2')" 
                            :rules="{
                                required: true,
                                message: $t('wgr.field_require'),
                                trigger: 'blur',
                            }"
                            prop="funds">
                            <a-input-number
                                v-model="form.funds"
                                :disabled="viewMode"
                                :step="0.01"
                                class="w-full"
                                :placeholder="$t('invest.total_project_cost')" 
                                size="large" />
                        </a-form-model-item>
                    </div>
                    <div class="grid gap-4 xl:gap-6 grid-cols-1 xl:grid-cols-2">
                    </div>
                    <div v-if="actionInfo?.funding_sources || viewMode" class="form_block">
                        <div 
                            v-for="(source, index) in form.funding_sources" 
                            :key="source.key"
                            :class="form.funding_sources.length > 1 && 'mb-3'">
                            <div class="equipment_header flex items-center justify-between">
                                <div class="e_label">{{ $t('invest.funding_source') }}</div>
                                <div v-if="form.funding_sources.length > 1">
                                    <a-button :disabled="viewMode" type="link" size="small" @click="removeSource(index)">
                                        {{ $t('invest.remove') }}
                                    </a-button>
                                </div>
                            </div>
                            <div class="grid gap-4 md:gap-0 xl:gap-6 grid-cols-1 xl:grid-cols-2 2xl:grid-cols-2">
                                <div>
                                    <a-form-model-item 
                                        :label="$t('invest.source')" 
                                        :prop="'funding_sources.' + index + '.funding_source'"
                                        :rules="{
                                            required: true,
                                            message: $t('wgr.field_require'),
                                            trigger: 'blur',
                                        }">
                                        <a-select 
                                            v-model="source.funding_source"
                                            :disabled="viewMode"
                                            :placeholder="$t('invest.funding_source_placeholder')" 
                                            size="large" 
                                            class="w-full"
                                            :default-active-first-option="false"
                                            :not-found-content="null"
                                            show-search
                                            :filter-option="filterOption"
                                            :loading="sourceLoading">
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
                                        :label="$t('invest.funding_volume2')" 
                                        :rules="{
                                            required: true,
                                            message: $t('wgr.field_require'),
                                            trigger: 'blur',
                                        }">
                                        <a-input-number
                                            v-model="source.amount"
                                            :disabled="viewMode"
                                            :step="0.01"
                                            class="w-full"
                                            :placeholder="$t('invest.funding_volume_placeholder')" 
                                            size="large" />
                                    </a-form-model-item>
                                </div>
                                <a-form-model-item 
                                    :prop="'funding_sources.' + index + '.comment'"  
                                    :label="$t('invest.comment')"
                                    :rules="{
                                        required: false,
                                        message: $t('wgr.field_require'),
                                        trigger: 'blur',
                                    }">
                                    <a-textarea
                                        v-model="source.comment"
                                        :disabled="viewMode"
                                        class="equipment_textarea"
                                        :placeholder="$t('invest.comment_placeholder')"
                                        :auto-size="{ minRows: 6, maxRows: 6 }" />
                                </a-form-model-item>
                            </div>
                        </div>
                        <a-button :disabled="viewMode" type="default" block size="large" class="mt-1 mb-5" @click="addSource()">
                            {{ $t('invest.add_funding_source') }}
                        </a-button>
                    </div>
                </div>
                <div class="form_block">
                    <div class="form_block__header">
                        <h3>{{ $t('invest.workplaces') }}</h3>
                    </div>
                    <div class="grid gap-4 xl:gap-6 grid-cols-1 xl:grid-cols-2">
                        <a-form-model-item 
                            v-if="actionInfo?.jobs_temporary || viewMode" 
                            ref="jobs_temporary" 
                            :label="$t('invest.temporary')" 
                            :rules="{
                                required: false,
                                message: $t('wgr.field_require'),
                                trigger: 'blur',
                            }"
                            prop="jobs_temporary">
                            <a-input-number
                                v-model="form.jobs_temporary"
                                :disabled="viewMode"
                                class="w-full"
                                :placeholder="$t('invest.temporary_jobs_placeholder')" 
                                size="large" />
                        </a-form-model-item>
                        <a-form-model-item 
                            v-if="actionInfo?.jobs_permanent || viewMode" 
                            ref="jobs_permanent" 
                            :label="$t('invest.permanent')" 
                            :rules="{
                                required: false,
                                message: $t('wgr.field_require'),
                                trigger: 'blur',
                            }"
                            prop="jobs_permanent">
                            <a-input-number
                                v-model="form.jobs_permanent"
                                :disabled="viewMode"
                                class="w-full"
                                :placeholder="$t('invest.permanent_jobs_placeholder')" 
                                size="large" />
                        </a-form-model-item>
                    </div>
                </div>
                <div class="form_block">
                    <div class="form_block__action_buttons">
                        <a-button-group>
                            <a-button
                                v-if="actions?.change_status?.availability && currentStatus"
                                type="primary"
                                size="large"
                                class="md:px-6 lg:px-6"
                                :loading="loading"
                                @click="changeStatus(currentStatus)">
                                {{ currentStatus?.btn_title ? currentStatus.btn_title : currentStatus.name }}
                            </a-button>
                            <a-dropdown type="primary" size="large" placement="topRight" v-if="showActionMenu">
                                <a-button
                                    type="primary"
                                    size="large"
                                    :loading="loading"
                                    flaticon
                                    icon="fi-rr-menu-dots-vertical" />
                                <a-menu slot="overlay">
                                    <template v-if="statusList.length">
                                        <a-menu-item 
                                            v-for="status in statusList"
                                            :key="status.code"
                                            class="flex items-center"
                                            @click="changeStatus(status)">
                                            <a-badge :color="status.color" />
                                            {{ status.btn_title ? status.btn_title : status.name }}
                                        </a-menu-item>
                                    </template>
                                    <template v-if="showActions">
                                        <a-menu-divider />
                                        <a-menu-item 
                                            v-if="showEdit"
                                            key="edit"
                                            class="flex items-center"
                                            @click="editProject()">
                                            <i class="fi fi-rr-edit mr-2"></i>
                                            {{ $t('invest.edit') }}
                                        </a-menu-item>
                                        <a-menu-item 
                                            v-if="showDelete"
                                            key="delete"
                                            class="flex items-center"
                                            @click="deleteProject()">
                                            <i class="fi fi-rr-trash mr-2"></i>
                                            {{ $t('invest.delete') }}
                                        </a-menu-item>
                                    </template>
                                </a-menu>
                            </a-dropdown>
                        </a-button-group>
                        <a-button v-if="actionInfo" type="default" :loading="loading" block size="large" @click="formSubmit()">
                            {{ $t('invest.save_changes') }}
                        </a-button>
                    </div>
                </div>
            </a-form-model>
            <a-skeleton v-else active />
        </div>
    </div>
</template>

<script>
import eventBus from '@/utils/eventBus'
const formData = {
    funds: '',
    installation_stage: '',
    jobs_permanent: '',
    jobs_temporary: '',
    measure_unit: null,
    project_capacity: '',
    questions: '',
    stage: '',
    work_experience: '',
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
    props: {
        project: {
            type: Object,
            default: () => {}
        },
        actionInfo: {
            type: Object,
            default: () => {}
        },
        actions: {
            type: Object,
            default: () => {}
        },
        statusList: {
            type: Array,
            default: () => []
        },
        viewMode: {
            type: Boolean,
            required: true
        }
    },
    data() {
        return {
            countryLoading: false,
            sourceLoading: false,
            stageLoading: false,
            loading: false,
            form: {...formData},
            measureUnitLoading: false,
            measureUnitList: {
                results: []
            },
            fundingSourceList: {
                results: []
            },
            stageList: {
                results: []
            }
        }
    },
    created() {
        this.getMeasureUnit()
        this.getProjectStages()
        this.getFundingSourcesList()
        this.formInit()
    },
    mounted() {
        eventBus.$on('update_actualization_form', (data) => {
            this.formInit(data)
        })
    },
    beforeDestroy() {
        eventBus.$off('update_actualization_form')
    },
    computed: {
        currentStatus() {
            if(!this.statusList.length || !this.project.status.code) return null
            const currentStatus = this.statusList.find(status => status.depends.includes(this.project.status.code))
            return currentStatus ? currentStatus : null
        },
        showActions() {
            return this.showDelete || this.showEdit
        },
        showDelete() {
            return ('delete' in this.actions) && this.actions.delete?.availability
        },
        showEdit() {
            return ('edit' in this.actions) && this.actions.edit?.availability
        },
        showActionMenu() {
            return (('change_status' in this.actions) && this.actions.change_status?.availability) ||
                this.showActions
        }
    },
    methods: {
        formInit(data=null) {
            const formInit = data ? {...data} : {...this.project}
            if(formInit.funding_sources && formInit.funding_sources?.length) {
                formInit.funding_sources = formInit.funding_sources.map(source => {
                    return {
                        ...source,
                        key: source.id,
                        funding_source: source.funding_source.id
                    }
                })
            }
            if(formInit.measure_unit && formInit.measure_unit?.code)
                formInit.measure_unit = formInit.measure_unit.code
            if(formInit.stage && formInit.stage?.id)
                formInit.stage = formInit.stage.id
            this.form = formInit
        },
        editProject() {
            eventBus.$emit('add_invest_project', this.project)
        },
        deleteProject() {
            this.$confirm({
                title: this.$t('invest.delete_project.confirm_title', { project_name: this.project.project_name }),
                content: '',
                okText: this.$t('invest.delete_project.confirm_okText'),
                okType: 'danger',
                zIndex: 2000,
                closable: true,
                maskClosable: true,
                cancelText: this.$t('invest.delete_project.confirm_cancelText'),
                onOk: () => {
                    return new Promise((resolve, reject) => {
                        this.$http.put(`/invest_projects_info/delete/`, { id: this.project.id })
                            .then((data) => {
                                this.$message.info(this.$t('invest.delete_project.success_message', { project_name: this.project.project_name }));
                                this.$router.push({ name: 'invest-project' });
                                eventBus.$emit('update_invest_list');
                                eventBus.$emit('update_invest_project_statistic');
                                eventBus.$emit('reload_filters');
                                resolve();
                            })
                            .catch(e => {
                                console.log(e);
                                this.$message.error(this.$t('invest.delete_project.error_message'));
                                reject(e);
                            })
                            .finally(() => {
                                this.loading = false;
                            });
                    });
                }
            });
        },

        async changeStatus(status) {
            if (!this.actions?.change_status?.availability) {
                return;
            }
            this.loading = true;
            try {
                const { data } = await this.$http.put(`/invest_projects_info/${this.project.id}/update_status/`, {
                    status: status.code
                });
                if (data) {
                    this.$message.success(this.$t('invest.change_status.success_message'));
                    eventBus.$emit('reload_invest_full_project');
                }
            } catch (error) {
                console.log(error);
                this.$message.error(this.$t('invest.change_status.error_message'));
            } finally {
                this.loading = false;
            }
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
                    }
                } catch(e) {
                    console.log(e)
                } finally {
                    this.measureUnitLoading = false
                }
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
        removeSource(index) {
            if(this.viewMode)
                return
            this.form.funding_sources.splice(index, 1)
        },
        addSource() {
            if(this.viewMode)
                return
            this.form.funding_sources.push({
                key: Date.now(),
                funding_source: null,
                amount: null,
                comment: ''
            })
        },
        filterOption(input, option) {
            return (
                option.componentOptions.children[0].text.toLowerCase().indexOf(input.toLowerCase()) >= 0
            )
        },
        formSubmit() {
            if (!this.actionInfo) return;
            this.$refs['investForm'].validate(async valid => {
                if (valid) {
                    try {
                        this.loading = true;
                        const formData = { ...this.form };
                        formData.has_documentation = formData.has_documentation === 'true';
                        if (formData.organization?.id) {
                            formData.organization = formData.organization.id;
                        }
                        if (formData.category?.id) {
                            formData.category = formData.category.id;
                        }
                        if (formData.subcategory?.id) {
                            formData.subcategory = formData.subcategory.id;
                        }
                        if (formData.location?.id) {
                            formData.location = formData.location.id;
                        }
                        if (formData.attachments.length) {
                            formData.attachments = formData.attachments.map(each => each.id);
                        }
                        delete formData.author;

                        const { data } = await this.$http.put(`/invest_projects_info/${formData.id}/`, formData);
                        if (data) {
                            this.$message.success(this.$t('invest.form_submit.success_message'));
                            eventBus.$emit('update_invest_full_project', data);
                            eventBus.$emit('update_price_chart');
                        }
                    } catch (error) {
                        console.log(error);
                        this.$message.error(this.$t('invest.form_submit.error_message'));
                    } finally {
                        this.loading = false;
                    }
                } else {
                    return false;
                }
            });
        }
    }
}
</script>

<style lang="scss" scoped>
.project_form{
    .equipment_header{
        margin-bottom: 10px;
        .e_label{
            font-size: 16px;
            color: #000;
        }
    }
    .equipment_textarea{
        height: 80px!important;
        min-height: 80px!important;
        max-height: 80px!important;
        @media (min-width: 1280px) {
            height: 130px!important;
            min-height: 130px!important;
            max-height: 130px!important;
        }
    }
    &__wrapper{
        border: 1px solid var(--border2);
        border-radius: var(--borderRadius);
        padding: 15px;
        @media (max-width: 767px) {
            background: #fff;
        }
        @media (min-width: 768px) {
            padding: 20px;
        }
        @media (min-width: 1700px) {
            padding: 30px;
        }
        .top{
            display: flex;
            justify-content: space-between;
            .status{
                height: 36px;
                font-size: 13px;
                font-weight: 400;
                line-height: 13px;
                text-align: center;
                color: rgba(255, 255, 255, 1);
                width: max-content;
                padding-left: 20px;
                padding-right: 20px;
                border-radius: 4px;
                display: flex;
                align-items: center;
            }
            h2{
                font-size: 22px;
                color: #000;
                margin-bottom: 15px;
                margin-top: 0px;
                @media (min-width: 768px) {
                    margin-bottom: 30px;
                    font-size: 32px;
                }
            }        
        }
    }
    .form_block{
        &:not(:last-child){
            margin-bottom: 20px;
            border-bottom: 1px solid var(--border2);
            padding-bottom: 10px;
        }
        &__header{
            margin-bottom: 10px;
            h3{
                font-size: 20px;
                margin: 0px;
                font-weight: 400;
            }
        }
        &__action_buttons{
            display: grid;
            grid-template-columns: auto 1fr;
            column-gap: 20px;
        }
    }
}
</style>