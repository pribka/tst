<template>
    <a-date-picker
        v-model="date"
        style="width: 100%"
        :disabled="disabled"
        :dropdownClassName="dropdownClass"
        :placeholder="$t(placeholder)"
        :size="size"
        :iconPosition="iconPosition"
        :format="dateFormat"
        :inputType="inputType"
        :show-time="showTimeOptions"
        :getCalendarContainer="getCalendarContainer"
        :allowClear="allowClear"
        :showToday="showToday"
        :valueFormat="valueFormat"
        :disabled-date="checkDisabledDate"
        :disabled-time="checkDisabledTime"
        :autoFocus="autoFocus"
        :open="pickerOpen"
        @openChange="dateOpenChange"
        @change="dateChange">
        <template #suffixIcon>
            <slot name="suffixIcon">
                <i class="fi fi-rr-calendar" />
            </slot>
        </template>
        <template v-if="renderExtraFooter" #renderExtraFooter>
            <div class="dp-shortcuts mt-1" style="display:flex;flex-wrap:wrap;gap:6px;">
                <a-button
                    v-for="item in quickShortcuts"
                    :key="item.key"
                    size="small"
                    type="ui"
                    :title="item.title"
                    :disabled="item.disabled"
                    @click="applyShortcut(item.key)">
                    {{ item.label }}
                </a-button>
            </div>
        </template>
    </a-date-picker>
</template>

