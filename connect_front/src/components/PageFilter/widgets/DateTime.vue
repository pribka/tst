<template>
    <div class="w-full">
        <template v-if="isMobile">
            <div class="range_input flex items-center ant-input" @click="openDrawer">
                <i class="fi fi-rr-calendar-day mr-2" />
                <span v-if="range && range[0] && range[1]">
                    {{ range[0].format('DD.MM.YYYY HH:mm') }} - {{ range[1].format('DD.MM.YYYY HH:mm') }}
                </span>
                <span v-else class="input_placeholder">
                    {{ $t('select_date') }}
                </span>
                <div v-if="range && range.length" class="clear_btn" @click.stop="clearDate()">
                    <i class="fi fi-rr-cross-circle" />
                </div>
            </div>
            <DrawerTemplate
                v-model="visible"
                width="100%"
                height="570px"
                wrapClassName="date_drawer select-none"
                placement="bottom"
                destroyOnClose
                @close="closeDrawer">
                <div ref="dateWrapper">
                    <div class="drawer_controls flex items-center justify-between gap-2">
                        <div class="flex items-center gap-2">
                            <a-button shape="circle" type="ui" flaticon icon="fi-rr-angle-double-small-left" @click="goMonthPrev" />
                            <a-button v-if="tempRange && tempRange.length" shape="circle" type="ui" flaticon icon="fi-rr-angle-small-left" @click="shiftRange(-1)" />
                        </div>

                        <transition name="slowfade_up" appear>
                            <a-button v-if="!isTodayRange" type="ui" @click="setToday">
                                {{ $t('today') }}
                            </a-button>
                        </transition>

                        <div class="flex items-center gap-2">
                            <a-button v-if="tempRange && tempRange.length" shape="circle" type="ui" flaticon icon="fi-rr-angle-small-right" @click="shiftRange(1)" />
                            <a-button shape="circle" type="ui" flaticon icon="fi-rr-angle-double-small-right" @click="goMonthNext" />
                        </div>
                    </div>

                    <div class="header_date">{{ headerDate }}</div>

                    <div class="calendar_wrapper">
                        <RangeCalendar
                            prefixCls="ant-calendar"
                            :selectedValue="tempRange"
                            :value="panelValue"
                            :showDateInput="false"
                            :showToday="false"
                            :timePicker="null"
                            @change="onCalendarChange"
                            @valueChange="onPanelChange" />
                    </div>
                    <div
                        class="time_selectors flex items-center gap-2">
                        <div class="time_item w-full">
                            <div class="time_label">{{ $t('from') }}</div>
                            <input
                                type="time"
                                class="native_time"
                                :disabled="!(tempRange.length === 2 && time)"
                                :value="nativeTimeFrom"
                                @input="onNativeTimeFrom"/>
                        </div>

                        <div class="time_item w-full">
                            <div class="time_label">{{ $t('to') }}</div>
                            <input
                                type="time"
                                class="native_time"
                                :disabled="!(tempRange.length === 2 && time)"
                                :value="nativeTimeTo"
                                @input="onNativeTimeTo"/>
                        </div>

                    </div>

                    <div
                        v-if="Object.keys(presets).length"
                        class="preset_buttons">
                        <div
                            v-for="(range, label) in presets"
                            :key="label"
                            class="preset_btn"
                            @click="applyPreset(range)">
                            {{ label }}
                        </div>
                    </div>
                </div>
                <template #footer>
                    <div class="flex items-center gap-2 w-full">
                        <a-button type="primary" block @click="applyAndClose">
                            {{ $t('apply_btn') }}
                        </a-button>
                        <a-button block type="ui_ghost" @click="closeDrawer">
                            {{ $t('cancel') }}
                        </a-button>
                    </div>
                </template>
            </DrawerTemplate>
        </template>

        <a-range-picker
            v-else
            v-model="range"
            class="date_select"
            :class="isVertical ? 'mt-2' : ''"
            :format="dateFormat"
            :show-time="time ? { format: 'HH:mm' } : false"
            separator="-"
            allowClear
            :ranges="presets"
            :mask="{ mask: '00.00.0000 00:00', lazy: true, autofix: true }"
            :placeholder="[$t('from'), $t('to')]"
            @change="changeValue"
            @openChange="focus" />
    </div>
</template>

<script>
import filtersCheckbox from '../mixins/filtersCheckbox'
import { formatsInMoments } from '@/utils/dateSettings'

