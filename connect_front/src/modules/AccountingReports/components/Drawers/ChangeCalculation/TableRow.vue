<template>
    <tr class="table-row">
        <td class="functional-group" :class="danger && 'danger'">
            <!-- Функциональная группа -->
            <a-tooltip placement="right" :overlayStyle="{zIndex: 1100}">
                <template slot="title">
                    {{calculation.functional_group.name}}
                </template>
                {{calculation.functional_group.code}}
            </a-tooltip>
        </td>
        <td class="functional-sub-group" :class="danger && 'danger'">
            <!-- Функциональная подгруппа -->
            <a-tooltip placement="right" :overlayStyle="{zIndex: 1100}">
                <template slot="title">
                    {{calculation.functional_subgroup.name}}
                </template>
                {{calculation.functional_subgroup.code}}
            </a-tooltip>
        </td>
        <td class="budget-program-administrator" :class="danger && 'danger'">
            <!-- Администратор бюджетных программ -->
            <a-tooltip placement="right" :overlayStyle="{zIndex: 1100}">
                <template slot="title">
                    {{calculation.budget_program_administrator.name}}
                </template>
                {{calculation.budget_program_administrator.code}}
            </a-tooltip>
        </td>
        <td class="program">
            <!-- Программа -->
            <a-select
                v-model="calculation.program"
                :disabled="programSelectIsDisabled" >
                <a-select-option
                    v-for="program in fileData"
                    :key="program.id"
                    :value="program.id">
                    <a-tooltip placement="right" :overlayStyle="{zIndex: 1100}" :class="danger && 'danger'">
                        <template slot="title">
                            {{program.name}}
                        </template>
                        {{program.code}}
                    </a-tooltip>
                </a-select-option>
            </a-select>
        </td>
        <td class="subprogram">
            <!-- Подпрограмма -->
            <a-select
                v-model="calculation.subprogram"
                :disabled="subProgramSelectIsDisabled" >
                <a-select-option
                    v-for="subprogram in subprograms"
                    :key="subprogram.id"
                    :value="subprogram.id">
                    <a-tooltip placement="right" :overlayStyle="{zIndex: 1100}" :class="danger && 'danger'">
                        <template slot="title">
                            {{subprogram.name}}
                        </template>
                        {{subprogram.code}}
                    </a-tooltip>
                </a-select-option>
            </a-select>
        </td>
        <td class="specificity-code">
            <!-- Специфика -->
            <a-select
                v-model="calculation.specificity.id"
                :disabled="specificitySelectIsDisabled" >
                <a-select-option
                    v-for="specificity in specificities"
                    :key="specificity.id"
                    :value="specificity.id">
                    <a-tooltip placement="right" :overlayStyle="{zIndex: 1100}" :class="danger && 'danger'">
                        <template slot="title">
                            {{specificity.name}}
                        </template>
                        {{specificity.code}}
                    </a-tooltip>
                </a-select-option>
            </a-select>
        </td>
        <td class="specificity" :class="danger && 'danger'">
            <div v-if="calculation.specificity.name">
                {{ calculation.specificity.name }}
            </div>
            <div v-else class="no-data">
                Не выбрана
            </div>
        </td>
        <td class="value-cell">
            <a-input-number
                v-model="calculation.plan_quantity"
                :precision=0
                class="quantity-input"
                :class="danger && 'danger'"
                :disabled="viewMode || !calculation.specificity.id" />
        </td>
        <td class="value-cell pr-3" :class="danger && 'danger'">{{ calculation.plan_amount }}</td>
        <td class="value-cell">
            <a-input-number
                v-model="calculation.actual_quantity"
                :precision=0
                class="quantity-input"
                :class="danger && 'danger'"
                :disabled="viewMode || !calculation.specificity.id" />
        </td>
        <td class="value-cell pr-3" :class="danger && 'danger'">{{ calculation.actual_amount }}</td>
        <td class="value-cell pr-3" :class="danger && 'danger'">{{ quantityDeviation }}</td>
        <td class="value-cell pr-3" :class="danger && 'danger'">{{ amountDeviation }}</td>
        <td class="borderless" v-if="!viewMode"><a-button v-if="showDeleteButton" type="danger" icon="delete" @click="removeCalculation"/></td>
    </tr>
</template>

<script>
import eventBus from '@/utils/eventBus'

