<template><div class="wrapper">
    <div class="switch">
        <span class="label">
            {{ $t('No IPF applications for the specified period') }}
        </span>
        <span class="switcher">
            <a-switch
                v-model="form.without_attachments"
                @change="noChangesIsChange"/>
        </span>
    </div>

    <a-spin :spinning="loading">
        <div v-if="showEmpty">
            <div v-if="showInfo" class="info">
                {{ $t('Could not get reports for the specified period') }}
            </div>
            <a-empty :description="false" />
        </div>
        <div v-else class="list">
            <a-checkbox-group
                v-model="form.ipf_proposals"
                :disabled="form.without_attachments">
                <div v-for="report in reports" :key="report.id" class="item">
                    <div
                        class="name"
                        :class="form.without_attachments && 'no-data'">
                        {{ $t('Report № {number} dated {date}, request type - "{subtype}"', {
                            number: report.number,
                            date: $moment(report.date).format('DD MMMM YYYYг.'),
                            subtype: report.subtype.name
                        }) }}
                    </div>
                    <div class="checkbox">
                        <a-checkbox :value="report.id" />
                    </div>
                </div>
            </a-checkbox-group>
        </div>
    </a-spin>
</div>

</template>
<script>
export default{
    name: 'AddIpfProposalReports',
    props: {
        consolidation: {
            type: Object,
            required: true
        },
        report: {
            type: Object,
            required: true
        },
        form: {
            type: Object,
            required: true
        },
        file: {
            type: Object,
            required: true
        },
    },
    data() {
        return {
            loading: false,
            showInfo: false,
            showEmpty: false,
            reports: [],
        }
    },
    mounted() {
        if(!('ipf_proposals' in this.form)) {
            this.$set(this.form, 'ipf_proposals', this.report.ipf_proposals.map(proposal => proposal.id)
            )
        }
        this.getReports()
    },
    methods: {
        noChangesIsChange(val) {
            if(val) {
                this.form.ipf_proposals = new Array()
            }
        },
        async getReports() {
            if(!this.loading) {
                try {
                    this.loading = true
                    const params = {
                        start: this.consolidation.start,
                        end: this.consolidation.end,
                        organization: this.report.contractor.id,
                        subtype: this.consolidation?.ipf_proposal_extra?.subtype?.code ? this.consolidation?.ipf_proposal_extra?.subtype?.code : null,
                        report_type: 'finance_plan_change',
                    }
                    const { data } = await this.$http.get('/accounting_reports/get_reports', {
                        params
                    })
                    if(data.length) {
                        this.reports = data
                        if(!this.form.without_attachments && !this.form.ipf_proposals.length)
                            this.form.ipf_proposals = this.reports.map(report => report.id)
                    } else {
                        this.showInfo = true
                        this.showEmpty = true
                    }
                } catch(e) {
                    console.log(e)
                    this.showInfo = true
                    this.showEmpty = true
                } finally {
                    this.loading = false
                }
            }
        }
    }
}
</script>
<style lang="scss" scoped>
.wrapper{
    .switch {
        display: grid;
        grid-template-columns: 1fr auto;
        grid-template-rows: auto;
        column-gap: 30px;
        width: 100%;
        margin-bottom: 20px;
        align-items: center;
        .label{
            line-height: normal;
        }
        .switcher{
        }
    }
    .list{
        .ant-checkbox-group{
            width: 100%;
            .item{
                display: grid;
                grid-template-columns: 1fr auto;
                column-gap: 30px;
                padding: 5px;
                align-items: center;
                padding-top: 10px;
                &:not(:last-child){
                        padding-bottom: 10px;
                        border-bottom: 1px solid var(--Neutral-5, #D9D9D9);
                    }
                .name{
                    width: auto;
                }
                .checkbox{}
            }
        }
    }
    .info{
        margin-bottom: 20px;
    }
}
</style>