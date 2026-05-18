<template>
    <div ref="wrap">
        <a-range-picker
            v-model="valueProxy"
            inputType="ghost"
            class="w-full"
            :mask="{ mask: '00.00.0000', lazy: true, autofix: true }"
            allowClear
            :getCalendarContainer="() => $refs.wrap"
            :ranges="presets"
            format="DD.MM.YYYY"
            :placeholder="[$t('Start date'), $t('End date')]" />
    </div>
</template>

<script>
export default {
    props: {
        item: { type: Object, required: true },
        changeItemValue: { type: Function, required: true }
    },
    computed: {
        valueProxy: {
            get() {
                if (Array.isArray(this.item.value) && this.item.value.length === 2) {
                    return [
                        this.$moment(this.item.value[0]),
                        this.$moment(this.item.value[1])
                    ]
                }
                return []
            },
            set(v) {
                if (Array.isArray(v) && v.length === 2) {
                    const a = v[0] ? v[0].format('YYYY-MM-DD') : null
                    const b = v[1] ? v[1].format('YYYY-MM-DD') : null
                    this.changeItemValue([a, b])
                } else {
                    this.changeItemValue([])
                }
            }
        },
        presets() {
            const now = this.$moment()
            return {
                [this.$t('today')]: [now.clone().startOf('day'), now.clone().endOf('day')],
                [this.$t('yesterday')]: [now.clone().subtract(1, 'day').startOf('day'), now.clone().subtract(1, 'day').endOf('day')],
                [this.$t('tomorrow')]: [now.clone().add(1, 'day').startOf('day'), now.clone().add(1, 'day').endOf('day')],
                [this.$t('current_week')]: [now.clone().startOf('week'), now.clone().endOf('week')],
                [this.$t('current_month')]: [now.clone().startOf('month'), now.clone().endOf('month')],
                [this.$t('current_quarter')]: [now.clone().startOf('quarter'), now.clone().endOf('quarter')],
                [this.$t('current_year')]: [now.clone().startOf('year'), now.clone().endOf('year')],
                [this.$t('week')]: [now.clone().startOf('day'), now.clone().add(6, 'day').endOf('day')],
                [this.$t('month')]: [now.clone().startOf('day'), now.clone().add(1, 'month').subtract(1, 'day').endOf('day')],
                [this.$t('quarter')]: [now.clone().startOf('day'), now.clone().add(3, 'month').subtract(1, 'day').endOf('day')],
                [this.$t('year')]: [now.clone().startOf('day'), now.clone().add(1, 'year').subtract(1, 'day').endOf('day')]
            }
        }
    }
}
</script>