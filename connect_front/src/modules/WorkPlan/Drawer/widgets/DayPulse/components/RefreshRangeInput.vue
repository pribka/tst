<template>
    <div class="refresh_range_input">
        <div class="range_input flex items-center">
            <a-button
                type="link"
                flaticon
                style="min-width: 30px;max-width: 30px;color: #888888;"
                icon="fi-rr-angle-small-left"
                shape="circle"
                @click="goPrev" />
            <a-range-picker
                :value="normalizedValue"
                format="DD.MM.YYYY"
                :allowClear="false"
                separator="-"
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
                @click="goNext" />
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
            @click="setToday" />
    </div>
</template>

<script>
export default {
    props: {
        value: {
            type: Array,
            default: () => []
        }
    },
    computed: {
        normalizedValue() {
            return this.normalizeRange(this.value)
        },
        isTodayRange() {
            const start = this.normalizedValue[0]
            const end = this.normalizedValue[1]
            if (!start || !end) return false
            const t = this.$moment()
            return start.isSame(t.clone().startOf('day'), 'second') && end.isSame(t.clone().endOf('day'), 'second')
        },
    },
    methods: {
        emitRange(value) {
            const normalized = this.normalizeRange(value)
            this.$emit('input', normalized)
            this.$emit('change', normalized)
        },
        normalizeRange(arrayLike) {
            if (!arrayLike || !arrayLike[0] || !arrayLike[1]) {
                const t = this.$moment()
                return [t.clone().startOf('day'), t.clone().endOf('day')]
            }

            return [
                this.$moment(arrayLike[0]).startOf('day'),
                this.$moment(arrayLike[1]).endOf('day')
            ]
        },
        setToday() {
            const t = this.$moment()
            this.emitRange([t.clone().startOf('day'), t.clone().endOf('day')])
        },
        shiftRange(days) {
            const [start, end] = this.normalizedValue
            this.emitRange([
                start.clone().add(days, 'day').startOf('day'),
                end.clone().add(days, 'day').endOf('day')
            ])
        },
        goPrev() {
            this.shiftRange(-1)
        },
        goNext() {
            this.shiftRange(1)
        },
        changeDate(value) {
            this.emitRange(value)
        }
    }
}
</script>

<style scoped lang="scss">
.refresh_range_input {
    display: flex;
    align-items: center;
    gap: 8px;
}

.range_input {
    box-shadow: 0 2px 0 rgba(0, 0, 0, 0.015);
    background: #fff;
    border-radius: 8px;
    flex: 1;
}

.date_picker {
    max-width: 100%;

    &::v-deep {
        .ant-input {
            border: 0;
            cursor: pointer;
            box-shadow: initial;
            padding-left: 0;
            padding-right: 0;
            outline: none !important;

            .ant-calendar-range-picker-input {
                cursor: pointer;
            }
        }
    }
}
</style>
