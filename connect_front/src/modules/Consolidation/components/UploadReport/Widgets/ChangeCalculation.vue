<template>
    <div class="wrapper">
        <div class="switch">
            <span class="label">
                {{ $t('No changes in IPF for the specified period') }}
            </span>
            <span class="switcher">
                <a-switch
                    v-model="form.without_attachments"
                    @change="noChangesIsChange" />
            </span>
        </div>

        <a-spin :spinning="loading">
            <div v-if="showEmpty">
                <div v-if="showInfo" class="info">
                    {{ $t('Failed to get reports for the specified period') }}
                </div>
                <a-empty :description="false" />
            </div>

            <div v-else class="list">
                <a-checkbox-group v-model="form.calculations" :disabled="form.without_attachments">
                    <div v-for="calculation in calculations" :key="calculation.id" class="item">
                        <div class="name" :class="form.without_attachments && 'no-data'">
                            {{ report_label(calculation) }}
                        </div>
                        <div class="checkbox">
                            <a-checkbox :value="calculation.id" />
                        </div>
                    </div>
                </a-checkbox-group>
            </div>
        </a-spin>
    </div>
</template>
<script>
export default{
    name: 'AddChangeCalculationReports',
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
            calculations: []
        }
    },
    mounted() {
        if(!('calculations' in this.form)) {
            this.$set(this.form, 'calculations', this.report.calculations.map(calculation => calculation.id)
            )
        }
        this.getReports()
    },
    methods: {
        noChangesIsChange(val) {
            if(val) {
                this.form.calculations = new Array()
            }
        },
        report_label(calculation) {
            const startDate = this.$moment(calculation.start, 'YYYY-MM-DD').format('DD.MM.YY');
            const endDate = this.$moment(calculation.end, 'YYYY-MM-DD').format('DD.MM.YY');
            const createdDate = this.$moment(calculation.created_at).format('DD.MM.YY');
            const createdTime = this.$moment(calculation.created_at).format('HH:mm');

            return this.$t(
                'Changes to IPF for the period from {start} to {end} (created {date} at {time})',
                { start: startDate, end: endDate, date: createdDate, time: createdTime }
            );
        },
        async getReports() {
            if(!this.loading) {
                try {
                    this.loading = true
                    const params = {
                        start: this.consolidation.start,
                        end: this.consolidation.end,
                        organization: this.report.contractor.id,
                        report_type: 'change_calculation',
                    }
                    const { data } = await this.$http.get('/accounting_reports/get_reports', {
                        params
                    })
                    if(data.length) {
                        this.calculations = data
                        if(!this.form.without_attachments && !this.form.calculations.length)
                            this.form.calculations = this.calculations.map(calculation => calculation.id)
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