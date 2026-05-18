<template>
    <tr class="table-row">
        <td class="functional-group" :class="danger && 'danger'">
            <!-- Функциональная группа -->
            <a-tooltip placement="right" :overlayStyle="{zIndex: 1100}">
                <template slot="title">
                    {{proposal.functional_group?.name}}
                </template>
                {{proposal.functional_group?.code}}
            </a-tooltip>
        </td>
        <td class="functional-sub-group" :class="danger && 'danger'">
            <!-- Функциональная подгруппа -->
            <a-tooltip placement="right" :overlayStyle="{zIndex: 1100}">
                <template slot="title">
                    {{proposal.functional_subgroup?.name}}
                </template>
                {{proposal.functional_subgroup?.code}}
            </a-tooltip>
        </td>
        <td class="budget-program-administrator" :class="danger && 'danger'">
            <!-- Администратор бюджетных программ -->
            <a-tooltip placement="right" :overlayStyle="{zIndex: 1100}">
                <template slot="title">
                    {{proposal.budget_program_administrator?.name}}
                </template>
                {{proposal.budget_program_administrator?.code}}
            </a-tooltip>
        </td>
        <td class="program">
            <!-- Программа -->
            <a-select
                v-model="proposal.program"
                :loading="programLoading"
                :disabled="viewMode || !proposal.budget_program_administrator" >
                <a-select-option
                    v-for="program, index in programs"
                    :key="index"
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
                v-model="proposal.subprogram"
                :loading="subprogramLoading"
                :disabled="viewMode || !proposal.program" >
                <a-select-option
                    v-for="subprogram, index in subprograms"
                    :key="index"
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
                v-model="proposal.specificity.id"
                :loading="specificityLoading"
                :disabled="viewMode || !proposal.program" >
                <a-select-option
                    v-for="specificity, index in specificities"
                    :key="index"
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
            <div v-if="proposal.specificity.name">
                {{ proposal.specificity.name }}
            </div>
            <div v-else class="no-data">
                Не выбрана
            </div>
        </td>
        <td class="row-sum" :class="danger && 'danger'">{{ rowSum }}</td>
        <td class="value-cell"><a-input-number :precision=1 v-model="proposal.january" :disabled="viewMode" :class="danger && 'danger'" /></td>
        <td class="value-cell"><a-input-number :precision=1 v-model="proposal.february" :disabled="viewMode" :class="danger && 'danger'" /></td>
        <td class="value-cell"><a-input-number :precision=1 v-model="proposal.march" :disabled="viewMode" :class="danger && 'danger'" /></td>
        <td class="value-cell"><a-input-number :precision=1 v-model="proposal.april" :disabled="viewMode" :class="danger && 'danger'" /></td>
        <td class="value-cell"><a-input-number :precision=1 v-model="proposal.may" :disabled="viewMode" :class="danger && 'danger'" /></td>
        <td class="value-cell"><a-input-number :precision=1 v-model="proposal.june" :disabled="viewMode" :class="danger && 'danger'" /></td>
        <td class="value-cell"><a-input-number :precision=1 v-model="proposal.july" :disabled="viewMode" :class="danger && 'danger'" /></td>
        <td class="value-cell"><a-input-number :precision=1 v-model="proposal.august" :disabled="viewMode" :class="danger && 'danger'" /></td>
        <td class="value-cell"><a-input-number :precision=1 v-model="proposal.september" :disabled="viewMode" :class="danger && 'danger'" /></td>
        <td class="value-cell"><a-input-number :precision=1 v-model="proposal.october" :disabled="viewMode" :class="danger && 'danger'" /></td>
        <td class="value-cell"><a-input-number :precision=1 v-model="proposal.november" :disabled="viewMode" :class="danger && 'danger'" /></td>
        <td class="value-cell"><a-input-number :precision=1 v-model="proposal.december" :disabled="viewMode" :class="danger && 'danger'" /></td>
        <td class="borderless" v-if="!viewMode"><a-button v-if="showDeleteButton" type="danger" icon="delete" @click="removeProposal"/></td>
    </tr>
</template>

<script>
import eventBus from '@/utils/eventBus'

