export default {
    methods: {
        getReportTypeObj(type) {
            let moment = this.$moment
            let set = this.$set

            class ReportType {
                formValidation() {}
                formPrepare() {}
                fillSpecificFormFields() {}
            }
            
            class ChangeCalculationReportType extends ReportType {
                formValidation(form) {
                    return form.calculations.length ? form.calculations.every(calculation => calculation.rationale) : false
                }
                formPrepare(form) {
                    delete form.range
                    delete form.fileData
                    form.pdf_file = form.pdf_file.id
                    let calculations = JSON.parse(JSON.stringify(form.calculations))
                    calculations.forEach(each => {
                        delete each.key
                        each.functional_group = each.functional_group.id
                        each.functional_subgroup = each.functional_subgroup.id
                        each.budget_program_administrator = each.budget_program_administrator.id
                        each.specificity = each.specificity.id
                        each.attachments = each.attachments.map(file => {
                            return file.id
                        })
                    })
                    form.calculations = calculations
                }
                fillSpecificFormFields(form, data) {
                    form.start = data.start
                    form.end = data.end
                    set(form, 'range', [
                        moment(data.start, 'YYYY-MM-DD'),
                        moment(data.end, 'YYYY-MM-DD')
                    ])
                    form.responsible_position = data.responsible_position
                    form.responsible_name = data.responsible_name
                    form.pdf_file = data.pdf_file
                    form.calculations = data.calculations
                    form.fileData = data.file_data
                    form.is_accumulated = data.is_accumulated
                }
            }
            
            class FinancePlanChangeReportType extends ReportType {
                formValidation(form) {
                    return form.proposals.length ? form.proposals.every(proposal => proposal.rationale) : false
                }
                formPrepare(form) {
                    form.date = moment(form.date).format('YYYY-MM-DD')
                    let proposals = JSON.parse(JSON.stringify(form.proposals))
                    proposals.forEach(each => {
                        delete each.key
                        each.functional_group = each.functional_group.id
                        each.functional_subgroup = each.functional_subgroup.id
                        each.budget_program_administrator = each.budget_program_administrator.id
                        each.specificity = each.specificity.id
                        each.attachments = each.attachments.map(file => {
                            return file.id
                        })
                    })
                    form.proposals = proposals
                }
                fillSpecificFormFields(form, data) {
                    form.proposals = data.proposals
                    form.subtype = data.subtype.code
                    form.responsible_position = data.responsible_position
                    form.responsible_name = data.responsible_name
                    form.date = moment(data.date, 'YYYY-MM-DD')
                    form.number = data.number
                }
            }

            if (type === 'change_calculation') return new ChangeCalculationReportType()
            if (type === 'finance_plan_change') return new FinancePlanChangeReportType()

            return new ReportType()
        }
    }
}