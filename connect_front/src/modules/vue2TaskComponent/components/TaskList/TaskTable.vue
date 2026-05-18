<template>
    <div 
        v-if="showTableEmpty"
        class="list_table">
        <div class="flex items-center pb-4">
            <AddButton
                v-if="addButton"
                :formParams="formParams"
                :addButton="addButton"
                :extendDrawer="extendDrawer"
                :windowWidth="windowWidth"
                class="mr-2" />
            <div>
                <slot />
            </div>
            <ExcelBtn
                v-if="toExcel"
                :page_name="pageName"
                :queryParams="queryParams"
                :requestData="requestData"
                :orderQuery="orderQuery"
                :task_type="taskType"
                class="ml-2" />
        </div>
        <div class="table_container task_table">
            <a-table
                :scroll="scroll"
                :loading="listLoading"
                :columns="columnsVisible"
                @change="handleTableChange"
                :expandedRowKeys="expandedRowKeys"
                :expandIconColumnIndex="1"
                :size="tableSize"
                :pagination="false"
                :locale="{
                    emptyText: $t('task.no_data')
                }"
                :data-source="currentTaskList"
                :row-key="(record, index) => `${record.id}-${index}`">
                <div slot="titleWithSettings">
                    <div class="flex items-center">
                        <a-button
                            v-if="currentTaskList && currentTaskList.length" 
                            type="link"
                            size="small"
                            @click="settingsVisible = true"
                            class="flex items-center">
                            <i  
                                class="fi fi-rr-settings"
                                style="line-height: 100%;"></i>
                        </a-button>
                    </div>
                </div>
                <div slot="counter" slot-scope="text, record">
                    <a-tooltip 
                        v-if="record.rejected" 
                        destroyTooltipOnHide
                        :title="$t('task.problem_task_tooltip')">
                        <span
                            class="cursor-pointer counter_rejected"
                            @click="openTask(record)">
                            {{ record.counter }}
                        </span>
                    </a-tooltip>
                    <span
                        v-else
                        class="cursor-pointer"
                        @click="openTask(record)">
                        {{ record.counter }}
                    </span>
                </div>
                <template 
                    slot="name" 
                    slot-scope="text, record, expanded, indent">
                    <div class="flex items-center">
                        <TableName
                            v-model="expandedRowKeys"
                            :main="main"
                            :extendDrawer="extendDrawer"
                            :reloadTask="reloadTask"
                            :text="text"
                            :showChildren="showChildren"
                            :expanded="expanded"
                            :indent="indent"
                            :record="record" />
                    </div>
                </template>
                <template 
                    slot="contractor" 
                    slot-scope="text">
                    <Contractor 
                        :contractor="text" />
                </template>
                <template
                    slot="customer_card"
                    slot-scope="text">
                    <Contractor
                        :contractor="text" />
                </template>
                <template
                    slot="organization"
                    slot-scope="text">
                    <Contractor
                        :contractor="text" />
                </template>
                <template 
                    slot="potential_contractor" 
                    slot-scope="text">
                    <Contractor 
                        :contractor="text" />
                </template>
                <template 
                    slot="date_start" 
                    slot-scope="text">
                    <template v-if="text">
                        {{ $moment(text).format('D MMMM, HH:mm') }}
                    </template>
                </template>
                <template 
                    slot="date_start_plan" 
                    slot-scope="text">
                    <template v-if="text">
                        {{ $moment(text).format('D MMMM, HH:mm') }}
                    </template>
                </template>
                <template 
                    slot="date_start_fact" 
                    slot-scope="text">
                    <template v-if="text">
                        {{ $moment(text).format('D MMMM, HH:mm') }}
                    </template>
                </template>
                <template 
                    slot="owner" 
                    slot-scope="text">
                    <Profiler
                        :avatarSize="22"
                        nameClass="text-sm"
                        :user="text" />
                </template>
                <template 
                    slot="operator" 
                    slot-scope="text, record">
                    <template v-if="user && record.is_auction">
                        <a-popconfirm
                            :title="$t('task.take_task_confirm')"
                            :ok-text="$t('task.yes')"
                            :cancel-text="$t('task.no')"
                            @confirm="takeTask(record)">
                            <a-button 
                                size="small"
                                type="primary"
                                ghost
                                class="flex items-center"
                                :loading="takeLoader">
                                <i class="fi fi-rr-user-add mr-2"></i>
                                {{ $t('task.take_task_button') }}
                            </a-button>
                        </a-popconfirm>
                    </template>
                    <Operator
                        v-else 
                        :item="text" 
                        :record="record"/>
                </template>
                <template 
                    slot="workgroup" 
                    slot-scope="text">

                    <a-popover
                        v-if="text"
                        overlayClassName="profile_popover"
                        :mouseEnterDelay="1.1"
                        :mouseLeaveDelay="0.9"
                        :destroyTooltipOnHide="true">
                        <template slot="content">
                            <div class="flex items-start">
                                <div class="mr-2 mt-1">
                                    <a-avatar 
                                        v-if="text.author.avatar" 
                                        :src="text.author.avatar.path" />
                                    <a-avatar 
                                        v-else 
                                        icon="user" />
                                </div>
                                <div>
                                    <div>{{ userName(text.author) }}</div>
                                    <div 
                                        v-if="text.author.email" 
                                        class="text-gray text_mail" 
                                        style="font-size: 12px;">
                                        {{ text.author.email }}
                                    </div>
                                    <slot name="actions" />
                                    <div class="mt-2 profile_menu">
                                        <a-button
                                            size="small"
                                            block
                                            class="flex items-center btn"
                                            @click="writeMessage(text.author)">
                                            <i class="fi fi-rr-comment mr-2"></i>
                                            {{$t('profiler.write_a_message')}}
                                        </a-button>
                                    </div>
                                </div>
                            </div>
                        </template>
                        <div>
                            <div @click="$emit('click')">
                            
                                <div class="flex items-center truncate">
                                    <div>
                                        <a-avatar 
                                            :size="22" 
                                            icon="team" 
                                            :src="workgroupLogo(text)" />
                                    </div>
                                    <div class="pl-2 truncate">
                                        {{ text.name }}
                                    </div>
                                </div>
                            </div>
                        </div>
                    </a-popover>
                </template>
                <template 
                    slot="dead_line" 
                    slot-scope="text, record">
                    <DeadLine 
                        :taskStatus="record.status" 
                        :date="text" />
                </template>
                <template 
                    slot="status" 
                    slot-scope="text">
                    <TaskStatus :status="text" />
                </template>
                <template  
                    slot="actions" 
                    slot-scope="text, record">
                    <div class="flex">
                        <TaskAction :item="record" />
                    </div>
                </template>
            </a-table>
            <div class="flex justify-end items-center mt-1">
                <div 
                    v-if="currentTaskList && currentTaskList.length"
                    class="mr-2">
                    <a-modal
                        @cancel="settingsVisible = false"
                        :visible="settingsVisible">
                        <div class="columns_checkbox_group flex flex-col">
                            <div class="mb-2 font-semibold">
                                {{ $t('task.column_settings_title') }}
                            </div>
                            <a-checkbox 
                                ref="columnsCheckbox"
                                class="mb-2 pb-1 border-b border-gray-300"
                                :indeterminate="indeterminate" 
                                :checked="checkAllColumns" 
                                @change="onCheckAllChange">
                                {{ $t('task.all_columns') }}
                            </a-checkbox>
                            <a-checkbox-group 
                                v-model="columnsActive"
                                @change="onColumnCheckboxChange">
                                <a-row
                                    v-for="column in columnOptions"
                                    :key="column.value"
                                    class="flex mt-1 first:mt-0">
                                    <CheckboxColumn
                                        :setColumnName="setColumnName"
                                        :tableColumns="taskTableColumns"
                                        :column="column" />
                                </a-row>
                            </a-checkbox-group>
                        </div>
                        <template #footer>
                            <div class="flex">
                                <a-button 
                                    class="mr-2"
                                    block
                                    @click="dropColumns(); settingsVisible = false">
                                    {{ $t('task.default_columns') }}
                                </a-button>
                                <a-button 
                                    block
                                    type="primary"
                                    @click="setColumns(); settingsVisible = false">
                                    {{ $t('task.confirm_columns') }}
                                </a-button>
                            </div>
                        </template>
                    </a-modal>
                </div>
                <Pager
                    v-if="showPager && currentTaskList && currentTaskList.length && currentTaskCount > pageSize"
                    ref="Pager"
                    :hash="hash"
                    :changePage="changePage"
                    :changeSize="changeSize"
                    :page_size="taskTablePageSize || pageSize"
                    :scrollElements="[
                        '.task_table .ant-table-body-inner',
                        '.task_table .ant-table-body'
                    ]"
                    :page="page"
                    :count="currentTaskCount" />
            </div>
        </div>
    </div>
