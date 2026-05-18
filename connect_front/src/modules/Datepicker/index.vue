<template>
    <a-date-picker
        v-model="date"
        style="width: 100%"
        :dropdownClassName="dropdownClass"
        :placeholder="placeholder"
        :size="size"
        :iconPosition="iconPosition"
        :inputType="inputType"
        :format="dateFormat"
        :show-time="showTime"
        :allowClear="allowClear"
        :valueFormat="valueFormat"
        v-bind="dateLimitBindings"
        :autoFocus="autoFocus"
        @focus="focusHandler"
        @change="dateChange" />
</template>

<script>
export default {
    name: 'appComponentsDatepicker',
    props: {
        value: { type: [String, Date, Object] },
        getCalendarContainer: { type: [String, Function], default: null },
        placeholder: { type: String, default: 'Выберите дату' },
        dateFormat: { type: String, default: 'DD.MM.YYYY HH:mm' },
        showTime: { type: [Boolean, Object], default: false },
        allowClear: { type: Boolean, default: false },
        autoFocus: { type: Boolean, default: false },
        size: { type: String, default: 'default' },
        dropdownClassName: { type: String },
        dateLimit: { type: String, default: '' },
        valueFormat: { type: [Object, String], default: null },
        focusHandler: { type: Function, default: () => {} },
        iconPosition: { type: String, default: 'default' },
        inputType: { type: String, default: 'default' }
    },
    computed: {
        date: {
            get() {
                return this.value
            },
            set(val) {
                this.$emit('input', val || null)
            }
        },
        dropdownClass() {
            return this.dropdownClassName ? this.dropdownClassName : `popup_date_${this._uid}`
        },
        dateLimitBindings() {
            if (!this.dateLimit) return {}
            return {
                disabledDate: this.disabledDate,
                disabledTime: this.disabledDateTime
            }
        }
    },
    methods: {
        range(start, end) {
            const r = []
            for (let i = start; i < end; i++) r.push(i)
            return r
        },
        disabledDateTime(current) {
            const limit = this.$moment(this.dateLimit)
            if (!current) return {}
            const cur = this.$moment(current)
            if (!cur.isSame(limit, 'day')) return {}
            const h = limit.hour()
            const m = limit.minute()
            return {
                disabledHours: () => this.range(0, h),
                disabledMinutes: selectedHour => selectedHour === h ? this.range(0, m) : []
            }
        },
        disabledDate(current) {
            const limit = this.$moment(this.dateLimit).subtract(1, 'days').endOf('day')
            return current && current < limit
        },
        dateChange(val) {
            this.$emit('input', val)
        }
    }
}
</script>

<style lang="scss" scoped>
::v-deep .ant-calendar-picker-input.ant-input {
  padding-right: 30px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
</style>
