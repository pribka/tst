<template>
    <div :id="`field_${field.key}`">
        <a-form-model-item
            :ref="field.key"
            class="form_item"
            :prop="field.key"
            :rules="rules">
            <div :class="!isMobile && 'grid grid-cols-2 gap-3'">
                <div :class="isMobile && 'mb-3'">
                    <div class="ant-col ant-form-item-label">
                        <label>
                            {{ dateLabel }}
                        </label>
                    </div>
                    <a-date-picker 
                        v-model="dateInput"
                        :format="dateFormat" 
                        :size="field.size"
                        style="width: 100%"
                        valueFormat="YYYY-MM-DD"
                        :getCalendarContainer="getPopupContainer"
                        @change="selectDate" />
                </div>
                <div>
                    <div class="ant-col ant-form-item-label">
                        <label>
                            {{ dateTimeLabel }}
                        </label>
                    </div>
                    <div :class="!isMobile && 'grid grid-cols-2 gap-3'">
                        <a-time-picker 
                            v-model="timeInputGte"
                            style="width: 100%" 
                            :size="field.size"
                            placeholder="От"
                            :minute-step="30"
                            :disabled="dateInput ? false : true"
                            :format="dateTimeFormat"
                            :getPopupContainer="getPopupContainer"
                            @change="selectDate" />
                        <a-time-picker 
                            v-model="timeInputLte"
                            style="width: 100%" 
                            :size="field.size"
                            placeholder="До"
                            :minute-step="30"
                            :disabled="dateInput ? false : true"
                            :format="dateTimeFormat"
                            :getPopupContainer="getPopupContainer"
                            @change="selectDate" />
                    </div>
                </div>
            </div>
        </a-form-model-item>
    </div>
</template>