export default {
    name: 'TableRow',
    props: {
        proposal: {
            type: Object,
            require: true
        },
        index: {
            type: Number,
            require: true
        },
        lastProgram: {
            type: String,
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
        isAddProposal: {
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
            programs: [],
            programLoading: false,
            subprograms: [],
            subprogramLoading: false,
            specificities: [],
            specificityLoading: false,
            isCellFilling: false,
            danger: false
        }
    },
    created() {
        eventBus.$on(`dangerOFF_${this._uid}`, () => {
            this.danger = false
        })
    },
    beforeDestroy() {
        eventBus.$off(`dangerOFF_${this._uid}`)
    },
    computed: {
        rowSum() {
            const rowSum = Number(this.proposal.january)+
                           Number(this.proposal.february)+
                           Number(this.proposal.march)+
                           Number(this.proposal.april)+
                           Number(this.proposal.may)+
                           Number(this.proposal.june)+
                           Number(this.proposal.july)+
                           Number(this.proposal.august)+
                           Number(this.proposal.september)+
                           Number(this.proposal.october)+
                           Number(this.proposal.november)+
                           Number(this.proposal.december)
            return rowSum.toFixed(1)
        },
    },
    watch: {
        'proposal.program': {
            handler: async function(val) {
                if(val && !this.isCellFilling) {
                    this.proposal.subprogram = null
                    this.subprograms = []
                    this.proposal.specificity.id = null
                    this.proposal.specificity.code = null
                    this.proposal.specificity.name = null
                    this.getSubPrograms(val)
                    if(this.specificities.length === 0)
                        this.getSpecificities()
                }
            },
        },
        'proposal.specificity.id': {
            handler: async function(val) {
                if(val) {
                    const index = this.specificities.findIndex(specificity => specificity.id === val)
                    if(index !== -1) {
                        this.proposal.specificity.name = this.specificities[index].name
                        this.proposal.specificity.code = this.specificities[index].code
                        this.proposal.rationale = null
                        this.proposal.attachments = new Array()
                    }
                }
            },
        },
    },
    methods: {
        async getPrograms() {
            if(!this.programLoading) {
                this.programLoading = true
                const params = {
                    budget_program_administrator: this.proposal.budget_program_administrator.id
                }
                try {
                    const { data } = await this.$http.get('/accounting_catalogs/get_programs', {
                        params
                    })
                    if(data.length) {
                        this.programs = data
                        if(!this.viewMode && this.lastProgram) {
                            this.proposal.program = this.lastProgram
                            this.$emit('dropLastProgram')
                        }
                    }
                } catch(e) {
                    console.log(e)
                } finally {
                    this.programLoading = false
                }

            }
        },
        async getSubPrograms(program) {
            if(!this.subprogramLoading) {
                this.subprogramLoading = true
                const params = {
                    program: program
                }
                try {
                    const { data } = await this.$http.get('/accounting_catalogs/get_subprograms', {
                        params
                    })
                    if(data.length) {
                        this.subprograms = data
                    }
                } catch(e) {
                    console.log(e)
                } finally {
                    this.subprogramLoading = false
                }

            }
        },
        async getSpecificities() {
            if(!this.specificityLoading) {
                this.specificityLoading = true
                try {
                    const { data } = await this.$http.get('/accounting_reports/get_specificities')
                    if(data.length) {
                        this.specificities = data
                    }
                } catch(e) {
                    console.log(e)
                } finally {
                    this.specificityLoading = false
                }

            }
        },
        async fillCells() {
            this.$emit('setTableSpinning', true)
            this.isCellFilling = true
            await this.getPrograms(this.proposal.budget_program_administrator)
            await this.getSubPrograms(this.proposal.program)
            await this.getSpecificities()
            this.isCellFilling = false
            this.$emit('setTableSpinning', false)
        },
        removeProposal() {
            this.danger = true
            this.$emit('removeProposal', this.index, this._uid)
        }
    },
    mounted() {
        this.getPrograms()
        if((this.edit && !this.isAddProposal) ||  this.viewMode) {
            this.fillCells()
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
        width: 55px;
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