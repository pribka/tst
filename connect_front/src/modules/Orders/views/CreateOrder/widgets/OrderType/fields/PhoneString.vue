<template>
    <div class="flex">
        <a-select
            class="country_select mr-1"
            size="large"
            :getPopupContainer="trigger => trigger.parentElement"
            v-model="currentCountry"
            @change="setCountry">
            <a-select-option
                v-for="mask in maskList" 
                :key="mask.country" 
                :value="mask.country">
                <template v-if="mask.icon">
                    <img 
                        width="24"
                        height="16"
                        :src="mask.icon">
                </template>
                <template v-else>
                    <div class="flex items-center justify-center w-6 h-4 bg-gray-100 text-sm text-gray-400">
                        ?
                    </div>
                </template>
            </a-select-option>
        </a-select>
        
        <input 
            @focus="focusHandler"
            @input="inputHandler"
            :ref="`${field.key}_field`"
            class='ant-input ant-input-lg' 
            type='tel'>
    </div>
</template>

<script>
export default {
    name: 'PhoneString',
    props: {
        form: {
            type: Object,
            required: true
        },
        field: {
            type: Object,
            required: true
        },
        visible: {
            type: Boolean,
            default: false
        }
    },
    data() {
        return {
            currentCountry: 'Unknown',
            defaultCountry: 'Unknown',
            previousPhone: this.form[this.field.key],
            phoneInput: null,
            savedPhoneOverflow: '',
            maskList: [
                {
                    mask: '+___________',
                    code: '+',
                    icon: '',
                    country: 'Unknown'
                },
                {
                    mask: '+_ (___) ___ __ __',
                    code: '7',
                    icon: 'https://cdn.kcak11.com/CountryFlags/countries/ru.svg',
                    country: 'Russia',
                    // nonuniqueCode: true
                },
                {
                    mask: '+_ (___) ___ __ __',
                    code: '7',
                    icon: 'https://cdn.kcak11.com/CountryFlags/countries/kz.svg',
                    country: 'Kazakhstan',
                    // nonuniqueCode: true
                },
                // {
                //     mask: '+___ (__) ___ __ __',
                //     code: '380',
                //     icon: 'https://cdn.kcak11.com/CountryFlags/countries/ua.svg',
                //     country: 'Ukraine',
                // },
                {
                    mask: '+___ __ ___ ____',
                    code: '998',
                    icon: 'https://cdn.kcak11.com/CountryFlags/countries/uz.svg',
                    country: 'Uzbekistan',
                },
                {
                    mask: '+___ (___) ___ ___',
                    code: '996',
                    icon: 'https://cdn.kcak11.com/CountryFlags/countries/kg.svg',
                    country: 'Kyrgyzstan',
                },
                {
                    mask: '+___ (__) ___ __ __',
                    code: '375',
                    icon: 'https://cdn.kcak11.com/CountryFlags/countries/by.svg',
                    country: 'Belarus',
                },
                // TODO Armenia
            ],
        }
    },
    mounted() {
        this.phoneInput = this.$refs[`${this.field.key}_field`]

        const contractorPhone = this.form[this.field.key]
        if(contractorPhone) {
            this.initPhone(contractorPhone)
        }
    },
    methods: {
        getMaskByPhone(phoneValue, phone='') {
            let mask = {
                mask: '____________',
                code: ''
            }
            if(/^\d/g.test(phone)) {
                return mask
            }
            this.maskList.forEach(maskItem => {
                const regExp = maskItem.code === '+' ? new RegExp('^\\+') : new RegExp('^\\+?' + maskItem.code)
                if(regExp.test(phoneValue))
                    mask = maskItem
                if(phone && regExp.test(phone))
                    mask = maskItem
            })
            return mask
        },
        getMaskedPhone(mask, phoneValue) {
            let i = 0
            const regExp = /./g
            return mask.replace(regExp, maskChar => {
                const isMaskChar = /[_\d]/.test(maskChar)
                if(isMaskChar && i < phoneValue.length)
                    return phoneValue.charAt(i++)
                else
                    return maskChar
            })
        },
        checkLimitExceeding(mask, phoneValue) {
            const digitLimit = mask.match(/_/g).length
            return phoneValue.length > digitLimit
        },
        alignCursor(inputType, phone, currentCode, cursorPositon) {
            if(inputType === 'insertFromPaste') {
                const match = phone.match(/_/)
                cursorPositon = match ? match.index : phone.length
            } else if(inputType === 'insertText') {
                // Нужно, чтобы предотвратить расхождение курсора с позицией ввода
                const phoneValue = this.getPhoneValue(phone)
                if(currentCode === phoneValue) 
                    cursorPositon = currentCode.length + 1
                    
                cursorPositon = this.moveCursorToLeftDigit(phone, cursorPositon)
                cursorPositon = this.moveCursorToRightDigit(phone, cursorPositon)
            } else if(inputType === 'deleteContentBackward') {
                cursorPositon = this.moveCursorToLeftDigit(phone, cursorPositon)
            } else if(inputType === 'deleteContentForward') {
                cursorPositon = this.moveCursorToRightDigit(phone, cursorPositon)
            }

            return cursorPositon
        },
        setCountry(selectedCountry) {
            const phone = this.phoneInput.value
            const phoneValue = this.getPhoneValue(phone)
            const countryMask = this.maskList.find(maskItem => maskItem.country === selectedCountry)
            const currentMask = this.getMaskByPhone(phoneValue, phone)
            const currentCode = currentMask.code
            
            let newPhone
            if((currentCode === '') || (currentCode === '+')) {
                newPhone = countryMask.code + phoneValue
            } else {
                const regExp = new RegExp('^\\+?' + currentCode)
                const newCode = countryMask.code === '+' ? '' : countryMask.code
                newPhone = phoneValue.replace(regExp, newCode)
            }

            const currentMaskLength = (currentMask.mask.match(/_/g) || []).length
            const countryMaskLength = (countryMask.mask.match(/_/g) || []).length
            
            // Сохраняем затираемое число
            if(phoneValue.length === currentMaskLength) {
                console.log('Телефон заполнен')
                // Если новый телефон превышает длину новой маски
                if(newPhone.length > countryMaskLength) {
                    // то узнаем на сколько символов он её превышает
                    const overflowNumber = newPhone.length - countryMaskLength
                    // сохраняем эти символы
                    this.savedPhoneOverflow = newPhone.substring(newPhone.length-overflowNumber)
                    // а у нового телефона обрезаем их
                    newPhone = newPhone.substring(0, newPhone.length-overflowNumber)
                // А если текущий телефон меньше новой маски
                } else if(newPhone.length < countryMaskLength) {
                    console.log('Телефон короче новой маски')
                    // то добавляем ему в конец сохраненные символы
                    
                    newPhone += this.savedPhoneOverflow
                    // и очищаем стираем их
                    this.savedPhoneOverflow = ''
                }
            }
            if(countryMask.code === '+') {
                const overflowNumber = newPhone.length - countryMaskLength
                newPhone = newPhone.substring(0, newPhone.length-overflowNumber)
                newPhone = '+' + newPhone
            }
            this.phoneInput.value =  newPhone
            this.imitateInput()
        },
        inputHandler(event) {
            if(event.inputType === 'insertText')
                this.savedPhoneOverflow = ''

            const phone = event.target.value
            const phoneValue = this.getPhoneValue(phone)
            const matchedMask = this.getMaskByPhone(phone)
            const currentCode = matchedMask.code
            const currentMask = matchedMask.mask
            
            let cursorPositon = event.target.selectionStart

            const isLimitExceeded = this.checkLimitExceeding(currentMask, phoneValue)
            if(isLimitExceeded) {
                this.phoneInput.value = this.previousPhone
                this.phoneInput.setSelectionRange(cursorPositon-1, cursorPositon-1)
                return
            }

            this.updateCountry(currentCode)

            const newPhone = this.getMaskedPhone(currentMask, phoneValue)
            this.phoneInput.value = newPhone
    
            const newCursorPosition = this.alignCursor(event.inputType, newPhone, currentCode, cursorPositon)
            this.phoneInput.setSelectionRange(newCursorPosition, newCursorPosition)
            
            this.form[this.field.key] = newPhone
            this.previousPhone = newPhone
        },
        focusHandler(event) {
            const phone = this.phoneInput.value
            let cursorPositon = event.target.selectionStart
            cursorPositon = this.moveCursorToLeftDigit(phone, cursorPositon)
            this.phoneInput.setSelectionRange(cursorPositon, cursorPositon)
        },
        getPhoneValue(phone) {
            return phone.replace(/\D/g, '')
        },
        initPhone(phone) {
            const phoneValue = this.getPhoneValue(phone)
            const matchedMask = this.getMaskByPhone(phoneValue)
            this.phoneInput.value = this.getMaskedPhone(matchedMask.mask, phoneValue)
            this.updateCountry(matchedMask.code, true)
        },
        imitateInput() {
            this.phoneInput.dispatchEvent(new Event('input', { bubbles: true }));
        },
        moveCursorToLeftDigit(phone, cursorPositon) {
            while(
                ((cursorPositon-1) >= 0) &&
                (!/\+|\d/.test(phone[cursorPositon-1]))
            ) {
                cursorPositon--
            }
            return cursorPositon
        },
        moveCursorToRightDigit(phone, cursorPositon) {
            while(
                ((cursorPositon+1) < phone.length) &&
                (!/[_\d]/.test(phone[cursorPositon]))
            ) {
                cursorPositon++
            }
            return cursorPositon
        },
        getPreviousPhoneCode() {
            const previousPhoneValue = this.getPhoneValue(this.previousPhone)
            const previousPhoneCode = this.getMaskByPhone(previousPhoneValue).code
            return previousPhoneCode
        },
        updateCountry(code, init=false) {
            const newMask = this.maskList.find(mask => mask.code === code)
            const previousPhoneCode = this.getPreviousPhoneCode()
            if(newMask)
                if(init || (previousPhoneCode !== newMask.code))
                    this.currentCountry = newMask.country
        }
    },

}
</script>

<style scoped lang="scss">
::v-deep .country_select.ant-select {
    width: 70px;
    .ant-select-selection__rendered {
        display: flex;
        align-items: center;
        padding-right: 2px;
    }
}
</style>