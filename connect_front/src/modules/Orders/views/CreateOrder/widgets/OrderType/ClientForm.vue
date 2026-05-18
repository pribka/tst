<template>
    <div>
        <a-button 
            v-if="contractor"
            size="large"
            :loading="viewLoader"
            class="ant-btn-icon-only"
            @click="openEdit()">
            <i class="fi fi-rr-edit"></i>
        </a-button>
        <!-- :title="edit ? 'Редактировать клиента' : 'Добавить клиента'" -->
        <a-modal
            :title="getModalTitle"
            :visible="visible"
            :afterClose="afterClose"
            :zIndex="1500"
            :width="670"
            destroyOnClose
            @cancel="visible = false">
            <template v-if="contractorsType === 'contractors'">
                <a-tabs default-active-key="contractor">
                    <a-tab-pane key="contractor" tab="Клиент">
                        <a-form-model
                            ref="clientForm"
                            :model="form">
                            <template v-for="field in contractorFormInfo">
                                <FieldSwitch
                                    v-if="dependsForm(field)"
                                    :key="field.key" 
                                    :field="field"
                                    :mainForm="mainForm"
                                    :visible="init"
                                    :checkboxHidden="checkboxHidden"
                                    :form="form" />
                            </template>
                        </a-form-model>
                    </a-tab-pane>
                    <a-tab-pane key="extraFields" tab="Доп. информация">
                        <a-form-model
                            ref="contactsExtraForm"
                            :model="form">
                            <template v-for="field in contractorExtraFormInfo">
                                <FieldSwitch
                                    v-if="dependsForm(field)"
                                    :key="field.key"
                                    :field="field"
                                    :mainForm="mainForm"
                                    :visible="init"
                                    :form="form" />
                            </template>
                        </a-form-model>
                    </a-tab-pane>
                    <a-tab-pane key="contacts" tab="Контакты">
                        <a-form-model
                            ref="contactsForm"
                            :model="form">
                            <template v-for="field in contactsFormInfo">
                                <FieldSwitch
                                    v-if="dependsForm(field)"
                                    :key="field.key"
                                    :field="field"
                                    :mainForm="mainForm"
                                    :visible="init"
                                    :form="form" />
                            </template>
                        </a-form-model>
                    </a-tab-pane>
                    <a-tab-pane key="bankRequisites" tab="Банковские реквизиты">
                        <a-form-model
                            ref="requisitesForm"
                            :model="form">
                            <FieldSwitch
                                v-for="field in requisitesFormInfo"
                                :key="field.key"
                                :field="field"
                                :mainForm="mainForm"
                                :visible="init"
                                :form="form" />
                        </a-form-model>
                    </a-tab-pane>
                </a-tabs>
            </template>
            <template v-else-if="contractorsType === 'leads'">
                <a-form-model
                    ref="clientForm"
                    :model="form">
                    <!-- <template v-for="field in formInfo"> -->
                    <template v-for="field in leadFormInfo">
                        <FieldSwitch
                            v-if="dependsForm(field)"
                            :key="field.key" 
                            :field="field"
                            :mainForm="mainForm"
                            :visible="init"
                            :checkboxHidden="checkboxHidden"
                            :form="form" />
                    </template>
                </a-form-model>
            </template>
            <template slot="footer">
                <a-button
                    v-if="showCreateDPointButton"
                    type="primary"
                    size="large"
                    class="truncate"
                    :block="isMobile ? true : false"
                    :loading="loading"
                    @click="onSubmitAndDPointCreate()">
                    {{ item?.createDPointButtonText ? item.createDPointButtonText : 'Сохранить и выбрать адрес доставки' }}
                </a-button>
                <a-button 
                    type="primary"
                    size="large"
                    :loading="loading"
                    :class="isMobile ? 'mt-2' : 'ml-2'"
                    :style="isMobile && 'margin-left: 0px;'"
                    :block="isMobile ? true : false"
                    @click="onSubmit()">
                    Сохранить
                </a-button>
            </template>
        </a-modal>
    </div>
</template>

