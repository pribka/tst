<template>
    <a-form-model-item
        :prop="field.key"
        :rules="rulesField"
        class="w-full form_field"
        :class="smallForm && 'form_field_small'"
        :label="field.name">
        <component
            v-if="!disabled"
            :is="fieldWidget"
            :form="form"
            :inputSize="inputSize"
            :uniqKey="uniqKey"
            :goods="goods"
            :liveUpdate="liveUpdate"
            :changeMeasureUnit="changeMeasureUnit"
            :changeCount="changeCount"
            :defaultValues="defaultValues"
            :changeAmountQuantity="changeAmountQuantity"
            :setOrderFormCalculated="setOrderFormCalculated"
            :edit="edit"
            :field="field"/>
        <div v-else class="flex justify-center">
            <div v-if="field.key === 'coefficient'">
                {{ form.coefficient }}
            </div>
            <div v-if="field.key === 'measure_unit'">
                {{ defaultValues.measure_unit.name_plural }}
            </div>
        </div>
    </a-form-model-item>
</template>

<script>
export default {
    props: {
        form: {
            type: Object,
            required: true
        },
        smallForm: {
            type: Boolean,
            default: false
        },
        field: {
            type: Object,
            required: true
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
        defaultValues: {
            type: Object,
            default: () => null
        },
        changeCount: {
            type: Function,
            default: () => {}
        },
        liveUpdate: {
            type: Boolean,
            default: false
        },
        goods: {
            type: Object,
            default: () => null
        },
        changeAmountQuantity: {
            type: Function,
            default: () => {}
        },
        changeMeasureUnit: {
            type: Function,
            default: () => {}
        },
        disabled: {
            type: Boolean,
            default: true
        },
        setOrderFormCalculated: {
            type: Function,
            default: () => {}
        },
        edit: {
            type: Boolean,
            default: false
        }
    },
    computed: {
        rulesField() {
            if(this.checkRules) {
                return this.field.rulesConfig
            } else
                return null
        },
        fieldWidget() {
            return () => import(`./${this.field.widget}.vue`)
                .then(module => {
                    return module
                })
                .catch(e => {
                    console.log('error')
                    return import(`./NotWidget.vue`)
                })
        }
    }
}
</script>

<style lang="scss">
.form_field{
    &.form_field_small{
        .ant-form-item-label{
            line-height: 18px;
        }
    }
    .ant-form-item-label {
        text-align: left;
    }
    .ant-form-item-label label {
        white-space: normal;
    }
}
</style>

<style lang="scss" scoped>
.form_field{
    &:not(:last-child){
        margin-right: 10px;
    }
    &.form_field_small{
        &:not(:last-child){
            margin-bottom: 5px;
        }
        &:last-child{
            margin-bottom: 0px;
        }
    }
}
</style>