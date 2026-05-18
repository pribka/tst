<template>
    <div :class="main && !extendDrawer && 'page_padding'">
        <div v-if="showPageTitle && pageH1Title" class="flex items-center justify-between gap-2 m_page_head">
            <h1 class="m_page_title">
                {{ pageH1Title }}
            </h1>
            <HelpButton partCode="tasks" type="button" />
        </div>
        <div v-if="forceMobile" class="filter_slot mb-4">
            <slot name="default" />
        </div>
        <div :style="minVh && 'min-height: 90vh;'">
            <div 
                v-if="showEmpty && !currentLoading" 
                class="pt-8">
                <a-empty>
                    <template #description>
                        {{ $t('task.task_empty') }}
                    </template>
                </a-empty>
            </div>
            <component 
                :is="cardWidget"
                v-for="item in currentTaskList" 
                :item="item" 
                :bgWhite="isMobile"
                :key="item.id"
                :isScrolling="isScrolling"
                activeMobile
                :bgInvert="bgInvert"
                :reloadTask="reloadTask"
                :myTaskEnabled="false"
                :showStatus="true"/>
            <infinite-loading 
                ref="infiniteLoading"
                @infinite="getTaskList"
                :identifier="infiniteId"
                v-bind:distance="10">
                <div 
                    slot="spinner"
                    class="flex items-center justify-center inf_spinner">
                    <a-spin />
                </div>
                <div slot="no-more"></div>
                <div slot="no-results"></div>
            </infinite-loading>
        </div>
        <div v-if="showHeader && !forceMobile" class="float_add">
            <div class="mb-2">
                <SortMobile 
                    :model="model"
                    :page_name="pageName"/>
            </div>
            <div class="filter_slot">
                <slot name="default" />
            </div>
            <a-button 
                v-if="addButton"
                flaticon
                shape="circle"
                size="large"
                type="primary"
                icon="fi-rr-plus"
                @click="addTaskDrawer()" />
        </div>
    </div>
</template>

