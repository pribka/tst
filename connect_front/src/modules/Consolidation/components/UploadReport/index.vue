<template>
    <a-drawer
        title="Загрузить отчет"
        :visible="visible"
        class="upload-drawer"
        @close="visible = false"
        destroyOnClose
        :zIndex="zIndex"
        :width="drawerWidth"
        :afterVisibleChange="afterVisibleChange"
        placement="right">
        <div class="drawer_body" ref="docAddBody">
            <a-spin :spinning="docLoading">
                <a-form-model
                    ref="reportForm"
                    :model="form"
                    :rules="rules">
                    <a-form-model-item v-for="file in report_files" :key="file.id">
                        <WidgetSwitch
                            :file="file"
                            :form="form"
                            :consolidation="consolidation"
                            :report="report"
                            :period="period"
                            :noInquiries="noInquiries"
                            :handleFileChange="handleFileChange"
                            :clearFile="clearFile"
                            :fileLoading="fileLoading"
                            :formSubmit="loading"
                            :fileIcon="fileIcon"
                            :deleteIcon="deleteIcon"
                            :reportID="reportID"
                            :report_files="report_files"
                            :showFormError="showFormError"
                            :isPersonalReceptionRequired="isPersonalReceptionRequired"
                            :edit="edit"
                            :fileChangeIsDisabled="fileChangeIsDisabled" />                        
                    </a-form-model-item>
                </a-form-model>
            </a-spin>
        </div>
        <div class="drawer_footer">
            <a-spin :spinning="docLoading">
                <a-button 
                    type="primary"
                    :loading="loading"
                    @click="formSubmit()"
                    :disabled="fileLoading || fileChangeIsDisabled">
                    {{ buttonText }}
                </a-button>
                <a-button 
                    type="ui"
                    class="ml-2"
                    @click="visible = false">
                    {{ $t('Cancel') }}
                </a-button>
            </a-spin>
        </div>

        <a-modal 
            v-model="errorModalVisible" 
            :title="$t('Data validation failed')" 
            :zIndex="1200" 
            :closable="false" 
            dialogClass="error-modal">

            <template slot="footer">
                <a-button type='primary' @click="errorModalVisible=false">
                    {{ $t('Close') }}
                </a-button>
            </template>

            <div v-for="(each, index) in errorList" :key="index" class="error-list-item">
                <i class="fi fi-rr-exclamation icon"></i> 
                <span class="message">{{ each }}</span>
            </div>
        </a-modal>
    </a-drawer>
</template>

<script>
import eventBus from '@/utils/eventBus'

