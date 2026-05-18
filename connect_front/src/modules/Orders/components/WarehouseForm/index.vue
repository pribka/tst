<template>
    <a-form-model
        ref="warehouseForm"
        :model="form"
        class="w-full"
        :class="[inlineForm && 'flex', isCart && 'grid grid-cols-3 gap-3']">
        <FieldSwitch
            v-for="field in warehouseFormInfo.formInfo"
            :key="field.key"
            :uniqKey="uniqKey"
            :inputSize="inputSize"
            :defaultValues="defaultValues"
            :checkRules="checkRules"
            :smallForm="smallForm"
            :field="field"
            :changeMeasureUnit="changeMeasureUnit"
            :changeAmountQuantity="changeAmountQuantity"
            :goods="goods"
            :disabled="disabled"
            :liveUpdate="liveUpdate"
            :changeCount="changeCount"
            :edit="edit"
            :setOrderFormCalculated="setOrderFormCalculated"
            :form="form" />
        <QuantityInMeasureUnits
            key="quantityInMeasureUnits"
            :uniqKey="uniqKey"
            :inputSize="inputSize"
            :defaultValues="defaultValues"
            :checkRules="checkRules"
            :smallForm="smallForm"
            :changeAmountQuantity="changeAmountQuantity"
            :count="count"
            :goods="goods"
            :warehouseId="warehouseId"
            :liveUpdate="liveUpdate"
            :changeCount="changeCount"
            :inputBlur="inputBlur"
            :disabled="disabled"
            :measureUnitName="measureUnitName"
            :countInputChange="countInputChange"
            :form="form"/>
    </a-form-model>
</template>

<script>
import { mapState } from 'vuex'
export default {
    components: {
        FieldSwitch: () => import('./fields/FieldSwitch.vue'),
        QuantityInMeasureUnits: () => import('./QuantityInMeasureUnits.vue')
    },
    props: {
        inlineForm: {
            type: Boolean,
            default: true
        },
        smallForm: {
            type: Boolean,
            default: false
        },
        uniqKey: {
            type: [String, Number],
            default: 'warehouse'
        },
        inputSize: {
            type: String,
            default: 'default'
        },
        checkRules: {
            type: Boolean,
            default: true
        },
        liveUpdate: {
            type: Boolean,
            default: false
        },
        defaultValues: {
            type: Object,
            default: () => null
        },
        changeCount: {
            type: Function,
            default: () => {}
        },
        goods: {
            type: Object,
            default: () => null
        },
        updateInjectQuantity: {
            type: Function,
            default: () => {}
        },
        isCart: {
            type: Boolean,
            default: false
        },
        count: {
            type: [String, Number],
            required: true
        },
        countInputChange: {
            type: Function,
            default: () => {}
        },
        inputBlur: {
            type: Function,
            default: () => {}
        },
        warehouseId: {
            type: String,
            default: ''
        },
        edit: {
            type: Boolean,
            default: false
        },
        setOrderFormCalculated: {
            type: Function,
            default: () => {}
        },
    },
    computed: {
        ...mapState({
            warehouseFormInfo: state => state.orders.warehouseFormInfo
        }),
        disabled() {
            return !this.$store.state.user.user.has_full_access_to_order_editing
        }
    },
    data () {
        return {
            form: {},
            amountQuantity: 0,
            measureUnitName: ''
        }
    },
    created() {
        if(this.warehouseFormInfo?.form) {
            let initForm = JSON.parse(JSON.stringify(this.warehouseFormInfo.form))

            if(this.goods) {
                for(let key in initForm) {
                    if(this.goods[`base_${key}`]) {

                        const find = this.warehouseFormInfo.formInfo.find(f => f.key === key)

                        if(find?.widget === 'Select') {
                            initForm[key] = this.goods[`base_${key}`].id
                        } else {
                            initForm[key] = this.goods[`base_${key}`]
                        }
                    }
                }
            }

            this.form = initForm
        }
    },
    methods: {
        changeAmountQuantity() {
            const formInfo = this.warehouseFormInfo.formInfo
            this.amountQuantity = 0

            formInfo.forEach(item => {
                if(item.participatesTotal && this.form[item.key]) {
                    const value = parseFloat(this.form[item.key])
                    this.amountQuantity = this.amountQuantity + value
                }
            })

            this.updateInjectQuantity(this.amountQuantity)
        },
        resetForm() {
            this.$refs.warehouseForm.resetFields()
        },
        validations() {
            let validForm = false
            this.$refs.warehouseForm.validate(valid => {
                if (valid) {
                    validForm = true
                } else {
                    validForm = false
                }
            })
            return validForm
        },
        changeMeasureUnit(measureUnitName) {
            this.measureUnitName = measureUnitName
        }
    }
}
</script>

<style>
.cart_info .ant-form {
    max-width: 100% !important;
}
</style>