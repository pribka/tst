<template>
    <a-drawer
        :title="drawerTitle"
        :visible="visible"
        class="new-consolidation-drawer"
        @close="visible = false"
        destroyOnClose
        :zIndex="zIndex"
        :width="drawerWidth"
        :afterVisibleChange="afterVisibleChange"
        placement="right">
        <div class="drawer_body" ref="consolidationAddBody">
            <a-spin :spinning="consolidationLoading">
                <a-form-model
                    ref="consolidationForm"
                    :model="form"
                    :rules="rules">
                    <div class="wrap">
                        <div v-if="templateEdit" class="step">
                            <div class="template-edit">
                                <a-alert
                                    :message="$t('Attention')"
                                    :description="$t('Deleting a template is an irreversible operation. If you plan to use this template later, you can disable it instead of deleting.')"
                                    type="error"
                                    show-icon >
                                    <template slot="icon">
                                        <a-icon type="exclamation-circle" />
                                    </template>
                                </a-alert>
                                <div class="buttons">
                                    <div class="template-on-off">
                                        <span class="label">{{$t('Template is active')}}</span>
                                        <a-switch
                                            v-model="form.is_template_on"
                                            :loading="statusChanging"
                                            @change="toggleTemplateStatus" />
                                    </div>
                                    <div class="template-delete">
                                        <a-button
                                            size="large"
                                            type="danger"
                                            icon="delete"
                                            @click="deleteTemplate">
                                            {{$t('Delete template')}}
                                        </a-button>
                                    </div>
                                </div>
                            </div>
                        </div>
                        <div class="step">
                            <div class="title">
                                <div class="step-number">{{$t('step')}} 1</div>
                                <div class="step-title">{{$t('Participants')}}</div>
                                <div class="step-description">{{$t('Specify organizations that will participate in report formation and consolidation')}}</div>
                            </div>
                            <div class="form-wrap">
                                <div class="step-one-form">
                                    <div class="org-administrator">
                                        <a-form-model-item ref="org_administrator" :label="$t('Administrator organization')" prop="org_administrator" class="">
                                            <a-select
                                                v-model="form.org_administrator"
                                                size="large"
                                                :disabled="orgSelectIsDisabled"
                                                :getPopupContainer="trigger => trigger.parentElement"
                                                :loading="myOrganizationsLoading"
                                                :placeholder="$t('Administrator organization')">
                                                <a-select-option v-for="org in myOrganizations" :key="org.id" :value="org.id">
                                                    <div class="ogr-name">{{ org.name }}</div>
                                                </a-select-option>
                                            </a-select>
                                        </a-form-model-item>
                                    </div>
                                    <div class="add-to-members">
                                        <div class="switcher ant-form-item inline-block align-middle">
                                            <span class="label">{{$t('Add to participants list')}}</span>
                                            <span class="switch">
                                                <a-switch
                                                    v-model="form.add_org_administrator_in_members"
                                                    :disabled="addToMembersSwitchIsDisabled"/>
                                            </span>
                                        </div>
                                    </div>
                                    <div class="members-list">
                                        <a-form-model-item ref="members" :label="$t('Organizations')" prop="members" class="">
                                            <a-select
                                                v-model="form.members"
                                                mode="multiple"
                                                :maxTagCount="1"
                                                size="large"
                                                :getPopupContainer="trigger => trigger.parentElement"
                                                :loading="membersListLoading"
                                                :disabled="membersListIsDisabled"
                                                :placeholder="$t('Participant organizations')"
                                                option-label-prop>
                                                <a-select-option
                                                    v-for="item in members"
                                                    :key="item.id"
                                                    :value="item.id"
                                                    :label="item.name">
                                                    <span class="member-name">{{ item.name }}</span>
                                                </a-select-option>
                                            </a-select>
                                        </a-form-model-item>
                                    </div>
                                </div>
                            </div>
                        </div>
                        <div class="step">
                            <div class="title">
                                <div class="step-number">{{$t('step')}} 2</div>
                                <div class="step-title">{{$t('Reports')}}</div>
                                <div class="step-description">{{$t('Select a report form for consolidation from the list')}}</div>
                            </div>
                            <div class="form-wrap">
                                <div class="step-two-form">
                                    <div class="report-form">
                                        <a-form-model-item ref="report_form" :label="$t('Report form')" prop="report_form" class="w-full">
                                            <a-select
                                                v-model="form.report_form"
                                                size="large"
                                                :getPopupContainer="trigger => trigger.parentElement"
                                                :loading="reportFormsLoading"
                                                :disabled="reportFormSelectIsDisabled"
                                                @change="reportFormIsChange"
                                                :placeholder="$t('Select report form')">
                                                <a-select-option v-for="rForm in reportForms" :key="rForm.id" :value="rForm.id">
                                                    {{ rForm.name }}
                                                </a-select-option>
                                            </a-select>
                                        </a-form-model-item>
                                    </div>
                                    <div class="options">
                                        <div class="auto-approve">
                                            <span class="label">{{$t('Auto approval of reports')}}</span>
                                            <a-switch
                                                v-model="form.auto_approve"
                                                :disabled="autoApproveSwitchIsDisabled" />
                                        </div>
                                        <!--<div v-if="useInquiriesModuleIsPossible" class="use-inquiries-module-data">
                                            <span class="label">Использовать данные модуля "Обращения"</span>
                                            <a-switch
                                                v-model="form.generate_report_files"
                                                :disabled="useInquiriesModuleDataIsDisabled" />
                                        </div>-->
                                    </div>
                                    <div v-if="isIPFProposal" class="ipf-proposal-extra">
                                        <a-form-model-item ref="ipfProposalSubtype" :label="$t('Application type')" prop="ipf_proposal_subtype">
                                            <a-radio-group
                                                name="radioGroup"
                                                v-model="form.ipf_proposal_subtype"
                                                :disabled="ipfProposalSubtypeRadioGroupIsDisabled">
                                                <a-radio v-for="item in ipfProposalSubtypes" :key="item.id" :value="item.id">
                                                    <span>{{ item.name }}</span>
                                                </a-radio>
                                            </a-radio-group>
                                        </a-form-model-item>

                                        <div class="date-and-number">
                                            <a-form-model-item ref="ipfProposalDate" :label="$t('Report creation date')" prop="ipf_proposal_date">
                                                <a-date-picker
                                                    v-model="form.ipf_proposal_date"
                                                    :getPopupContainer="trigger => trigger.parentElement"
                                                    :disabled="ipfProposalSubtypeDatePickerIsDisabled"
                                                    :placeholder="$t('Select date')"
                                                    format="DD.MM.YYYY"
                                                    class="w-full"
                                                    size="large" />
                                            </a-form-model-item>

                                            <a-form-model-item ref="ipfProposalNumber" :label="$t('Document number in your accounting system')" prop="ipf_proposal_number">
                                                <a-input
                                                    size="large"
                                                    :maxLength="31"
                                                    v-model="form.ipf_proposal_number"
                                                    :disabled="ipfProposalSubtypeInputIsDisabled"
                                                    :placeholder="$t('Enter the document number in your accounting system')" />
                                            </a-form-model-item>                                        </div>
                                    </div>
                                    <template v-if="templateEdit">
                                        <div class="ant-col ant-form-item-label">
                                            {{$t('Description')}}:
                                        </div>
                                        <div v-if="form.description" >
                                            <TextViewer
                                                :body="form.description"/>
                                        </div>
                                        <div v-else class="text-gray-300" >
                                            {{$t('Absent')}}
                                        </div>
                                        <div v-if="form.attachments.length">
                                            <div class="ant-col ant-form-item-label attachments-label">{{$t('Attached files')}}:</div>
                                            <div class="attachment_files">
                                                <CommentFile
                                                    v-for="file in form.attachments"
                                                    :key="file.id"
                                                    :file="file"
                                                    :id="form.id" />
                                            </div>
                                        </div>
                                    </template>
                                    <template v-else>
                                        <div class="description">
                                            <a-form-model-item ref="description" :label="$t('Description')" prop="description">
                                                <div class="editor">
                                                    <Editor 
                                                        v-model="form.description"
                                                        ref="editor"
                                                        commentEditor />
                                                </div>
                                                <div class="attachments-btn">
                                                    <a-button @click="openFileModal">{{$t('Attach files')}}</a-button>
                                                </div>
                                            </a-form-model-item>
                                        </div>
                                        <div class="attachments">
                                            <div v-if="form?.attachments.length" class="label">{{$t('Attached files')}}:</div>
                                            <FileAttach 
                                                ref="fileAttach"
                                                :zIndex="1100"
                                                :attachmentFiles="form.attachments"
                                                :maxMBSize="50"
                                                createFounder
                                                :getModalContainer="getPopupContainer"
                                                :class="form.attachments.length && 'mt-2 mb-5'"
                                                class="ml-2" />
                                        </div>
                                    </template>
                                </div>
                            </div>
                        </div>
                        <div class="step">
                            <div class="title">
                                <div class="step-number">{{$t('step')}} 3</div>
                                <div class="step-title">{{$t('Planning')}}</div>
                                <div class="step-description">{{$t('Specify the reporting period and report submission deadline')}}</div>
                            </div>
                            <div class="form-wrap">
                                <div class="step-three-form">
                                    <template v-if="isNarrowScreen">
                                        <div class="start">
                                            <a-form-model-item ref="start" :label="$t('Period start')" prop="start">
                                                <a-date-picker
                                                    v-model="form.start"
                                                    :getPopupContainer="trigger => trigger.parentElement"
                                                    :disabled="rangePickerIsDisabled"
                                                    placeholder="Выберите дату"
                                                    format="DD.MM.YYYY"
                                                    class="w-full"
                                                    size="large" />
                                            </a-form-model-item>
                                        </div>
                                        <div class="end">
                                            <a-form-model-item ref="end" :label="$t('Period end')" prop="end">
                                                <a-date-picker
                                                    v-model="form.end"
                                                    :getPopupContainer="trigger => trigger.parentElement"
                                                    :disabled="rangePickerIsDisabled"
                                                    placeholder="Выберите дату"
                                                    format="DD.MM.YYYY"
                                                    class="w-full"
                                                    size="large" />
                                            </a-form-model-item>
                                        </div>
                                    </template>
                                    <div v-else class="range">
                                        <a-form-model-item ref="range" :label="$t('Period')" prop="range">
                                            <a-range-picker
                                                v-model="form.range"
                                                :getPopupContainer="trigger => trigger.parentElement"
                                                :ranges="ranges"
                                                :disabled="rangePickerIsDisabled"
                                                format="DD.MM.YYYY"
                                                class="w-full"
                                                size="large"
                                                :placeholder=rangePlaceholder
                                                :allowClear="false"
                                                @change="onRangeChange" />
                                        </a-form-model-item>
                                    </div>
                                    <div class="deadline" :class="{'grid-column-span-2' : isNarrowScreen}">
                                        <a-form-model-item ref="dead_line" :label="$t('Report submission deadline')" prop="dead_line" class="w-full">
                                            <a-date-picker
                                                v-model="form.dead_line"
                                                :getPopupContainer="trigger => trigger.parentElement"
                                                :disabled="deadlineDatePickerIsDisabled"
                                                placeholder="Выберите дату"
                                                format="DD.MM.YYYY"
                                                class="w-full"
                                                size="large" />
                                        </a-form-model-item>
                                    </div>
                                </div>
                            </div>
                        </div>
                        <div class="step">
                            <div class="title">
                                <div class="step-number">{{$t('step')}} 4</div>
                                <div class="step-title">{{$t('Repetition')}}</div>
                                <div class="step-description">{{$t('Configure consolidation template parameters')}}</div>
                            </div>
                            <div class="form-wrap">
                                <div class="step-four-form">
                                    <div class="repeat-switcher">
                                        <span class="label">{{ $t('Repeat consolidation') }}</span>
                                        <a-switch
                                            v-model="form.is_scheduled"
                                            :disabled="repeatSwitcherIsDisabled"
                                            @change="isScheduledOnChange" />
                                    </div>

                                    <div class="repeat-period">
                                        <a-form-model-item ref="repeat_period" label="Повторять через" prop="repeat_period">
                                            <a-select
                                                v-model="form.repeat_period"
                                                size="large"
                                                :disabled="repeatPeriodSelectIsDisabled"
                                                :getPopupContainer="trigger => trigger.parentElement">
                                                <a-select-option v-for="item, index in repetitions" :value="item.value" :key="index">
                                                    {{ item.name }}
                                                </a-select-option>
                                            </a-select>
                                        </a-form-model-item>
                                    </div>
                                    <div class="start-data">
                                        <a-form-model-item ref="start_data" label="Дата начала" prop="start_data">
                                            <a-date-picker
                                                v-model="nextCreationDateInfo"
                                                disabled
                                                :getPopupContainer="trigger => trigger.parentElement"
                                                placeholder=""
                                                format="DD.MM.YYYY"
                                                class="w-full"
                                                size="large" />
                                        </a-form-model-item>
                                    </div>
                                    <div class="end-data">
                                        <a-form-model-item ref="repeat_to" label="Дата завершения" prop="repeat_to">
                                            <a-date-picker
                                                v-model="form.repeat_to"
                                                :disabled="endDatePickerIsDisabled"
                                                :getPopupContainer="trigger => trigger.parentElement"
                                                placeholder="Выберите дату"
                                                format="DD.MM.YYYY"
                                                class="w-full"
                                                size="large" />
                                        </a-form-model-item>
                                    </div>
                                    <div v-if="repeatInfo" class="repeat-info">
                                        <a-alert
                                            :description="repeatInfo"
                                            type="info"
                                            show-icon />
                                    </div>
                                </div>
                            </div>
                        </div>
                        <div class="buttons">
                            <a-button 
                                type="primary"
                                class="add-button"
                                :loading="loading"
                                @click="formSubmit()">
                                {{ submitButtonText }}
                            </a-button>
                            <a-button 
                                type="ui"
                                class="cancel-button"
                                @click="visible = false">
                                {{ $t('Cancel') }}
                            </a-button>
                        </div>
                    </div>
                </a-form-model>
            </a-spin>
        </div>
    </a-drawer>
