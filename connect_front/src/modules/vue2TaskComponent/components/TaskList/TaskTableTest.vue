<template>
    <div class="list_table flex-grow flex flex-col">
        <div v-if="showHeader" class="flex items-center pb-4">
            <AddButton
                v-if="addButton && showAddButton"
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
            <SettingsButton
                :pageName="pageName"
                class="ml-2" />
        </div>
        <div class="table_container flex flex-grow task_table min-h-0">
            <UniversalTable 
                :model="model"
                :pageName="pageName"
                :tableType="tableType"
                :autoHeight="autoHeight"
                :endpoint="getDataEndpoint"
                :params="queryParams"
                :openHandler="openTask"
                :childParams="{
                    task_type: 'task'
                }"
                :main="main"
                :taskType="taskType"
                :takeTask="takeTask"
                :showChildren="showChildren"
                :reloadTask="reloadTask"
                :extendDrawer="extendDrawer"
                :hideActionColumn="hideActionColumn"
                :hash="hash" />
        </div>
    </div>
</template>

<script>
import taskHandler from '../mixins/taskHandler.js'

import eventBus from '@/utils/eventBus'
import config from '../mixins/config'
import TaskSocket from '../../mixins/TaskSocket'
import { mapActions, mapState } from 'vuex'
export default {
    name: 'TaskTypeTable',
    components: {
        AddButton: () => import('../AddButton'),
        UniversalTable: () => import('@/components/TableWidgets/UniversalTable'),
        SettingsButton: () => import('@/components/TableWidgets/SettingsButton'),
        ExcelBtn: () => import('../Analytics/ExcelBtn.vue')
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
        }),
        getDataEndpoint() {
            return `/tasks/task/list/?task_type=${this.taskType}`
        },
        toExcel() {
            const page_name_list = ['task-list-page-task', 'interest-interest', 'tasks-task']
            return page_name_list.includes(this.name)
        }
    },
    data() {
        return {
            page_size: this.pageSize,
            page: 1,
            requestData: {
                name: this.$t('task.task-list-page')
            },
            orderQuery: null,
        }
    },
    created() {
        if(this.main)
            this.$store.commit('task/SET_MAIN_KEY', this.name)
    },
    methods: {
        ...mapActions({
            getTas: 'task/getTas',
            takeAuctionTask: 'task/takeAuctionTask',
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
                this.$message.success(this.$t('task.task_taken_success'))
            } catch(error) {
                this.$message.error(this.$t('task.error') + ": " + this.$t('task.task_already_taken'))
                console.error(error)
            }
        },
    },
    beforeDestroy() {
        if(this.main) {
            this.$store.commit('task/SET_MAIN_KEY', null)
        }
    }
}
</script>
