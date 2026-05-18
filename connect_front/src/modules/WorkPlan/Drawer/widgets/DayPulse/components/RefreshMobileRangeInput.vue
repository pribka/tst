<template>
    <div class="range_input flex items-center" @click="visible = true">
        <i class="fi fi-rr-calendar-day mr-2" />
        {{ displayValue }}
        <DrawerTemplate
            v-model="visible"
            width="100%"
            height="400px"
            wrapClassName="date_drawer"
            placement="bottom"
            @afterVisibleChange="afterVisibleChange"
            destroyOnClose
            @close="closeDrawer">
            <div class="drawer_controls flex items-center justify-between gap-2">
                <div class="flex items-center gap-2">
                    <a-button shape="circle" type="ui" flaticon icon="fi-rr-angle-double-small-left" @click="goMonthPrev" />
                    <a-button shape="circle" type="ui" flaticon icon="fi-rr-angle-small-left" @click="goPrev" />
                </div>
                <transition name="slowfade_up" appear :duration="{ enter: 600, leave: 300 }">
                    <a-button v-if="!isTodayRange" type="ui" @click="setToday">{{ $t('today') }}</a-button>
                </transition>
                <div class="flex items-center gap-2">
                    <a-button shape="circle" type="ui" flaticon icon="fi-rr-angle-small-right" @click="goNext" />
                    <a-button shape="circle" type="ui" flaticon icon="fi-rr-angle-double-small-right" @click="goMonthNext" />
                </div>
            </div>
            <div class="header_date">{{ headerDate }}</div>
            <div class="calendar_wrapper">
                <RangeCalendar
                    prefixCls="ant-calendar"
                    :selectedValue="selectedValue"
                    :value="calendarValue"
                    :showDateInput="true"
                    :showToday="false"
                    :timePicker="null"
                    @select="onCalendarSelect"
                    @valueChange="onValueChange" />
            </div>
            <template #footer>
                <div class="flex items-center gap-2 w-full">
                    <a-button type="primary" block @click="applyAndClose">{{ $t('workplan.apply') }}</a-button>
                    <a-button block type="ui_ghost" @click="closeDrawer">{{ $t('cancel') }}</a-button>
                </div>
            </template>
        </DrawerTemplate>
    </div>
</template>