export default {
    name: 'TableRow',
    props: {
        calculation: {
            type: Object,
            require: true
        },
        index: {
            type: Number,
            require: true
        },
        fileData: {
            type: Array,
            default: null
        },
        edit: {
            type: Boolean,
            default: false
        },
        viewMode: {
            type: Boolean,
            default: false
        },
        isAccumulated: {
            type: Boolean,
            default: false
        },
        showDeleteButton: {
            type: Boolean,
            default: true
        }
    },
    data() {
        return {
            subprograms: [],
            specificities: [],
            danger: false
        }
    },
    created() {
        if(this.calculation.program) {
            const p_index = this.fileData.findIndex(program => program.id === this.calculation.program)
            if(p_index !== -1) {
                this.subprograms = this.fileData[p_index].subprograms
                if(this.calculation.subprogram) {
                    const sp_index = this.subprograms.findIndex(subprogram => subprogram.id === this.calculation.subprogram)
                    if(sp_index !== -1) {
                        this.specificities = this.subprograms[sp_index].specifics
                    }
                }
            }
        } else {
            if(this.fileData.length === 1) {
                this.calculation.program = this.fileData[0].id
            }
        }
        eventBus.$on(`dangerOFF_${this._uid}`, () => {
            this.danger = false
        })
    },
    beforeDestroy() {
        eventBus.$off(`dangerOFF_${this._uid}`)
    },
    watch: {
        'calculation.program': {
            handler: async function(val) {
                if(val) {
                    const index = this.fileData.findIndex(program => program.id === val)
                    if(index !== -1) {
                        this.dropCalculation()
                        this.subprograms = []
                        this.calculation.subprogram = null
                        this.specificities = []
                        this.calculation.attachments = new Array()
                        this.calculation.rationale = null
                        this.calculation.specificity.id = null
                        this.calculation.specificity.code = null
                        this.calculation.specificity.name = null
                        this.subprograms = this.fileData[index].subprograms
                        if(this.subprograms.length === 1) {
                            this.calculation.subprogram = this.subprograms[0].id
                        }
                    }
                }
            },
        },
        'calculation.subprogram': {
            handler: async function(val) {
                if(val) {
                    const index = this.subprograms.findIndex(subprogram => subprogram.id === val)
                    if(index !== -1) {
                        this.dropCalculation()
                        this.specificities = []
                        this.calculation.attachments = new Array()
                        this.calculation.rationale = null
                        this.calculation.specificity.id = null
                        this.calculation.specificity.code = null
                        this.calculation.specificity.name = null
                        this.specificities = this.subprograms[index].specifics
                        if(this.specificities.length === 1) {
                            this.calculation.actual_amount = this.getActualAmount(this.specificities[0])
                            this.calculation.specificity.id = this.specificities[0].id
                            this.calculation.plan_amount = this.specificities[0]?.plan_amount ? this.specificities[0].plan_amount : 0
                            this.calculation.specificity.name = this.specificities[index].name
                            this.calculation.specificity.code = this.specificities[index].code
                        }
                    }
                }
            },
        },
        'calculation.specificity.id': {
            handler: async function(val) {
                if(val) {
                    this.dropCalculation()
                    const index = this.specificities.findIndex(specificity => specificity.id === val)
                    if(index !== -1) {
                        this.calculation.plan_amount = this.specificities[index]?.plan_amount ? this.specificities[index].plan_amount : 0
                        this.calculation.actual_amount = this.getActualAmount(this.specificities[index])
                        this.calculation.specificity.name = this.specificities[index].name
                        this.calculation.specificity.code = this.specificities[index].code
                        this.calculation.rationale = null
                        this.calculation.attachments = new Array()
                    }
                }
            },
        },
    },
    computed: {
        programSelectIsDisabled() {
            return this.viewMode
        },
        subProgramSelectIsDisabled() {
            return this.viewMode || this.subprograms.length === 0
        },
        specificitySelectIsDisabled() {
            return this.viewMode || this.specificities.length === 0
        },
        quantityDeviation() {
            const deviation = this.calculation.actual_quantity - this.calculation.plan_quantity
            return deviation.toFixed(0)
        },
        amountDeviation() {
            const deviation = this.calculation.actual_amount - this.calculation.plan_amount
            return deviation.toFixed(2)
        },
    },
    methods: {
        dropCalculation() {
            this.calculation.plan_quantity = 0
            this.calculation.plan_amount = 0
            this.calculation.actual_quantity = 0
            this.calculation.actual_amount = 0
        },
        getActualAmount(specificity) {
            if(this.isAccumulated) {
                return specificity?.actual_amount_accumulated ? specificity.actual_amount_accumulated : 0
            } else {
                return specificity?.actual_amount ? specificity.actual_amount : 0
            }
        },
        removeCalculation() {
            this.danger = true
            this.$emit('removeCalculation', this.index, this._uid)
        }
    }
}
</script>

<style lang="scss" scoped>
.table-row{
    .danger{
        color: red;
    }
    td{
        font-size:13px;
        border: 1px solid grey;
    }
    .borderless{
        border: 0;
        padding-left: 10px;
    }
    .functional-group, .functional-sub-group, .budget-program-administrator, .program, .subprogram, .row-sum, .specificity-code{
        width: 75px; 
    }
    .specificity{
        width: 200px;
    }
    .value-cell{
        width: 115px;
        text-align: right;
        .quantity-input{
            width: 100%;
        }
    }
    .no-data{
        color: rgb(185, 185, 185);
    }
    &::v-deep{
        .ant-input-number .ant-input-number-handler-wrap {
            display: none;
        }
        .ant-input-number-input {
            text-align: right;
        }
    }
}
    
</style>