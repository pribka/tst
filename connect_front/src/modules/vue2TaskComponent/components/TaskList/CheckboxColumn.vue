<template>
    <div class="flex items-center h-8">
        
        <a-button
            size="small"
            class="flex items-center"
            @click="moveColumnDown">
            <i 
                class="fi fi-rr-angle-down"
                style="line-height: 100%;"></i>
        </a-button>
        <a-button
            size="small"
            class="flex items-center ml-1"
            @click="moveColumnUp">
            <i 
                class="fi fi-rr-angle-up"
                style="line-height: 100%;"></i>
        </a-button>
        
        <a-button
            size="small"
            type="link"
            class="ml-2"
            @click="toogleEditMode">
            <i class="fi fi-rr-pencil"></i>
        </a-button>
        <a-checkbox 
            size="small"
            :value="column.value"
            class="flex items-center">
            <template v-if="isEdit">
                <div class="flex items-center">
                    <a-input v-model="columnName" />
                    <a-button
                        @click="setColumnName(column.value, columnName); isEdit = false"
                        class="ml-2 flex items-center">
                        <i 
                            class="fi fi-rr-disk"
                            style="line-height: 100%;"></i>
                    </a-button>
                </div>
            </template>
            <template v-else>
                {{ column.label }}
            </template>
        </a-checkbox>
    </div>
</template>

<script>
export default {
    props: {
        column: {
            type: Object,
            required: true
        },
        tableColumns: {
            type: Array,
            required: true
        },
        setColumnName: {
            type: Function,
            required: true
        }
    },
    data() {
        return {
            isEdit: false,
            columnName: this.column.label
        }
    },
    methods: {
        toogleEditMode() {
            this.isEdit = !this.isEdit
        },
        moveColumnUp() {
            const index = this.tableColumns.findIndex(column => column.dataIndex === this.column.value)
            if(this.tableColumns[index - 1]?.hidable) {
                const currentColumn = {...this.tableColumns[index]}
                const nextColumn = {...this.tableColumns[index - 1]}
                currentColumn.fixed = false
                nextColumn.fixed = false
                this.$set(this.tableColumns, index, nextColumn)
                this.$set(this.tableColumns, index - 1, currentColumn)
            }
        },
        moveColumnDown() {
            const index = this.tableColumns.findIndex(column => column.dataIndex === this.column.value)
            if(this.tableColumns[index + 1]?.hidable) {
                const currentColumn = {...this.tableColumns[index]}
                const nextColumn = {...this.tableColumns[index + 1]}
                currentColumn.fixed = false
                nextColumn.fixed = false
                this.$set(this.tableColumns, index, nextColumn)
                this.$set(this.tableColumns, index + 1, currentColumn)
            }
        }
    }
}
</script>

<style>
.columns_checkbox_group .ant-checkbox-group label {
    display: flex !important;
}
</style>