<script>
export default {
    name: "appComponentsDatepicker",
    props: {
        field: {
            type: Object,
            required: true
        },
        form: {
            type: Object,
            required: true
        },
        rules: {
            type: Object,
            required: false
        },
        value: {
            type: [String, Date, Object]
        },
        getCalendarContainer: {
            type: [String, Function],
            default: null
        },
        placeholder: {
            type: [String],
            default: "Выберите дату"
        },
        startTime: {
            type: Boolean,
            default: true
        },
        mask: {
            type: [String],
            default: 'DD.MM.YYYY HH:mm'
        },
        showTime: {
            type: [Boolean, Object],
            default: false
        },
        allowClear: {
            type: Boolean,
            default: false
        },
        autoFocus: {
            type: Boolean,
            default: false
        },
        size: {
            type: String,
            default: 'default'
        },
        dropdownClassName: {
            type: String,
        },
        dateLimit: {
            type: [String, Object],
            default: null
        },
        dateLimitFrom: {
            type: [String, Object],
            default: null
        },
        valueFormat: {
            type: [Object, String],
            default: null
        },
        rangeLimit: {
            type: [String, Object],
            default: null
        },
        rangeLimitDeadLine: {
            type: [String, Object],
            default: null
        },
        planLimit: {
            type: [String, Object],
            default: null
        },
        edit: {
            type: Boolean,
            default: false
        },
        // setOrderFormCalculated: {
        //     type: Function,
        //     default: () => {}
        // }
    },
    computed: {
        date:{
            get(){
                return this.value
            },
            set(val){
                if(val)
                    this.$emit('input', val)
                else
                    this.$emit('input', null)
            }
        },
        dropdownClass(){
            return this.dropdownClassName ? this.dropdownClassName : `popup_date_${this.dropRandom}`
        },
        dateLabel() {
            return this.field.dateLabel || 'Время доставки'
        },
        dateTimeLabel() {
            return this.field.timeLabel || 'Время доставки'
        },
        dateFormat() {
            return this.field.dateFormat || 'DD-MM-YYYY'
        },
        dateTimeFormat() {
            return this.field.timeFormat || 'HH:mm'
        },
        isMobile() {
            return this.$store.state.isMobile
        }
    },
    data() {
        return{
            dropRandom: Math.floor(Math.random(100,100)),
            dateInput: null,
            timeInputGte: null, 
            timeInputLte: null
        }
    },
    created() {
        if(this.edit && this.form['delivery_date_plan']) {
            if(this.form.delivery_date_plan.delivery_date_plan_gte) {
                this.dateInput = this.$moment(this.form.delivery_date_plan.delivery_date_plan_gte)
                this.timeInputGte = this.$moment(this.form.delivery_date_plan.delivery_date_plan_gte)
            }
            if(this.form.delivery_date_plan.delivery_date_plan_lte) {
                this.timeInputLte = this.$moment(this.form.delivery_date_plan.delivery_date_plan_lte)
            }
        }
    },
    methods: {
        getPopupContainer() {
            return document.querySelector('.delivery_details')
        },
        selectDate() {
            const dateGte = this.$moment(this.dateInput),
                dateLte = this.$moment(this.dateInput)

            if(this.timeInputGte) {
                const timeGte = this.$moment(this.timeInputGte)
                dateGte.set('hour', timeGte.format('HH')).set('minute', timeGte.format('mm'))
            }
            if(this.timeInputLte) {
                const timeLte = this.$moment(this.timeInputLte)
                dateLte.set('hour', timeLte.format('HH')).set('minute', timeLte.format('mm'))
            }
            
            this.form['delivery_date_plan_gte'] = dateGte.format('YYYY-MM-DD HH:mm')
            this.form['delivery_date_plan_lte'] = dateLte.format('YYYY-MM-DD HH:mm')

            // if(this.edit)
            //     this.setOrderFormCalculated(false)
        },
        range(start, end) {
            const result = [];
            for (let i = start; i < end; i++) {
                result.push(i);
            }
            return result;
        },
        disabledDateTime() {
            return {
                disabledHours: () => this.range(0, this.$moment(this.dateLimit).add(1, 'hours').format('HH'))
            }
        },
        disabledDateTimeFrom() {
            return {
                disabledHours: () => this.range(this.$moment(this.dateLimit).subtract({hours:1}).format('HH'), 24)
            }
        },
        checkDisabledTime() {
            if(this.dateLimitFrom){
                return this.disabledDateTimeFrom()
            } else if(this.dateLimit){
                return this.disabledDateTime()
            } else {
                return false
            }
        },
        disabledDate(current) {
            return current && current < this.$moment(this.dateLimit).subtract(1, 'days').endOf('day')
        },
        disabledDateFrom(current) {
            return current && current > this.$moment(this.dateLimitFrom).endOf('day')
        },
        disabledDateRange(current) {
            const endDate = typeof this.dateLimitFrom ? this.dateLimitFrom : this.dateLimitFrom.format()
            if(this.$moment(this.rangeLimit).isSame(current.format(), 'day')) {
                return false
            } else
                return !this.$moment(current).isBetween(this.rangeLimit, endDate)
        },
        disabledDateRangeDeadLine(current) {
            if(this.$moment(this.rangeLimitDeadLine).isSame(current.format(), 'day') || this.$moment(this.planLimit).isSame(current.format(), 'day')) {
                return false
            } else
                return !this.$moment(current).isBetween(this.planLimit, this.rangeLimitDeadLine)
        },
        checkDisabledDate(current) {
            if(this.rangeLimit && this.dateLimitFrom) {
                return this.disabledDateRange(current)
            } else if(this.rangeLimitDeadLine && this.planLimit) {
                return this.disabledDateRangeDeadLine(current)
            } else {
                if(this.dateLimitFrom) {
                    return this.disabledDateFrom(current)
                } else if(this.dateLimit) {
                    return this.disabledDate(current)
                } else {
                    return false
                }
            }
        },
        dateChange(val){
            this.$emit('input', val)
            this.$emit('change', val)
        }
    }

}
</script>