export default {
    mixins: [filtersCheckbox],
    components: {
        DrawerTemplate: () => import('@/components/DrawerTemplate.vue'),
        RangeCalendar: () => import('@apps/UIModules/antDesign/vc-calendar/src/RangeCalendar')
    },
    props: {
        filter: { type: Object, required: true },
        name: { type: String, required: true },
        vertical: { type: Boolean, default: false }
    },
    data() {
        return {
            range: null,
            tempRange: [],
            panelValue: [],
            dateFormat: 'YYYY.MM.DD HH:mm',
            time: true,
            timeFrom: null,
            timeTo: null,
            visible: false,
            nativeTimeFrom: '',
            nativeTimeTo: '',
        }
    },
    created() {
        const w = this.filter.widget
        this.dateFormat = w.dateFormat
        this.time = w.time

        if (this.selected?.start && this.selected?.end) {
            this.range = [
                this.$moment(this.selected.start, formatsInMoments),
                this.$moment(this.selected.end, formatsInMoments)
            ]
        }
    },
    computed: {
        isMobile() {
            return this.$store.state.isMobile
        },
        isVertical() {
            return this.vertical || this.windowWidth <= 1436
        },
        windowWidth() {
            return this.$store.state.windowWidth
        },
        selected: {
            get() {
                return this.$store.state.filter.filterSelected[this.name][this.filter.name]
            },
            set(val) {
                this.$store.commit('filter/SET_SELECTED_FILTER', {
                    name: this.name,
                    filterName: this.filter.name,
                    value: val
                })
            }
        },
        headerDate() {
            const d = this.panelValue[0] || this.$moment()
            const s = d.format('MMMM YYYY')
            return s.charAt(0).toUpperCase() + s.slice(1)
        },
        isTodayRange() {
            if (!this.tempRange[0] || !this.tempRange[1]) return false
            const t = this.$moment()
            return this.tempRange[0].isSame(t.clone().startOf('day'), 'day')
                && this.tempRange[1].isSame(t.clone().endOf('day'), 'day')
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
    },
    methods: {
        applyPreset(presetRange) {
            if (!presetRange || presetRange.length !== 2) return

            const start = presetRange[0].clone().startOf('day')
            const end = presetRange[1].clone().endOf('day')

            this.tempRange = [start, end]
            this.panelValue = [start.clone(), start.clone().add(1, 'month')]

            if (this.time) {
                this.nativeTimeFrom = '00:00'
                this.nativeTimeTo = '23:59'
                this.timeFrom = this.$moment('00:00', 'HH:mm')
                this.timeTo = this.$moment('23:59', 'HH:mm')
            }
        },
        getPopupContainer() {
            return this.$refs.dateWrapper
        },
        clearDate() {
            this.range = null
            this.tempRange = []
            this.panelValue = []
            this.selected = null
            this.$store.commit('filter/DELETE_FILTER_TAG', {
                name: this.name,
                filterName: this.filter.name
            })
            this.$store.commit("filter/SET_ACTIVE_FILTERS", {name: this.name, filterName: this.filter.name, value: false})
        },
        changeValue(value, dateString) {
            if (!value || !value.length) {
                this.selected = null
                this.$store.commit('filter/DELETE_FILTER_TAG', {
                    name: this.name,
                    filterName: this.filter.name
                })
                return
            }

            const [startStr, endStr] = dateString

            if (!startStr || !endStr) return

            if (this.time) {
                if (!startStr.includes(':') || !endStr.includes(':')) return
            }

            const startMoment = this.$moment(startStr, this.dateFormat)
            const endMoment = this.$moment(endStr, this.dateFormat)

            if (!startMoment.isValid() || !endMoment.isValid()) return

            const start = startMoment.format(
                this.time ? 'YYYY-MM-DDTHH:mm:ssZ' : 'YYYY-MM-DD'
            )

            const end = endMoment.format(
                this.time ? 'YYYY-MM-DDTHH:mm:ssZ' : 'YYYY-MM-DD'
            )

            const data = { start, end }

            this.selected = data

            this.$store.commit('filter/SET_FILTER_TAG', {
                value: [start, end],
                name: this.name,
                filterName: this.filter.name
            })
        },
        openDrawer() {
            if (this.range && this.range.length === 2) {
                const start = this.range[0].clone()
                const end = this.range[1].clone()

                this.tempRange = [
                    start.clone().startOf('day'),
                    end.clone().startOf('day')
                ]

                if (this.time) {
                    this.timeFrom = start.clone()
                    this.timeTo = end.clone()
                    this.nativeTimeFrom = start.format('HH:mm')
                    this.nativeTimeTo = end.format('HH:mm')
                }
            } else {
                this.tempRange = []
                this.timeFrom = null
                this.timeTo = null
                this.nativeTimeFrom = ''
                this.nativeTimeTo = ''
            }

            const base = this.tempRange[0] || this.$moment()
            this.panelValue = [base.clone(), base.clone().add(1, 'month')]

            this.visible = true
        },
        closeDrawer() {
            this.visible = false
        },
        onNativeTimeFrom(e) {
            this.nativeTimeFrom = e.target.value
            if (this.nativeTimeFrom) {
                const [h, m] = this.nativeTimeFrom.split(':')
                this.timeFrom = this.$moment().hour(h).minute(m)
            }
        },

        onNativeTimeTo(e) {
            this.nativeTimeTo = e.target.value
            if (this.nativeTimeTo) {
                const [h, m] = this.nativeTimeTo.split(':')
                this.timeTo = this.$moment().hour(h).minute(m)
            }
        },
        onCalendarChange(val) {
            if (!val || !val.length) return

            if (val.length === 1) {
                this.tempRange = [val[0].clone()]
                return
            }

            if (val.length === 2) {
                this.tempRange = [val[0].clone(), val[1].clone()]

                if (this.time && !this.nativeTimeFrom && !this.nativeTimeTo) {
                    this.nativeTimeFrom = '00:00'
                    this.nativeTimeTo = '23:59'
                    this.timeFrom = this.$moment('00:00', 'HH:mm')
                    this.timeTo = this.$moment('23:59', 'HH:mm')
                }
            }
        },
        onPanelChange(val) {
            if (!val?.[0]) return
            this.panelValue = [
                val[0].clone(),
                val[1] ? val[1].clone() : val[0].clone().add(1, 'month')
            ]
        },
        applyAndClose() {
            if (this.tempRange.length !== 2) {
                this.visible = false
                return
            }

            let start = this.tempRange[0].clone()
            let end = this.tempRange[1].clone()

            if (this.timeFrom) {
                start = start
                    .hour(this.timeFrom.hour())
                    .minute(this.timeFrom.minute())
            }

            if (this.timeTo) {
                end = end
                    .hour(this.timeTo.hour())
                    .minute(this.timeTo.minute())
            }

            this.range = [start, end]
            this.commitRange()
            this.focus()
            this.visible = false
        },
        setToday() {
            const t = this.$moment()
            this.tempRange = [t.clone().startOf('day'), t.clone().endOf('day')]
            this.panelValue = [t.clone(), t.clone().add(1, 'month')]
        },
        shiftRange(days) {
            if (!this.tempRange[0] || !this.tempRange[1]) return
            this.tempRange = [
                this.tempRange[0].clone().add(days, 'day'),
                this.tempRange[1].clone().add(days, 'day')
            ]
        },
        goMonthPrev() {
            const base = this.panelValue[0].clone().subtract(1, 'month')
            this.panelValue = [base, base.clone().add(1, 'month')]
        },
        goMonthNext() {
            const base = this.panelValue[0].clone().add(1, 'month')
            this.panelValue = [base, base.clone().add(1, 'month')]
        },
        commitRange() {
            if (!this.range?.[0] || !this.range?.[1]) return

            const start = this.range[0].format(
                this.time ? 'YYYY-MM-DDTHH:mm:ssZ' : 'YYYY-MM-DD'
            )
            const end = this.range[1].format(
                this.time ? 'YYYY-MM-DDTHH:mm:ssZ' : 'YYYY-MM-DD'
            )

            this.selected = { start, end }

            this.$store.commit('filter/SET_FILTER_TAG', {
                value: [start, end],
                name: this.name,
                filterName: this.filter.name
            })
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

<style lang="scss" scoped>
.native_time {
    width: 100%;
    height: 32px;
    border: 0;
    border-radius: 4px;
    padding: 4px 8px;
    font-size: 14px;
    -webkit-appearance: none;
    color: var(--text);
    background-color: #f0f1f6;
    &:disabled {
        opacity: 0.6;
    }
}
.preset_buttons{
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
    .preset_btn{
        background-color: #f0f1f6;
        border-color: #f0f1f6;
        cursor: pointer;
        border-radius: 4px;
        padding: 3px 5px;
        transition: all 0.3s cubic-bezier(0.645, 0.045, 0.355, 1);
        &:hover,
        &:focus{
            color: var(--blue);
        }
    }
}
.time_selectors{
    border-top: 1px solid var(--borderColor);
    padding-top: 8px;
    margin-top: 8px;
    margin-bottom: 15px;
    .time_label{
        margin-bottom: 5px;
        text-transform: capitalize;
        color: var(--placeholder);
        font-size: 13px;
    }
}
.clear_btn{
    position: absolute;
    right: 0;
    top: 0;
    height: 100%;
    width: 34px;
    z-index: 10;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    background: #fff;
    font-size: 16px;
}
.range_input{
    position: relative;
    overflow: hidden;
    padding-right: 36px;
    .input_placeholder{
        color: var(--placeholder);
    }
}
.header_date{
    text-align: center;
    font-weight: 600;
    border-bottom: 1px solid var(--borderColor);
    padding-bottom: 10px;
    padding-top: 15px;
}
.slowfade_down-enter-active,
.slowfade_down-leave-active {
  transition: opacity .4s ease, transform .4s ease;
}
.slowfade_down-enter,
.slowfade_down-leave-to {
  opacity: 0;
  transform: translateY(8px);
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
.date_select{
    width: 100%!important;
    &::v-deep{
        .ant-calendar-range-picker-input{
            text-transform: capitalize;
            &::placeholder{
                &::first-letter{
                    text-transform: uppercase;
                }
            }
        }
    }
}
</style>