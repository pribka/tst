<template>
    <div class="form_wrap">
        <div class="panel">
            <div class="panel_header w-full flex justify-between">
                <div>
                    <div class="panel_title">Формирование отчета</div>
                    <div class="mt-2 panel_description">Заполните заявку на изменение плана финансирования по платежам</div>
                </div>
                <div class="panel_step">шаг 2</div>
            </div>
            <div class="grid_cols_2 row">
                <a-form-model-item 
                    class="form_item"
                    prop="date"
                    label="Дата формирования отчета">
                    <a-date-picker
                        v-model="form.date"
                        :getPopupContainer="trigger => trigger.parentElement"
                        :disabled="dateSelectIsDisabled"
                        placeholder="Укажите дату формирования отчета"
                        format="DD.MM.YYYY"
                        class="w-full"
                        size="large" />
                </a-form-model-item>
                <a-form-model-item
                    class="form_item"
                    prop="number"
                    label="Номер документа в вашей учетной системе">
                    <a-input
                        size="large"
                        :disabled="numberInputIsDisabled"
                        v-model="form.number"
                        placeholder="Введите номер документа в вашей учетной системе" />
                </a-form-model-item>
            </div>
            <div class="table-top">
                <div class="report-subtype">
                    <a-radio-group name="radioGroup" v-model="form.subtype" :disabled="viewMode">
                        <a-radio v-for="item in reportSubtypes" :key="item.id" :value="item.code">
                            <span>{{ item.name }}</span>
                        </a-radio>
                    </a-radio-group>
                </div>
                <div v-if="viewMode" class="excel-export">
                    <a-button
                        type="primary"
                        :loading="uploadGeneration"
                        @click="generateUploadFor1C">
                        Сформировать выгрузку для 1С
                    </a-button>
                </div>
            </div>
            <a-spin :spinning="tableSpinning">
                <div class="table-wrap">
                    <table class="table">
                        <tbody>
                            <tr>
                                <td colspan="6" class="left-header">Функциональная группа</td>
                                <td rowspan="6">Наименование расходов</td>
                                <td rowspan="6">Сумма изменений (+,-), всего</td>
                                <td colspan="12" rowspan="4">в том числе по месяцам (в текущем месяце - изменения с нарастающим итогом за период с начала года, в последующие месяцы - изменения помесячные)</td>
                            </tr>
                            <tr>
                                <td></td>
                                <td colspan="5" class="left-header">Функциональная подгруппа</td>
                            </tr>
                            <tr>
                                <td></td>
                                <td></td>
                                <td colspan="4" class="left-header">Администратор бюджетных программ</td>
                            </tr>
                            <tr>
                                <td></td>
                                <td></td>
                                <td></td>
                                <td colspan="3" class="left-header">Программа</td>
                            </tr>
                            <tr>
                                <td></td>
                                <td></td>
                                <td></td>
                                <td></td>
                                <td colspan="2" class="left-header">Подпрограмма</td>
                                <td rowspan="2">январь</td>
                                <td rowspan="2">февраль</td>
                                <td rowspan="2">март</td>
                                <td rowspan="2">апрель</td>
                                <td rowspan="2">май</td>
                                <td rowspan="2">июнь</td>
                                <td rowspan="2">июль</td>
                                <td rowspan="2">август</td>
                                <td rowspan="2">сентябрь</td>
                                <td rowspan="2">октябрь</td>
                                <td rowspan="2">ноябрь</td>
                                <td rowspan="2">декабрь</td>
                            </tr>
                            <tr>
                                <td></td>
                                <td></td>
                                <td></td>
                                <td></td>
                                <td></td>
                                <td class="left-header">Специфика</td>
                            </tr>
                            <TableRow
                                v-for="proposal, index in form.proposals"
                                :key="proposal.key"
                                :proposal="proposal"
                                :lastFunctionalGroup="lastFunctionalGroup"
                                :lastFunctionalSubgroup="lastFunctionalSubgroup"
                                :lastBudgetProgramAdministrator="lastBudgetProgramAdministrator"
                                :lastProgram="lastProgram"
                                :edit="edit"
                                :viewMode="viewMode"
                                :isAddProposal="isAddProposal"
                                :index="index"
                                @removeProposal="removeProposal"
                                :showDeleteButton="showDeleteButton"
                                @setTableSpinning="setTableSpinning"
                                @dropLastFunctionalGroup="dropLastFunctionalGroup"
                                @dropLastFunctionalSubgroup="dropLastFunctionalSubgroup"
                                @dropLastBudgetProgramAdministrator="dropLastBudgetProgramAdministrator"
                                @dropLastProgram="dropLastProgram" />
                            <tr class="sum-row">
                                <td></td>
                                <td></td>
                                <td></td>
                                <td></td>
                                <td></td>
                                <td></td>
                                <td></td>
                                <td class="total">{{ total }}</td>
                                <td>{{ januarySum }}</td>
                                <td>{{ februarySum }}</td>
                                <td>{{ marchSum }}</td>
                                <td>{{ aprilSum }}</td>
                                <td>{{ maySum }}</td>
                                <td>{{ juneSum }}</td>
                                <td>{{ julySum }}</td>
                                <td>{{ augustSum }}</td>
                                <td>{{ septemberSum }}</td>
                                <td>{{ octoberSum }}</td>
                                <td>{{ novemberSum }}</td>
                                <td>{{ decemberSum }}</td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </a-spin>
            <template v-if="!viewMode">
                <div class="buttons">
                    <a-button
                        class="add-button"
                        @click="addProposal">
                        Добавить
                    </a-button>
                </div>
            </template>
        </div>
        <div class="panel">
            <div class="panel_header w-full flex justify-between">
                <div>
                    <div class="panel_title">Обоснование</div>
                    <div class="mt-2 panel_description">Укажите обоснование</div>
                </div>
                <div class="panel_step">шаг 3</div>
            </div>
            <div class="rationales-wrap row">
                <Rationale
                    v-for="proposal, index in form.proposals"
                    :key="index"
                    :proposal="proposal"
                    :rationales="rationales"
                    :edit="edit"
                    :unfilled="unfilled"
                    :viewMode="viewMode" />
            </div>
        </div>
        <div class="panel">
            <div class="panel_header w-full flex justify-between">
                <div>
                    <div class="panel_title">Ответственный</div>
                    <div class="mt-2 panel_description">Укажите должность и ФИО ответственного</div>
                </div>
                <div class="panel_step">шаг 4</div>
            </div>
            <div class="row">
                <a-form-model-item 
                    class="form_item"
                    prop="responsible_position"
                    label="Укажите должность ответственного за формирование отчета">
                    <a-input
                        v-model="form.responsible_position"
                        size="large"
                        :disabled="viewMode"
                        placeholder="Должность ответственного за формирование отчета" />
                </a-form-model-item>
            </div>
            <div class="row">
                <a-form-model-item 
                    class="form_item"
                    prop="responsible_name"
                    label="Укажите ФИО ответственного за формирование отчета">
                    <a-input
                        v-model="form.responsible_name"
                        size="large"
                        :disabled="viewMode"
                        placeholder="Укажите ФИО ответственного за формирование отчета" />
                </a-form-model-item>
            </div>
        </div>
    </div>
