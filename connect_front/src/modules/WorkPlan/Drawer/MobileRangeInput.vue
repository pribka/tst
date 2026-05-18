<template>
    <div class="range_input flex items-center" @click="visible = true">
        <i class="fi fi-rr-calendar-day mr-2" />
        {{ $moment(mainDate[0]).format('DD.MM.YYYY') }} - {{ $moment(mainDate[1]).format('DD.MM.YYYY') }}
        <DrawerTemplate
            v-model="visible"
            width="100%"
            height="400px"
            wrapClassName="date_drawer"
            placement="bottom"
            @afterVisibleChange="afterVisibleChange"
            destroyOnClose
            @close="closeDrawer()">
            <div class="drawer_controls flex items-center justify-between gap-2">
                <div class="flex items-center gap-2">
                    <a-button shape="circle" type="ui" flaticon icon="fi-rr-angle-double-small-left" @click="goMounthPrev" />
                    <a-button shape="circle" type="ui" flaticon icon="fi-rr-angle-small-left" @click="goPrev" />
                </div>
                <transition name="slowfade_up" appear :duration="{ enter: 600, leave: 300 }">
                    <a-button v-if="!isTodayRange" type="ui" @click="setToday">{{ $t('today') }}</a-button>
                </transition>
                <div class="flex items-center gap-2">
                    <a-button shape="circle" type="ui" flaticon icon="fi-rr-angle-small-right" @click="goNext" />
                    <a-button shape="circle" type="ui" flaticon icon="fi-rr-angle-double-small-right" @click="goMountNext" />
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
                    @valueChange="onValueChange"/>
            </div>
            <template #footer>
                <div class="flex items-center gap-2 w-full">
                    <a-button type="primary" block @click="applyAndClose()">{{ $t('workplan.apply') }}</a-button>
                    <a-button block type="ui_ghost" @click="closeDrawer()">{{ $t('cancel') }}</a-button>
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
        reloadAllData: {
            type: Function,
            default: () => {}
        },
        storeKey: {
            type: String,
            required: true
        }
    },
    data() {
        return {
            visible: false,
            internalShowDate: this.$moment().clone(),
            initDate: this.$moment().clone(),
            oneSelected: []
        }
    },
    computed: {
        headerDate() {
            const date = this.selectedValue && this.selectedValue[0] ? this.selectedValue[0] : this.internalShowDate
            if (!date) return ''
            const formatted = this.$moment(date).format('MMMM YYYY')
            return formatted.charAt(0).toUpperCase() + formatted.slice(1)
        },
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
        selectedValue() {
            if (!this.mainDate || !this.mainDate[0] || !this.mainDate[1]) {
                const t = this.$moment()
                return [t.clone().startOf('day'), t.clone().endOf('day')]
            }
            return [this.$moment(this.mainDate[0]).clone(), this.$moment(this.mainDate[1]).clone()]
        },
        calendarValue() {
            if (this.selectedValue && this.selectedValue.length === 2 && this.selectedValue[0]) {
                return [this.selectedValue[0].clone(), this.selectedValue[1] ? this.selectedValue[1].clone() : this.selectedValue[0].clone().add(1, 'month')]
            }
            const t = this.$moment()
            return [t.clone(), t.clone().add(1, 'month')]
        }
    },
    methods: {
        closeDrawer() {
            this.mainDate = this.initDate
            this.visible = false
        },
        afterVisibleChange(vis) {
            if(vis) {
                this.initDate = this.normalizeRange([...this.mainDate])
            } else {
                this.initDate = this.$moment().clone()
                this.oneSelected = []
            }
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
        setToday() {
            const t = this.$moment()
            this.mainDate = [t.clone().startOf('day'), t.clone().endOf('day')]
        },
        shiftRange(days) {
            const start = this.mainDate[0]
            const end = this.mainDate[1]
            const newStart = start.clone().add(days, 'day').startOf('day')
            const newEnd = end.clone().add(days, 'day').endOf('day')
            this.mainDate = [newStart, newEnd]
        },
        goMounthPrev() {
            const start = this.mainDate[0]
            const end = this.mainDate[1]
            if (!start || !end) {
                this.internalShowDate = this.internalShowDate.clone().subtract(1, 'month')
                return
            }
            const dayStart = start.date()
            const dayEnd = end.date()
            const newStartBase = start.clone().subtract(1, 'month')
            const newEndBase = end.clone().subtract(1, 'month')
            const newStartDay = Math.min(dayStart, newStartBase.daysInMonth())
            const newEndDay = Math.min(dayEnd, newEndBase.daysInMonth())
            const newStart = newStartBase.date(newStartDay).startOf('day')
            const newEnd = newEndBase.date(newEndDay).endOf('day')
            this.mainDate = [newStart, newEnd]
            this.internalShowDate = newStart.clone()
        },
        goMountNext() {
            const start = this.mainDate[0]
            const end = this.mainDate[1]
            if (!start || !end) {
                this.internalShowDate = this.internalShowDate.clone().add(1, 'month')
                return
            }
            const dayStart = start.date()
            const dayEnd = end.date()
            const newStartBase = start.clone().add(1, 'month')
            const newEndBase = end.clone().add(1, 'month')
            const newStartDay = Math.min(dayStart, newStartBase.daysInMonth())
            const newEndDay = Math.min(dayEnd, newEndBase.daysInMonth())
            const newStart = newStartBase.date(newStartDay).startOf('day')
            const newEnd = newEndBase.date(newEndDay).endOf('day')
            this.mainDate = [newStart, newEnd]
            this.internalShowDate = newStart.clone()
        },
        goPrev() {
            this.shiftRange(-1)
        },
        goNext() {
            this.shiftRange(1)
        },
        onCalendarChange(selected) {
            this.oneSelected = selected
            if (!selected || !selected.length)
                return
            const s = selected[0]
            const e = selected[1]
            if (s && e)
                this.changeDate([s, e])
            else
                this.setTempSelection(selected)
        },
        onCalendarSelect(selected) {
            if (!selected || !selected.length) {
                return
            }
            const s = selected[0]
            const e = selected[1]
            if (s && e) {
                this.changeDate([s, e])
                this.visible = false
            } else {
                this.setTempSelection(selected)
            }
        },
        onValueChange(val) {
            this.internalShowDate = val && val[0] ? val[0].clone() : this.internalShowDate
        },
        setTempSelection(selected) {
            this.internalShowDate = selected && selected[0] ? selected[0].clone() : this.internalShowDate
        },
        applyAndClose() {
            if(this.oneSelected?.length === 1)
                this.changeDate([this.oneSelected[0], this.oneSelected[0]])
            if (this.selectedValue && this.selectedValue[0] && this.selectedValue[1])
                this.changeDate(this.selectedValue)
            this.visible = false
        }
    }
}
</script>

