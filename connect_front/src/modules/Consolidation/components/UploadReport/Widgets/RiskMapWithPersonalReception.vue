<template>
    <div class="risk-map-with-personal-reception-wrapper">
        <div class="switch">
            <span class="label">
                {{ $t('No personal reception in reporting period') }}
            </span>
            <span class="switcher">
                <a-switch
                    v-model="form.no_personal_reception"
                    :loading="loading"
                    :disabled="loading"
                    @change="noPersonalReceptionIsChange"/>
            </span>
        </div>

        <template v-if="!form.no_personal_reception">
            <div class="personal-reception-count" ref="issue-quantity">
                <div class="label" :class="isPersonalReceptionRequired && 'ant-form-item-required'">
                    {{ $t('Number of personal receptions held') }}
                </div>
                <div class="input input-number">
                    <a-form-model-item
                        ref="personal_reception_quantity"
                        prop="personal_reception_quantity">
                        <a-input-number
                            :disabled="isIssueListEmpty"
                            v-model="form.personal_reception_quantity"
                            :formatter="value => `$ ${value}`.replace(/\D/g, '')"/>
                    </a-form-model-item>
                </div>
            </div>

            <a-alert
                v-if="isIssueListEmpty"
                :message="$t('No appeals')"
                :description="alertDescription"
                type="info"
                show-icon/>

            <div v-else class="issues-table">
                <div class="table-header">
                    <div class="column">{{ $t('Appeal number') }}</div>
                    <div class="column">{{ $t('Appeal date') }}</div>
                    <div class="column">{{ $t('Status') }}</div>
                    <div class="column">{{ $t('Days in queue') }}</div>
                </div>

                <div class="table-body">
                    <div
                        v-for="issue in form.personal_reception_issues"
                        :key="issue.id"
                        class="row"
                        :ref="`issue-${issue.id}`">
                        <div class="cell">{{ issue.number }}</div>
                        <div class="cell">
                            {{ $moment(issue.issue_date).format('DD.MM.YYYY') }}
                        </div>
                        <div class="cell">{{ issue.personal_reception?.status }}</div>
                        <div
                            class="cell input-number"
                            :class="(showFormError && issue.personal_reception?.status_code === 'in_queue' && issue.personal_reception?.days_in_queue === null) && 'ant-form-item-control has-error'">
                            <a-input-number
                                v-if="issue.personal_reception && Object.hasOwn(issue.personal_reception, 'days_in_queue')"
                                class="w-full"
                                :disabled="issue.personal_reception?.status_code === 'completed'"
                                v-model="issue.personal_reception.days_in_queue"
                                :formatter="value => `$ ${value}`.replace(/\D/g, '')"/>
                        </div>
                    </div>
                </div>

                <div class="table-footer">
                    <div class="cell">
                        {{ $t('Total: {count}', { count: form.personal_reception_issues ? form.personal_reception_issues.length : '' }) }}
                    </div>
                </div>
            </div>
        </template>
    </div>
</template>
<script>
import eventBus from '@/utils/eventBus'

