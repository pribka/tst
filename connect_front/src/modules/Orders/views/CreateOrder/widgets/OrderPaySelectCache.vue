<template>
    <div class="payment_select" :id="`field_${field.key}`">
        <a-form-model-item
            :ref="field.key"
            :label="field.name"
            class="form_item"
            :prop="field.key"
            :rules="field.rules">
            <a-select
                :size="field.size"
                v-model="form[field.key]"
                :loading="paymentLoader"
                :not-found-content="null"
                :getPopupContainer="getPopupContainer"
                @dropdownVisibleChange="dropdownVisibleChange"
                @change="selectTypeChange">
                <a-select-option
                    v-for="item in paymentList"
                    :value="item.id"
                    :key="item.id">
                    {{ item.string_view }}
                </a-select-option>
            </a-select>
        </a-form-model-item>
        <template v-if="selectPayType && selectPayType.code === 'cache'">
            <div 
                class="mb-2" 
                :class="!isMobile && 'flex items-center justify-between'">
                <!--<div class="w-1/2">
                    <a-form-model-item
                        label="Получатель"
                        prop="cash_pay_recipient">
                        <UserDrawer
                            v-model="form['cash_pay_recipient']"
                            canClearValue
                            :form="form"
                            :field="{ name: 'Получатель', rules: {} }"
                            inputSize="large"
                            :apiPath="'/user/list_by_task/'"
                            title="Выбрать пользователя" />
                    </a-form-model-item>
                </div>-->
                <div class="w-1/2">
                    <a-form-model-item
                        label="Способ получения">
                        <a-tree-select
                            v-model="form['cash_pay_type']"
                            tree-data-simple-mode
                            :size="field.size"
                            :loading="cashLoader"
                            :getPopupContainer="getPopupContainer"
                            treeDefaultExpandAll
                            style="width: 100%"
                            :dropdown-style="{ maxHeight: '400px', overflow: 'auto' }"
                            :tree-data="cashTypes"
                            :replaceFields="{
                                title:'name', 
                                key:'id',
                                value: 'id'
                            }"
                            :load-data="onLoadData"/>
                        <!--<a-select
                            v-model="form['cash_pay_type']"
                            size="large"
                            :loading="paymentLoader"
                            :not-found-content="null">
                            <a-select-option
                                v-for="item in cashTypes"
                                :value="item.id"
                                :key="item.code">
                                {{ item.string_view }}
                            </a-select-option>
                        </a-select>-->
                    </a-form-model-item>
                </div>
                <div class="w-1/2">
                    <a-form-model-item
                        label="Остаток по оплате"
                        :class="!isMobile && 'ml-2'">
                        <a-input-number
                            size="large"
                            v-model="form['amount_paid']"
                            disabled
                            :min="null"
                            :formatter="value => `${value}`.replace(/\B(?=(\d{3})+(?!\d))/g, ' ')"
                            class="w-full" />
                    </a-form-model-item>
                </div>
            </div>
            <div :class="!isMobile && 'flex items-center'">
            </div>
        </template>
        <template v-if="selectPayType && selectPayType.code === 'non-cache'">
            <div class="flex justify-between">
                <div class="w-1/2">
                    <a-form-model-item
                        label="Дата оплаты"
                        :rules="dataPickerRules()"
                        prop="pay_date_plan"
                        :class="!isMobile && 'ml-2'">
                        <a-date-picker
                            v-model="form['pay_date_plan']"
                            size="large"
                            :locale="locale"
                            placeholder="Введите дату"
                            :format="dateFormat"
                            :formatter="dateFormat"
                            :valueFormat="valueFormat"
                            :getCalendarContainer="getPopupContainer"
                            @change="onChange"
                            class="w-full" />
                    </a-form-model-item>
                </div>
                <div class="w-1/2">
                    <a-form-model-item
                        label="Остаток по оплате"
                        :class="!isMobile && 'ml-2'">
                        <a-input-number
                            size="large"
                            v-model="form['amount_paid']"
                            disabled
                            :min="null"
                            :formatter="value => `${value}`.replace(/\B(?=(\d{3})+(?!\d))/g, ' ')"
                            class="w-full" />
                    </a-form-model-item>
                </div>
            </div>
        </template>
        <template v-if="selectPayType && item.selectCodeMessage && item.selectCodeMessage[selectPayType.code]">
            <a-alert type="info" show-icon>
                <template slot="description">
                    <div v-html="item.selectCodeMessage[selectPayType.code]"></div>
                </template>
            </a-alert>
        </template>
    </div>
</template>

<script>
//import UserDrawer from './UserDrawer';
import locale from 'ant-design-vue/es/date-picker/locale/ru_RU'

