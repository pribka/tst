<template>
    <ModuleWrapper 
        :pageTitle="pageTitle"
        :bodyPadding="viewType === 'table' ? true :false"
        :bodyOHidden="viewType === 'table' ? false :true">
        <template v-slot:h_left>
            <slot />
        </template>
        <template v-slot:h_right>
            <AddButton
                v-if="addButton || showAddButton"
                class="mr-2"
                :formParams="formParams"
                :addButton="addButton"
                :extendDrawer="extendDrawer"
                :windowWidth="windowWidth"
                :toExcel="toExcel"
                :page_name="pageName"
                :queryParams="queryParams"
                :requestData="requestData"
                :orderQuery="orderQuery" />
            <OpenReportModalButton
                class="ml-1"
                sectionCode="tasks" />
            <HelpButton partCode="tasks" type="button" class="ml-2" />
            <SettingsButton
                v-if="viewType === 'table'"
                :pageName="pageName"
                size="default"
                class="ml-2" />
        </template>
        <div class="flex items-center gap-5 mb-3" :class="viewType !== 'table' && 'header_pd'">
            <Segmented 
                v-model="viewType" 
                :options="listType"
                localStorageKey="task_list_type"
                useLocalStorageSave />
            <StatusFilters 
                :page_name="pageName" 
                :model="model" />
        </div>
        <div class="flex flex-col flex-grow min-h-0">
            <component 
                v-if="viewType === 'table'"
                :is="pageWidget" 
                ref="tableWidget"
                :model="model"
                :pageName="pageName"
                :tableType="tableType"
                :autoHeight="!main"
                :endpoint="getDataEndpoint"
                :params="queryParams"
                :openHandler="openTask"
                :main="main"
                :childParams="{
                    task_type: 'task'
                }"
                :taskType="taskType"
                :takeTask="takeTask"
                :showChildren="showChildren"
                :reloadTask="reloadTask"
                :extendDrawer="extendDrawer"
                :hideActionColumn="hideActionColumn"
                :hash="hash" />
            <component 
                v-else
                :is="pageWidget" 
                main
                class="kanban_main_view"
                :taskType="taskType"        
                :queryParams="{
                    page_name: pageName
                }"
                showPageTitle>
                <slot />
            </component>
        </div>
    </ModuleWrapper>
</template>

<script>
import taskHandler from '../mixins/taskHandler.js'
import config from '../mixins/config'
import TaskSocket from '../../mixins/TaskSocket'
import { mapActions, mapState } from 'vuex'
export default {
    name: 'TaskTablePage',
    sockets: {
        task_update({ data }) {
            if (data) {
                this.updateTaskRow(data)
            }
        }
    },
    components: {
        AddButton: () => import('../AddButton'),
        UniversalTable: () => import('@/components/TableWidgets/UniversalTable'),
        SettingsButton: () => import('@/components/TableWidgets/SettingsButton'),
        ModuleWrapper: () => import('@/components/ModuleWrapper/index.vue'),
        StatusFilters: () => import('./StatusFilters.vue'),
        OpenReportModalButton: () => import('@apps/Reports/components/OpenReportModalButton.vue'),
        Segmented: () => import('@apps/UIModules/Segmented'),
        HelpButton: () => import('@apps/Support/components/HelpButton.vue')
    },
    mixins: [
        TaskSocket,
        config,
        taskHandler
    ],
    props: {
        autoHeight: {
            type: Boolean,
            default: false
        },
        tableType: {
            type: String,
            default: 'tasks'
        },
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
        },
        showHeader: {
            type: Boolean,
            default: true
        },
        endpoint: {
            type: String,
            default: ''
        },
        hideActionColumn: {
            type: Boolean,
            default: false
        }
    },
    computed: {
        ...mapState({
            windowWidth: state => state.windowWidth,
            user: state => state.user.user,
            config: state => state.config.config,
            windowHeight: state => state.windowHeight,
        }),
        pageWidget() {
            if(this.viewType === 'table')
                return () => import('@/components/TableWidgets/UniversalTable')
            return () => import('../Kanban/KanbanTaskInject.vue')
        },
        getDataEndpoint() {
            if (this.taskType === 'task') {
                return `/tasks/task/list/?task_type=task`
            }
            return `/tasks/task/list/?task_type=${this.taskType}`
        },
        pageTitle() {
            return this.$route?.meta?.title || ''
        },
        toExcel() {
            const page_name_list = ['task-list-page-task', 'interest-interest', 'tasks-task']
            if(this.viewType !== 'table')
                return false
            return page_name_list.includes(this.name)
        }
    },
    data() {
        return {
            viewType: 'table',
            listType: [
                {
                    key: 'table',
                    title: this.$t('task.list')
                },
                {
                    key: 'kanban',
                    title: this.$t('task.kanban')
                }
            ],
            page_size: this.pageSize,
            page: 1,
            requestData: {
                name: this.$t('task.task-list-page')
            },
            orderQuery: null,
        }
    },
    created() {
        this.getStatusList({ task_type: this.taskType })
        if(this.main)
            this.$store.commit('task/SET_MAIN_KEY', this.name)
    },
    methods: {
        ...mapActions({
            getTas: 'task/getTas',
            takeAuctionTask: 'task/takeAuctionTask',
            getStatusList: 'task/getStatusList'

        }),
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
                this.$message.success(this.$t('task.handler.success'))
            } catch(error) {
                this.$message.error(this.$t('task.error') + `: ${this.$t('task.took_on_task')}`)
                console.error(error)
            }
        },
        updateTaskRow(task) {
            const table = this.$refs.tableWidget
            if (table && typeof table.replaceRow === 'function') {
                table.replaceRow(task)
            }
        }
    },
    beforeDestroy() {
        if(this.main) {
            this.$store.commit('task/SET_MAIN_KEY', null)
        }
    }
}
</script>

<style lang="scss" scoped>
.kanban_main_view{
    &::v-deep{
        .kanban-main{
            padding: 0px;
        }
    }
}
.header_pd{
    padding: 15px 15px 0 15px;
}
</style>