export default {
    name: 'RiskMapWithPersonalReception',
    props: {
        report: {
            type: Object,
            required: true
        },
        form: {
            type: Object,
            required: true
        },
        showFormError: {
            type: Boolean,
            required: false
        },
        edit: {
            type: Boolean,
            default: false
        },
        isPersonalReceptionRequired: {
            type: Boolean,
            default: true
        },
        period: {
            type: String,
            default: ''
        }
    },
    data() {
        return {
            loading: false,
            isIssueListEmpty : false,
        }
    },
    created() {
        eventBus.$on('scroll_to_error', () => {
            const errorFieldID = this.getErrorFieldID()
            if (errorFieldID) this.scrollToItem(errorFieldID)
        })
        if (!this.form.no_personal_reception) {
            eventBus.$emit('add-personal-reception', true)
            this.getIssues()
        }
    },
    beforeDestroy() {
        eventBus.$off('scroll_to_error')
    },
    computed: {
        alertDescription() {
            return `Обращения с категорией вопроса "Личный прием заявителей" за период${this.period ? ` ${this.period} ` : ' '}отсутствуют`
        }
    },
    methods: {
        getErrorFieldID() {
            const errorIssue = this.form.personal_reception_issues.find(issue => issue.personal_reception.status_code === 'in_queue' && issue.personal_reception.days_in_queue === null)
            const errorQuantity = this.form.personal_reception_quantity === null ? 'quantity' : null
            return errorQuantity || errorIssue.id
        },
        scrollToItem(id) {
            const el = this.$refs[`issue-${id}`]
            if (!el) return

            if (Array.isArray(el) && el[0]) {
                el[0].scrollIntoView({ behavior: "smooth" })
            } else {
                el.scrollIntoView({ behavior: "smooth" })
            }
        },
        noPersonalReceptionIsChange(val) {
            eventBus.$emit('add-personal-reception', !val)
            if (val) {
                this.form.personal_reception_issues = []
                this.form.personal_reception_quantity = null
            } else {
                this.getIssues()
            }
        },
        async getIssues() {
            this.loading = true
            try {
                const params = {
                    report: this.report.id,
                }
                const { data } = await this.$http.get('/risk_assessment/personal_reception/', { params })
                if (!this.report.personal_reception_is_edit) {
                    data.forEach(issue => {
                        issue.personal_reception.days_in_queue = null
                    })
                }
                this.$set(this.form, 'personal_reception_issues', data)
                this.isIssueListEmpty = this.form.personal_reception_issues.length === 0
                if (this.isIssueListEmpty)
                    this.form.personal_reception_quantity = null
            }
            catch(e) {
                console.log(e)
                this.$message.error('Ошибка загрузки данных об обращениях')
            }
            finally {
                this.loading = false
            }
        }
    }

}
</script>
<style lang="scss" scoped>
.risk-map-with-personal-reception-wrapper {
    .switch {
    display: grid;
    grid-template-columns: 1fr auto;
    grid-template-rows: auto;
    column-gap: 30px;
    width: 100%;
    margin-bottom: 20px;
    align-items: center;
    .label {
        line-height: normal;
    }
    .switcher {}
    }
    .personal-reception-count {
    width: 90%;
    display: grid;
    grid-template-columns: auto 130px;
    column-gap: 30px;
    line-height: normal;
    }
    .input-number::v-deep{
        .ant-input-number .ant-input-number-handler-wrap {
            display: none;
        }
        .ant-input-number{
            width: 100%;
        }
        .ant-input-number-input {
            text-align: right;
        }
    }
    .issues-table {
        .table-header {
            line-height: normal;
            background-color: #f8f8f8;
            border: 1px solid #babfc7;
            border-radius: 8px 8px 0 0;
            display: flex;
            width: 100%;
            justify-content: space-between;
            align-items: center;
            font-weight: 700;
            color: #181d1f;
            font-size: 13px;
            .column {
                flex: 1;
                text-align: center;
                padding: 3px 0;
                position: relative;
            }
            .column:not(:last-child)::after {
                content: "|";
                position: absolute;
                right: -10px;
                top: 50%;
                transform: translateY(-50%);
                color: #babfc7;
            }
        }
        .table-body {
            max-height: 200px;
            overflow-y: auto;
            width: 100%;
            line-height: normal;
            border-left: 1px solid #babfc7;
            border-right: 1px solid #babfc7;
            .row{
                display: flex;
                width: 100%;
                justify-content: space-between;
                align-items: center;
                .cell {
                    flex: 1;
                    text-align: left;
                    padding: 3px 3px 3px 17px;
                }
            }
            .row:not(:last-child) {
                border-bottom: 1px solid #babfc7;
            }
        }
        .table-footer {
            line-height: normal;
            background-color: #f8f8f8;
            border: 1px solid #babfc7;
            border-radius: 0 0 8px 8px;
            width: 100%;
            padding: 10px 10px 10px 17px;
            font-weight: 700;
            color: #181d1f;
            font-size: 13px;
        }
    }
}
</style>