<template>
    <DrawerTemplate 
        :width="drawerWidth"
        class="sprint_show_drawer"
        v-model="visible"
        :closable="false"
        useCopyLink
        useOpenLink
        useShare
        :shareObject="
            sprint ? {
                model: 'tasks.TaskSprintModel',
                shareId: sprint.id,
                object: sprint,
                shareTitle: `${$t('task.sprint_menu')} - ${sprint.name}`,
            } : null
        "
        :link="{
            sprint: sprint ? sprint.id : null,
            sptab: tab
        }"
        @afterVisibleChange="afterVisibleChange"
        @close="visible = false">
        <template #title>
            <template v-if="sprint">
                <div class="w-full flex items-center justify-between">
                    <div class="drawer_title">{{ sprint.name }}</div>
                    <div class="flex items-center pl-3">
                        <a-button 
                            v-if="actions && actions.delete && actions.delete.availability"
                            type="ui" 
                            ghost
                            v-tippy
                            :content="$t('task.remove')"
                            class="mr-2"
                            flaticon
                            shape="circle"
                            icon="fi-rr-trash"
                            @click="deleteSprint()" />
                        <a-button 
                            v-if="isMobile && actions.edit"
                            type="ui" 
                            ghost
                            v-tippy
                            :content="$t('task.edit')"
                            class="mr-2"
                            flaticon
                            shape="circle"
                            icon="fi-rr-edit"
                            @click="editSprint()" />
                    </div>
                </div>
            </template>
        </template>
        <template #tabs>
            <div class="drawer_tabs">
                <a-tabs 
                    v-if="sprint" 
                    class="h-full"
                    v-model="tab"
                    @change="changeTab">
                    <a-tab-pane 
                        v-for="item in tabs"
                        :key="item.key">
                        <template #tab>
                            {{ item.title }}
                        </template>
                    </a-tab-pane>
                </a-tabs>
            </div>
        </template>
        <template 
            v-if="showAside"
            #aside>
            <div class="aside">
                <div class="aside_block">
                    <div class="flex items-center justify-between mb-2">
                        <a-tag :color="statusColor">
                            {{ $t(`sprint.${sprint.status}`) }}
                        </a-tag>
                        <a-button 
                            v-if="!isMobile && actions.edit"
                            type="link" 
                            flaticon
                            v-tippy="{ inertia : true, duration : '[600,300]'}"
                            :content="$t('task.edit')"
                            icon="fi-rr-edit"
                            @click="editSprint()" />
                    </div>
                    <div v-if="sprint.begin_date && sprint.dead_line" class="aside_row">
                        <div class="aside_row__title">
                            {{ $t('task.deadlines') }}
                        </div>
                        <div class="aside_row__value">
                            {{ $moment(sprint.begin_date).format('DD.MM.YY') }} - {{ $moment(sprint.dead_line).format('DD.MM.YY') }}
                        </div>
                    </div>
                    <div class="aside_row">
                        <div class="aside_row__title">
                            {{ $t('task.tasks') }}
                        </div>
                        <div class="aside_row__value">
                            {{ taskCount }}
                        </div>
                    </div>
                    <div v-if="sprint.target" class="aside_row">
                        <div class="aside_row__title">
                            {{ $t('task.goal') }}
                        </div>
                        <div class="aside_row__value">
                            {{ sprint.target }}
                        </div>
                    </div>
                    <div v-if="sprint.expected_result && sprint.expected_result.length" class="aside_row">
                        <div class="aside_row__title">
                            {{ $t('task.expected_result') }}
                        </div>
                        <div class="aside_row__value">
                            {{ sprint.expected_result.join(', ') }}
                        </div>
                    </div>
                    <div v-if="sprintProjects" class="aside_row">
                        <div class="aside_row__title">
                            {{ $t('Projects') }}
                        </div>
                        <div class="aside_row__value">
                            {{ sprintProjects }}
                        </div>
                    </div>
                    <div v-if="sprint.author" class="aside_row">
                        <div class="aside_row__title">
                            {{ $t('task.author') }}
                        </div>
                        <div class="aside_row__value">
                            <Profiler
                                :avatarSize="22"
                                :user="sprint.author" />
                        </div>
                    </div>
                    <a-button 
                        v-if="sprint.status !== 'completed' && actions.set_status" 
                        type="primary" 
                        size="large"
                        block
                        :loading="loading"
                        @click="actionHandler()">
                        <template v-if="sprint.status === 'new'">
                            {{ $t('task.start_sprint_full') }}
                        </template>
                        <template v-if="sprint.status === 'in_process'">
                            {{ $t('task.complete_sprint') }}
                        </template>
                    </a-button>
                </div>
                <template v-if="tab === 'analytics'">
                    <a-button 
                        type="primary" 
                        ghost 
                        size="large" 
                        block 
                        :loading="reportLoading"
                        class="mt-3"
                        @click="analyticsDownload('report', 'reportLoading')">
                        {{ $t('task.download_analytics') }}
                    </a-button>
                    <a-button 
                        type="primary" 
                        ghost 
                        size="large" 
                        block 
                        :loading="actLoading"
                        class="mt-2"
                        @click="analyticsDownload('act', 'actLoading')">
                        {{ $t('task.download_work_report') }}
                    </a-button>
                </template>
                <div class="mt-2 md:mt-4">
                    <a-collapse v-if="isMobile" :bordered="false" v-model="collapseKey">
                        <a-collapse-panel key="1" :header="$t('task.comments')">
                            <vue2CommentsComponent
                                bodySelector=".sprint_drawer_body"
                                :related_object="sprint.id"
                                model="tasks" />
                        </a-collapse-panel>
                    </a-collapse>
                    <template v-else>
                        <div class="mb-1">{{ $t('task.comments') }}</div>
                        <vue2CommentsComponent
                            bodySelector=".sprint_drawer_body"
                            :related_object="sprint.id"
                            model="tasks" />
                    </template>
                </div>
            </div>
        </template>
        <template>
            <div class="sprint_drawer_body h-full" :class="isKanban && 'body_kanban'">
                <template v-if="sprint">
                    <div class="h-full">
                        <a-tabs
                            :activeKey="tab" 
                            class="body_tab h-full">
                            <a-tab-pane key="info" class="flex flex-col">
                                <template #tab>{{ $t('task.about_sprint') }}</template>
                                <TaskTab 
                                    ref="sprintTask"
                                    :sprint="sprint" 
                                    :pageName="page_name"
                                    :changeActive="changeActive"
                                    :actions="actions" />
                            </a-tab-pane>
                            <a-tab-pane key="members" class="flex flex-col">
                                <template #tab>{{ $t('task.participants') }}</template>
                                <component
                                    :is="pageWidget"
                                    ref="taskResultsTab"
                                    :sprint="sprint" 
                                    :page_name="page_name"
                                    :actions="actions" />
                            </a-tab-pane>
                            <a-tab-pane key="analytics">
                                <template #tab>{{ $t('task.analytics') }}</template>
                                <AnalyticsTab 
                                    v-if="tab === 'analytics'"
                                    ref="analyticsTab"
                                    :sprint="sprint" 
                                    :page_name="page_name"
                                    :actions="actions" />
                            </a-tab-pane>
                            <a-tab-pane key="task_results">
                                <template #tab>{{ $t('task.task_results') }}</template>
                                <component
                                    :is="pageWidget"
                                    ref="taskResultsTab"
                                    :sprint="sprint" 
                                    :page_name="page_name"
                                    :actions="actions" />
                            </a-tab-pane>
                            <a-tab-pane key="retrospective">
                                <template #tab>{{ $t('task.retrospective') }}</template>
                                <Retrospective 
                                    v-if="tab === 'retrospective'"
                                    :related_object="sprint" />
                            </a-tab-pane>
                        </a-tabs>
                    </div>
                </template>
                <a-skeleton
                    v-else
                    active
                    :paragraph="{ rows: 5 }" />
            </div>
        </template>
    </DrawerTemplate>