<script>
export default {
    components: {
        DrawerTemplate: () => import('@/components/DrawerTemplate.vue'),
        RangeCalendar: () => import('@apps/UIModules/antDesign/vc-calendar/src/RangeCalendar')
    },
    props: {
        value: {
            type: Array,
            default: () => []
        }
    },
    data() {
        return {
            visible: false,
            internalValue: [],
            initialValue: [],
            internalShowDate: this.$moment().clone(),
            oneSelected: []
        }
    },
    computed: {
        normalizedValue() {
            return this.normalizeRange(this.value)
        },
        displayValue() {
            const [start, end] = this.normalizedValue
            return `${start.format('DD.MM.YYYY')} - ${end.format('DD.MM.YYYY')}`
        },
        selectedValue() {
            return this.normalizeRange(this.internalValue)
        },
        calendarValue() {
            const selected = this.selectedValue
            if (selected[0]) {
                return [selected[0].clone(), selected[1] ? selected[1].clone() : selected[0].clone().add(1, 'month')]
            }
            const t = this.$moment()
            return [t.clone(), t.clone().add(1, 'month')]
        },
        headerDate() {
            const date = this.selectedValue?.[0] || this.internalShowDate
            if (!date) return ''
            const formatted = this.$moment(date).format('MMMM YYYY')
            return formatted.charAt(0).toUpperCase() + formatted.slice(1)
        },
        isTodayRange() {
            const [start, end] = this.selectedValue
            if (!start || !end) return false
            const t = this.$moment()
            return start.isSame(t.clone().startOf('day'), 'second') && end.isSame(t.clone().endOf('day'), 'second')
        }
    },
    watch: {
        value: {
            immediate: true,
            deep: true,
            handler(value) {
                if (this.visible) return
                this.internalValue = this.normalizeRange(value)
            }
        }
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
        afterVisibleChange(visible) {
            if (visible) {
                this.initialValue = this.normalizeRange(this.value)
                this.internalValue = this.normalizeRange(this.value)
                this.oneSelected = []
                this.internalShowDate = this.internalValue[0].clone()
                return
            }
            this.oneSelected = []
        },
        closeDrawer() {
            this.internalValue = this.normalizeRange(this.initialValue)
            this.visible = false
        },
        setToday() {
            const t = this.$moment()
            this.internalValue = [t.clone().startOf('day'), t.clone().endOf('day')]
        },
        shiftRange(days) {
            const [start, end] = this.selectedValue
            this.internalValue = [
                start.clone().add(days, 'day').startOf('day'),
                end.clone().add(days, 'day').endOf('day')
            ]
            this.internalShowDate = this.internalValue[0].clone()
        },
        goPrev() {
            this.shiftRange(-1)
        },
        goNext() {
            this.shiftRange(1)
        },
        goMonthPrev() {
            const [start, end] = this.selectedValue
            const newStartBase = start.clone().subtract(1, 'month')
            const newEndBase = end.clone().subtract(1, 'month')
            this.internalValue = [
                newStartBase.date(Math.min(start.date(), newStartBase.daysInMonth())).startOf('day'),
                newEndBase.date(Math.min(end.date(), newEndBase.daysInMonth())).endOf('day')
            ]
            this.internalShowDate = this.internalValue[0].clone()
        },
        goMonthNext() {
            const [start, end] = this.selectedValue
            const newStartBase = start.clone().add(1, 'month')
            const newEndBase = end.clone().add(1, 'month')
            this.internalValue = [
                newStartBase.date(Math.min(start.date(), newStartBase.daysInMonth())).startOf('day'),
                newEndBase.date(Math.min(end.date(), newEndBase.daysInMonth())).endOf('day')
            ]
            this.internalShowDate = this.internalValue[0].clone()
        },
        onCalendarSelect(selected) {
            if (!selected || !selected.length) return
            const [start, end] = selected
            if (start && end) {
                this.internalValue = this.normalizeRange([start, end])
                this.emitRange(this.internalValue)
                this.visible = false
            } else {
                this.oneSelected = selected
                this.internalShowDate = start ? start.clone() : this.internalShowDate
            }
        },
        onValueChange(val) {
            this.internalShowDate = val && val[0] ? val[0].clone() : this.internalShowDate
        },
        applyAndClose() {
            if (this.oneSelected?.length === 1) {
                this.internalValue = this.normalizeRange([this.oneSelected[0], this.oneSelected[0]])
            }
            this.emitRange(this.internalValue)
            this.visible = false
        }
    }
}
</script>

<style lang="scss">
.date_drawer {
    .drawer_header {
        display: none !important;
    }

    .ant-drawer-content {
        border-radius: 16px 16px 0 0;
    }
}
</style>

<style scoped lang="scss">
.range_input {
    width: 100%;
    min-height: 44px;
    padding: 0 14px;
    border-radius: 8px;
    background: #f7f7fb;
}

.header_date {
    text-align: center;
    font-weight: 600;
    border-bottom: 1px solid var(--borderColor);
    padding-bottom: 10px;
    padding-top: 15px;
}

.slowfade_up-enter-active,
.slowfade_up-leave-active {
    transition: opacity .4s ease, transform .4s ease;
}

.slowfade_up-enter,
.slowfade_up-leave-to {
    opacity: 0;
    transform: translateY(-8px);
}

.calendar_wrapper {
    &::v-deep {
        .ant-calendar-body {
            border-top: 0;
        }

        .ant-calendar-header,
        .ant-calendar-prev-year-btn,
        .ant-calendar-prev-month-btn,
        .ant-calendar-range-right,
        .ant-calendar-input-wrap {
            display: none;
        }

        .ant-calendar {
            box-shadow: initial;
            border: 0;

            &.ant-calendar-range {
                width: 100%;

                .ant-calendar-range-left {
                    float: initial;
                    width: 100%;

                    .ant-calendar-body {
                        padding-left: 0;
                        padding-right: 0;
                        padding-bottom: 0;
                    }
                }
            }
        }
    }
}
</style>
