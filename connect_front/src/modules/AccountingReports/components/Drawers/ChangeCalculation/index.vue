<template>
    <div class="form_wrap" ref="changeCalculationComponent">
        <div class="panel">
            <div class="panel_header w-full flex justify-between">
                <div>
                    <div class="panel_title">Формирование отчета</div>
                    <div class="mt-2 panel_description">Укажите данные для расчета на внесение изменений в индивидуальный план финансирования по платежам</div>
                </div>
                <div class="panel_step">шаг 2</div>
            </div>
            <div class="range">
                <a-form-model-item 
                    class="form_item"
                    prop="range_"
                    label="Укажите период отчетности">
                    <div class="date-setting">
                        <a-month-picker
                            v-model="form.month"
                            :disabled="monthPickerIsDisabled"
                            :getPopupContainer="trigger => trigger.parentElement"
                            placeholder="Укажите месяц"
                            @change="onMonthChange"
                            format="MMMM YYYY"
                            size="large" />
                        <div class="switch">
                            <span class="label">
                                С начала года
                            </span>
                            <span class="switcher">
                                <a-switch
                                    v-model="form.is_accumulated"
                                    :disabled="viewMode"
                                    @change="isAccumulatedChange" />
                            </span>
                        </div>
                    </div>
                </a-form-model-item>
                <div class="info">
                    Период формирования отчета:
                    <span v-if="form?.start && form?.end">
                        {{ $moment(form.start, 'YYYY-MM-DD').format('DD.MM.YY') }} - {{ $moment(form.end, 'YYYY-MM-DD').format('DD.MM.YY') }}
                    </span>
                    <span v-else class="no-data">
                        Не указан
                    </span>
                </div>
            </div>
            <div class="attachments">
                <a-form-model-item
                    ref="pdf_file"
                    label='Загрузите файл "Сводный отчёт по расходам по бюджетной классификации" (форма № 4-20) за указанный период в формате pdf'
                    prop="pdf_file"
                    class="form_item w-full">
                    <template v-if="viewMode">
                        <template v-if="form?.pdf_file">
                            {{ form.pdf_file.name }}.{{ form.pdf_file.extension }}
                        </template>
                        <template v-else>
                            <span class="no-data">Не загружен</span>
                        </template>
                    </template>
                    <template v-else>
                        <div v-if="fileUploadIsDisabled">
                            <div class="flex items-center">
                                <label for="pdf_file" class="ant-input ant-input-disabled ant-input-lg flex items-center truncate cursor-not-allowed">
                                    <template v-if="form.pdf_file">
                                        {{ form.pdf_file.name }}.{{ form.pdf_file.extension }}
                                    </template>
                                    <template v-else>
                                        <a-spin :spinning="fileLoading" size="small">
                                            <div class="flex items-center">
                                                <i class="fi fi-rr-cloud-upload-alt"></i>
                                                <span class="ml-2">Выбрать файл</span>
                                            </div>
                                        </a-spin>
                                    </template>
                                </label>
                                <a-button v-if="form.pdf_file" type="ui" size="large" class="ml-1" ghost flaticon icon="fi-rr-trash" disabled />
                            </div>
                            <input
                                type="file"
                                id="pdf_file"
                                style="display: none;"
                                disabled />
                        </div>
                        <div v-else>
                            <div class="flex items-center">
                                <label for="pdf_file" class="ant-input ant-input-lg flex items-center truncate cursor-pointer">
                                    <template v-if="form.pdf_file">
                                        {{ form.pdf_file.name }}.{{ form.pdf_file.extension }}
                                    </template>
                                    <template v-else>
                                        <a-spin :spinning="fileLoading" size="small">
                                            <div class="flex items-center blue_color">
                                                <i class="fi fi-rr-cloud-upload-alt"></i>
                                                <span class="ml-2">Выбрать файл</span>
                                            </div>
                                        </a-spin>
                                    </template>
                                </label>
                                <a-button v-if="form.pdf_file" type="ui" size="large" class="ml-1" ghost flaticon icon="fi-rr-trash" @click="clearReport()" />
                            </div>
                            <input
                                type="file"
                                id="pdf_file"
                                style="display: none;"
                                ref="pdf_file"
                                @change="handleFileChange"
                                accept=".pdf" />
                        </div>
                    </template>
                </a-form-model-item>
            </div>
            <template v-if="form.calculations.length">
                <a-spin :spinning="fileLoading">
                    <div class="table-wrap opacity-animation">
                        <table class="table">
                            <tbody>
                                <tr>
                                    <td colspan="6" class="left-header">Функциональная группа</td>
                                    <td rowspan="6">Наименование расходов</td>
                                    <td colspan="2" rowspan="2">План</td>
                                    <td colspan="2" rowspan="2">Факт</td>
                                    <td colspan="2" rowspan="2">Отклонение (+, -)</td>
                                </tr>
                                <tr>
                                    <td></td>
                                    <td colspan="5" class="left-header">Функциональная подгруппа</td>
                                </tr>
                                <tr>
                                    <td></td>
                                    <td></td>
                                    <td colspan="4" class="left-header">Администратор бюджетных программ</td>
                                    <td rowspan="4">к-во</td>
                                    <td rowspan="4">сумма</td>
                                    <td rowspan="4">к-во</td>
                                    <td rowspan="4">сумма</td>
                                    <td rowspan="4">к-во</td>
                                    <td rowspan="4">сумма</td>
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
                                    v-for="calculation, index in form.calculations"
                                    :key="calculation.key"
                                    :calculation="calculation"
                                    :fileData="form.fileData"
                                    :edit="edit"
                                    :viewMode="viewMode"
                                    :index="index"
                                    @removeCalculation="removeCalculation"
                                    :showDeleteButton="showDeleteButton"
                                    :isAccumulated="form.is_accumulated" />
                                <tr class="sum-row">
                                    <td></td>
                                    <td></td>
                                    <td></td>
                                    <td></td>
                                    <td></td>
                                    <td></td>
                                    <td></td>
                                    <td>{{ planQuantitySum }}</td>
                                    <td>{{ planAmountSum }}</td>
                                    <td>{{ actualQuantitySum }}</td>
                                    <td>{{ actualAmountSum }}</td>
                                    <td>{{ quantityDeviationSum }}</td>
                                    <td>{{ amountDeviationSum }}</td>
                                </tr>
                                <tr v-if="!viewMode">
                                    <td colspan="13" class="buttons-row">
                                        <div class="buttons">
                                            <a-button
                                                class="add-button"
                                                @click="addCalculation">
                                                Добавить
                                            </a-button>
                                        </div>
                                    </td>
                                </tr>
                            </tbody>
                        </table>
                    </div>
                </a-spin>
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
            <div v-if="form.calculations.length" class="rationales-wrap row opacity-animation">
                <Rationale
                    v-for="calculation, index in form.calculations"
                    :key="index"
                    :calculation="calculation"
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
import TableRow from './TableRow.vue'
import Rationale from './Rationale.vue'

