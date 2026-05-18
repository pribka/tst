<template>
    <div class="flex w-full justify-between h-8">
        <div class="flex items-center">
            <a-button
                size="small"
                type="ui"
                shape="circle"
                flaticon
                icon="fi-rr-arrow-down"
                class="flex items-center justify-center"
                @click="moveColumn('down')" />
            <a-button
                size="small"
                type="ui"
                shape="circle"
                flaticon
                icon="fi-rr-arrow-up"
                class="flex items-center justify-center ml-1"
                @click="moveColumn('up')" />
            
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
                    {{ $t(column.label) }}
                </template>
            </a-checkbox>
        </div>
        <template v-if="!isEdit">
            <div>
                <a-radio-group 
                    v-model="columnFixed" 
                    @change="pinColumn"
                    class="flex">
                    <a-radio 
                        v-for="option in fixedOptions"
                        :key="option.value"
                        :value="option.value">
                        <i :class="option.label"></i>
                    </a-radio>
                </a-radio-group>
            </div>
        </template>
    </div>
</template>

<script>
export default {
    name: 'CheckboxColumn',
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
        },
        tableName: {
            type: String,
            required: true
        }
    },
    data() {
        return {
            isEdit: false,
            columnName: this.column.label,
            columnFixed: this.column.fixed,
            fixedOptions: [
                { label: 'fi fi-rr-align-justify', value: false },
                { label: 'fi fi-rr-align-left', value: 'left' },
                { label: 'fi fi-rr-symbol', value: 'right' },
            ],
        }
    },
    methods: {
        toogleEditMode() {
            this.isEdit = !this.isEdit
        },
        // moveColumnUp() {
        //     const index = this.tableColumns.findIndex(column => column.dataIndex === this.column.value)
        //     if(this.tableColumns[index - 1]?.hidable) {
        //         const currentColumn = {...this.tableColumns[index]}
        //         const nextColumn = {...this.tableColumns[index - 1]}
        //         currentColumn.fixed = false
        //         nextColumn.fixed = false
        //         this.$set(this.tableColumns, index, nextColumn)
        //         this.$set(this.tableColumns, index - 1, currentColumn)
        //     }
        // },
        // moveColumnDown() {
        //     const index = this.tableColumns.findIndex(column => column.dataIndex === this.column.value)
        //     if(this.tableColumns[index + 1]?.hidable) {
        //         const currentColumn = {...this.tableColumns[index]}
        //         const nextColumn = {...this.tableColumns[index + 1]}
        //         currentColumn.fixed = false
        //         nextColumn.fixed = false
        //         this.$set(this.tableColumns, index, nextColumn)
        //         this.$set(this.tableColumns, index + 1, currentColumn)
        //     }
        // },
        /**
         * @param delta принимает 'up' или 'down' взависимости от направления перемещения столбца
         */
        moveColumn(direction) {
            let delta 
            if(direction === 'up')
                delta = -1
            else if(direction === 'down')
                delta = 1

            const index = this.tableColumns.findIndex(column => column.dataIndex === this.column.value)
            if(this.tableColumns[index + delta]?.hidable) {
                const currentColumn = {...this.tableColumns[index]}
                const nextColumn = {...this.tableColumns[index + delta]}
                currentColumn.fixed = false
                nextColumn.fixed = false
                this.$set(this.tableColumns, index, nextColumn)
                this.$set(this.tableColumns, index + delta, currentColumn)
            }
        },
        pinColumn(event) {
            const column = this.tableColumns.find(column => column.dataIndex === this.column.value)
            const fixed = event.target.value
            column.fixed = fixed
        }
    }
}
</script>

<style>
.columns_checkbox_group .ant-checkbox-group label {
    display: flex !important;
}
</style>