<script>
import config from '../mixins/config'
import TaskSocket from '../../mixins/TaskSocket'
import eventBus from '@/utils/eventBus'
import { useScroll } from '@vueuse/core'
import { mapState, mapActions } from 'vuex'
import { errorHandler } from '@/utils/index.js'
export default {
    name: 'TaskListTypeMobile',
    sockets: {
        task_update({ data }) {
            if (data) {
                this.$store.commit('task/UPDATE_TASK_SOCKET', data)
            }
        }
    },
    components: {
        KanbanItem: () => import('../Kanban/Item.vue'),
        InfiniteLoading: () => import('vue-infinite-loading'),
        SortMobile: () => import('./SortMobile.vue'),
        HelpButton: () => import('@apps/Support/components/HelpButton.vue')
    },
    mixins: [
        TaskSocket,
        config
    ],
    props: {
        forceMobile: {
            type: Boolean,
            default: false
        },
        bgInvert: {
            type: Boolean,
            default: false
        },
        minVh: {
            type: Boolean,
            default: false
        },
        extendDrawer: {
            type: Boolean,
            default: false
        },
        formParams: { // Заполнитель данных в форме по умолчанию
            type: Object,
            default: () => {}
        },
        model: { // Модель нужна для фильтров, если не указывать модель фильтры так же не буду показаны
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
        tableScroll: {
            type: Object,
            default: () => {}
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
        showPageTitle: {
            type: Boolean,
            default: false
        },
        showHeader: {
            type: Boolean,
            default: true
        }
    },
    computed: {
        ...mapState({
            isMobile: state => state.isMobile,
            taskList: state => state.task.taskList,
            taskNext: state => state.task.next,
            taskCount: state => state.task.taskCount,
            taskPages: state => state.task.taskPages,
            taskListLoading: state => state.task.taskListLoading,
            windowWidth: state => state.windowWidth
        }),
        cardWidget() {
            if(this.taskType === 'interest') 
                return () => import('../Kanban/CardTypes/CardInterest')
            return () => import('../Kanban/Item.vue')
        },
        currentNext() {
            if(this.taskNext[this.name] === null)
                return false
            return true
        },
        currentTaskCount() {
            return this.taskCount[this.name]
        },
        currentTaskList() {
            return this.taskList[this.name]
        },
        nextPage() {
            return this.taskPages[this.name]
        },
        currentLoading() {
            return this.taskListLoading[this.name]
        },
        pageH1Title() {
            return this.$route?.meta?.title ? this.$route.meta.title : null
        }
    },
    data() {
        return {
            listLoading: false,
            filters: null,
            sort: '',
            page_size: this.pageSize,
            page: 0,
            routeQuery: this.$route.query,
            infiniteId: this.pageName,
            showEmpty: false,
            isScrolling: false
        }
    },
    created() {
        if(this.main)
            this.$store.commit('task/SET_MAIN_KEY', this.name)
    },
    methods: {
        ...mapActions({
            getTas: 'task/getTas',
            getTaskTable: 'task/getTaskTable',
        }),
        toKanbanView() {
            if(this.taskType === 'interest') {
                return this.$router.push('interest-kanban')
            }
            return this.$router.push('tasks-kanban')
        },
        addTaskDrawer() {
            if(this.extendDrawer)
                this.$store.commit('task/SET_TASK_DRAWER_ZINDEX', 1010)

            this.$store.dispatch('task/sidebarOpen', {
                ...this.formParams,
                task_type: this.taskType
            })
        },
        reload() {
            this.page = 0
            this.$store.commit('task/CLEAR_TASK_LIST', { key: this.name })
            /*this.$store.state.task.taskList = {}
            this.$store.state.task.next = {}
            this.$store.state.task.taskPages[this.name] = 0*/
            
            this.$nextTick(()=> {
                if(this.$refs.infiniteLoading)
                    this.$refs.infiniteLoading.stateChanger.reset()
            })
        },
        async getTaskList($state) {
            if (!this.currentNext) {
                $state.complete()
                return
            }
            try {
                this.setLoadingState(true)
                this.showEmpty = false
                this.$store.commit('task/UPDATE_TASK_PAGE', { key: this.name })
                this.page = this.page+1
                let params = {
                    page: this.nextPage,
                }
                if(this.hash) {
                    params = this.$route.query
                    if(!params.page_size)
                        params.page_size = 15
                } else {
                    params.page = this.nextPage
                    params.page_size = this.page_size
                }
                if(this.sort)
                    params.ordering = this.sort
                if(this.queryParams)
                    params = {...params, ...this.queryParams}
                if(this.filters)
                    params = {...params, ...this.filters}
                if(this.pageName?.length)
                    params.page_name = this.pageName
                await this.getTas({
                    params, 
                    infinite: true, 
                    key: this.name,
                    task_type: params.task_type || this.taskType
                })

                if(this.nextPage === 1 && !this.currentTaskList?.length)
                    this.showEmpty = true 

                if(this.currentNext)
                    $state.loaded()
                else
                    $state.complete()
            } catch(error) {
                errorHandler({error, show: false})
            } finally {
                this.setLoadingState(false)
            }
        },
        setLoadingState(value) {
            this.$store.commit('task/SET_LOADING', {
                key: this.name,
                value
            })
        }
    },
    mounted () {
        this.$nextTick(() => {
            const { isScrolling } = useScroll(document)
            this.isScrolling = isScrolling
        })

        if(this.main) {
            eventBus.$on('UPDATE_LIST', () => {
                this.reload()
            })
            eventBus.$on(`update_filter_tasks.TaskModel`, () => {
                this.reload()
            })
        }
    },
    beforeDestroy() {
        if(this.main)
            this.$store.commit('task/SET_MAIN_KEY', null)

        eventBus.$off('UPDATE_LIST')
        eventBus.$off('update_filter_tasks.TaskModel')
    }
}
</script>

<style lang="scss" scoped>
.page_padding{
    padding: 15px;
}
</style>

<style>
.task_list_header {
    top: var(--headerHeight);
    background-color: var(--eBg);    
}
</style>