export default{
    name: 'ChangeCalculation',
    components: {
        TableRow,
        Rationale
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
    data() {
        return {
            fileLoading: false,
            rationaleLoading: false,
            rationales: [],
            bpaLoading: false,
            bpa: null,  // Администратор бюджетных программ
            newCalculation: {
                specificity: {
                    id: null,
                    code: null,
                    name: null
                },
                plan_quantity: 0,
                plan_amount: 0,
                actual_quantity: 0,
                actual_amount: 0,
                attachments:[],
                functional_group: null,
                functional_subgroup: null,
                budget_program_administrator: null,
                program: null,
                subprogram: null,
                rationale: null,
                key: 0
            }
        }
    },
    computed: {
        showDeleteButton() {
            return this.form.calculations.length > 1
        },
        planQuantitySum() {
            const result = this.form.calculations.reduce((sum, calculation) => {
                return sum + Number(calculation.plan_quantity)
            }, 0)
            return result.toFixed(0)
        },
        planAmountSum() {
            const result = this.form.calculations.reduce((sum, calculation) => {
                return sum + Number(calculation.plan_amount)
            }, 0)
            return result.toFixed(2)
        },
        actualQuantitySum() {
            const result = this.form.calculations.reduce((sum, calculation) => {
                return sum + Number(calculation.actual_quantity)
            }, 0)
            return result.toFixed(0)
        },
        actualAmountSum() {
            const result = this.form.calculations.reduce((sum, calculation) => {
                return sum + Number(calculation.actual_amount)
            }, 0)
            return result.toFixed(2)
        },
        quantityDeviationSum() {
            const result = this.form.calculations.reduce((sum, calculation) => {
                return sum + (Number(calculation.actual_quantity) - Number(calculation.plan_quantity))
            }, 0)
            return result.toFixed(0)
        },
        amountDeviationSum() {
            const result = this.form.calculations.reduce((sum, calculation) => {
                return sum + (Number(calculation.actual_amount) - Number(calculation.plan_amount))
            }, 0)
            return result.toFixed(2)
        },
        fileUploadIsDisabled() {
            return !this.form.start || !this.form.end
        },
        monthPickerIsDisabled() {
            return this.form.is_accumulated || this.viewMode
        }
    },
    methods: {
        onMonthChange(date, dateString) {
            this.clearReport()
            if(date) {
                this.$set(this.form, 'month', date)
                this.$set(this.form, 'start', date.startOf('month').format('YYYY-MM-DD'))
                this.$set(this.form, 'end', date.endOf('month').format('YYYY-MM-DD'))
            } else {
                this.$set(this.form, 'start', null)
                this.$set(this.form, 'end', null)
            }
        },
        isAccumulatedChange(val) {
            this.clearReport()
            if(val) {
                this.$set(this.form, 'month', null)
                this.$set(this.form, 'start', this.$moment().startOf('year').format('YYYY-MM-DD'))
                this.$set(this.form, 'end', this.$moment().endOf('month').format('YYYY-MM-DD'))
            } else {
                this.$set(this.form, 'start', null)
                this.$set(this.form, 'end', null)
            }
        },
        addCalculation() {
            const calculation = JSON.parse(JSON.stringify(this.newCalculation))
            calculation.functional_group = this.bpa?.functional_group ? this.bpa.functional_group : null
            calculation.functional_subgroup = this.bpa?.functional_subgroup ? this.bpa.functional_subgroup : null
            calculation.budget_program_administrator = this.bpa?.budget_program_administrator ? this.bpa.budget_program_administrator : null
            calculation.key = new Date().valueOf()
            this.form.calculations.push(calculation)
        },
        removeCalculation(index, uid) {
            this.$confirm({
                title: "Вы действительно хотите удалить запись?",
                content: '',
                okText: 'Удалить',
                okType: 'danger',
                zIndex: 2000,
                closable: true,
                maskClosable: true,
                cancelText: 'Закрыть',
                onOk: () => {
                    if(this.form.calculations.length > 1) {
                        this.form.calculations.splice(index, 1)
                    }
                },
                onCancel() {
                    eventBus.$emit(`dangerOFF_${uid}`)
                },
            })
        },
        async handleFileChange(event) {
            const file = Object.values(event.target.files)[0]
            if(file) {
                try {
                    this.fileLoading = true
                    let formData = new FormData()
                    formData.append("upload", file)
                    formData.append("contractor", this.form.organization)
                    const {data} = await this.$http.post('/accounting_reports/expense_report/', formData, {
                        headers: {
                            "Content-Type": "multipart/form-data"
                        }
                    })
                    if(data?.file && data?.file_data.length) {
                        this.clearReport()
                        this.form.pdf_file = data.file
                        this.form.fileData = data.file_data
                        this.addCalculation()
                    } else {
                        this.clearReport()
                        this.$message.error('Не удалось получить данные из файла')
                    }
                } catch(e) {
                    this.clearReport()
                    this.$message.error('Ошибка при получении данных из файла')
                    console.log(e)
                } finally {
                    this.fileLoading = false
                }
            }
        },
        clearReport() {
            this.form.pdf_file = null
            this.form.fileData = new Array()
            if(this.$refs.pdf_file?.value) {
                this.$refs.pdf_file.value = ''
            }
            this.$set(this.form, 'calculations', new Array())
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
    },
    mounted() {
        this.getRationales()
        if(!this.viewMode || !this.edit)
            this.getBudgetProgramAdministrator()
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
        .range{
            margin-bottom: 30px;
            .date-setting{
                display: grid;
                grid-template-columns: repeat(2, max-content);
                column-gap: 30px;
                .switch {
                    display: grid;
                    grid-template-columns: repeat(2, auto);
                    grid-template-rows: auto;
                    column-gap: 30px;
                    width: fit-content;
                    align-items: center;
                    .label{
                        line-height: normal;
                    }
                    .switcher{
                    }
                }
            }
            .info{
                margin-top: 30px;
            }
        }
        .label-text{
            margin-bottom: 1.25rem;
        }
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
        .table-wrap{
            width: 100%;
            min-width: 0;
            overflow-y: auto;
            margin-top: 30px;

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
                .buttons-row{
                    border: 0;
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
    .no-data{
        color: rgb(209 213 219);
    }
    // END FORM
}
</style>