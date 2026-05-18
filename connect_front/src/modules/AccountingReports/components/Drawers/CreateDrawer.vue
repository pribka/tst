<template>
    <a-drawer
        :title="title"
        :visible="visible"
        class="drawer"
        @close="closeDrawer"
        destroyOnClose
        :zIndex="zIndex"
        :width="drawerWidth"
        :afterVisibleChange="afterVisibleChange"
        placement="right">
        <div class="drawer_body">
            <a-spin :spinning="reportLoading">
                <a-form-model 
                    class="form row"
                    :model="form"
                    ref="newReportForm"
                    :rules="rules" 
                    layout="vertical">
                    <div class="panel">
                        <div class="panel_header w-full flex justify-between">
                            <div>
                                <div class="panel_title">Отчёты</div>
                                <div class="mt-2 panel_description">Выберите из списка форму отчета</div>
                            </div>
                            <div class="panel_step">шаг 1</div>
                        </div>
                        <a-form-model-item
                            ref="organization"
                            label="Организация"
                            prop="organization"
                            class="form_item row">
                            <a-select
                                v-model="form.organization"
                                size="large"
                                :getPopupContainer="trigger => trigger.parentElement"
                                :loading="organizationsLoading"
                                :disabled="organizationSelectIsDisabled"
                                placeholder="Выберите организацию">
                                <a-select-option v-for="org in organizations" :key="org.id" :value="org.id">
                                    <div class="truncate type-name">{{ org.name }}</div>
                                </a-select-option>
                            </a-select>
                        </a-form-model-item>
                        <a-form-model-item
                            ref="type"
                            label="Форма отчета"
                            prop="type"
                            class="form_item row">
                            <a-select
                                v-model="form.type"
                                size="large"
                                :getPopupContainer="trigger => trigger.parentElement"
                                :loading="formatLoading"
                                :disabled="typeSelectIsDisabled"
                                placeholder="Выберите форму отчета">
                                <a-select-option v-for="reportForm in reportForms" :key="reportForm.id" :value="reportForm.code">
                                    <div class="truncate type-name">{{ reportForm.name }}</div>
                                </a-select-option>
                            </a-select>
                        </a-form-model-item>
                    </div>
                    <div v-if="widget" class="opacity-animation">
                        <component 
                            :is="widget"
                            ref="reportFormedWidget"
                            :form="form"
                            :viewMode="viewMode"
                            :unfilled="unfilled"
                            :edit="edit" />                                    
                    </div>
                </a-form-model>
                <template v-if="viewMode">
                    <a-button
                        class="custom_button"
                        type="primary"
                        @click="cancel">
                        Закрыть
                    </a-button>
                </template>
                <template v-else>
                    <a-button
                        class="custom_button"
                        type="primary"
                        :disabled="!form.type"
                        @click="formSubmit">
                        {{ addButtonText }}
                    </a-button>
                    <a-button
                        class="custom_button ml-2"
                        type="ui"
                        @click="cancel">
                        Отменить
                    </a-button>
                </template>
            </a-spin>
        </div>
    </a-drawer>
</template>

