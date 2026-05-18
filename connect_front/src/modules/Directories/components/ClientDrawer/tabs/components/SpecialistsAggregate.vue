<template>
    <a-spin :spinning="loading" size="small">
        <div class="mb-2 flex">
            <div class="aggregate_block">
                <div class="aggregate_block__item">
                    {{ $t('directories.plan') }}: {{ formattedTotalPlan }}
                </div>
                <div class="aggregate_block__item">
                    {{ $t('directories.fact') }}: {{ formattedTotalFact }}
                </div>
                <div class="aggregate_block__item">
                    {{ $t('directories.remainder_overspend') }}:
                    <span :class="diffClass">{{ formattedDiff }}</span>
                </div>
            </div>
        </div>
    </a-spin>
</template>

<script>
import eventBus from '@/utils/eventBus'
import { errorHandler } from '@/utils/index.js'
export default {
    props: {
        client: {
            type: Object,
            required: true
        },
        listModel: {
            type: String,
            required: true
        },
        listPageName: {
            type: String,
            required: true
        },
        page: {
            type: Number,
            default: 1
        }
    },
    data() {
        return {
            loading: false,
            list: []
        }
    },
    created() {
        this.getList()
    },
    computed: {
        totalPlanHours() {
            const arr = this.list
                .map(i => this.toNum(i?.duration_plan))
                .filter(n => n != null)
            if (!arr.length) return null
            return arr.reduce((a, b) => a + b, 0)
        },

        totalFactSeconds() {
            const arr = this.list
                .map(i => this.toNum(i?.duration_fact))
                .filter(n => n != null)
            if (!arr.length) return null
            return arr.reduce((a, b) => a + b, 0)
        },

        formattedTotalPlan() {
            return this.formatHours(this.totalPlanHours)
        },

        formattedTotalFact() {
            return this.formatSeconds(this.totalFactSeconds)
        },

        diffSeconds() {
            if (this.totalPlanHours == null || this.totalFactSeconds == null) return null
            return this.totalPlanHours * 3600 - this.totalFactSeconds
        },

        formattedDiff() {
            if (this.diffSeconds == null) return '—'

            const sign = this.diffSeconds > 0 ? '+' : this.diffSeconds < 0 ? '−' : ''
            const abs = Math.abs(this.diffSeconds)

            return `${sign}${this.formatSeconds(abs)}`
        },

        diffClass() {
            if (this.diffSeconds == null) return ''
            if (this.diffSeconds > 0) return 'diff-pos'
            if (this.diffSeconds < 0) return 'diff-neg'
            return 'diff-zero'
        }
    },
    methods: {
        async getList() {
            try {
                this.loading = true
                const params = {
                    page: this.page,
                    page_name: this.listPageName,
                    page_size: 15
                }
                const { data } = await this.$http.get(
                    `/help_desk/customer_cards/${this.client.id}/specialists/`,
                    { params }
                )
                if (data) this.list = data.results
            } catch(error) {
                errorHandler({error, show: false})
            } finally {
                this.loading = false
            }
        },

        toNum(v) {
            if (v === null || v === undefined || v === '') return null
            const n = typeof v === 'string' ? Number(v.replace(',', '.')) : Number(v)
            return Number.isFinite(n) ? n : null
        },

        formatHours(v) {
            if (v == null) return '0 ч'
            const val = Number.isInteger(v) ? v : +v.toFixed(1)
            return `${val} ч`
        },

        formatSeconds(sec) {
            if (!sec) return `0 ${this.$t('directories.second3')}`

            const hours = Math.floor(sec / 3600)
            const minutes = Math.floor((sec % 3600) / 60)
            const seconds = sec % 60

            const plural = (num, one, few, many) => {
                const n = Math.abs(num) % 100
                const n1 = n % 10
                if (n > 10 && n < 20) return many
                if (n1 > 1 && n1 < 5) return few
                if (n1 === 1) return one
                return many
            }

            let res = ''

            if (hours > 0) {
                res += `${hours} ${plural(
                    hours,
                    this.$t('directories.hour1'),
                    this.$t('directories.hour2'),
                    this.$t('directories.hour3')
                )}`
            }

            if (minutes > 0) {
                if (res) res += ' '
                res += `${minutes} ${plural(
                    minutes,
                    this.$t('directories.minute1'),
                    this.$t('directories.minute2'),
                    this.$t('directories.minute3')
                )}`
            }

            if (!res) {
                res = `${seconds} ${plural(
                    seconds,
                    this.$t('directories.second1'),
                    this.$t('directories.second2'),
                    this.$t('directories.second3')
                )}`
            }

            return res
        }
    },
    mounted() {
        eventBus.$on(`update_filter_${this.listModel}_${this.listPageName}_aggregate`, () => {
            this.getList()
        })
    },
    beforeDestroy() {
        eventBus.$off(`update_filter_${this.listModel}_${this.listPageName}_aggregate`)
    }
}
</script>

<style lang="scss" scoped>
.aggregate_block{
    display: flex;
    align-items: center;
    gap: 10px;
    &__item{
        background: #f0f1f6;
        padding: 7px 15px;
        border-radius: 8px;
        color: var(--text);
    }
}
.diff-pos { color: #368225 }
.diff-neg { color: #FF5C5C }
.diff-zero { color: inherit }
</style>