<script>
import FieldSwitch from './fields/FieldSwitch.vue'
import eventBus from '@/utils/eventBus.js'
import { replacePath } from '@/utils'
export default {
    components: {
        FieldSwitch
    },
    props: {
        item: {
            type: Object,
            required: true
        },
        updateContractor: {
            type: Function,
            default: () => {}
        },
        contractor: {
            type: [String, Number],
            default: ''
        },
        mainForm: {
            type: Object,
            required: true
        },
        contractorsType: {
            type: String,
            default: 'contractors'
        },
        pageName: {
            type: String,
            default: null
        },
    },
    computed: {
        showCreateDPointButton() {
            if('showCreateDPointButton' in this.item) {
                return this.item.showCreateDPointButton
            } else {
                return true
            }
        },
        getModalTitle() {
            if(this.edit) {
                return this.item?.editModalTitle ? this.item.editModalTitle : 'Редактировать клиента'
            } else {
                return this.item?.createModalTitle ? this.item.createModalTitle : 'Редактировать клиента'
            }
        },
        clientForm() {
            return this.item.clientForm
        },
        isMobile() {
            return this.$store.state.isMobile
        }
    },
    data() {
        return {
            edit: false,
            visible: false,
            form: {},
            loading: false,
            viewLoader: false,
            init: false,
            isDPointCreate: false,
            leadFormInfo: [],
            contractorFormInfo: [],
            contractorExtraFormInfo: [],
            contactsFormInfo: [],
            requisitesFormInfo: [],
            checkboxHidden: false,
            isContractorFromLead: false,
            leadID: null,

        }
    },
    methods: {

        dependsForm(field) {
            if(field.dependsForm) {
                let dep = []
                for(let key in field.dependsForm) {
                    if(field.dependsForm[key] === this.form[key])
                        dep.push(true)
                }

                if(dep.length === Object.keys(field.dependsForm)?.length)
                    return true
                
                return false
            } else
                return true
        },
        generatedForm(edit = false) {
            if(this.contractorsType === 'contractors') {
                if(this.clientForm.contractorFormInfoActions) {
                    const formType = edit ? 'edit' : 'save'
                    const contractorFormFields = this.clientForm.contractorFormInfoActions?.[formType] || []
                    const contractorExtraFormFields = this.clientForm.contractorExtraFormInfoActions?.[formType] || []
                    const contactsFormFields = this.clientForm.contactsFormInfoActions?.[formType] || []
                    const requisitesFormFields = this.clientForm.requisitesFormInfoActions?.[formType] || []
                    let contractorFormWidgets = []
                    let contractorExtraFormWidgets = []
                    let contactsFormWidgets = []
                    let requisitesFormWidgets = []

                    this.clientForm.formInfo.forEach(widget => {
                        const contractorFind = contractorFormFields.find(f => f === widget.key)
                        const contractorExtraFind = contractorExtraFormFields.find(f => f === widget.key)
                        const contactsFind = contactsFormFields.find(f => f === widget.key)
                        const requisitesFind = requisitesFormFields.find(f => f === widget.key)
                        if(contractorFind)
                            contractorFormWidgets.push(widget)
                        if(contractorExtraFind)
                            contractorExtraFormWidgets.push(widget)
                        if(contactsFind)
                            contactsFormWidgets.push(widget)
                        if(requisitesFind)
                            requisitesFormWidgets.push(widget)
                    })

                    this.contractorFormInfo = contractorFormWidgets
                    this.contractorExtraFormInfo = contractorExtraFormWidgets
                    this.contactsFormInfo = contactsFormWidgets
                    this.requisitesFormInfo = requisitesFormWidgets
                } else {
                    this.contractorFormInfo = this.clientForm.formInfoActions
                }
            } else if (this.contractorsType === 'leads') {
                if(this.clientForm.formInfoActions) {
                    const formType = edit ? 'edit' : 'save'
                    const formFields = this.clientForm.formInfoActions?.[formType] || []
                    let formWidgets = []

                    this.clientForm.formInfo.forEach(widget => {
                        const find = formFields.find(f => f === widget.key)
                        if(find)
                            formWidgets.push(widget)
                    })

                    this.leadFormInfo = formWidgets
                } else
                    this.leadFormInfo = this.clientForm.formInfoActions
            }
        },
        openModal(edit = false) {
            this.generatedForm(edit)
            if(edit)
                this.edit = true
            else {
                if(this.clientForm.form) {
                    this.form = JSON.parse(JSON.stringify(this.clientForm.form))
                }
            }
            this.visible = true
            this.init = true
        },
        createContractorFromLead(injectObj = null, leadID= null) {
            this.generatedForm()
            if(injectObj) {
                this.form = { ...injectObj }
                this.isContractorFromLead = true
                this.leadID = leadID
            } else if(this.clientForm.form) {
                this.form = JSON.parse(JSON.stringify(this.clientForm.form))
            }

            this.visible = true
            this.init = true
        },
        async openEdit() {
            if(this.clientForm.formActions?.view) {
                try {
                    this.viewLoader = true
                    const viewUrl = this.clientForm.formActions.view.replace('<id>', this.contractor)
                    const { data } = await this.$http.get(viewUrl)
                    this.checkboxHidden = data.registered

                    if(data) {

                        if(this.clientForm.form) {
                            this.form = JSON.parse(JSON.stringify(this.clientForm.form))
                        }

                        this.form = {
                            ...data
                        }
                        this.openModal(true)
                    }
                } catch(e) {
                    console.log(e)
                    this.$message.error('Ошибка')
                } finally {
                    this.viewLoader = false
                }
            } else {
                this.$message.error('Нет пути для получения данных')
            }
        },
        afterClose() {
            this.form = {}
            this.edit = false
            this.init = false
        },
        onSubmit() {
            this.$refs.clientForm.validate(async valid => {
                if (valid) {
                    try {
                        this.loading = true
                        if(this.edit) {
                            const queryPath = replacePath({path: this.clientForm.formActions.edit, params: this.form})
                            const { data } = await this.$http.put(queryPath, this.form)
                            if(data) {
                                this.visible = false
                                if(this.item?.widgetName === 'contractors')
                                    eventBus.$emit('need_update_contractor', data)
                                if(!this.isDPointCreate)
                                    eventBus.$emit('need_update_contractor_list')
                                this.updateContractor(data, true)
                                if(this.isDPointCreate) {
                                    eventBus.$emit('open_delivery_points_drawer', data.id)
                                    this.isDPointCreate = false
                                }
                                eventBus.$emit(`table_row_${this.pageName}`, {
                                    action: 'update',
                                    row: data
                                })

                                this.$message.info('Запись обновлена')
                            }
                        } else {
                            const { data } = await this.$http.post(this.clientForm.formActions.save, this.form)
                            if(data) {
                                this.visible = false
                                this.updateContractor(data)
                                if(!this.isDPointCreate)
                                    eventBus.$emit('need_update_contractor_list')
                                if(this.isDPointCreate) {
                                    eventBus.$emit('open_delivery_points_drawer', data.id)
                                    this.isDPointCreate = false
                                }
                                if(this.item?.widgetName === 'contractors')
                                    if(this.isContractorFromLead) {
                                        eventBus.$emit('lead_convert_to_contractor', data)
                                        eventBus.$emit('set_arhive_to_lead', this.leadID)
                                    } else {
                                        eventBus.$emit('need_add_contractor', data)
                                    }
                                eventBus.$emit(`table_row_${this.pageName}`, {
                                    action: 'create',
                                    row: data
                                })

                                this.$message.info('Запись создана')
                                this.leadID = null
                            }
                        }
                    } catch(e) {
                        if(e?.inn[0]) {
                            this.$message.error(e.inn[0])
                        }
                        else {
                            this.$message.error(e)
                        }
                        console.log(e)
                    } finally {
                        this.loading = false
                    }
                } else {
                    return false
                }
            })
        },
        onSubmitAndDPointCreate() {
            this.isDPointCreate = true
            this.onSubmit()
        }
    }
}
</script>