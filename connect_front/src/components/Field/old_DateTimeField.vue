<template>
    <div class="flex date_input_wrapper">
        <input
            class="px-2 py-1 border rounded focus:outline-none ant-input focus:border-blue-300"
            :class="size === 'large' && 'ant-input-lg'"
            v-model="valueInput"
            v-mask="mask"
            ref="input_datetime"
            @focus="focus"
            @change="changeInput"
            @keyup.enter="enterHandler"
            :disabled="disabled"
            :placeholder="placeholder"/>
        <a-popover
            class="datePickerPopover"
            v-model="visible"
            destroyTooltipOnHide
            trigger="click"
            @visibleChange="popupVisibleChange">
            <template slot="content">
                <v-date-picker
                    ref="datepicker"
                    v-model="valueDate"
                    :mode="time ? 'dateTime' : 'date'" is24hr
                    :masks="masks"/>
            </template>
            <div class="flex">
                <a-button
                    :disabled="disabled"
                    type="link"
                    class="select_btn ant-btn-icon-only">
                    <i class="fi fi-rr-calendar-lines-pen"></i>
                </a-button>
            </div>
        </a-popover>
    </div>
</template>

<script>
import {formatsInMoments} from '@/utils/dateSettings'
export default {
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
        }
    },
    computed: {
        size() {
            if (this.wConfig) {
                return this.wConfig.size;
            } else return "default";
        },
        disabled(){
            if(this.wConfig.disabled !== undefined){
                return false
            } else {
                return this.wConfig.disabled
            }
        }
    },
    watch:{
        'valueDate'(val) {
            if(this.edit){ 
                const date = val ? this.$moment(val, this.dateFormat).format(this.dateFormat) : null
                this.$emit("input", date)
                this.$emit('change', date)
                this.valueDate = val ? val : null
                this.valueInput = date
            }
        },
        value(val){
            if(val === null){
                this.valueInput = ""
            } else {
                this.edit = false
                if(this.value){ 
                    this.valueDate = val
                    const date = val ? this.$moment(val,  formatsInMoments ).format(this.dateFormat) : null
                    this.valueInput = date
                }
                setTimeout(() => {
                    this.edit = true 
                }, 300);
               
            }
            
        }
    },
    data() {
        return {
            visible: false,
            valueDate: "",
            valueInput: "",
            edit: true,
            masks: {
                input: this.dateFormat,
                inputTime: this.dateFormat,
                inputTime24hr: this.dateFormat,
                inputDateTime24hr: this.dateFormat,
                inputDateTime: this.dateFormat
            },
            mask: this.dateFormat.replace(/[A-Z,a-z]/g, '#')
        }
    },
    created() {
        if(this.currentDate && !this.value)
            this.valueDate = new Date()

        if(this.value)
            this.valueDate = this.$moment(this.value, [this.dateFormat, ...formatsInMoments ]).toDate()
    
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
        changeInput(){
            if(this.valueInput) { 
                const date = this.$moment(this.valueInput, this.dateFormat).toDate()

                if(isNaN(date)){
                    this.valueDate = new Date()
                    this.$message.error("Неверная дата")
                }else this.valueDate = date
            } else {
                this.$emit("input", null)
                this.$emit('change', null)
            }
        },
        visibleChange(){
            if(!this.visible)
                this.$emit('hidePopover')
        },
        focus(){
            this.$emit('focus')
        }
    }
}
</script>

<style lang="scss" scoped>
.date_input_wrapper {
    position: relative;
    .select_btn{
    position: absolute;
    top: 0;
    right: 0;
    height: 30px;
    width: 30px;
   
  }

    .ant-input {
        // border-radius: var(--borderRadius) 0 0 var(--borderRadius);
    }
    .select_btn {
        // border-radius: 0 var(--borderRadius) var(--borderRadius) 0;
        margin-left: -1px;
        // height: 32px;
    }
}
.vc-select select{
    min-height: 40px !important;
    min-width: 60px;
}
.vc-time-picker{
    border: none;
    padding: 0;
}
.vc-container{
    border: none;
}
</style>