<style lang="scss">
.date_drawer{
    .drawer_header{
        display: none!important
    }
    .ant-drawer-content{
        border-radius: 16px 16px 0 0
    }
}
</style>

<style scoped lang="scss">
.header_date{
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
.calendar_wrapper{
    &::v-deep{
        .ant-calendar-body{
            border-top: 0px;
        }
        .ant-calendar-header,
        .ant-calendar-prev-year-btn,
        .ant-calendar-prev-month-btn,
        .ant-calendar-range-right,
        .ant-calendar-input-wrap,
        .ant-calendar-input-wrap{
            display: none;
        }
        .ant-calendar{
            box-shadow: initial;
            border: 0px;
            &.ant-calendar-range{
                width: 100%;
                .ant-calendar-range-left{
                    float: initial;
                    width: 100%;
                    .ant-calendar-body{
                        padding-left: 0px;
                        padding-right: 0px;
                        padding-bottom: 0px;
                    }
                }
            }
        }
    }
}
.range_input{
    height: 40px;
    padding-left: 15px;
    padding-right: 15px;
    line-height: 40px;
    --alpha: 1;
    backdrop-filter: blur(calc(7px * (2 - var(--alpha))));
    background: rgba(71, 119, 255, 0.2);
    box-shadow: 0 0 0 1px #e6e6e8;
    border-radius: 30px;
    cursor: pointer;
    user-select: none;
}
</style>