</template>

<script>
import { declOfNum } from '@/utils/utils.js'
import eventBus from '@/utils/eventBus'
import { errorHandler } from '@/utils/index.js'
import { clearTabQuery } from '@/utils/routerUtils.js'
export default {
    components: {
        TaskTab: () => import('./TaskTab/index.vue'),
        AnalyticsTab: () => import('./AnalyticsTab/index.vue'),
        MembersTab: () => import('./MembersTab/index.vue'),
        Retrospective: () => import('@/components/Retrospective'),
        DrawerTemplate: () => import('@/components/DrawerTemplate.vue'),
        vue2CommentsComponent: () => import('@apps/vue2CommentsComponent')
    },
    computed: {
        pageWidget() {
            if (this.tab === 'task_results') {
                return () => import('./TaskResults/index.vue')
            }
            if (this.tab === 'members') {
                return () => import('./MembersTab/index.vue')
            }
            return null
        },
        sprintProjects() {
            if (this.sprint?.projects?.length) {
                return this.sprint.projects.map(project => project.name).join(', ')
            }
            return ''
        },  
        isKanban() {
            if(this.active === 2) {
                return this.tab === 'info'
            } else {
                return false
            }
        },
        showAside() {
            if(!this.sprint || this.isKanban)
                return false
            if(this.isMobile)
                return this.tab === 'info'
            return true
        },
        xxlColWidth() {
            if(this.active === 2) {
                if(this.tab === 'info')
                    return 24
                else
                    return this.isMobile ? 24 : 18
            } else {
                return this.isMobile ? 24 : 18
            }
        },
        xlColWidth() {
            if(this.active === 2) {
                if(this.tab === 'info')
                    return 24
                else
                    return this.isMobile ? 24 : 17
            } else {
                return this.isMobile ? 24 : 17
            }
        },
        isMobile() {
            return this.$store.state.isMobile
        },
        isInject() {
            return this.inject ? `_inject` : ''
        },
        taskCount() {
            return `${this.sprint.task_count || 0} ${declOfNum(this.sprint.task_count, [this.$t('task.task_singular'), this.$t('task.task_plural_2_4'), this.$t('task.task_plural_5_plus')])}`
        },
        windowWidth() {
            return this.$store.state.windowWidth
        },
        drawerWidth() {
            if(this.windowWidth > 1575)
                return 1575
            else {
                return '100%'
            }
        },
        page_name() {
            return `tasks_sprint_${this.sprint.id}_task.TaskModel`
        },
        statusColor() {
            switch (this.sprint.status) {
            case "new":
                return "blue";
                break;
            case "in_process":
                return "purple";
                break;
            case "completed":
                return "green";
                break;
            default:
                return "blue";
            }
        }
    },
    data() {
        return {
            detailLoading: false,
            visible: false,
            infoLoading: false,
            sprint: null,
            tab: 'info',
            loading: false,
            actions: null,
            inject: false,
            actLoading: false,
            reportLoading: false,
            active: 1,
            collapseKey: [],
            tabs: [
                {
                    key: 'info',
                    title: this.$t('task.about_sprint')
                },
                {
                    key: 'members',
                    title: this.$t('task.participants')
                },
                {
                    key: 'analytics',
                    title: this.$t('task.analytics')
                },
                {
                    key: 'task_results',
                    title: this.$t('task.task_results')
                },
                {
                    key: 'retrospective',
                    title: this.$t('task.retrospective')
                }
            ]
        }
    },
    watch: {
        '$route.query'(val, oldVal) {
            if(val.sprint) {
                if(!this.visible)
                    this.visible = true
                if(val.sptab && val.sptab !== this.tab)
                    this.tab = val.sptab
            } else if(oldVal.sprint && this.visible) {
                this.visible = false
            }
        }
    },
    methods: {
        changeActive(active) {
            this.active = active
        },
        async analyticsDownload(file_code, loadingType, file_type = 'xlsx') {
            try {
                this[loadingType] = true
                const response = await this.$http.get(`/tasks/sprint/${this.sprint.id}/report/file/`, {
                    responseType: 'blob',
                    params: {
                        file_code,
                        file_type
                    }
                })
                const blob = new Blob([response.data], {
                    type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                })
                const url = window.URL.createObjectURL(blob)
                const a = document.createElement('a')
                a.href = url
                const fileName = file_code === 'report' ? this.$t('task.analytics') : this.$t('task.work_report')
                a.download = `${fileName} ${this.$t('task.by_sprint')} ${this.sprint.name} ${this.$t('task.from')} ${this.$moment().format('DD.MM.YYYY HH:mm')}.xlsx`
                document.body.appendChild(a)
                a.click()
                window.URL.revokeObjectURL(url)
                document.body.removeChild(a)
            } catch(error) {
                errorHandler({error})
            } finally {
                this[loadingType] = false
            }
        },
        changeTab(val) {
            const query = {...this.$route.query}
            query.sptab = val
            this.$router.push({query})
        },
        deleteSprint() {
            this.$confirm({
                title: this.$t('task.confirm_delete_sprint'),
                closable: true,
                maskClosable: true,
                cancelText: this.$t('task.cancel'),
                okText: this.$t('task.remove'),
                zIndex: 999999,
                onOk: () => {
                    return new Promise((resolve, reject) => {
                        this.$http.post('/table_actions/update_is_active/', [{ id: this.sprint.id, is_active: false }])
                            .then(() => {
                                this.$message.success(this.$t('task.sprint_deleted'))
                                this.visible = false
                                eventBus.$emit(`update_sprints_list${this.isInject}`)
                                resolve()
                            })
                            .catch(error => {
                                errorHandler({error})
                                reject()
                            })
                    })
                }
            })
        },
        editSprint() {
            this.visible = false
            eventBus.$emit('edit_sprint', {
                ...this.sprint,
                back: true,
                inject: this.inject
            })
        },
        async actionHandler() {
            if(this.sprint.status === 'new') {
                try {
                    this.loading = true
                    await this.$http.put(`tasks/sprint/${this.sprint.id}/update_status/`, {status: 'in_process'})
                    this.$message.success(this.$t('task.sprint_started'))
                    eventBus.$emit('update_filter_tasks.TaskSprintModel')
                } catch(error) {
                    errorHandler({error})
                } finally {
                    this.loading = false
                    this.getSprint()
                }
            }
            if(this.sprint.status === 'in_process') {
                eventBus.$emit('end_sprint', this.sprint)
                /*try {
                    this.loading = true
                    await this.$http.put(`tasks/sprint/${this.sprint.id}/update_status/`, {status: 'completed'})
                    this.$message.success("Спринт завершен")
                    eventBus.$emit('update_filter_tasks.TaskSprintModel')
                } catch(e) {
                    this.$message.error(this.$t('error'))
                } finally {
                    this.loading = false
                    this.getSprint()
                }*/
            }
        },
        afterVisibleChange(vis) {
            if(vis) {
                if(this.$route.query?.viewProject || this.$route.query?.viewGroup)
                    this.inject = true
                if(this.$route.query?.sptab)
                    this.tab = this.$route.query.sptab
                this.getSprint()
            } else {
                this.closeDrawer()
            }
        },
        closeDrawer() {
            this.offEvents()
            const hadSprint = Boolean(this.$route.query?.sprint)
            const query = clearTabQuery({
                ...this.$route.query,
                sprint: undefined,
                sptab: undefined
            })
            this.sprint = null
            this.actions = null
            this.inject = false
            this.active = 1
            this.tab ='info'
            if(hadSprint) {
                this.$router.push({query})
            }
        },
        async getSprintActions(query) {
            try {
                const { data } = await this.$http.get(`/tasks/sprint/${query.sprint}/action_info/`)
                if(data) {
                    this.actions = data
                }
            } catch(e) {
                console.log(e)
            }
        },
        sprintReload() {
            this.$nextTick(() => {
                if(this.$refs.analyticsTab)
                    this.$refs.analyticsTab.analyticsUpdate()
                if(this.$refs.sprintTask)
                    this.$refs.sprintTask.tableReload()
            })
            this.getSprint(true)
        },
        offEvents() {
            if(this.sprint)
                eventBus.$off(`update_sprint_${this.sprint.id}`)
            eventBus.$off('update_sprint_detail')
            eventBus.$off(`update_task_data_detail${this.isInject}`)
        },
        async getSprint(reload = false) {
            try {
                this.detailLoading = true
                if(!reload)
                    this.infoLoading = true
                const query = Object.assign({}, this.$route.query)
                const { data } = await this.$http.get(`/tasks/sprint/${query.sprint}/`)
                if(data) {
                    if(!reload)
                        await this.getSprintActions(query)
                    this.sprint = data
                    if(!reload) {
                        eventBus.$on('update_sprint_detail', () => {
                            this.sprintReload()
                        })
                        eventBus.$on(`update_sprint_${this.sprint.id}`, () => {
                            this.sprintReload()
                        })
                        eventBus.$on(`update_task_data_detail${this.isInject}`, () => {
                            this.sprintReload()
                        })
                    }
                }
            } catch(error) {
                errorHandler({error})
                this.visible = false
                this.closeDrawer()
                this.offEvents()
            } finally {
                this.detailLoading = false
                if(!reload)
                    this.infoLoading = false
            }
        }
    },
    mounted() {
        if(this.$route.query?.sprint)
            this.visible = true
        eventBus.$on('close_sprint_drawer', () => {
            this.visible = false
            this.closeDrawer()
            this.offEvents()
        })
    },
    beforeDestroy() {
        eventBus.$off('close_sprint_drawer')
    }
}
</script>