export default {
    name: 'UploadReport',
    components: {
        WidgetSwitch: () => import('./Widgets/WidgetSwitch.vue')
    },
    props: {
        zIndex: {
            type: Number,
            default: 1100
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
            if(this.windowWidth > 600)
                return 600
            else {
                return '100%'
            }
        },
        fileChangeIsDisabled() {
            if(this.edit) {
                if(this.auto_approve && !['consolidated',].includes(this.reportStatus?.code)) {
                    return false
                } else if(!this.auto_approve && ['approved', 'consolidated'].includes(this.reportStatus?.code)) {
                    return true
                } else {
                    return false
                }
            } else {
                return false
            }
        },
        buttonText() {
            return this.edit ? 'Сохранить' : 'Загрузить'
        },
        fileIcon() {
            return require(`@/assets/images/files/uploaded_file.svg`)
        },
        deleteIcon() {
            return require(`@/assets/images/files/DeleteOutlined.svg`)
        },
        addNoInquiriesField() {
            return new Set(['f2go', 'risk_map_with_personal_reception']).has(this.reportFormCode)
        },
        isPersonalReceptionRequired() {
            return this.addPersonalReceptionRules && this.form.personal_reception_issues.length > 0
        },
        rules() {
            let rules = {}
            if(new Set(['f2go', 'f2go_with_verification_act', 'risk_map_with_personal_reception']).has(this.reportFormCode)) {
                this.$set(rules, 'revoked_without_routing', [
                    { required: true, message: 'Обязательное поле', trigger: 'blur' },
                ])
                this.$set(rules, 'transferring_to_another_system', [
                    { required: true, message: 'Обязательное поле', trigger: 'blur' },
                ])
            }
            if(this.isPersonalReceptionRequired) {
                this.$set(rules, 'personal_reception_quantity', [
                    { required: true, message: 'Обязательное поле', trigger: 'blur' },
                ])
            }
            return rules
        },
        period() {
            if (this.consolidation?.start && this.consolidation?.end) {
                return `${this.$moment(this.consolidation.start).format('DD.MM.YYYY')} - ${this.$moment(this.consolidation.end).format('DD.MM.YYYY')}`
            } else {
                return ''
            }
        }
    },
    data() {
        return {
            form: {
                contractor: null,
                report_files: null,
            },
            actions: null,
            addPersonalReceptionRules: false,
            auto_approve: false,
            consolidation: null,
            consolidationID: null,
            docLoading: false,
            edit: false,
            errorList: [],
            errorModalVisible: false,
            fileLoading: false,
            loading: false,
            noInquiries: false,
            report: null,
            reportFormCode: null,
            reportID: null,
            reportStatus: null,
            report_files: [],
            viewEdit: false,
            visible: false,
            showFormError: false
        }
    },
    created() {
        eventBus.$on('upload_report', (consolidation, report) => {
            this.consolidation = consolidation
            this.report = report
            this.consolidationID = consolidation.id
            this.reportID = report.id
            this.auto_approve = consolidation.auto_approve
            this.noInquiries = report.no_inquiries
            this.reportFormCode = consolidation.report_form.code
            if(report?.contractor) {
                this.form.contractor = report.contractor.id
            }
            if(report?.report_files) {
                this.report_files = JSON.parse(JSON.stringify(report.report_files))
                this.edit = true
            }
            if(report?.status) {
                this.reportStatus = report.status
            }
            this.$set(this.form, 'without_attachments', report.without_attachments)
            if('revoked_without_routing' in report)
                this.$set(this.form, 'revoked_without_routing', report.revoked_without_routing)
            if('transferring_to_another_system' in report)
                this.$set(this.form, 'transferring_to_another_system', report.transferring_to_another_system)
            if('personal_reception_quantity' in report)
                this.$set(this.form, 'personal_reception_quantity', report.personal_reception_quantity)
            if ('no_personal_reception' in report) 
                this.$set(this.form, 'no_personal_reception', report.no_personal_reception)
            if (this.reportFormCode === 'risk_map_with_personal_reception')
                this.$set(this.form, 'personal_reception_issues', [])
            this.visible = true
        })
        eventBus.$on('create_report', () => {
            this.visible = true
        })
        eventBus.$on('edit_report', (report, view = false) => {
            this.edit = true
            this.viewEdit = view
            this.getReport(report.id)
            this.visible = true
        })
        eventBus.$on('no-inquiries', (val) => {
            this.noInquiries = val
        })
        eventBus.$on('add-personal-reception', (val) => {
            this.addPersonalReceptionRules = val
        })
    },
    methods: {
        clearFile(event, file) {
            if(!this.fileLoading && !this.loading) {
                let index = this.report_files.findIndex(item => item === file)
                if(index !== -1) {
                    this.report_files[index].original_file=null
                }
            }
        },
        async reportValid(id, code='') {
            if(id && this.consolidationID) {
                try {
                    const { data } = await this.$http.get(`consolidation/${this.consolidationID}/report_validation/`, {
                        params: {
                            file: id,
                            code: code,
                        }
                    })
                    if(data.validate === true) {
                        this.$message.success('Данные прошли проверку')
                        return true
                    } else {
                        this.$message.error('Данные не прошли проверку')
                        return false
                    }
                } catch(e) {
                    this.handleError(e)
                    if(this.$refs.pdf_file?.value) {
                        this.$refs.pdf_file.value = ''
                    }
                }
            } else {
                this.$message.error('Проверка файла невозможна!')
                return false
            }
        },
        async handleFileChange(event, reportFile) {
            const file = Object.values(event.target.files)[0]
            if(file) {
                try {
                    this.fileLoading = true
                    const data = await this.$uploadFile({
                        file,
                        url: '/common/upload/',
                        fieldName: 'upload',
                        fileName: file.name,
                        extraData: {
                            is_confined: true
                        }
                    })
                    if(data?.length && data[0].id && await this.reportValid(data[0].id, reportFile.code)) {
                        let index = this.report_files.findIndex(item => item === reportFile)
                        if(index !== -1) {
                            this.report_files[index].original_file=data[0]
                            this.report_files[index].is_generated=false
                        }
                    }
                    
                } catch(e) {
                    console.log(e)
                } finally {
                    this.fileLoading = false
                    eventBus.$emit('clear_file_input')
                }
            }
        },
        async getReport(id) {
            try {
                this.docLoading = true
                const { data } = await this.$http.get(`/consolidation/${id}/`)
                if(data) {
                    const formData = data
                    this.form = formData
                    this.form.range = [this.form.start, this.form.end]
                    this.getActions(id)
                }
            } catch(e) {
                console.log(e)
            } finally {
                this.docLoading = false
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
        afterVisibleChange(vis) {
            if(!vis) {
                if(this.viewEdit) {
                    const { id } = this.form
                    let query = Object.assign({}, this.$route.query)
                    if(query.report && Number(query.report) !== id || !query.report) {
                        query.report = id
                        this.$router.push({query})
                    }
                }

                this.actions = null
                this.consolidationID = null
                this.consolidation = null
                this.report = null
                this.form = {
                    contractor: null,
                    report_files: null,
                }
                this.edit = false
                this.viewEdit = false
                this.report_files = []
                this.reportID = null
                this.noInquiries = false
                this.reportFormCode = null
                this.errorModalVisible = false
                this.errorList = []
                this.addPersonalReceptionRules = false
                this.showFormError = false
            }
        },
        personalReceptionValidate() {
            if (this.form.no_personal_reception) return true
            let valid = true
            this.form.personal_reception_issues.forEach(issue => {
                if (issue.personal_reception.status_code === 'in_queue' ) {
                    valid = valid && issue.personal_reception.days_in_queue !== null
                }
            })
            return valid
        },
        additionalValidation() {
            // Дополнительные проверки данных в форме
            let valid = true
            if (this.reportFormCode === 'risk_map_with_personal_reception')
                valid = valid && this.personalReceptionValidate()
            return valid
        },
        formSubmit() {
            this.$refs.reportForm.validate(async valid => {
                let additionalValid = this.additionalValidation()

                if (!(valid && additionalValid)) {
                    this.$message.error('Одно или несколько полей заполнены некорректно')
                    this.showFormError = true
                    eventBus.$emit('scroll_to_error')
                    return false
                }
                try {
                    this.loading = true
                    this.form.report_files = this.report_files
                    const formData = JSON.parse(JSON.stringify(this.form))

                    if(formData.contractor?.id) {
                        formData.contractor = formData.contractor.id
                    }
                    if(this.addNoInquiriesField) {
                        formData.no_inquiries = this.noInquiries
                    }
                    if(this.edit) {
                        const { data } = await this.$http.post(`/consolidation/${this.consolidationID}/report/`, formData)
                        if(data) {
                            this.visible = false
                            eventBus.$emit('reload_report')
                            // eventBus.$emit('consolidationTableReload')
                            eventBus.$emit('update_report_in_list', data.report)
                            eventBus.$emit('update_open_consolidation', data.consolidation)
                            this.$message.info('Отчет обновлен')

                            let query = Object.assign({}, this.$route.query)
                        }
                    } else {
                        const { data } = await this.$http.post(`/consolidation/${this.consolidationID}/report/`, formData)
                        if(data) {
                            this.visible = false
                            // eventBus.$emit('consolidationTableReload')
                            eventBus.$emit('update_report_in_list', data.report)
                            eventBus.$emit('update_open_consolidation', data.consolidation)
                            this.$message.info('Отчет загружен')
                        }
                    }
                } catch(e) {
                    this.handleError(e)
                } finally {
                    this.loading = false
                }
            })
        },
        onRangeChange(dates, dateStrings) {
            if(dates.length !== 0) {
                this.form.start = this.$moment(dates[0]).format('YYYY-MM-DD')
                this.form.end = this.$moment(dates[1]).format('YYYY-MM-DD')
            }
        },
        handleError(e) {
            console.log(e)
            if(typeof e === "object" && e[0]) {
                this.$message.error(e[0])
            } else if(typeof e === "object") {
                this.errorList = Object.values(e)
                this.errorModalVisible = true
            } else {
                this.$message.error('Ошибка при загрузке файла')    
            }
        }
    },
    beforeDestroy() {
        eventBus.$off('create_report')
        eventBus.$off('edit_report')
        eventBus.$off('upload_report')
        eventBus.$off('no-inquiries')
        eventBus.$off('add-personal-reception')
    }
}
</script>

<style lang="scss" scoped>
.upload-drawer{
    &::v-deep{
        .temp_sel{
            .ant-select-dropdown-menu-item{
                white-space: initial;
                overflow: initial;
                text-overflow: initial;
            }
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
        .drawer_body{
            height: calc(100% - 40px);
            overflow-y: auto;
            overflow-x: hidden;
            padding: 20px;
            display: flex;
            width: 100%;
            flex-direction: column;
            align-items: flex-start;
            gap: 20px;
            .file{
                border-radius: 15px;
                border: 1px solid #D9D9D9;
                width: 100%;
                padding: 30px;
                display: flex;
                gap: 30px;
                flex-direction: column;
                .title{
                    display: grid;
                    grid-template-columns: 1fr;
                    grid-template-rows: auto;
                    grid-template-areas: "title number" "description description";
                    color: #000;
                    font-family: Roboto;
                    font-style: normal;
                    font-weight: 400;
                    line-height: 100%;
                    .file-number{
                        grid-area: number;
                        font-size: 18px;
                        opacity: 0.3;
                    }
                    .file-title{
                        grid-area: title;
                        font-size: 20px;
                    }
                    .file-description{
                        grid-area: description;
                        font-size: 16px;
                        opacity: 0.6;
                    }
                }
                .form{
                    .add-file-input{
                        width: fit-content;
                        .add-file-label {
                            display: flex;
                            align-items: center;
                            color: var(--blue);
                        }
                    }
                    .uploaded-file{
                        margin-top: 20px;
                        .label {
                            color: #000;
                            font-family: Roboto;
                            font-size: 14px;
                            font-style: normal;
                            font-weight: 400;
                            line-height: 100%;
                            opacity: 0.6;
                            margin-bottom: 10px;
                        }
                        .card{
                            border: 1px solid var(--Neutral-5, #D9D9D9);
                            border-radius: 4px;
                            height: 66px;
                            width: 65%;
                            display: grid;
                            grid-template-columns: 39px 1fr 14px;
                            column-gap: 15px;
                            padding-left: 15px;
                            padding-right: 15px;
                            align-content: center;
                            align-items: center;
                            .icon{
                                .file-icon{
                                    width: 100%;
                                    max-height: 100%;
                                    object-fit: contain;
                                }
                            }
                            .file-name{
                            }
                            .delete{
                                .file-icon{
                                    width: 100%;
                                    max-height: 100%;
                                    object-fit: contain;
                                    cursor: pointer;
                                }
                                .disabled-file-icon{
                                    width: 100%;
                                    max-height: 100%;
                                    object-fit: contain;
                                    opacity: 0.3;
                                }
                            }
                        }
                    }
                }
                @media (max-width: 600px) {
                    .form {
                        .uploaded-file{
                            .card{
                                width: 100%;
                            }
                        }
                    }
                }
            }
            .no-data{
                color: rgb(209 213 219);
            }
        }
        .drawer_footer{
            display: flex;
            align-items: center;
            height: 40px;
            border-top: 1px solid #e8e8e8;
            padding-left: 20px;
            padding-right: 20px;
        }
    }
}
.error-list-item{
    margin-bottom: 20px;
    display: grid;
    grid-template-columns: auto 1fr;
    column-gap: 20px;
    align-items: center;
    .icon{
        color: red;
    }
    .message{
    }
}
</style>