</template>

<script>
import eventBus from '@/utils/eventBus'
export default {
    name: 'CreateConsolidation',
    components: {
        CommentFile: () => import('@apps/vue2CommentsComponent/CommentFIle.vue'),
        Editor: () => import('@apps/CKEditor/index.vue'),
        FileAttach: () => import('@apps/vue2Files/components/FileAttach'),
        TextViewer: () => import('@apps/CKEditor/TextViewer.vue')
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
    watch: {
        'form.org_administrator': {
            handler: async function(val) {
                if(val) {
                    this.getMembers(val)
                    this.getReportForms(val).then(() => {
                        if(this.isIPFProposal)
                            this.getIpfProposalSubtypes()
                    })
                }
            }
        }
    },
    computed: {
        orgSelectIsDisabled() {
            return this.templateEdit
        },
        addToMembersSwitchIsDisabled() {
            return this.templateEdit
        },
        membersListIsDisabled() {
            return !this.members.length || this.templateEdit
        },
        reportFormSelectIsDisabled() {
            return !this.form.org_administrator || this.reportForms.length === 0 || this.templateEdit
        },
        autoApproveSwitchIsDisabled() {
            return this.templateEdit
        },
        ipfProposalSubtypeRadioGroupIsDisabled() {
            return this.templateEdit
        },
        ipfProposalSubtypeDatePickerIsDisabled() {
            return this.templateEdit
        },
        ipfProposalSubtypeInputIsDisabled() {
            return this.templateEdit
        },
        rangePickerIsDisabled() {
            return this.templateEdit
        },
        deadlineDatePickerIsDisabled() {
            return this.templateEdit
        },
        repeatSwitcherIsDisabled() {
            return this.templateEdit
        },
        repeatPeriodSelectIsDisabled() {
            return this.templateEdit
        },
        useInquiriesModuleDataIsDisabled() {
            return this.templateEdit
        },
        endDatePickerIsDisabled() {
            return !this.form.is_scheduled || this.templateEdit
        },
        drawerTitle() {
            if(this.templateEdit) {
                return this.$t('View template')
            } else if(this.edit) {
                return this.$t('Edit consolidation')
            } else {
                return this.$t('Add consolidation')
            }
        },
        windowWidth() {
            return this.$store.state.windowWidth
        },
        isMobile() {
            return this.$store.state.isMobile
        },
        isNarrowScreen() {
            return this.windowWidth < 700
        },
        useInquiriesModuleIsPossible() {
            if(this.form.report_form) {
                const index = this.reportForms.findIndex(item => item.id === this.form.report_form)
                if(index !== -1) {
                    return ['f2go', ].includes(this.reportForms[index].code)
                }
            }
            return false
        },
        drawerWidth() {
            if(this.windowWidth > 1200)
                return 1107
            else if(this.windowWidth <= 1200 && this.windowWidth > 700) {
                return '95%'
            } else {
                return '100%'
            }
        },
        ranges() {
            return { 
                [this.$t('Current month')]: [
                    this.$moment().startOf('month'),
                    this.$moment().endOf('month')
                ],
                [this.$t('Previous month')]: [
                    this.$moment().subtract(1, 'months').startOf('month'),
                    this.$moment().subtract(1, 'months').endOf('month')
                ],
                [this.$t('Current quarter')]: [
                    this.$moment().startOf('quarter'),
                    this.$moment().endOf('quarter')
                ],
                [this.$t('Previous quarter')]: [
                    this.$moment().subtract(3, 'months').startOf('quarter'),
                    this.$moment().subtract(3, 'months').endOf('quarter')
                ],
                [this.$t('From the beginning of the year to the end of the previous month')]: [
                    this.$moment().startOf('year'),
                    this.$moment().subtract(1, 'months').endOf('month')
                ],
                [this.$t('Previous year')]: [
                    this.$moment().subtract(1, 'year').startOf('year'),
                    this.$moment().subtract(1, 'year').endOf('year')
                ],
            }
        },
        submitButtonText() {
            return this.edit
                ? this.$t('Save report')
                : this.$t('Add report')
        },
        repeatInfo() {
            let text = '', next_creation_date, next_dead_line
            if (this.form.is_scheduled && this.form.dead_line) {
                [next_creation_date, next_dead_line] = this.getNextDates()
                text = this.$t(
                    'The next consolidation will be created on {date}, the report submission deadline is {deadline}',
                    { date: next_creation_date, deadline: next_dead_line }
                )
            }
            return text
        },

        rules() {
            const rules = {
                report_form: [
                    { required: true, message: this.$t('Required field'), trigger: 'change' }
                ],
                org_administrator: [
                    { required: true, message: this.$t('Required field'), trigger: 'blur' }
                ],
                dead_line: [
                    { required: true, message: this.$t('Required field'), trigger: 'change' }
                ],
                members: [
                    { required: true, message: this.$t('Required field'), trigger: 'blur' }
                ],
                repeat_to: [
                    { required: false, message: this.$t('Required field'), trigger: 'change' }
                ],
            }

            if (this.windowWidth < 700) {
                rules.start = [
                    { required: true, message: this.$t('Required field'), trigger: 'change' }
                ]
                rules.end = [
                    { required: true, message: this.$t('Required field'), trigger: 'change' }
                ]
            } else {
                rules.range = [
                    { required: true, message: this.$t('Required field'), trigger: 'change' },
                    { type: 'array', min: 2, message: this.$t('Select at least two dates'), trigger: 'change' },
                ]
            }

            if (this.isIPFProposal) {
                rules.ipf_proposal_subtype = [
                    { required: true, message: this.$t('Required field'), trigger: 'change' }
                ]
            }

            return rules
        },

        isIPFProposal() {
            const index = this.reportForms.findIndex(reportForm => reportForm.id === this.form.report_form)
            return index === -1 ? false : this.reportForms[index].code === 'ipf_proposal'
        }
    },
    data() {
        return {
            actions: null,
            consolidationLoading: false,
            delLoading: false,
            edit: false,
            empty: false,
            loading: false,
            members: [],
            membersListLoading: false,
            myOrganizations: [],
            myOrganizationsLoading: false,
            nextCreationDateInfo: null,
            rangePlaceholder: [
                this.$t('Period start'),
                this.$t('Period end')
            ],            
            reportForms: [],
            ipfProposalSubtypes: [],
            ipfProposalSubtypesLoading: false,
            reportFormsLoading: false,
            report_forms: [],
            templateEdit: false,
            statusChanging: false,
            visible: false,
            form: {
                add_org_administrator_in_members: true,
                is_scheduled: false,
                attachments: [],
                auto_approve: false,
                dead_line: null,
                description: '',
                end: null,
                members: [],
                name: '',
                org_administrator: null,
                range: [],
                repeat_period: 'MONTHLY',
                repeat_to: null,
                report_form: null,
                start: null,
                generate_report_files: false,
                ipf_proposal_subtype: null,
                ipf_proposal_date: null,
                ipf_proposal_number: null
            },
            repetitions: [
                {
                    name: this.$t('Week'),
                    value: 'WEEKLY'
                },
                {
                    name: this.$t('Month'),
                    value: 'MONTHLY'
                },
                {
                    name: this.$t('Year'),
                    value: 'YEARLY'
                },
            ],
        }
    },
    created() {
        eventBus.$on('create_consolidation', () => {
            this.visible = true
        })
        eventBus.$on('edit_consolidation', (id) => {
            this.edit = true
            this.getConsolidation(id)
            this.visible = true
        })
        eventBus.$on('view_template', (id) => {
            this.edit = true
            this.templateEdit = true
            this.getConsolidation(id)
            this.visible = true
        })
    },
    methods: {
        async toggleTemplateStatus(val) {
            this.statusChanging = true
            const payload = {
                is_template_on: val
            }
            this.$http.put(`/consolidation/${this.form.id}/set_template_status/`, payload)
                .then(response => {
                    this.$message.success(response.data.message)
                    eventBus.$emit('update_status', this.form.id, 'is_template_on', val)
                })
                .catch(e => {
                    this.form.is_template_on = !val
                    console.log(e)
                    this.$message.error(
                        e?.message ? e.message : this.$t('Status change error')
                    )
                })
                .finally(() => {
                    this.statusChanging = false
                })
        },
        deleteTemplate() {
            this.$confirm({
                title: this.$t('Do you really want to delete the template "{name}"?', { name: this.form.name }),
                content: '',
                okText: this.$t('Delete'),
                okType: 'danger',
                zIndex: 2000,
                closable: true,
                maskClosable: true,
                cancelText: this.$t('Close'),
                onOk: () => {
                    return new Promise((resolve, reject) => {
                        this.$http.post(`/consolidation/${this.form.id}/delete/`)
                            .then(() => {
                                this.$message.success(this.$t('Template deleted'))
                                eventBus.$emit('consolidation_list_reload')
                                this.visible = false
                                resolve()
                            })
                            .catch(e => {
                                console.log(e)
                                this.$message.error(e[0] ? e[0] : this.$t('Deletion error'))
                                reject(e)
                            })
                    })
                }
            })
        },
        getNextDates() {
            const timeDelta = {
                WEEKLY: 'weeks',
                MONTHLY: 'months',
                YEARLY: 'year'
            }

            const delta = timeDelta[this.form.repeat_period]
            let next_creation_date, next_dead_line
            
            if(this.form.repeat_period === 'WEEKLY') {
                next_creation_date = this.$moment().add(1, delta).startOf('week').format('DD.MM.YYYY')
            } else if(this.form.repeat_period === 'MONTHLY') {
                next_creation_date = this.$moment().add(1, delta).startOf('month').format('DD.MM.YYYY')
            } else if(this.form.repeat_period === 'YEARLY') {
                next_creation_date = this.$moment().add(1, delta).startOf('year').format('DD.MM.YYYY')
            }
            this.nextCreationDateInfo = this.$moment(next_creation_date, 'DD.MM.YYYY')
            

            if(['MONTHLY', 'YEARLY'].includes(this.form.repeat_period) && this.isLastDayOfMonth(this.form.dead_line)) {
                next_dead_line = this.$moment(this.form.dead_line).add(1, delta).endOf('month').format('DD.MM.YYYY')
            } else {
                next_dead_line = this.$moment(this.form.dead_line).add(1, delta).format('DD.MM.YYYY')
            }

            return [next_creation_date, next_dead_line]
        },
        isLastDayOfMonth(date) {
            let endOfMonth = this.$moment(date).endOf('month');
            return this.$moment(date).isSame(endOfMonth, 'day');
        },
        isScheduledOnChange(checked) {
            if(checked) {
                this.rules.repeat_to[0].required = true
            } else {
                this.rules.repeat_to[0].required = false
            }
        },
        reportFormIsChange(value) {
            let repForm
            const index = this.reportForms.findIndex(rf => rf.id === value)
            if(index !== -1) {
                repForm = this.reportForms[index]
            }
            if(repForm) {
                this.form.description = repForm.description
                this.form.attachments = repForm.attachments
            }
            if(this.isIPFProposal) {
                this.getIpfProposalSubtypes()
            }
        },
        async getIpfProposalSubtypes() {
            if(!this.ipfProposalSubtypesLoading && !this.ipfProposalSubtypes.length) {
                this.ipfProposalSubtypesLoading = true
                try {
                    const { data } = await this.$http.get('/accounting_reports/get_report_subtypes')
                    if(data.length) {
                        this.ipfProposalSubtypes = data
                        if((!this.edit && this.ipfProposalSubtypes)) {
                            const index = this.ipfProposalSubtypes.findIndex(item => item.code === 'current')
                            if(index !== -1) {
                                return this.form.ipf_proposal_subtype = this.ipfProposalSubtypes[index].id
                            }
                        }
                    }
                } catch(e) {
                    console.log(e)
                } finally {
                    this.ipfProposalSubtypesLoading = false
                }
            }
        },
        openFileModal() {
            this.$nextTick(() => {
                this.$refs.fileAttach.openFileModal()
            })
        },
        extractMembersFromRelations(relations) {
            return relations.map(obj => obj['contractor'])
        },
        async getMembers(org_administrator) {
            this.members = []
            if(!this.edit)
                this.form.members = []
            if(!this.membersListLoading) {
                try {
                    this.membersListLoading = true
                    const params = {
                        page_size: 'all'
                    }
                    const { data } = await this.$http.get(`/users/my_organizations/${org_administrator}/relations/`, {
                        params
                    })
                    if(data.results.length) {
                        this.empty = false
                        if(this.edit) {
                            this.members = this.extractMembersFromRelations(data.results)
                        } else {
                            this.members = this.extractMembersFromRelations(data.results)
                            this.form.members = this.members.map(member => {
                                return member.id
                            })
                        }
                    }
                    else
                        this.empty = true
                } catch(e) {
                    console.log(e)
                } finally {
                    this.membersListLoading = false
                }
            }
        },
        async getConsolidation(id) {
            try {
                this.consolidationLoading = true
                const { data } = await this.$http.get(`/consolidation/${id}/`)
                if(data) {
                    data.members = data.members.map(member => member.id)
                    this.form = {...data}
                    this.$set(
                        this.form,
                        'range',
                        [
                            this.$moment(this.form.start, 'YYYY-MM-DD'),
                            this.$moment(this.form.end, 'YYYY-MM-DD')
                        ]
                    )
                    if(this.form.report_form?.id)
                        this.form.report_form = this.form.report_form.id
                    if(this.form.org_administrator?.id)
                        this.form.org_administrator = this.form.org_administrator.id
                    if(data.ipf_proposal_extra?.subtype?.id)
                        this.$set(this.form, 'ipf_proposal_subtype', data.ipf_proposal_extra.subtype.id)
                    if(data.ipf_proposal_extra?.date)
                        this.$set(this.form, 'ipf_proposal_date', this.$moment(data.ipf_proposal_extra.date, 'YYYY-MM-DD'))
                    if(data.ipf_proposal_extra?.number)
                        this.$set(this.form, 'ipf_proposal_number', data.ipf_proposal_extra.number)
                    if(data.repeat_period === '')
                        this.$set(this.form, 'repeat_period', 'MONTHLY')
                    this.getActions(id)
                }
            } catch(e) {
                console.log(e)
            } finally {
                this.consolidationLoading = false
            }
        },
        async getActions(id) {
            try {
                const { data } = await this.$http.get(`/consolidation/${id}/action_info/`)
                if(data?.actions) {
                    this.actions = data.actions
                }
            } catch(e) {
                console.log(e)
            }
        },
        getPopupContainer() {
            return this.$refs['consolidationAddBody']
        },
        async getMyOrganizations() {
            if(!this.myOrganizationsLoading) {
                try {
                    this.myOrganizationsLoading = true
                    const { data } = await this.$http.get(`/consolidation/get_org_administrators`)
                    if(data.length) {
                        this.myOrganizations = data
                        if(data.length === 1)
                            this.form.org_administrator = data[0].id
                    }
                } catch(e) {
                    console.log(e)
                } finally {
                    this.myOrganizationsLoading = false
                }
            }
        },
        async getReportForms(org_administrator) {
            this.reportForms = []
            if(!this.edit)
                this.form.report_form = null
            if(!this.reportFormsLoading) {
                try {
                    this.reportFormsLoading = true
                    const params = {
                        org_administrator: org_administrator
                    }
                    const { data } = await this.$http.get(`/consolidation/report_forms/`, {
                        params
                    })
                    if(data.results.length) {
                        this.reportForms = data.results
                        if(data.results.length === 1) {
                            this.form.report_form = data.results[0].id
                            this.reportFormIsChange(this.form.report_form)
                        }
                    }
                } catch(e) {
                    console.log(e)
                } finally {
                    this.reportFormsLoading = false
                }
            }
        },
        async afterVisibleChange(vis) {
            if(vis) {
                await this.getMyOrganizations()
            } else {
                this.myOrganizations = []
                this.members = []
                this.reportForms = []
                this.actions = null
                this.nextCreationDateInfo = null
                this.form = {
                    add_org_administrator_in_members: true,
                    is_scheduled: false,
                    attachments: [],
                    auto_approve: false,
                    dead_line: null,
                    description: '',
                    end: null,
                    members: [],
                    name: '',
                    org_administrator: null,
                    range: [],
                    repeat_period: 'MONTHLY',
                    repeat_to: null,
                    report_form: null,
                    start: null,
                    generate_report_files: false,
                    ipf_proposal_date: null,
                    ipf_proposal_number: null,
                    ipf_proposal_subtype: null
                }
                this.edit = false
                this.templateEdit = false
                this.ipfProposalSubtypes = []
            }
        },
        getConsolidationName(reportFormID) {
            let reportName
            const index = this.reportForms.findIndex(org => org.id === reportFormID)
            if (index !== -1) {
                reportName = this.reportForms[index].name
            } else {
                reportName = this.$t('Unknown form')
            }
            const startDate = this.$moment(this.form.start).format('DD.MM.YYYY')
            const endDate = this.$moment(this.form.end).format('DD.MM.YYYY')

            return this.$t('{reportName} for the period from {start} to {end}', {
                reportName,
                start: startDate,
                end: endDate
            })
        },

        info(data) {
            const modal = this.$success({
                title: this.$t('a_new_template_has_been_created'),
                content: (`
            <div>
                <p>
                    ${this.$t(
                    'The next consolidation will be created on {creationDate} for the period from {start} to {end}, with a report submission deadline of {deadline}',
                    {
                        creationDate: this.$moment(data.template.next_creation_date).format('DD.MM.YYYY'),
                        start: this.$moment(data.template.next_start).format('DD.MM.YYYY'),
                        end: this.$moment(data.template.next_end).format('DD.MM.YYYY'),
                        deadline: this.$moment(data.template.next_dead_line).format('DD.MM.YYYY')
                    }
                )}
                </p>
            </div>`
                ),
            })
        },
        add_extra(formData) {
            if(this.isIPFProposal) {
                formData.ipf_proposal_extra = {
                    date: this.$moment(formData.ipf_proposal_date).format('YYYY-MM-DD'),
                    number: formData.ipf_proposal_number,
                    subtype: formData.ipf_proposal_subtype
                }
                delete formData.ipf_proposal_date
                delete formData.ipf_proposal_number
                delete formData.ipf_proposal_subtype
            }
        },
        formSubmit() {
            this.$refs.consolidationForm.validate(async valid => {
                if (valid) {
                    try {
                        this.loading = true
                        this.form.name = this.getConsolidationName(this.form.report_form)
                        const formData = JSON.parse(JSON.stringify(this.form))

                        if(formData.dead_line) {
                            formData.dead_line = this.$moment(formData.dead_line).format('YYYY-MM-DD')
                        }
                        if(formData.start) {
                            formData.start = this.$moment(formData.start).format('YYYY-MM-DD')
                        }
                        if(formData.end) {
                            formData.end = this.$moment(formData.end).format('YYYY-MM-DD')
                        }
                        if(formData.repeat_to) {
                            formData.repeat_to = this.$moment(formData.repeat_to).format('YYYY-MM-DD')
                        }
                        if(formData.hasOwnProperty('range'))
                            delete formData.range
                        if(!formData.is_scheduled)
                            delete formData.repeat_period
                        if(formData.attachments.length)
                            formData.attachments = formData.attachments.map(file => {
                                return file.id
                            })
                        if(!this.isIPFProposal) {
                            if(formData.hasOwnProperty('ipf_proposal_date'))
                                delete formData.ipf_proposal_date
                            if(formData.hasOwnProperty('ipf_proposal_number'))
                                delete formData.ipf_proposal_number
                            if(formData.hasOwnProperty('ipf_proposal_subtype'))
                                delete formData.ipf_proposal_subtype
                            if(formData.hasOwnProperty('ipf_proposal_extra'))
                                delete formData.ipf_proposal_extra
                        }
                        this.add_extra(formData)
                        if(this.edit) {
                            const { data } = await this.$http.put(`/consolidation/${formData.id}/`, formData)
                            if(data) {
                                this.visible = false
                                if(this.isMobile) {
                                    eventBus.$emit('consolidation_list_reload')
                                } else {
                                    eventBus.$emit('consolidationTableReload')
                                }
                                this.$message.info('Отчет обновлен')
                                
                                // TODO: Рефакторинг
                                const consolidationResponse = await this.$http.get(`/consolidation/${data.id}/`)
                                eventBus.$emit(`table_row_${this.pageName}`, {
                                    action: 'update',
                                    row: consolidationResponse.data
                                })
                                
                                let query = Object.assign({}, this.$route.query)
                                if(query.consolidation) {
                                    eventBus.$emit('reload_open_consolidation')
                                }
                                if(formData.is_scheduled)
                                    eventBus.$emit('template_list_reload')
                            }
                        } else {
                            const { data } = await this.$http.post('/consolidation/', formData)
                            if(data) {
                                this.visible = false
                                if(formData.is_scheduled) {
                                    this.info(data)
                                }
                                eventBus.$emit('consolidationTableReload')
                                eventBus.$emit('consolidation_list_reload')
                                this.$message.info(this.$t('con_report_created'))
                                // TODO: Рефакторинг
                                const consolidationResponse = await this.$http.get(`/consolidation/${data.id}/`)
                                eventBus.$emit(`table_row_${this.pageName}`, {
                                    action: 'create',
                                    row: consolidationResponse.data
                                })
                            }

                        }
                    } catch(e) {
                        console.log(e)
                        this.$message.error(e[0] ? e[0] : this.$t('Error'))
                    } finally {
                        this.loading = false
                    }
                } else {
                    this.$message.error(this.$t('Invalid data'))
                    return false
                }
            })
        },
        onRangeChange(dates, dateStrings) {
            if(dates.length !== 0) {
                this.form.start = this.$moment(dates[0]).format('YYYY-MM-DD')
                this.form.end = this.$moment(dates[1]).format('YYYY-MM-DD')
            }
        },
    },
    beforeDestroy() {
        eventBus.$off('create_consolidation')
        eventBus.$off('edit_consolidation')
        eventBus.$off('view_template')
    }
}
</script>

<style lang="scss" scoped>
.new-consolidation-drawer{
    .drawer_body{
        height: 100%;
        overflow-y: auto;
        overflow-x: hidden;
        padding: 30px;
        .wrap{
            display: flex;
            width: 100%;
            flex-direction: column;
            align-items: flex-start;
            gap: 20px;
            .step{
                border-radius: 15px;
                border: 1px solid #D9D9D9;
                width: 100%;
                padding: 30px;
                .title{
                    display: grid;
                    grid-template-columns: 1fr 50px;
                    grid-template-rows: auto;
                    grid-template-areas: "title number" "description description";
                    color: #000;
                    font-family: Roboto;
                    font-style: normal;
                    font-weight: 400;
                    line-height: 100%;
                    .step-number{
                        grid-area: number;
                        font-size: 18px;
                        opacity: 0.3;
                    }
                    .step-title{
                        grid-area: title;
                        font-size: 20px;
                        margin-bottom: 10px;
                    }
                    .step-description{
                        grid-area: description;
                        font-size: 16px;
                        opacity: 0.6;
                    }
                }
                .form-wrap{
                    margin-top: 30px;
                    .step-one-form{
                        display: grid;
                        grid-template-columns: repeat(2, 1fr);
                        column-gap: 30px;
                        .org-administrator{
                            min-width: 0;
                            &::v-deep{
                                li.ant-select-dropdown-menu-item{
                                    overflow: visible;
                                    text-overflow: clip;
                                    white-space: normal;
                                }
                            }
                        }
                        .members-list{
                            min-width: 0;
                        }
                        .ogr-name{
                            font-size: 14px;
                        }
                        .member-name{
                            font-size: 14px;
                            text-wrap: wrap;
                        }
                        .add-to-members{
                            align-self: start;
                            margin-top: 26px;
                            
                            .switcher{
                                height: 38px;
                                display: grid;
                                grid-template-columns: auto 1fr;
                                column-gap: 30px;
                                .label{
                                    align-self: center;
                                    color: #000;
                                    font-family: Roboto;
                                    font-size: 14px;
                                    font-style: normal;
                                    font-weight: 400;
                                    line-height: 100%;
                                }
                                .switch{
                                    align-self: center;
                                }
                            }
                        }
                    }
                    .step-two-form{
                        .report-form{}
                        .options{
                            display: grid;
                            grid-template-columns: repeat(2, auto);
                            column-gap: 30px;
                            width: fit-content;
                            .label{
                                align-self: center;
                                color: #000;
                                font-family: Roboto;
                                font-size: 14px;
                                font-style: normal;
                                font-weight: 400;
                                line-height: 100%;
                            }
                            .auto-approve{
                                display: grid;
                                grid-template-columns: repeat(2, auto);
                                column-gap: 30px;
                            }
                            .use-inquiries-module-data{
                                display: grid;
                                grid-template-columns: repeat(2, auto);
                                column-gap: 30px;
                            }
                        }
                        .ipf-proposal-extra{
                            margin-top: 24px;
                            .date-and-number{
                                display: grid;
                                grid-template-columns: repeat(2, 1fr);
                                column-gap: 30px;
                            }
                        }
                        .description{
                            margin-top: 20px;
                            &::v-deep{
                                .editor{
                                    height: 180px;
                                    display: flex;
                                    flex-direction: column;
                                    min-height: 0;
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
                                }
                            }
                            .attachments-btn{
                                padding-top: 10px;
                            }
                        }
                        .attachments{}
                    }
                    .step-three-form{
                        display: grid;
                        grid-template-columns: repeat(2, 1fr);
                        column-gap: 30px;
                        .range{}
                        .start{
                            grid-column: span 2;
                        }
                        .end{
                            grid-column: span 2;
                        }
                        .grid-column-span-2{
                            grid-column: span 2;
                        }
                        .deadline{}
                    }
                    .step-four-form{
                        display: grid;
                        grid-template-columns: repeat(2, 1fr);
                        column-gap: 30px;
                        .repeat-switcher{
                            grid-column: span 2;
                            display: grid;
                            grid-template-columns: repeat(2, auto);
                            column-gap: 30px;
                            width: fit-content;
                            margin-bottom: 20px;
                        }
                        .repeat-period{
                            grid-column: span 2;
                        }
                        .start-data{}
                        .end-data{}
                        .repeat-info{
                            grid-column: span 2;
                            border-radius: 4px;
                            background: rgb(217, 217, 217, 0.3);
                            .text{
                                color: #000;
                                font-family: Roboto;
                                font-size: 16px;
                                font-style: normal;
                                font-weight: 400;
                                line-height: 100%;
                                padding: 25px 30px;
                            }
                        }
                    }
                }
                .attachments-label{
                    margin-top: 15px;
                }
                .attachment_files{
                    margin-top: 0.25rem;
                    display: flex;
                    flex-wrap: wrap;
                }
                .template-edit{
                    grid-column: span 2;
                    margin-top: 30px;
                    .buttons{
                        margin-top: 30px;
                        display: grid;
                        grid-template-columns: repeat(2, auto);
                        gap: 30px;
                    }
                    .template-on-off{
                        display: grid;
                        grid-template-columns: repeat(2, auto);
                        column-gap: 30px;
                        width: fit-content;
                        align-content: center;
                        align-items: center;
                    }
                }
            }
            .buttons{
                .add-button{}
                .cancel-button{
                    margin-left: 10px;
                }
            }
        }
        @media screen and (max-width: 700px) {
            .wrap {
                .step {
                    padding: 20px;
                    .title {
                        grid-template-columns: 1fr;
                        grid-template-areas: "number" "title" "description";
                        .step-number {
                            opacity: 0.6;
                            margin-bottom: 10px;
                        }
                    }
                    .form-wrap {
                        .step-one-form {
                            grid-template-columns: 1fr;
                        }
                        .step-two-form {
                            .options{
                                grid-template-columns: 1fr;
                                row-gap: 15px;
                                .auto-approve{
                                    width: fit-content;
                                }
                            }
                        }
                        .step-three-form {
                            grid-template-columns: 1fr;
                        }
                        .step-four-form {
                            grid-template-columns: 1fr;
                            .repeat-switcher, .repeat-period, .repeat-info {
                                grid-column: unset;
                            }
                        }
                    }
                }
                .buttons {
                    display: grid;
                    grid-template-columns: repeat(2, 1fr);
                    column-gap: 10px;
                    width: 100%;
                    .cancel-button{
                        margin-left: unset;
                    }
                }
            }
        }
    }
    
    &::v-deep{
        .ant-select-lg .ant-select-selection--multiple .ant-select-selection__rendered li {
            max-width: 65%;
        }
        .ant-drawer-wrapper-body,
        .ant-drawer-content{
            overflow: hidden;
            padding: 0px;
        }
        .ant-drawer-header{
            padding-left: 20px;
            padding-right: 20px;
        }
        .ant-drawer-body{
            height: calc(100% - 40px);
            padding: 0px;
        }
        .ant-form-item-label{
            opacity: 0.6;
        }
    }
}
</style>