<style lang="scss" scoped>
.aside_row{
    &:not(:last-child){
        margin-bottom: 10px;
    }
    &__title{
        opacity: 0.6;
    }
}
.sprint_show_drawer{
    &::v-deep{
        .ant-drawer-wrapper-body,
        .ant-drawer-content{
            overflow: hidden;
        }
        .ant-drawer-body{
            padding: 0px;
            display: flex;
            flex-direction: column;
            height: 100%;
        }
        .drawer_title{
            font-weight: 400;
            font-size: 16px;
            line-height: 18.75px;
            color: #000;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }
        .drawer_row{
            @media (max-width: 575.98px) {
                display: flex;
                flex-direction: column-reverse;
            }
        }
      
        .sprint_drawer_body{
            flex-grow: 1;
            @media (min-width: 768px) {
            }
            .ant-tabs{
                .ant-tabs-bar{
                    display: none;
                }
            }
            &.body_kanban{
                overflow: hidden;
                padding: 0!important;
                .ant-row{
                    height: 100%;
                    overflow: hidden;
                    .task_tab,
                    .ant-tabs-tabpane,
                    .ant-tabs-content,
                    .body_tab,
                    .ant-col{
                        height: 100%;
                        overflow: hidden;
                    }
                    .task_tab{
                        display: flex;
                        flex-direction: column;
                        .sprint_kanban_wrapp{
                            height: 100%;
                            
                            min-width: 500px;
                            flex-grow: 1;
                            overflow: hidden;
                            // margin-left: 0px;
                            // margin-right: 0px;
                            
                        }
                    }
                }
            }
        }
    }
    .aside_block{
        // background: #F8F8F8;
        // border-radius: 8px;
        // padding: 15px;
        // border: 1px solid var(--border2);
        // color: #000;
    }
}
</style>
