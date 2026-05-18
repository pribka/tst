<template>
    <DSelect
        v-model="form[`x_${widget.property.code}`]"
        :label="widget.property.label"
        :name="`x_${widget.property.code}`"
        size="large"
        class="w-full"
        :oneSelect="oneSelect"
        :valueKey="valueKey"
        :params="params"
        :apiUrl="apiUrl"
        :listObject="listObject"
        :listHeight="listHeight"
        :firstSelected="firstSelected"
        :labelKey="labelKey"
        :allowClear="allowClear"
        :showSearch="showSearch"
        :page_size="page_size"
        initList
        :placement="placement"
        :infinity="infinity"
        :multiple="multiple"
        :placeholder="placeholder"
        @changeGetObject="changeGetObject" />
</template>

<script>
import DSelect from '@apps/DrawerSelect/Select.vue'
export default {
    components: {
        DSelect
    },
    props: {
        widget: {
            type: Object,
            required: true
        },
        form: {
            type: Object,
            default: () => {}
        },
        setSelectsList: {
            type: Function,
            default: () => {}
        }
    },
    computed: {
        valueKey() {
            return this.widget.widget.valueKey || 'code'
        },
        oneSelect() {
            return this.widget.widget.oneSelect || false
        },
        params() {
            return this.widget.widget.params || {}
        },
        placeholder() {
            return this.widget.widget.placeholder || this.$t('sports.selectFromList')
        },
        multiple() {
            return this.widget.widget.multiple || false
        },
        infinity() {
            return this.widget.widget.infinity || false
        },
        listObject() {
            return this.widget.widget.listObject || 'selectList'
        },
        labelKey() {
            return this.widget.widget.labelKey || 'string_view'
        },
        apiUrl() {
            return this.widget.widget.apiUrl || '/app_info/select_list/'
        },
        showSearch() {
            return this.widget.widget.showSearch || false
        },
        page_size() {
            return this.widget.widget.page_size || 15
        },
        firstSelected() {
            return this.widget.widget.firstSelected || false
        },
        initList() {
            return this.widget.widget.initList || true
        },
        maxTagCount() {
            return this.widget.widget.maxTagCount || 30
        },
        listHeight() {
            return this.widget.widget.listHeight || 256
        },
        placement() {
            return this.widget.widget.placement || 'bottomLeft'
        },
        allowClear() {
            return this.widget.widget.allowClear || false
        }
    },
    methods: {
        changeGetObject(obj) {
            this.setSelectsList(`x_${this.widget.property.code}`, obj)
        }
    }
}
</script>