</template>
<script>
import eventBus from '@/utils/eventBus'
import Rationale from './Rationale.vue'
import TableRow from './TableRow.vue'

export default {
    name: 'FinancePlanChange',
    components: {
        Rationale,
        TableRow,
    },
    props: {
        form: {
            type: Object,
            require: true
        },
        edit: {
            type: Boolean,
            default: false
        },
        viewMode: {
            type: Boolean,
            default: false
        },
        unfilled: {
            type: Boolean,
            default: false
        }
    },
    computed: {
        dateSelectIsDisabled() {
            return !this.form.type || this.viewMode
        },
        numberInputIsDisabled() {
            return !this.form.type || this.viewMode
        },
        showDeleteButton() {
            return this.form.proposals.length > 1
        },
        januarySum() {
            const result = this.form.proposals.reduce((sum, proposal) => {
                return sum + Number(proposal.january)
            }, 0)
            return result.toFixed(1)
        },
        februarySum() {
            const result = this.form.proposals.reduce((sum, proposal) => {
                return sum + Number(proposal.february)
            }, 0)
            return result.toFixed(1)
        },
        marchSum() {
            const result = this.form.proposals.reduce((sum, proposal) => {
                return sum + Number(proposal.march)
            }, 0)
            return result.toFixed(1)
        },
        aprilSum() {
            const result = this.form.proposals.reduce((sum, proposal) => {
                return sum + Number(proposal.april)
            }, 0)
            return result.toFixed(1)
        },
        maySum() {
            const result = this.form.proposals.reduce((sum, proposal) => {
                return sum + Number(proposal.may)
            }, 0)
            return result.toFixed(1)
        },
        juneSum() {
            const result = this.form.proposals.reduce((sum, proposal) => {
                return sum + Number(proposal.june)
            }, 0)
            return result.toFixed(1)
        },
        julySum() {
            const result = this.form.proposals.reduce((sum, proposal) => {
                return sum + Number(proposal.july)
            }, 0)
            return result.toFixed(1)
        },
        augustSum() {
            const result = this.form.proposals.reduce((sum, proposal) => {
                return sum + Number(proposal.august)
            }, 0)
            return result.toFixed(1)
        },
        septemberSum() {
            const result = this.form.proposals.reduce((sum, proposal) => {
                return sum + Number(proposal.september)
            }, 0)
            return result.toFixed(1)
        },
        octoberSum() {
            const result = this.form.proposals.reduce((sum, proposal) => {
                return sum + Number(proposal.october)
            }, 0)
            return result.toFixed(1)
        },
        novemberSum() {
            const result = this.form.proposals.reduce((sum, proposal) => {
                return sum + Number(proposal.november)
            }, 0)
            return result.toFixed(1)
        },
        decemberSum() {
            const result =  this.form.proposals.reduce((sum, proposal) => {
                return sum + Number(proposal.december)
            }, 0)
            return result.toFixed(1)
        },
        total() {
            const total = Number(this.januarySum) +
                          Number(this.februarySum) +
                          Number(this.marchSum) +
                          Number(this.aprilSum) +
                          Number(this.maySum) +
                          Number(this.juneSum) +
                          Number(this.julySum) +
                          Number(this.augustSum) +
                          Number(this.septemberSum) +
                          Number(this.octoberSum) +
                          Number(this.novemberSum) +
                          Number(this.decemberSum)
            return total.toFixed(1)
                
        }
    },
    data() {
        return {
            newProposal: {
                specificity: {
                    id: null,
                    code: null,
                    name: null
                },
                functional_group: null,
                functional_subgroup: null,
                budget_program_administrator: null,
                program: null,
                subprogram: null,
                january: 0,
                february: 0,
                march: 0,
                april: 0,
                may: 0,
                june: 0,
                july: 0,
                august: 0,
                september: 0,
                october: 0,
                november: 0,
                december: 0,
                rationale: null,
                attachments: [],
                key: 0
            },
            reportSubtypeLoading: false,
            reportSubtypes: [],
            lastFunctionalGroup: null,
            lastFunctionalSubgroup: null,
            lastBudgetProgramAdministrator: null,
            lastProgram: null,
            rationales: [],
            rationaleLoading: false,
            tableSpinning: false,
            isAddProposal: false,
            bpa: null,
            bpaLoading: false,
            uploadGeneration: false
        }
    },
    methods: {
        async generateUploadFor1C() {
            if(!this.uploadGeneration) {
                this.uploadGeneration = true
                try {
                    const { data } = await this.$http.get(`/accounting_reports/${this.form.id}/get_upload_for_1C/`, {
                        responseType: 'blob'
                    })
                    if(data) {
                        const url = window.URL.createObjectURL(new Blob([data]))
                        const link = document.createElement('a')
                        link.href = url
                        link.setAttribute('download', `Заявка на изменение плана финансирования ${this.$moment().format("DD-MM-YYYY")}.xlsx`)
                        document.body.appendChild(link)
                        link.click()
                        link.remove()
                    }
                } catch(e) {
                    console.log(e)
                    this.$message.error('Не удалось сформировать выгрузку')
                } finally {
                    this.uploadGeneration = false
                }
            }
        },
        async getBudgetProgramAdministrator() {
            if(!this.bpaLoading) {
                this.bpaLoading = true
                const params = {
                    contractor: this.form.organization
                }
                try {
                    const { data } = await this.$http.get('/accounting_catalogs/budget_program_admin_by_contractor', {
                        params
                    })
                    if(data) {
                        this.bpa = data
                    }
                } catch(e) {
                    console.log(e)
                } finally {
                    this.bpaLoading = false
                }
            }
        },
        addProposal() {
            const item = JSON.parse(JSON.stringify(this.newProposal))
            if(this.form.proposals.length) {
                this.lastProgram = this.form.proposals[this.form.proposals.length-1].program
            }
            item.functional_group = this.bpa?.functional_group ? this.bpa.functional_group : null
            item.functional_subgroup = this.bpa?.functional_subgroup ? this.bpa.functional_subgroup : null
            item.budget_program_administrator = this.bpa?.budget_program_administrator ? this.bpa.budget_program_administrator : null
            this.isAddProposal = true
            item.key = new Date().valueOf()
            this.form.proposals.push(item)
        },
        removeProposal(index, uid) {
            this.$confirm({
                title: "Вы действительно хотите удалить заявку?",
                content: '',
                okText: 'Удалить',
                okType: 'danger',
                zIndex: 2000,
                closable: true,
                maskClosable: true,
                cancelText: 'Закрыть',
                onOk: () => {
                    if(this.form.proposals.length > 1) {
                        this.form.proposals.splice(index, 1)
                    }
                },
                onCancel() {
                    eventBus.$emit(`dangerOFF_${uid}`)
                },
            })
        },
        async getReportSubtype() {
            if(!this.reportSubtypeLoading) {
                this.reportSubtypeLoading = true
                try {
                    const { data } = await this.$http.get('/accounting_reports/get_report_subtypes')
                    if(data.length) {
                        this.reportSubtypes = data
                        if(!this.edit && !this.viewMode && this.reportSubtypes) {
                            const index = this.reportSubtypes.findIndex(item => item.code === 'current')
                            if(index !== -1) {
                                return this.form.subtype = this.reportSubtypes[index].code
                            }
                        }
                    }
                } catch(e) {
                    console.log(e)
                } finally {
                    this.reportSubtypeLoading = false
                }

            }
        },
        async getRationales() {
            if(!this.rationaleLoading) {
                this.rationaleLoading = true
                try {
                    const { data } = await this.$http.get('/accounting_reports/get_rationales')
                    if(data.length) {
                        this.rationales = data
                    }
                } catch(e) {
                    console.log(e)
                } finally {
                    this.rationaleLoading = false
                }

            }
        },
        setTableSpinning(val) {
            this.tableSpinning = val
        },
        dropLastFunctionalGroup() {
            this.lastFunctionalGroup = null
        },
        dropLastFunctionalSubgroup() {
            this.lastFunctionalSubgroup = null
        },
        dropLastBudgetProgramAdministrator() {
            this.lastBudgetProgramAdministrator = null
        },
        dropLastProgram() {
            this.lastProgram = null
        }
    },
    mounted() {
        this.getReportSubtype()
        this.getRationales()
        if(!this.viewMode) {
            this.getBudgetProgramAdministrator().then(() => {
                if(this.form.proposals.length === 0 && !this.edit)
                    this.addProposal()
            }
            )
        }
    }
}
</script>
<style lang="scss" scoped>
.form_wrap{
    margin-top: 20px;
    // PANEL
    .panel {
        padding: 30px;
        border: 1px solid #e8e8e8;
        border-radius: 15px;
        .table-wrap{
            width: 100%;
            min-width: 0;
            overflow-y: auto;

            .table{
                text-decoration: none;
                border-collapse:collapse;
                width: max-content;
                text-align:center;
                .left-header{
                    text-align: left;
                }
                th{
                    font-weight:normal;
                    font-size:14px;
                    color:#ffffff;
                }
                td{
                    font-size:13px;
                    color:#354251;
                }
                th{
                    white-space:pre-wrap;
                    padding:10px 5px;
                    line-height:13px;
                    vertical-align: middle;
                }
                th, td {
                    border: 1px solid grey;
                }
                td {
                }
                .sum-row{
                    height: 35px;
                    text-align: right;
                    td {
                        padding-right: 13px;
                    }
                    .total{
                        text-align: center;
                        padding-right: 0;
                    }
                }
            }
        }
        .table-top{
            display: grid;
            grid-template-columns: 1fr auto;
            grid-template-rows: auto;
            .report-subtype{
                margin-bottom: 15px;
            }
            .excel-export{
            }


        }
        .buttons{
            width: 100%;
            text-align: left;
            margin-top: 10px;
            .add-button{
                width: 110px;
            }
            .remove-button{
                width: 110px;
                margin-left: 10px;
            }
        }
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
    .form_item::v-deep {
        .ant-form-item-label label {
            color: hsl(0, 0%, 0%, 0.6);
        }
    }
    .rationales-wrap{
        display: grid;
        row-gap: 30px;
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
}
</style>

