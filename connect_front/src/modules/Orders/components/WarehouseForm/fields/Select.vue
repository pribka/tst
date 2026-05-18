<template>
    <div :ref="`select_${uniqKey}`">
        <a-select
            v-model="form[field.key]"
            :loading="loading"
            class="w-full"
            :size="inputSize"
            :getPopupContainer="getPopupContainer"
            :not-found-content="null"
            @dropdownVisibleChange="dropdownVisibleChange"
            @change="changeValue">
            <a-select-option v-for="item in list" :key="item.id" :value="item.id">
                {{ item.string_view }}
            </a-select-option>
        </a-select>
    </div>
</template>

<script>
import eventBus from '@/utils/eventBus.js'
export default {
    props: {
        form: {
            type: Object,
            required: true
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
        changeMeasureUnit: {
            type: Function,
            default: () => {}
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
    data () {
        return {
            list: [],
            loading: false,
            reload: false
        }
    },
    created () {
        if(this.defaultValues?.[this.field.key]) {
            this.reload = true
            this.form[this.field.key] = this.defaultValues[this.field.key]?.id ? JSON.parse(JSON.stringify(this.defaultValues[this.field.key].id)) : null

            this.list = [JSON.parse(JSON.stringify({
                ...this.defaultValues[this.field.key],
                string_view: this.defaultValues[this.field.key]?.name_plural || 'Нет ключа названия'
            }))]
        } else {
            if(this.goods?.[`base_${this.field.key}`]) {
                this.reload = true
                this.list = [JSON.parse(JSON.stringify({
                    ...this.goods[`base_${this.field.key}`],
                    string_view: this.goods[`base_${this.field.key}`]?.name_plural || 'Нет ключа названия'
                }))]
            }
        }
        if(this.field.key === 'measure_unit')
            this.setMeasureUnitName(this.form[this.field.key])
    },
    methods: {
        changeValue(value) {
            if(this.liveUpdate)
                this.changeCount(null, {[this.field.key]: this.form[this.field.key] || null})

            if(this.goods?.[`base_${this.field.key}`]) {
                let baseValue = false

                if(this.goods?.[`base_${this.field.key}`].id === this.form[this.field.key]) {
                    baseValue = true
                } else {
                    baseValue = false
                }

                eventBus.$emit(`change_field_${this.field.key}_${this.uniqKey}`, baseValue)
            }
            if(this.field.key === 'measure_unit')
                this.setMeasureUnitName(value)
            
            if(this.edit)
                this.setOrderFormCalculated(false)
        },
        getPopupContainer() {
            return this.$refs[`select_${this.uniqKey}`] || document.body
        },
        dropdownVisibleChange(open) {
            if(open && !this.list.length || this.reload)
                this.getList()
        },
        async getList() {
            try {
                this.loading = true
                const { data } = await this.$http.get(this.field.apiPath)
                if(data?.filteredSelectList?.length) {
                    this.list = data.filteredSelectList
                    this.reload = false
                }
            } catch(e) {
                console.log(e)
            } finally {
                this.loading = false
            }
        },
        setMeasureUnitName(id) {
            const measureUnitString = this.getSelectOptionLabel(id)
            this.changeMeasureUnit(measureUnitString)
        },
        getSelectOptionLabel(optionId) {
            const selectOption = this.list.find(
                listItem => optionId === listItem.id
            )
            return selectOption?.string_view || ''
        }
    }
}
</script>