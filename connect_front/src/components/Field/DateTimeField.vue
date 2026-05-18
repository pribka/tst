<template>
    <Datepicker 
        v-model="valueDate"
        :focusHandler="focus"
        class="filter_date_picker"
        :show-time="time ? { format: 'HH:mm' } : false"
        :dateFormat="dateFormat"
        :allowClear="allowClear"
        :placeholder="placeholder"
        @input="changeInput" />
</template>

<script>
import {formatsInMoments} from '@/utils/dateSettings'
export default {
    name: 'DateTimeField',
    components: {
        Datepicker: () => import('@apps/Datepicker')
    },
    props: {
        value: {
            type: [String, Number, Date, null],
        },
        dateFormat: {
            type: String,
            default: "DD-MM-YYYY",
        },
        placeholder: {
            type: String,
            default: "__/__/____",
        },
        wConfig: {
            type: Object,
            default: () => null,
        },
        currentDate: {
            type: Boolean,
            default: false,
        },
        allowClear: {
            type: Boolean,
            default: false
        },
        time: {
            type: Boolean,
            default: false
        },
        opened: {
            type: Boolean,
            default: false
        },
        enterHandler: {
            type: Function,
            default: () => {}
        },
        focus: {
            type: Function,
            default: () => {}
        }
    },
    data() {
        return {
            visible: false,
            valueDate: "",
            valueInput: "",
            edit: true
        }
    },
    created() {
        if(this.currentDate && !this.value)
            this.valueDate = new Date()

        if(this.value)
            this.valueDate = this.$moment(this.value, [this.dateFormat, ...formatsInMoments ])
    
        if(this.value === null){
            this.valueInput = ""
        }

        if(this.opened)
            this.visible = true
    },
    methods: {
        inputFocus() {
            this.$refs.input_datetime.focus()
            this.$refs.input_datetime.select()
        },
        popupVisibleChange(val) {
            if(!val){
                this.$emit('hidePopover')
            } else {
                const datepicker = this.$refs.datepicker
                const date = this.$moment(this.valueInput, this.dateFormat).toDate()

                if(isNaN(date)) { 
                    // this.valueDate = new Date()
                } else
                    this.valueDate = date

                if(datepicker)
                    datepicker.move(this.valueDate);
            }
        },
        changeInput(newDate) {
            const date = newDate ? this.$moment(newDate, this.dateFormat).format(this.dateFormat) : null

            this.$emit('input', date)
            this.$emit('change')
        },
        visibleChange(){
            if(!this.visible)
                this.$emit('hidePopover')
        }
    }
}
</script>

<style lang="scss" scoped>
.filter_date_picker{
    min-width: initial !important;
}
</style>