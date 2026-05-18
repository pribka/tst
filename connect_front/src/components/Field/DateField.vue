<template>
    <div>
        <v-date-picker  v-model="valueDate" mode="date" is24hr :input-debounce="500"  :masks="masks" >
            <template v-slot="{ inputValue, inputEvents, togglePopover,  }">
                <div class="flex date_input_wrapper"> 
                    <input
                        class="px-2 py-1 border rounded focus:outline-none ant-input focus:border-blue-300"
                        :class="size === 'large' && 'ant-input-lg'"
                        :value="inputValue"
                        v-mask="mask"
                        :disabled="wConfig.disabled"
                        @change="inputEvents.change"
                        @input="inputEvents.input"
                        :placeholder="wConfig.placeholder"/>
                    <a-button :disabled="wConfig.disabled" @click="togglePopover()" class="select_btn" icon="calendar" />
                </div>
               
            </template>
        </v-date-picker>

    </div>
</template>

<script>
export default {
    props: {
        value: {
            type: [String, Number],
        },
        maskFormat: {
            type: String,
            default: "YYYY-MM-DD",
        },
        dateFormat: {
            type: String,
            default: "YYYY-MM-DD",
        },
        placeholder: {
            type: String,
            default: "____/__/__",
        },
        wConfig: {
            type: Object,
            default: () => null,
        },
        currentDate: {
            type: Boolean,
            default: false,
        },
        enterHandler: {
            type: Function,
            default: () => {},
        },
    },
    computed: {
        size() {
            if (this.wConfig) {
                return this.wConfig.size;
            } else return "default";
        },


    },
    watch:{
        'valueDate'(val){
            const date = this.$moment(val).format(this.dateFormat)
            this.$emit("input", date);
        }
    },
    data() {
        return {
            visible: false,
            valueDate: "",
            
            masks: {
                input: this.maskFormat,
                inputTime: this.maskFormat,
                inputTime24hr: this.maskFormat,
                inputDateTime24hr: this.maskFormat,
                inputDateTime: this.maskFormat
            },
            mask: this.maskFormat.replace(/[A-Z,a-z]/g, '#'),
           
        };
    },
    created() {
        if (this.currentDate && !this.value)
            this.$emit("input", this.$moment().format("YYYY-MM-DD"));
        this.valueDate = this.value
    },
};
</script>

<style lang="scss">
.date_input_wrapper {
    .ant-input {
        border-radius: var(--borderRadius) 0 0 var(--borderRadius);
    }
    .select_btn {
        border-radius: 0 var(--borderRadius) var(--borderRadius) 0;
        margin-left: -1px;
        height: 32px;
    }
}
.date_popup_content {
    min-width: 300px;
}
</style>