<script>
export default {
    name: 'EditTaskDatePicker',
    props: {
        value: [String, Date, Object],
        disabled: { type: Boolean, default: false },
        getCalendarContainer: [String, Function],
        placeholder: { type: String, default: 'select_date' },
        startTime: { type: Boolean, default: true },
        mask: { type: String, default: 'DD.MM.YYYY HH:mm' },
        dateFormat: { type: String, default: 'DD.MM.YYYY HH:mm' },
        showTime: { type: [Boolean, Object], default: false },
        allowClear: { type: Boolean, default: false },
        autoFocus: { type: Boolean, default: false },
        size: { type: String, default: 'default' },
        dropdownClassName: String,
        valueFormat: [Object, String],
        disabledAfter: [Object, String],
        disabledBefore: [Object, String],
        renderExtraFooter: { type: Boolean, default: false },
        showToday: { type: Boolean, default: false },
        iconPosition: { type: String, default: 'default' },
        inputType: { type: String, default: 'default' }
    },
    data() {
        return {
            pickerOpen: false,
            dropRandom: Math.floor(Math.random() * 100)
        }
    },
    computed: {
        date: {
            get() { return this.value },
            set(val) { this.$emit('input', val || null) }
        },
        dropdownClass() {
            return this.dropdownClassName || `popup_date_${this.dropRandom}`
        },
        showTimeOptions() {
            const options = typeof this.showTime === 'object' ? { ...this.showTime } : {}
            const defaultTime = this.startTime ? '09:00:00' : '18:00:00'
            options.defaultValue = this.$moment(defaultTime, 'HH:mm:ss')
            return options
        },
        quickShortcuts() {
            // Собираем список кнопок с превью датой и подсказкой
            const items = [
                { key: 'today', label: this.$t('task.date_today'), make: () => this.$moment() },
                { key: 'tomorrow', label: this.$t('task.date_tomorrow'), make: () => this.$moment().add(1, 'day') },
                { key: 'end_week', label: this.$t('task.date_end_week'), make: () => this.$moment().endOf('isoWeek') },
                { key: 'plus_week', label: this.$t('task.date_plus_week'), make: () => this.$moment().add(1, 'week') },
                { key: 'end_month', label: this.$t('task.date_end_month'), make: () => this.$moment().endOf('month') }
            ]

            return items.map(it => {
                const m = this.applyDefaultTime(it.make())
                const title = this.tooltipFormat(m)
                const disabled = this.checkDisabledDate(m)
                return { ...it, moment: m, title, disabled }
            })
        }
    },
    methods: {
        openPicker() { this.pickerOpen = true },
        getBoundaryMoment(value) {
            if (!value)
                return null

            const momentValue = this.$moment(value)

            return momentValue.isValid() ? momentValue : null
        },
        range(start, end) {
            const result = []
            for (let i = start; i < end; i++) result.push(i)
            return result
        },
        getHourAndMinute(date) {
            const momentDate = this.$moment(date)
            return { hour: momentDate.hour(), minute: momentDate.minute() }
        },
        getDisabledTimeRange({ before, after }) {
            const { hour: beforeHour, minute: beforeMinute } = before ? this.getHourAndMinute(before) : {}
            const { hour: afterHour, minute: afterMinute } = after ? this.getHourAndMinute(after) : {}

            return {
                disabledHours: () => {
                    const hours = []
                    if (before) hours.push(...this.range(0, beforeHour))
                    if (after) hours.push(...this.range(afterHour + 1, 24))
                    return hours
                },
                disabledMinutes: (selectedHour) => {
                    const minutes = []
                    if (before && selectedHour === beforeHour) {
                        minutes.push(...this.range(0, beforeMinute))
                    }
                    if (after && selectedHour === afterHour) {
                        minutes.push(...this.range(afterMinute + 1, 60))
                    }
                    return minutes
                }
            }
        },
        checkDisabledTime() {
            const selectedDate = this.$moment(this.date)
            const before = this.getBoundaryMoment(this.disabledBefore)
            const after = this.getBoundaryMoment(this.disabledAfter)
            const isBeforeDay = before && selectedDate.isSame(before, 'day')
            const isAfterDay = after && selectedDate.isSame(after, 'day')

            if (isBeforeDay && isAfterDay) {
                return this.getDisabledTimeRange({ before, after })
            }
            if (isBeforeDay) {
                return this.getDisabledTimeRange({ before })
            }
            if (isAfterDay) {
                return this.getDisabledTimeRange({ after })
            }
            return false
        },
        checkDisabledDate(current) {
            const before = this.getBoundaryMoment(this.disabledBefore)
            const after = this.getBoundaryMoment(this.disabledAfter)

            if (before && after) {
                return !current.isBetween(before, after, 'day', '[]')
            }

            if (before) {
                const endOfCurrentDay = this.$moment(current).endOf('day')
                return endOfCurrentDay.isBefore(before)
            }

            if (after) {
                const startOfCurrentDay = this.$moment(current).startOf('day')
                return startOfCurrentDay.isAfter(after)
            }

            return false
        },
        dateOpenChange(status) {
            this.pickerOpen = status
            this.$emit('openChange', status)
        },
        dateChange(val) {
            this.$emit('input', val)
            this.$emit('change', val)
        },

        // ====== Быстрые кнопки ======
        applyShortcut(key) {
            const item = this.quickShortcuts.find(i => i.key === key)
            if (!item || item.disabled) return

            // Приводим к типу, который ожидает внешний мир: либо moment, либо строка valueFormat
            const payload = this.normalizeForEmit(item.moment)

            // Отдаём наружу как будто пользователь сам выбрал в календаре
            this.dateChange(payload)
        },
        applyDefaultTime(baseMoment) {
            // Если showTime включён — ставим 09:00 или 18:00 (цццпо startTime),
            // иначе — начало дня.
            const m = this.$moment(baseMoment).clone()
            if (!this.showTime) {
                return m.startOf('day')
            }
            const def = this.showTimeOptions.defaultValue || this.$moment('00:00:00', 'HH:mm:ss')
            return m.hour(def.hour()).minute(def.minute()).second(def.second())
        },
        tooltipFormat(m) {
            const fmt = this.showTime ? (this.dateFormat || 'DD.MM.YYYY HH:mm') : 'DD.MM.YYYY'
            return this.$moment(m).format(fmt)
        },
        normalizeForEmit(m) {
            if (typeof this.valueFormat === 'string' && this.valueFormat) {
                return m ? this.$moment(m).format(this.valueFormat) : null
            }
            return m // moment
        }
    }
}
</script>
