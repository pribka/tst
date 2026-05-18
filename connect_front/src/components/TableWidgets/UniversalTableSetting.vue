<template>
    <div 
        ref="tableWrapper" 
        class="flex-grow">
        <div class="columns_checkbox_group flex flex-col">
            <div class="mb-2 font-semibold">
                {{ $t('table.settings') }}
            </div>
            <div class="">
                <div class="mb-2 pb-2 border-b">
                    <div class="mb-1 font-medium">{{ $t('table.size') }}</div>
                    <a-radio-group 
                        :value="tableSize" 
                        @change="changeTableSize">
                        <a-radio 
                            v-for="option in tableSizeOptions"
                            :key="option.value"
                            :value="option.value">
                            {{ option.label}}
                        </a-radio>
                    </a-radio-group>
                </div>
                <div>
                    <div class="mb-2 flex justify-between font-medium">
                        <span>{{ $t('table.columns') }}</span>
                        <span>{{ $t('table.fixed') }}</span>
                    </div>
                    <a-checkbox 
                        ref="columnsCheckbox"
                        class="mb-1 pb-1 border-gray-300"
                        :indeterminate="indeterminate" 
                        :checked="checkAllColumns" 
                        @change="onCheckAllChange">
                        {{ $t('table.all') }}
                    </a-checkbox>
                </div>
            </div>
            <a-checkbox-group 
                v-model="columnsActive"
                @change="onColumnCheckboxChange">
                <a-row
                    v-for="column in columnOptions"
                    :key="column.value"
                    class="flex mt-1 first:mt-0">
                    <CheckboxColumn
                        :tableName="model+pageName"
                        :setColumnName="setColumnName"
                        :tableColumns="tableColumns"
                        :column="column" />
                </a-row>
            </a-checkbox-group>
        </div>
    </div>
</template>

<script>
import { mapActions } from 'vuex'
export default {
    components: {
        CheckboxColumn: () => import('./CheckboxColumn.vue')
    },
    props: {
        /* ___ ОБЯЗАТЕЛЬНЫЕ ВХОДНЫЕ ПАРАМЕТРЫ ___ */

        /* Нужен для получения дефолтных настроек. Может быть:
            tasks,
            logistic,
            orders,
            chat_tasks,
            interests,
            projects,
            groups,
            meetings,
            sprints,
            analytics */ 
        tableType: {
            type: String,
            required: true
        },
        /* Связываясь с pageName образует ключ, 
            под которым настройки таблицы хранятся в сторе */
        model: {
            type: String,
            required: true
        },
        /* Связываясь с model образует ключ, 
            под которым настройки таблицы хранятся в сторе */
        pageName: {
            type: String,
            required: true
        },      
        /* Функция обновления списка записей.
            Используется при изменении сортировки, размера страницы и т.п.  */
        updateData: {
            type: Function,
            required: true
        }
    },
    data() {
        return {
            expandedRowKeys: [],
            settingsVisible: false,
            indeterminate: false,
            checkAllColumns: false,
            columnsActive: [],
            tableSizeOptions: [
                { label: this.$t('table.small'), value: 'small' },
                { label: this.$t('table.middle'), value: 'middle' },
                { label: this.$t('table.large'), value: 'large' },
            ]
        }
    },
    computed: {
        tablesInfo() {
            return this.$store.state.table.tablesInfo
        },
        tableInfo() {
            return this.tablesInfo?.[this.model+this.pageName]
        },
        tableColumns() {
            if(this.tableInfo?.columns?.length)
                return this.tableInfo.columns
            else
                return []
        },
        settingsColumn() {
            const titleName = 'titleWithSettings'
            const settingsColumn = this.tableColumns.find(column => column?.slots?.title === titleName)
            return settingsColumn?.defaultTitle || ''
        },
        tableSize() {
            const defaultSize = 'small'
            const tableSize = this.tableInfo?.table_size

            return tableSize || (this.config?.theme?.tableSize ? this.config.theme.tableSize : defaultSize)
        },
        columnOptions() {
            const availableOptions = []
            this.tableColumns.forEach(column => {
                if(column.hidable)
                    availableOptions.push({
                        label: column.title,
                        value: column.dataIndex,
                        fixed: column.fixed
                    })
            })
            return availableOptions
        },
        tablePageSize() {
            const tableInfo = this.tableInfo
            if(tableInfo?.page_size)
                return tableInfo.page_size
            else
                return null
        },
        columnsVisible() {
            return this.tableColumns.filter(column => column.visible)
        },
    },
    async created() {
        await this.getTableInfo({ 
            page_name: this.pageName, 
            model: this.model ,
            table_type: this.tableType
        })
    },
    methods: {
        ...mapActions({
            getTableInfo: 'table/getTableInfo',
            setTableInfo: 'table/setTableInfo'
        }),
        onColumnCheckboxChange(checkedList) {
            this.indeterminate = !!checkedList.length && checkedList.length < this.columnOptions.length;
            this.checkAllColumns = checkedList.length === this.columnOptions.length;
        },
        onCheckAllChange({target}) {
            if(target.checked)
                this.tableColumns.forEach(column => 
                    column.hidable && this.columnsActive.push(column.dataIndex)
                )
            else
                this.columnsActive = []

            this.indeterminate = false
            this.checkAllColumns = target.checked
        },
        setColumnName(columnValue, newName) {
            const column = this.tableColumns.find(column => column.dataIndex === columnValue)
            column.title = newName
        },
        async setColumns() {
            this.tableColumns.forEach((column, index) => {
                const isActive = this.columnsActive.includes(column.dataIndex)
                const isCustomizable = !!column.hidable
                if(isCustomizable)
                    if(isActive) 
                        this.tableColumns[index].visible = true
                    else 
                        this.tableColumns[index].visible = false
            })
            await this.sendTableInfo()
        },

        async sendTableInfo() {
            const defaultPageSize = 15
            const settings = { 
                columns: this.tableInfo.columns,
                page_size: this.tableInfo.page_size || defaultPageSize,
                ordering: this.tableInfo.ordering
            }
            const params = {
                page_name: this.pageName,
                model: this.model,
                table_type: this.tableType,

                settings: settings 
            }
            try {
                await this.setTableInfo(params)
                await this.$http.post(`table_info/`, params)
            } catch (error) {
                console.error(error)
            }
        },
        columnsActiveInit() {
            this.columnsActive.splice(0)
            this.tableColumns.forEach(column => 
                (column.visible && column.hidable) && this.columnsActive.push(column.dataIndex)
            )
            this.indeterminate = !!this.columnsActive.length && this.columnsActive.length < this.columnOptions.length;
            this.checkAllColumns = this.columnsActive.length === this.columnOptions.length
        },
        async dropColumns() {
            const tableName = {
                model: this.model,
                page_name: this.pageName,    
            }
            try {
                const { data } = await this.$http.post('/table_info/', {
                    ...tableName,
                    table_type: this.tableType,
                    drop: true,
                })
                const params = {
                    ...tableName,
                    settings: data 
                }
                await this.setTableInfo(params)
                await this.updateData()
            } catch(error) {
                console.error(error)
            }
        },
        changeTableSize(event) {
            const size = event.target.value
            this.$store.commit('table/SET_TABLE_SIZE', {
                key: this.model+this.pageName,
                data: size
            })
        },
    },
    mounted() {
        this.columnsActiveInit()
    }
}
</script>


