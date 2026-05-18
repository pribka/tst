<template>
    <div class="w-full">
        <a-spin v-if="loading"/>
        <DSelect
            v-else
            v-model="valueProxy"
            :multiple="multiple"
            :apiUrl="getURL"
            class="w-full custom-select"
            size="default"
            infinity
            :initList="false"
            disallowCustomValues
            inputType="ghost"
            showSearch
            :loading="true"
            :initOptionList="initOptionList"
            :listObject="false"
            :maxTagCount="2"
            :valueKey="item.to_field"
            :placeholder="item.verbose_name"
            :params="{ pagination: 'page' }"
            labelKey="repr"
            :default-active-first-option="false"
            :filter-option="false" >
            <template slot="option_item" slot-scope="{ data }">
                <span class="option-tag truncate">
                    <a-badge /> {{ data.repr }}
                </span>
            </template>
        </DSelect>
    </div>
</template>

<script>
export default {
    components: { 
        DSelect: () => import("@apps/DrawerSelect/Select.vue")
    },
    props: {
        item: {
            type: Object,
            required: true,
        },
        changeItemValue: {
            type: Function,
            required: true,
        },
    },

    computed: {
        multiple() {
            return ['in', 'not in'].includes(this.item.comparison_type)
        },
        normalizedInitOptionList() {
            const valueKey = this.item.to_field || 'id'
            return (this.item.initOptionList || []).map(option => {
                const id = option?.[valueKey] || option?.id || option?.value || null
                const repr = option?.repr
                    || option?.string_view
                    || option?.full_name
                    || option?.fullname
                    || option?.name
                    || [option?.last_name, option?.first_name].filter(Boolean).join(' ')
                    || (id ? `ID ${id}` : '')

                return {
                    ...option,
                    id,
                    value: id,
                    [valueKey]: id,
                    repr,
                    string_view: repr,
                    name: option?.name || repr,
                    full_name: option?.full_name || option?.fullname || repr
                }
            }).filter(option => option[valueKey])
        },
        valueProxy: {
            get() {
                return this.item.value || (this.multiple ? [] : null)
            },
            set(val) {
                this.changeItemValue(val)
            }
        },
        getURL() {
            return `/reports/${this.item.related_model.toLowerCase()}/select_list/`
        }
    },
    data() {
        return {
            initOptionList: [],
            loading: false
        }
    },
    watch: {
        normalizedInitOptionList: {
            immediate: true,
            handler(value) {
                this.initOptionList = value
            }
        }
    },
    mounted() {
        if ((this.multiple && !this.valueProxy.length) || !this.valueProxy) { return }
        if (this.initOptionList.length) { return }
        const url = `/reports/${this.item.related_model.toLowerCase()}/select_list/`
        const payload = {}
        const idsField = this.item.to_field || 'id'
        payload[idsField] = Array.isArray(this.valueProxy) ? this.valueProxy : [this.valueProxy]
        this.loading = true
        this.$http.post(url, payload)
            .then(({ data }) => this.initOptionList = data)
            .catch(error => { console.error(error) })
            .finally(() => {
                this.loading = false
            })
    },
    methods: {
        onChange(val) {
            this.$emit('change', val)
        },
    }
}
</script>

<style lang="scss" scoped>
::v-deep {
    .ant-select-selection__choice {
        .option-tag {
            display: inline-block;
            max-width: 100px;
        }
    }
    .ant-select-ghost:hover .ant-select-selection {
        background-color: #F0F1F7;
    }
}
</style>