</template>

<script>
import AddButton from '../AddButton'
import taskHandler from '../mixins/taskHandler.js'

import eventBus from '@/utils/eventBus'
import config from '../mixins/config'
import TaskSocket from '../../mixins/TaskSocket'
import TaskAction from '../TaskActions/List.vue'
import TableName from './TableName'
import DeadLine from '../DeadLine'
import TaskStatus from '../TaskStatus'
import Pager from './Pager'
import Operator from '../Operator'
import Contractor from '../Contractor.vue'
import CheckboxColumn from './CheckboxColumn.vue'
import { mapActions, mapState, mapGetters } from 'vuex'
import ExcelBtn from '../Analytics/ExcelBtn.vue'
export default {
    name: 'TaskTypeTable',
    components: {
        AddButton,
        TaskAction,
        TableName,
        DeadLine,
        TaskStatus,
        Pager,
        Operator,
        Contractor,
        CheckboxColumn,
        ExcelBtn
    },
    mixins: [
        TaskSocket,
        config,
        taskHandler
    ],
    props: {
        extendDrawer: {
            type: Boolean,
            default: false
        },
        formParams: { // Заполнитель данных в форме по умолчанию
            type: Object,
            default: () => {}
        },
        model: { // Модель нужна для фильтров, если не указывать модель фильтры так же не будут показаны
            type: String,
            default: ''
        },
        name: { //Уникальный ИД для этого компонента, нужен для фильтрации, пагинации
            type: String,
            required: true
        },
        hash: { // Использовать хэш страницы, когда вставляем эту таблицу внутри какого нибудь другого компонента лучше использовать false
            type: Boolean,
            default: true
        },
        showPager: { // Показать пагинацию
            type: Boolean,
            default: true
        },
        showFilter: { // Показать фильтр
            type: Boolean,
            default: true
        },
        showAddButton: { // Можно скрыть кнопку добавления задач
            type: Boolean,
            default: true
        },
        showActionButton: { // Показать кнопки управления в таблице
            type: Boolean,
            default: true
        },
        /* Сюда можем вставить параметры для запроса, например выбрать
        все задачи для указаного проекта, команды, пользоваетеля и тд, все параметры фильтрации есть в диске битрикса */
        queryParams: {
            type: Object,
            default: () => null
        },
        pageSize: { // Можно указать количество записей на странице по умолчанию
            type: Number,
            default: 15
        },
        showChildren: { // Показывать или возможность раскрыть задачу с подзадачами
            type : Boolean,
            default: true
        },
        reloadTask: {
            type: Function,
            default: () => null
        },
        showSort: {
            type: Boolean,
            default: true
        },
        main: { // Если вставляем этот компонент куда то помимо страницы задач, тут надо ставить false
            type: Boolean,
            default: false
        },
        showFastTaskAction: {
            type: Boolean,
            default: true
        },
        actionFix: {
            type: Boolean,
            default: true
        },
        columnNameWidth: {
            type: Number,
            default: 200
        },
        // tableScroll: {
        //     type: Object,
        //     default: () => {}
        // },
        scrollWrapper: {
            type: Object,
            default: () => null
        },
        size: {
            type: String,
            default: 'default'
        },
        taskType: {
            type: String,
            default: 'task'
        },
        pageName: {
            type: String,
            default: ''
        }
    },
    computed: {
        ...mapState({
            taskList: state => state.task.taskList,
            taskNext: state => state.task.next,
            taskCount: state => state.task.taskCount,
            tableEmpty: state => state.task.tableEmpty,
            taskTable: state => state.task.taskTable,
            windowWidth: state => state.windowWidth,
            user: state => state.user.user,
            config: state => state.config.config,
            windowHeight: state => state.windowHeight
        }),

        ...mapGetters({
            getPageSize: 'task/getTablePageSize'
        }),
        tableSize() {
            return this.config?.theme?.tableSize ? this.config.theme.tableSize : 'small'
        },
        tableScroll() {
            if(this.windowWidth > 1750)
                return false
            else
                return this.main ? 1300 : false
        },
        scroll() {
            if(this.scrollWrapper) {
                return this.scrollWrapper
            } else {
                if(this.tableScrollOpt)
                    return this.tableScrollOpt
                else
                    return {
                        x: this.tableScroll,
                        y: 'calc(100vh - 308px)'
                    }
            }
        },
        taskTableColumns() {
            if(this.taskTable?.[this.taskType]?.columns?.length)
                return this.taskTable[this.taskType].columns
            else
                return []
        },
        // currentNext() {
        //     return this.taskNext[this.name]
        // },
        currentTaskCount() {
            return this.taskCount[this.name]
        },
        currentTaskList() {
            return this.taskList[this.name]
        },
        currentTableEmpty() {
            return this.tableEmpty[this.name]
        },
        showTableEmpty() {
            if(this.main)
                return true
            else {
                if(this.currentTableEmpty)
                    return false
                else
                    return true
            }
        },
        columnsFilter() {
            const query = Object.assign({}, this.$route.query)
            let columnList = this.taskTableColumns
                .map(item => {
                    let colum = item

                    colum.sorter = item.sortable

                    let defaultSort = ''
                    if(query.ordering) {
                        let key
                        let order
                        if(query.ordering.substr(0, 1) === '-') {
                            key = query.ordering.substr(1)
                            order = 'descend'
                        } else {
                            order = 'ascend'
                            key = query.ordering
                        }

                        if(item.key === key) {
                            defaultSort = order
                        }
                    }
                    //if(defaultSort)
                    //colum.defaultSortOrder = defaultSort
                    
                    if(!item?.slots?.title)
                        colum.title = item.headerName

                    colum.dataIndex = item.field
                    colum.key = item.field
                    colum.scopedSlots = { customRender: item.field }

                    if(colum.sortOrder)
                        delete colum.sortOrder

                    return colum
                })

            if(this.showActionButton)
                return columnList
            else
                return columnList
                    .filter(item => item.key !== 'actions')
        },
        columnsVisible() {
            return this.columnsFilter.filter(column => column.visible)
        },
        columnOptions() {
            const availableOptions = []
            this.columnsFilter.forEach(column => {
                if(column.hidable)
                    availableOptions.push({
                        label: column.title,
                        value: column.dataIndex
                    })
            })
            return availableOptions
        },
        taskTablePageSize() {
            if(this.taskTable?.[this.taskType]?.pageSize)
                return this.taskTable[this.taskType].pageSize
            else
                return null
        },
        toExcel() {
            const page_name_list = ['task-list-page-task', 'interest-interest']
            return page_name_list.includes(this.name)
        }
    },
    data() {
        return {
            listLoading: false,
            filters: null,
            sort: '',
            page_size: this.pageSize,
            page: 1,
            // routeQuery: this.$route.query,

            loading: false,
            expandedRowKeys: [],
            // sortKeys: {},
            // wrapperHeight: 0,
            localPageSize: 0,

            columnsActive: [],
            indeterminate: false,
            checkAllColumns: false,
            settingsVisible: false,
            requestData: {
                name: this.$t('task.tasks_report_name')
            },
            orderQuery: null,
        }
    },
    async created() {
        const localPageSize = this.getPageSize(this.name)
        if(localPageSize)
            this.page_size = localPageSize 



        if(this.main)
            this.$store.commit('task/SET_MAIN_KEY', this.name)

        await this.getTaskList()
        this.columnsActiveInit()

    },
    methods: {
        ...mapActions({
            getTas: 'task/getTas',
            getTaskTable: 'task/getTaskTable',
            takeAuctionTask: 'task/takeAuctionTask',
            setTableInfo: 'task/setTableInfo'
        }),
        scrollTop() {
            document.body.scrollIntoView({ behavior: 'smooth', block: 'start' })
        },
        reload() {
            if(this.page !== 1) {
                this.$refs['TaskTable'].$refs['Pager'].page = 1
                this.page = 1
            }
            this.getTaskList()
        },
        changeSort(params) {
            this.sort = params
            this.getTaskList()
        },
        // filterUpdate(filters) {
        //     this.filters = filters
        //     this.page = 1
        //     this.getTaskList()
        // },
        updateList() {
            if(this.hash) {
                if(this.$route.query.page && Number(this.$route.query.page) !== 1) {
                    let query = Object.assign({}, this.$route.query)
                    for(let key in query) {
                        if(key !== 'page_size')
                            delete query[key]
                    }
                    this.$router.push({query})
                }
            } else {
                this.page = 1
            }
        },
        changePage(page) {
            this.page = page
            this.getTaskList()
        },
        async changeSize(size) {
            this.page = 1
            this.page_size = size
            await this.setPageSize()
            this.getTaskList()
        },
        async getTaskList(infinite) {
            try {
                this.listLoading = true
                let params = {}
                if(this.hash) {
                    params = this.$route.query
                    if(!params.page_size)
                        params.page_size = 15
                } else {
                    params.page = this.page
                    params.page_size = this.page_size
                }
                if(infinite) {
                    this.page = this.page+1
                    params.page = this.page
                }
                if(this.sort) {
                    params.ordering = this.sort
                }
                if(this.queryParams) {
                    params = Object.assign(params, this.queryParams)
                }
                if(this.filters) {
                    params = Object.assign(params, this.filters)
                }
                if(this.pageName?.length) {
                    params.page_name = this.pageName
                }
                await this.getTaskTable({ task_type: this.taskType })
                await this.getTas({
                    params, 
                    infinite, 
                    key: this.name,
                    task_type: this.taskType
                })
            } catch(e) {
                console.log(e, 'getTaskList')
            } finally {
                this.listLoading = false
            }
        },
        handleTableChange(pagination, filters, sorter) {
            let params = null

            /*
            const column = this.taskTable[this.taskType].columns.find(column => 
                column.dataIndex === sorter?.column?.dataIndex)
            if(column)
                column.sortOrder = sorter.order
                */
            
            if(sorter.order) {
                params = `${sorter.order === "ascend" ? '' : '-'}${sorter.field}`
            } else {
                params = null
            }
            this.orderQuery = params

            if(this.hash) {
                let query = Object.assign({}, this.$route.query)
                if(params) {
                    query.ordering = params
                } else {
                    if(query.ordering)
                        delete query.ordering
                }
                this.$router.push({query})
            } else {
                this.changeSort(params)
            }

            this.scrollTop()
        },
        async openTask(item) {
            if(this.main) {
                let query = Object.assign({}, this.$route.query)
                if(query.task && Number(query.task) !== item.id || !query.task) {
                    query.task = item.id
                    this.$router.push({query})
                }
            } else {
                let query = Object.assign({}, this.$route.query)
                delete query.task
                await this.$router.push({query})

                this.reloadTask(item)
            }
        },
        async takeTask(task) {
            try {
                await this.takeAuctionTask({ task: task, user: this.user })
                this.$message.success(this.$t('task.task_taken_success'))
            } catch(error) {
                this.$message.error(this.$t('task.error') + ": " + this.$t('task.task_already_taken'))
                console.error(error)
            } finally {

            }
        },
        workgroupLogo(workgroup) {
            return workgroup.workgroup_logo?.path || workgroup.workgroup_logo
        },
        writeMessage(user) {
            if(this.isMobile)
                this.$router.push({name: 'chat-body', params: { id: user.id }})
            else
                this.$router.push({name: 'chat', query: {user: user.id}})
        },
        userName(user) {
            if(user)
                if(user.full_name) {
                    return user.full_name
                } else
                    return `${user.last_name} ${user.first_name} ${user.middle_name}`
            else
                return ''
        },
        async setColumns() {
            this.taskTableColumns.forEach((column, index) => {
                const isActive = this.columnsActive.includes(column.dataIndex)
                const isCustomizable = !!column.hidable
                if(isCustomizable)
                    if(isActive) 
                        this.taskTableColumns[index].visible = true
                    else 
                        this.taskTableColumns[index].visible = false
            })

            await this.sendTableInfo()
        },
        async setPageSize() {
            this.taskTable[this.taskType].pageSize = this.page_size
            await this.sendTableInfo()
        },
        async sendTableInfo() {
            await this.setTableInfo({
                task_type: this.taskType, 
                value: {
                    columns: this.taskTable[this.taskType].columns,
                    pageSize: this.taskTable[this.taskType].pageSize,
                }
            })
            await this.$http.post(`tasks/table_info/?task_type=${this.taskType}`, {
                columns: this.taskTableColumns,
                pageSize: this.taskTablePageSize
            })
        },
        onColumnCheckboxChange(checkedList) {
            this.indeterminate = !!checkedList.length && checkedList.length < this.columnOptions.length;
            this.checkAllColumns = checkedList.length === this.columnOptions.length;
        },
        onCheckAllChange({target}) {
            if(target.checked)
                this.taskTableColumns.forEach(column => 
                    column.hidable && this.columnsActive.push(column.dataIndex)
                )
            else
                this.columnsActive = []

            this.indeterminate = false
            this.checkAllColumns = target.checked
        },
        columnsActiveInit() {
            this.columnsActive = []
            this.taskTableColumns.forEach(column => 
                (column.visible && column.hidable) && this.columnsActive.push(column.dataIndex)
            )

            this.indeterminate = !!this.columnsActive.length && this.columnsActive.length < this.columnOptions.length;
            this.checkAllColumns = this.columnsActive.length === this.columnOptions.length
        },
        async dropColumns() {
            await this.$http.post(`tasks/table_info/?task_type=${this.taskType}&drop=true`)
            await this.getTaskTable({ 
                task_type: this.taskType,
                isDrop: true 
            })
        },
        setColumnName(columnValue, newName) {
            const column = this.taskTableColumns.find(column => column.dataIndex === columnValue)
            column.headerName = newName
        }


    },
    mounted () {
        if(this.main) {
            eventBus.$on('UPDATE_LIST', () => {
                this.updateList()
            })
            if(this.showFilter) {
                eventBus.$on(`update_filter_tasks.TaskModel`, () => {
                    this.reload()
                })
            }
        }
    },
    beforeDestroy() {
        if(this.main) {
            this.$store.commit('task/SET_MAIN_KEY', null)
            this.$nextTick(() => {
                const bodyTable = document.querySelector('.table_container .ant-table-body'),
                    right = document.querySelectorAll('.table_container .ant-table-fixed-right'),
                    left = document.querySelectorAll('.table_container .ant-table-fixed-left')

                if(right.length) {
                    let arrRight = document.createElement("div")
                    arrRight.classList.add('table_arrow', 'arrow_right')
                    right.forEach(item => {
                        item.appendChild(arrRight)
                    })

                    let timer;

                    arrRight.addEventListener('mouseenter', () => {
                        timer = setInterval(() => {
                            bodyTable.scrollLeft += 5
                        }, 10);
                    })
                    arrRight.addEventListener('mouseleave', () => {
                        clearInterval(timer)
                    })
                }
                if(left.length) {
                    let arrLeft = document.createElement("div")
                    arrLeft.classList.add('table_arrow', 'arrow_left')
                    left.forEach(item => {
                        item.appendChild(arrLeft)
                    })

                    let timer;

                    arrLeft.addEventListener('mouseenter', () => {
                        timer = setInterval(() => {
                            bodyTable.scrollLeft -= 5
                        }, 10);
                    })
                    arrLeft.addEventListener('mouseleave', () => {
                        clearInterval(timer)
                    })
                }
                if(!right.length && left.length) {
                    const bodyMainScroll = document.querySelectorAll('.table_container .ant-table-scroll')
                    const arrRight = document.createElement("div")
                    arrRight.classList.add('table_arrow', 'arrow_right_main')
                    bodyMainScroll.forEach(item => {
                        item.appendChild(arrRight)
                    })

                    let timer;

                    arrRight.addEventListener('mouseenter', () => {
                        timer = setInterval(() => {
                            bodyTable.scrollLeft += 5
                        }, 10);
                    })
                    arrRight.addEventListener('mouseleave', () => {
                        clearInterval(timer)
                    })
                }
            })
        }

        eventBus.$off('UPDATE_LIST')
        if(this.showFilter) {
            eventBus.$off('update_filter_tasks.TaskModel')
        }
    }
}
</script>