<script>
import eventBus from '@/utils/eventBus'
import { mapState } from 'vuex'
import ReportTypeClasses from './ReportTypeClasses'
export default {
    name: "CreateAccountingReportDrawer",
    mixins: [ReportTypeClasses],
    components: {
    },
    props: {
        zIndex: {
            type: Number,
            default: 1010
        }
    },
    computed: {
        ...mapState({
            windowWidth: state => state.windowWidth,
            isMobile: state => state.isMobile
        }),
        drawerWidth() {
            const offset = 50
            if(this.windowWidth > 1500 + offset)
                return '95%'
            return '100%'
        },
        rules() {
            return {...this.default_rules, ...this.extra_rules}
        },
        addButtonText() {
            return this.edit ? 'Сохранить отчёт' : 'Добавить отчёт'
        },
        organizationSelectIsDisabled() {
            return this.edit || this.viewMode
        },
        typeSelectIsDisabled() {
            return !this.form.organization || this.edit || this.viewMode
        },
        title() {
            if(this.edit) {
                return this.$t('reports.edit_report')
            } else if(this.viewMode) {
                return this.$t('reports.view_report') 
            } else {
                return this.$t('reports.add_report')
            }
        }
    },
    data() {
        return {
            visible: false,
            reportForms: [],
            formatLoading: false,
            organizations: [],
            organizationsLoading: false,
            form: {
                organization: null,
                type: null
            },
            reportForm: {},
            default_rules: {
                type: [
                    { required: true, message: 'Обязательно для заполнения', trigger: 'blur' }
                ],
                organization: [
                    { required: true, message: 'Обязательно для заполнения', trigger: 'blur' }
                ],
            },
            widget: null,
            extra_rules: {},
            reportLoading: false,
            edit: false,
            viewMode: false,
            pageName: 'accounting_reports',
            unfilled: false,
            reportFormObj: null
        }
    },
    mounted() {
        eventBus.$on('open_create_accounting_order_drawer', () => {
            this.openDrawer()    
        })
        eventBus.$on('edit_accounting_report', (reportID) => {
            this.visible = true
            this.edit = true
            this.getReport(reportID)
        })
        eventBus.$on('view_accounting_report', (reportID) => {
            this.visible = true
            this.viewMode = true
            this.getReport(reportID)
        })
    },
    beforeDestroy() {
        eventBus.$off('open_create_accounting_order_drawer')
        eventBus.$off('edit_accounting_report')
        eventBus.$off('view_accounting_report')
    },
    watch: {
        'form.organization': {
            handler: async function(val) {
                if(val) {
                    if(!this.edit && !this.viewMode) {
                        this.reportForms = []
                        this.form.type = null
                        this.widget = null
                        this.extra_rules = {}
                        this.reportForm = {}
                        this.responsible_position = null
                        this.responsible_name = null
                    }
                    this.getReportTypes(val)
                }
            }
        },
        'form.type': {
            handler: async function(val) {
                if(val) {
                    const index = this.reportForms.findIndex(item => item.code === val)
                    if(index !== -1) {
                        this.cleanForm()
                        if(this.reportForms[index]?.widget) {
                            this.widget = this.get_widget(this.reportForms[index].widget)
                        }
                        if(this.reportForms[index]?.rules) {
                            this.extra_rules = this.reportForms[index].rules
                        }
                        if(this.reportForms[index]?.form) {
                            this.addFormExtraFields(this.reportForms[index].form)
                        }
                        this.reportFormObj = this.getReportTypeObj(val)
                    }
                }
            }
        }
    },
    methods: {
        cleanForm() {
            for (const key in this.form) {
                if (key !== 'organization' && key !== 'type') {
                    this.$delete(this.form, key)
                }
            }
        },
        addFormExtraFields(extraFields) {
            const tmpExtraFields = JSON.parse(JSON.stringify(extraFields))
            for(const key in tmpExtraFields) {
                this.$set(this.form, key, tmpExtraFields[key])
            }
        },
        get_widget(widget_name) {
            return () => import(`./${widget_name}`)
                .then(module => {
                    return module
                })
                .catch(e => {
                    console.log('error')
                    return import(`./NotWidget.vue`)
                })
        },
        openDrawer() {
            this.visible = true
        },
        closeDrawer() {
            this.visible = false
        },
        afterVisibleChange(visible) {
            if(visible) {
                this.getOrganizations()
            } else {
                this.reportForms = []
                this.formatLoading = false
                this.organizations = []
                this.organizationsLoading = false
                this.form = {
                    type: null,
                    organization: null,
                }
                this.reportForm = {}
                this.widget = null
                this.extra_rules = {}
                this.edit = false
                this.viewMode = false
                this.unfilled = false
                this.reportFormObj = null
            }
        },
        async getOrganizations() {
            if(!this.organizationsLoading) {
                try {
                    this.organizationsLoading = true
                    const { data } = await this.$http.get('/accounting_reports/get_organizations')
                    if(data.length) {
                        this.organizations = data
                        if(!this.edit && this.organizations.length === 1)
                            this.form.organization = this.organizations[0].id
                    }
                } catch(e) {
                    console.log(e)
                } finally {
                    this.organizationsLoading = false
                }
            }
        },
        async getReportTypes(organization) {
            if(!this.formatLoading) {
                const params = {
                    organization: organization
                }
                try {
                    this.formatLoading = true
                    const { data } = await this.$http.get(`/accounting_reports/get_report_types/`, {
                        params
                    })
                    if(data.length) {
                        this.reportForms = data
                        if(!this.edit && data.length === 1)
                            this.form.type = data[0].code
                    }
                } catch(e) {
                    console.log(e)
                } finally {
                    this.formatLoading = false
                }
            }
        },
        async getReport(id) {
            try {
                this.reportLoading = true
                const { data } = await this.$http.get(`/accounting_reports/${id}/`)
                if(data) {
                    this.addFormExtraFields(data.type.form)
                    this.widget = this.get_widget(data.type.widget)
                    this.reportFormObj = this.getReportTypeObj(data.type.code)
                    this.fillForm(data)
                }
            } catch(e) {
                console.log(e)
            } finally {
                this.reportLoading = false
            }
        },
        fillForm(data) {
            this.form.id = data.id
            this.form.organization = data.organization.id
            this.form.type = data.type.code
            this.extra_rules = data.type.rules
            this.reportFormObj.fillSpecificFormFields(this.form, data)
        },
        formSubmit() {
            this.$refs.newReportForm.validate(async valid => {
                if (valid && this.reportFormObj.formValidation(this.form)) {
                    this.unfilled = false
                    try {
                        this.reportLoading = true
                        const formData = JSON.parse(JSON.stringify(this.form))

                        this.reportFormObj.formPrepare(formData)
 
                        if(this.edit) {
                            const { data } = await this.$http.put(`/accounting_reports/${formData.id}/`, formData)
                            if(data) {
                                this.visible = false
                                this.$message.info('Отчет обновлен')
                                eventBus.$emit(`table_row_${this.pageName}`, {
                                    action: 'update',
                                    row: data
                                })
                            }
                        } else {
                            const { data } = await this.$http.post('/accounting_reports/', formData)
                            if(data) {
                                this.visible = false
                                this.$message.info('Отчет создан')  
                                eventBus.$emit(`table_row_${this.pageName}`, {
                                    action: 'create',
                                    row: data
                                })
                            }

                        }
                    } catch(e) {
                        console.log(e)
                        this.$message.error(e?.error[0] ? e.error[0] : 'Ошибка создания отчёта')
                    } finally {
                        this.reportLoading = false
                    }
                } else {
                    this.$message.error('Заполнены не все поля')
                    this.unfilled = true
                    return false
                }
            })
        },
        cancel() {
            this.visible = false
        }
    },
}
</script>

