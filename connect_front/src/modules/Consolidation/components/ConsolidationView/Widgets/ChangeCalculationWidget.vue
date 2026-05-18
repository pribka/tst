<template>
    <div class="wrapper">
        <template v-if="report.calculations.length">
            <div class="list-header">{{$t('Reports')}}:</div>
            <div v-for="calculation in report.calculations" :key="calculation.id" class="item" @click="open(calculation.id)">
                {{ report_label(calculation) }}
            </div>
        </template>
        <template v-else-if="report.without_attachments">
            {{$t('User indicated that there are no documents for consolidation')}}
        </template>
        <template v-else>
            <div class="no-data">
                {{$t('Reports not loaded')}}
            </div>
        </template>
        <div class="buttons-wrapper">
            <div v-if="showActionButtons" class="buttons">
                <a-button
                    type="success" 
                    ghost
                    :loading="loading"
                    :disabled="approveDisabled"
                    @click="approve()">
                    {{$t('Approve')}}
                </a-button>
                <a-button
                    type="danger" 
                    ghost
                    :loading="loading"
                    :disabled="rejectDisabled"
                    @click="reject()">
                    {{$t('Send for revision')}}
                </a-button>
            </div>
        </div>
        <div class="mt-5">
            <div class="mb-1 font-semibold">
                {{$t('Comments')}}
            </div>
            <vue2CommentsComponent
                bodySelector=".wrapper"
                :related_object="report.id"
                model="report" />
        </div>
    </div>
</template>
<script>
import eventBus from '@/utils/eventBus'
import vue2CommentsComponent from '@apps/vue2CommentsComponent'

export default {
    components: {
        vue2CommentsComponent
    },
    props: {
        report: {
            type: Object,
            require: true
        },
        actions: {
            type: Object,
            default: null
        }
    },
    data() {
        return {
            loading: false,
        }
    },
    computed: {
        approveDisabled() {
            return !this.actions?.approve?.availability || this.loading
        },
        rejectDisabled() {
            return !this.actions?.reject?.availability || this.loading
        },
        showActionButtons() {
            if(this.actions && this.report) {
                return this.actions &&
                       this.actions.hasOwnProperty('approve') &&
                       this.actions.hasOwnProperty('reject') &&
                       this.report?.status?.code !== 'consolidated' &&
                       (this.report?.calculations.length || this.report.without_attachments)
            } else {
                return false
            }
        }
    },
    methods: {
        report_label(calculation) {
            let label = (`Внесение изменений в ИПФ за период с ${this.$moment(calculation.start, 'YYYY-MM-DD').format('DD.MM.YY')} `+
                         `- ${this.$moment(calculation.end, 'YYYY-MM-DD').format('DD.MM.YY')} `+
                         `(создан ${this.$moment(calculation.created_at).format('DD.MM.YY в HH:mm')})`)
            return label
        },
        open(id) {
            eventBus.$emit('view_accounting_report', id)
        },
        async approve() {
            try {
                this.loading = true
                const { data } = await this.$http.post(`/consolidation/report/${this.report.id}/approve/ `)
                if(data) {
                    this.$message.success('Отчет утвержден')
                    this.$set(this.report, 'status', data.report.status)
                    eventBus.$emit('update_report_in_list', data.report)
                    eventBus.$emit('update_consolidation_in_list', data.consolidation)
                    eventBus.$emit('update_open_consolidation', data.consolidation)
                }
            } catch(e) {
                console.log(e)
                this.$message.error((typeof e === "object" && e[0]) ? e[0] : 'Ошибка при утверждении отчета')
            } finally {
                this.loading = false
            }
        },
        async reject() {
            try {
                this.loading = true
                const { data } = await this.$http.post(`/consolidation/report/${this.report.id}/reject/ `)
                if(data) {
                    this.$message.info('Отчет направлен на доработку')
                    this.$set(this.report, 'status', data.report.status)
                    eventBus.$emit('update_report_in_list', data.report)
                    eventBus.$emit('update_consolidation_in_list', data.consolidation)
                    eventBus.$emit('update_open_consolidation', data.consolidation)
                }
            } catch(e) {
                console.log(e)
                this.$message.error((typeof e === "object" && e[0]) ? e[0] : 'Ошибка направления на доработку')
            } finally {
                this.loading = false
            }
        },
    }
}
</script>
<style lang="scss" scoped>
.wrapper{
    .list-header{
        font-weight: 600;
        margin-bottom: 20px;
    }
    .item{
        &:not(:last-child){
            margin-bottom: 10px;
            color: #1d65c0;
            cursor: pointer;
        }
    }
    .no-data{
        color: rgba(209, 213, 219);
    }
    .buttons-wrapper{
        margin-top: 20px;
        .buttons{
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            column-gap: 10px;
            width: fit-content;
            margin-left: auto;
        }
    }
}
</style>