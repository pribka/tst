<template>
    <div class="flex items-center gap-1 min-w-0">
        <div class="range_input" :class="useInject && 'invert_bg'">
            <a-button 
                type="link" 
                flaticon
                style="min-width: 30px;max-width: 30px;color: #888888;"
                icon="fi-rr-angle-small-left"
                shape="circle"
                @click="goPrev()" />
            <a-range-picker 
                :value="mainDate"
                format="DD.MM.YYYY" 
                :allowClear="false"
                separator="-"
                :ranges="presets"
                :getCalendarContainer="trigger => trigger.parentNode"
                class="date_picker w-full"
                :mask="{ mask: '00.00.0000', lazy: true, autofix: true }"
                :placeholder="[$t('Start date'), $t('End date')]"
                @change="changeDate" />
            <a-button 
                type="link" 
                flaticon
                style="min-width: 30px;max-width: 30px;color: #888888;"
                icon="fi-rr-angle-small-right"
                shape="circle"
                @click="goNext()" />
        </div>
        <a-button 
            v-if="!isTodayRange"
            type="ui_ghost" 
            flaticon
            v-tippy
            :content="$t('workplan.today_short')"
            icon="fi-rr-calendar-day"
            class="blue_color" 
            shape="circle"
            @click="setToday()" />
    </div>
</template>

<script>
export default {
    props: {
        reloadAllData: {
            type: Function,
            default: () => {}
        },
        storeKey: {
            type: String,
            required: true
        },
        useInject: {
            type: Boolean,
            default: false
        }
    },
    computed: {
        isTodayRange() {
            const start = this.mainDate[0]
            const end = this.mainDate[1]
            if (!start || !end) return false
            const t = this.$moment()
            const dStart = start.isSame(t.clone().startOf('day'), 'second')
            const dEnd = end.isSame(t.clone().endOf('day'), 'second')
            return dStart && dEnd
        },
        mainDate: {
            get() {
                return this.$store.state.workplan.mainDate?.[this.storeKey] || []
            },
            set(value) {
                this.$store.commit('workplan/CHANGE_FIELD', {
                    value,
                    field: 'mainDate',
                    storeKey: this.storeKey
                })
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
                [this.$t('week')]: [now.clone().startOf('day'), now.clone().add(6, 'day').endOf('day')],
                [this.$t('month')]: [now.clone().startOf('day'), now.clone().add(1, 'month').subtract(1, 'day').endOf('day')]
            }
        },
    },
    methods: {
        setToday() {
            const t = this.$moment()

            this.mainDate = [
                t.clone().startOf('day'),
                t.clone().endOf('day')
            ]

            this.reloadAllData()
        },
        shiftRange(days) {
            const start = this.mainDate[0].clone().add(days, 'day')
            const end = this.mainDate[1].clone().add(days, 'day')

            this.mainDate = [
                start.startOf('day'),
                end.endOf('day')
            ]

            this.reloadAllData()
        },
        goPrev() {
            this.shiftRange(-1)
        },
        goNext() {
            this.shiftRange(1)
        },
        normalizeRange(arrayLike) {
            if (!arrayLike || !arrayLike[0] || !arrayLike[1]) {
                const t = this.$moment()
                return [
                    t.clone().startOf('day'),
                    t.clone().endOf('day')
                ]
            }

            return [
                this.$moment(arrayLike[0]).startOf('day'),
                this.$moment(arrayLike[1]).endOf('day')
            ]
        },
        changeDate(value) {
            this.mainDate = this.normalizeRange(value)
            this.reloadAllData()
        },
    }
}
</script>

<style lang="scss" scoped>
.range_input{
    box-shadow: 0 2px 0 rgba(0, 0, 0, 0.015);
    background: #fff;
    border-radius: 8px;
    &.invert_bg{
        background: #eef2f4;
    }
}
.date_picker{
    max-width: 170px;
    &::v-deep{
        .ant-input{
            border: 0px;
            cursor: pointer;
            box-shadow: initial;
            padding-left: 0px;
            padding-right: 0px;
            outline: none!important;
            .ant-calendar-range-picker-input{
                cursor: pointer;
            }
        }
    }
}
</style>