export default {
    //components: { UserDrawer },
    props: {
        item: {
            type: Object,
            required: true
        },
        form: {
            type: Object,
            required: true
        },
        amount: {
            type: [String, Number],
            required: true
        },
        getFormRef: {
            type: Function,
            default: () => {}
        },
        edit: {
            type: Boolean,
            default: false
        },
        payDatePlanRequired: {
            type: Boolean,
            default: false
        },
        setOrderFormCalculated: {
            type: Function,
            default: () => {}
        }
    },
    computed: {
        contractor() {
            return this.form.contractor
        },
        selectPayType () {
            if(this.form?.[this.field.key]) {
                const find = this.paymentList.find(f => f.id === this.form[this.field.key])
                if(find)
                    return find
                else
                    return null
            } else
                return null
        },
        cartAmount() {
            return parseFloat(this.amount)
        },
        isMobile() {
            return this.$store.state.isMobile
        }
    },
    data() {
        return {
            paymentLoader: false,
            paymentList: [],
            field: {},
            cashTypes: [],
            cashLoader: false,
            recipientDate: null,
            dateFormat: "DD-MM-YYYY",
            valueFormat: "YYYY-MM-DD",
            locale,
            selected: null
        }
    },
    created() {
        this.field = this.item.fields[0]

        if(this.form[this.field.key]?.id)
            this.form[this.field.key] = this.form[this.field.key].id
        if(this.edit && !this.paymentList.length)
            this.getPayTypes()
        if(this.form.cash_pay_type?.id)
            this.form.cash_pay_type = this.form.cash_pay_type.id
    },
    methods: {
        onChange(e) {
            if(this.edit)
                this.setOrderFormCalculated(false)
        },
        async onLoadData(treeNode) {
            try {
                const data = treeNode.dataRef
                this.selected = data
                if(data.is_group) {
                    await this.getCachTypes(false, data.id)
                }
            } catch(e) {
                console.log(e)
            }
        },
        getPopupContainer() {
            return document.querySelector('.payment_select')
        },
        dataPickerRules() {
            if (this.payDatePlanRequired) {
                return { required: true, message: 'Введите дату!'}
            } else {
                return {}
            }
        },
        selectTypeChange(e) {
            const find = this.paymentList.find(f => f.id === e)
            if(find?.code === 'cache') {
                this.cashTypes = []
                this.getCachTypes(true)
            }
            if(this.edit)
                this.setOrderFormCalculated(false)
        },
        selectChange() {
            this.$nextTick(() => {
                const formRef = this.getFormRef()
                if(formRef) {
                    formRef.validateField('amount_to_cash_secondary')
                    formRef.validateField('amount_to_cash')
                }
            })
        },
        closeUserDrawer() {
            this.userDrawer = false
        },
        clearSelect() {
            this.form['cash_unit_secondary'] = null
            this.form['amount_to_cash_secondary'] = null
            this.$nextTick(() => {
                const formRef = this.getFormRef()
                if(formRef) {
                    formRef.validateField('amount_to_cash_secondary')
                    formRef.validateField('amount_to_cash')
                }
            })
        },
        amountValid(rule, value, callback) {
            const formRef = this.getFormRef()
            if(formRef) {
                if(value) {
                    const fieldValue = parseFloat(value)
                    const amountSecondary = this.form['amount_to_cash_secondary'] ? parseFloat(this.form['amount_to_cash_secondary']) : 0
                    const plusSum = fieldValue + amountSecondary

                    formRef.validateField('cash_unit_secondary')

                    if(plusSum === this.cartAmount) {
                        return callback()
                    } else {
                        return callback(new Error('Не совпадает с суммой заказа'))
                    }
                } else
                    return callback(new Error('Обязательно для заполнения'))
            } else
                return callback(new Error('Ошибка формы'))
        },
        amountValid2(rule, value, callback) {
            const formRef = this.getFormRef()
            if(formRef) {
                if(this.form['cash_unit_secondary']) {
                    if(value) {
                        const fieldValue = parseFloat(value)
                        const amountFirst = this.form['amount_to_cash'] ? parseFloat(this.form['amount_to_cash']) : 0
                        const plusSum = fieldValue + amountFirst

                        formRef.validateField('amount_to_cash')

                        if(plusSum === this.cartAmount) {
                            return callback()
                        } else {
                            return callback(new Error('Не совпадает с суммой заказа'))
                        }
                    } else
                        return callback(new Error('Обязательно для заполнения'))
                } else
                    return callback()
            } else
                return callback(new Error('Ошибка формы'))
        },
        dropdownVisibleChange(val) {
            if(val) {
                this.getPayTypes()
            }
        },
        cacheVisibleChange(val) {
            if(val) {
                this.getCachTypes()
            }
        },
        async getPayTypes() {
            if(!this.paymentList?.length && this.contractor) {
                try {
                    this.paymentLoader = true
                    let params = {
                        ...this.field.params,
                    }
                    if(this.field?.filters) {
                        const filterURL = `{"${this.field.filters.name}":"${this[this.field.filters.from_field]}"}`
                        params.filters = filterURL
                    }
                    const { data } = await this.$http.get(this.field.apiPath, { params })
                    if(data?.selectList?.length) {
                        this.paymentList = data.selectList
                        if(this.edit) {
                            this.getCachTypes(true)
                        }
                    }
                } catch(e) {
                    console.log(e)
                } finally {
                    this.paymentLoader = false
                }
            }
        },
        async getCachTypes(parent = false, pId = null) {
            if(!this.cashTypes?.length || !parent) {
                try {
                    this.cashLoader = true
                    let params = {}

                    if(parent) {
                        params.filters = {
                            parent__isnull :true
                        }
                    } else {
                        params.filters = {
                            parent: pId
                        }
                    }

                    const { data } = await this.$http.get('/crm/cash_pay_types/', { params })
                    if(data?.results?.length) {
                        const results = data.results.map(item => {
                            return {
                                ...item,
                                isLeaf: !item.is_group,
                                children: [],
                                disabled: item.is_group
                            }
                        })

                        if(parent) {
                            this.cashTypes = results
                        } else {
                            const index = this.cashTypes.findIndex(f => f.id === pId)
                            if(index !== -1) {
                                this.cashTypes[index].children = results
                            }
                        }

                        if(this.edit) {
                            data.results.forEach(item => {
                                if(item.is_group) {
                                    this.getCachTypes(false, item.id)
                                }
                            })
                        }
                    }
                } catch(e) {
                    console.log(e)
                } finally {
                    this.cashLoader = false
                }
            }
        }
    },
    beforeDestroy() {
        this.form[this.field.key] = null
    }
}
</script>

<style lang="scss">
.payment_select{
    li.ant-select-tree-treenode-disabled > .ant-select-tree-node-content-wrapper span{
        color: #505050;
        cursor: default;
    }
}
</style>