<style lang="scss">
.table_card{
    .ant-card-body{
        padding: 0px;
    }
}

.columns_checkbox_group {
    .ant-checkbox-group {
        label {
            display: block;
        }
    }
}

.counter_rejected{
background: rgb(238, 42, 42);
color: white;
padding: 2px 4px;
border-radius: 4px;
}
.expand_title{
    text-align: center;
    font-weight: 600;
    font-size: 12px;
}
.table_container{
    .ant-table-row-indent{
        float: left;
        min-height: 1px;
    }
    .ant-table-row-expand-icon{
        display: none;
    }
    .ant-table{
        .ant-table-header{
            background-color: #f5f7f7;
        }
    }
    .ant-table-scroll-position-left{
        &.ant-table-scroll-position-right{
            .ant-table-fixed-right,
            .ant-table-fixed-left{
                display: none;
            }
            .ant-table-scroll table .ant-table-fixed-columns-in-body:not([colspan]){
                color: var(--textColor3);
            }
            .ant-table-scroll table .ant-table-fixed-columns-in-body:not([colspan]) > *{
                visibility: initial;
            }
        }
    }
    .ant-table-scroll-position-right{
        .arrow_right_main,
        .arrow_right{
            display: none;
        }
    }
    .ant-table-scroll-position-left{
        .arrow_left{
            display: none;
        }
    }
    .table_arrow{
        width: 20px;
        height: 30px;
        position: absolute;
        top: 50%;
        margin-top: -15px;
        z-index: 5;
        opacity: 0.3;
        &:hover{
            opacity: 0.4;
        }
        &.arrow_left{
            right: 0;
            margin-right: -20px;
            border-radius: 0px 30px 30px 0px;
            background: black url('../../assets/images/left-arrow.svg') no-repeat;
            background-size: 14px;
            background-position: 0px center;
        }
        &.arrow_right_main,
        &.arrow_right{
            &:not(.arrow_right_main) {
                left: 0;
                margin-left: -20px;
            }
            border-radius: 30px 0px 0px 30px;
            background: black url('../../assets/images/right-arrow.svg') no-repeat;
            background-size: 14px;
            background-position: 5px;
        }
        &.arrow_right_main{
            right: 15px;
            margin-top: -22px;
        }
    }
    .ant-table-fixed-right,
    .ant-table-fixed-left{
        overflow: initial;
    }
    .ant-table-fixed-right{
        .ant-table-body-inner{
            &::-webkit-scrollbar{
                background: transparent;
            }
        }
    }
    .ant-table-fixed-left{
        .ant-table-body-inner{
            -ms-overflow-style: none;
            scrollbar-width: none;
            &::-webkit-scrollbar{
                width: 0;
                background: transparent;
            }
            &::-webkit-scrollbar-thumb {
                background: transparent;
            }
        }
    }
}
</style>
