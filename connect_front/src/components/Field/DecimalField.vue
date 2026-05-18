<template>
    <div
        ref="input_number_wrap"
        class="flex input_number_wrap">
        <vue-autonumeric
            ref="input_number"
            id="input_number"
            class="numeric_input ant-input"
            @focus.native="focus"
            @input="inputChange"
            @keyup.native="keyDown"
            @keyup.esc.native="handleBlur"
            v-model="value"
            :placeholder="placeholder"
            :options="options"/>
    </div>
</template>

<script>
import Vue from "vue"
import VueAutonumeric from 'vue-autonumeric'
export default {
    components: {
        VueAutonumeric
    },
    props: {
        val: {
            type: [Number, String]
        },
        decimalLength: {
            type: Number,
            default: 3
        },
        
        minimumValue: {
            type: Number,
            default: -99999999999
        },
        
        maximumValue: {
            type: Number,
            default: 999999999999
        },
        placeholder: [String, Number]
        
    },
    data() {
        return {
            visibleCalc: false,
            value: null,
            calc: 0,
    
            // Кол-во символов после запятой
            // decimalLength: 3,
            // Позиция курсора
            oldSel: null,

            options: {
                caretPositionOnFocus: "decimalRight",
                allowDecimalPadding: true,
                alwaysAllowDecimalCharacter: true,
                decimalCharacter: ",",
                decimalCharacterAlternative: ".",
                decimalPlaces: 1,
                decimalPlacesRawValue: 2,
                decimalPlacesShownOnBlur: 2,
                decimalPlacesShownOnFocus: 2,
                digitGroupSeparator: " ",
                emptyInputBehavior: "null",
                leadingZero: "allow",
                isCancellable: false,

                selectOnFocus: true,
                watchExternalChanges: true,
                showWarnings: false,
                // minimumValue: 0,
                // maximumValue: 978789789789798,

            }
        }
    },
    watch:{
        val(val){
            this.value = val
        }
    },
    created() {
     
   
        // this.decimalLength = 3
        // // this.options.minimumValue = this.params.colDef?.cellEditorParams.minValue
        // // this.options.maximumValue = this.params.colDef?.cellEditorParams.maxValue

        this.options.decimalPlaces = this.decimalLength
        this.options.decimalPlacesRawValue = this.decimalLength
        this.options.decimalPlacesShownOnBlur = this.decimalLength
        this.options.decimalPlacesShownOnFocus = this.decimalLength

        // console.log("VALUE", this.val)
        // let startValue = this.val
            
        // // if(startValue === null){
        // //     startValue = 0.000
        // // }

        this.value = this.val
    },
    
    methods: {
       
        setValueCalc(value){
            this.value = value
            this.visibleCalc = false
            this.saveValue()
        },
        saveValue(){
            this.$emit('input', this.value)
            this.$emit('change', this.value)
        },
        keyDown(e){
            if(this.decimalLength > 0) {

                const value = e.target.value
                const key = e.key
                let valueLeft = parseInt(value?.split(',')[0]).toString()
                let valueRight = value?.split(',')[1]?.toString()


                if(key === "Backspace"){
                    if(value === "" || value == null){
                        this.value = ""
                    }else{ 

                        this.oldSel = e.target.selectionStart

                        let dValue;


                        if(valueRight?.length === 0 || valueRight === undefined){

                            dValue = this.toFloat(valueLeft + "." + "0000000000")

                        }else{
                            dValue = this.toFloat(valueLeft + "." + valueRight)
                        }


                        if(valueLeft.length === 0){

                            dValue = parseFloat(0 + '.' + valueRight)
                            this.oldSel = 1

                        }


                        if(value === ",000"){
                            dValue = "0.000"
                            this.oldSel = 1
                        }


                        e.target.value =  this.toFloat(dValue)


                        if(this.oldSel !== null){
                            setTimeout(() => {
                                e.target.setSelectionRange(this.oldSel, this.oldSel)
                            }, 1);

                        }
                    }
                }
            }

        },
        
        toFloat(value){
            return parseFloat(value).toFixed(this.decimalLength)
        },
        focus(){
            this.$emit('focus')
        },
        inputChange() {
            Vue.nextTick(() => {
                if(this.decimalLength > 0){
                    const input = this.$refs.input_number.anElement
                    const inputAutoNumeric = this.$refs.input_number.$refs.autoNumericElement
                    const value = input.lastVal?.toString()

                    let valueLeft = value?.split(',')[0].toString()
                    let valueRight = value?.split(',')[1]?.toString()

                      

                    if(value !== undefined){
                        if(value === "" || value == null){
                            this.value = ""
                        } else { 
                    

                            let finalValue = this.toFloat(value)
                            if(valueRight === undefined){
                                // Добавляем нули в конец если их нет
                                finalValue = this.toFloat(valueLeft + '.' + "00000000000")
                                this.value = finalValue


                                // Установка начального фокуса
                                if(value.length === 1){
                                    setTimeout(() => {
                                        inputAutoNumeric.setSelectionRange(1, 1)
                                    }, 10);
                                }

                            }
                        }
                    } 


                    this.saveValue()
                }

            })

        },
       
    },
   
}
</script>

<style lang="scss">
.input_number_wrap {
  position: relative;
  .select_btn{
    position: absolute;
    top: 0;
    right: 0;
    height: 30px;
    width: 30px;
   
  }


}
</style>