<style lang="scss" scoped>
.opacity-animation {
    animation-name: opacity-animation;
    animation-duration: 0.8s;
    animation-timing-function: ease-in;
}
@keyframes opacity-animation {
  from {
    opacity: 0;
  }
  to {
    opacity: 100%;
  }
}
// PANEL
.panel {
    padding: 30px;
    border: 1px solid #e8e8e8;
    border-radius: 15px;
}
.panel + .panel {
    margin-top: 20px;
}
.panel_header {
    margin-bottom: 30px;
}
.panel_title {
    font-size: 1.2rem;
    line-height: 1;
    color: #000;
}
.panel_description {
    font-size: 1rem;
    color: hsla(0, 0%, 0%, 0.6);
}
.panel_step {
    font-size: 1.1rem;
    color: hsla(0, 0%, 0%, 0.3);

}
// END PANEL
// ############################################


// FORM
.form {
    &::v-deep {
        .ant-form-item {
            margin: 0;
            padding: 0;
        }
    }
}
.form_item::v-deep {
    .ant-form-item-label label {
        color: hsl(0, 0%, 0%, 0.6);
    }
}
.grid_cols_2,
.grid_cols_3 {
    display: grid;
    gap: 30px;
}
.grid_cols_2 {
    grid-template-columns: repeat(2, 1fr);
}
.grid_cols_3 {
    grid-template-columns: repeat(3, 1fr);
}

.row:not(:last-child) {
    margin-bottom: 40px;
}
// END FORM
// ############################################


// BUTTONS
.custom_input {
    height: 50px;
    padding: 5px 12px;
    border-radius: 0.25rem;
}
.custom_select {
    height: 50px;
    // border-radius: 0.25rem;
}
.custom_button {
    height: 50px;
    padding: 0 40px;
    border-radius: 0.25rem;
    font-size: 1rem;
    line-height: 1.5rem;
}
// END BUTTONS

.drawer{
    &::v-deep{
        .ant-drawer-wrapper-body,
        .ant-drawer-content{
            overflow: hidden;
            padding: 0px;
        }
        .ant-drawer-header{
            padding-left: 20px;
            padding-right: 20px;
            @media (max-width: 900px) {
                padding-left: 15px;
                padding-right: 15px;
            }
        }
        .ant-drawer-body{
            $header-height: 40px;
            height: calc(100% - $header-height);
            padding: 0px;
        }
        .drawer_body{
            height: calc(100%);
            padding: 35px 30px;
            
            overflow-y: auto;
            overflow-x: hidden;
            @media (max-width: 900px) {
                padding: 15px;
            }
        }
    }
}
</style>