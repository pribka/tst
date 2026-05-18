<template>
    <component 
        :is="resolvedWidget"
        :tableType="tableType"
        :extendDrawer="extendDrawer"
        :formParams="formParams"
        :model="model"
        :name="`${name}-${taskType}`"
        :hash="hash"
        :showHeader="showHeader"
        :showPager="showPager"
        :showFilter="showFilter"
        :showAddButton="showAddButton"
        :showActionButton="showActionButton"
        :queryParams="queryParams"
        :pageSize="pageSize"
        :showChildren="showChildren"
        :reloadTask="reloadTask"
        :showPageTitle="showPageTitle"
        :taskType="taskType"
        :showSort="showSort"
        :pageName="pageName"
        :main="main"
        :showFastTaskAction="showFastTaskAction"
        :actionFix="actionFix"
        :columnNameWidth="columnNameWidth"
        :tableScroll="tableScroll"
        :scrollWrapper="scrollWrapper"
        :size="size"
        :pageConfig="pageConfig">
        <slot />
    </component>
</template>

<script>
import { mapState } from 'vuex'
export default {
    name: 'TaskPageSwitch',
    props: {
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
        pageConfig: {
            type: Object,
            default: () => null
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
            viewType: state => state.task.mobileViewType
        }),
        isMobile() {
            return this.$store.state.isMobile
        }
    },
    data() {
        return {
            resolvedWidget: null
        }
    },
    sockets: {
        task_update({data}) {
            if(data)
                this.$store.commit('task/UPDATE_TASK_SOCKET', data)
        }
    },
    created() {
        this.resolvedWidget = this.isMobile
            ? () => import('./TaskListMobile.vue')
            : () => import('./TaskTablePage.vue')
        this.$store.commit('task/SET_TASK_TYPE', this.taskType)
    }
} 
</script>