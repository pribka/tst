<template>
    <DrawerTemplate
        :width="drawerWidth"
        v-model="visible"
        :closable="false"
        :wrapClassName="isMobile ? '' : 'sprint_select_task'"
        destroyOnClose
        :afterVisibleChange="afterVisibleChange"
        @close="visible = false">
        <template #title>
            <div class="drawer_title">{{ $t('task.add_tasks_to_sprint') }}</div>
        </template>
        <div ref="drawerBody" class="h-full flex flex-col">
            <div v-if="!isMobile" class="flex items-center justify-between mb-2">
                <PageFilter 
                    :model="model"
                    :key="page_name"
                    size="large"
                    :excludeFields="['sprint__exclude', 'sprint']"
                    :getPopupContainer="getPopupContainer"
                    :page_name="page_name" />
                <div class="flex items-center gap-2">
                    <a-button 
                        type="primary"
                        size="large"
                        :disabled="selected.length ? false : true"
                        flaticon
                        :loading="loading"
                        icon="fi-rr-plus"
                        @click="addToSprint()">
                        {{ $t('task.add_tasks_to_sprint') }}
                    </a-button>
                    <SettingsButton
                        :pageName="page_name"
                        :zIndex="1250" />
                </div>
            </div>
            <component 
                v-if="visible"
                :is="listWidget" 
                :page_name="page_name"
                :visible="visible"
                :model="model"
                :selectedIds="selected"
                :rowSelected="rowSelected"
                :queryParams="queryParams" />
            <div 
                v-if="isMobile"
                class="float_add_sprints">
                <a-button 
                    type="primary"
                    size="large"
                    :disabled="selected.length ? false : true"
                    shape="round"
                    :loading="loading"
                    block
                    class="mr-2"
                    @click="addToSprint()">
                    {{ $t('task.add_to_sprint') }}
                </a-button>
                <div class="filter_slot">
                    <PageFilter 
                        :model="model"
                        :key="page_name"
                        size="large"
                        :excludeFields="['sprint__exclude', 'sprint']"
                        :getPopupContainer="getPopupContainer"
                        :page_name="page_name" />
                </div>
            </div>
        </div>
    </DrawerTemplate>
</template>

<script>
import eventBus from '@/utils/eventBus'
import { errorHandler } from '@/utils/index.js'
export default {
    components: {
        PageFilter: () => import('@/components/PageFilter'),
        SettingsButton: () => import('@/components/TableWidgets/SettingsButton'),
        DrawerTemplate: () => import("@/components/DrawerTemplate.vue")
    },
    computed: {
        isMobile() {
            return this.$store.state.isMobile
        },
        windowWidth() {
            return this.$store.state.windowWidth
        },
        drawerWidth() {
            if(this.windowWidth > 1375)
                return 1375
            else {
                return '100%'
            }
        },
        page_name() {
            return `tasks_select_sprint_${this.sid}_task.TaskModel`
        },
        isInject() {
            return this.inject ? `_inject` : ''
        },
        visible: {
            get() {
                return this.$store.state.task.sprintAddTaskShow
            },
            set(value) {
                this.$store.commit('task/SET_SPRINT_ADD_TASK_SHOW', value)
            }
        },
        listWidget() {
            if(this.isMobile)
                return () => import('./TaskList.vue')
            else
                return () => import('./TaskTable.vue')
        }
    },
    data() {
        return {
            queryParams: {
                task_type: 'task'
            },
            selected: [],
            sid: null,
            loading: false,
            inject: false,
            model: 'tasks.TaskModel'
        }
    },
    methods: {
        rowSelected(e) {
            if (!e || !e.source) return

            const validSources = ['checkboxSelected', 'rowClicked']
            if (!validSources.includes(e.source)) return

            const id = e.data.id
            const index = this.selected.indexOf(id)

            if (e.node.selected) {
                if (index === -1) {
                    this.selected.push(id)
                }
            } else {
                if (index !== -1) {
                    this.selected.splice(index, 1)
                }
            }
        },
        async addToSprint() {
            try {
                this.loading = true
                const { data } = await this.$http.post('/tasks/task/bulk_set_sprint/', {
                    sprint: this.sid,
                    tasks: this.selected
                })
                if(data === 'ok') {
                    eventBus.$emit(`update_sprints_list${this.isInject}`)
                    eventBus.$emit(`update_sprint_${this.sid}`)
                    eventBus.$emit('sprint_update_table_reload')
                    this.visible = false
                }
            } catch(error) {
                errorHandler({error})
            } finally {
                this.loading = false
            }
        },
        openDrawer() {
            this.visible = true
        },
        afterVisibleChange(vis) {
            if(!vis) {
                this.sid = null
                this.selected = []
                this.queryParams = {
                    task_type: 'task'
                }
                this.inject = false
            } else {
                if(this.$route.query?.viewProject || this.$route.query?.viewGroup)
                    this.inject = true
            }
        },
        
        getPopupContainer() {
            return this.$refs.drawerBody
        },
    },
    mounted() {
        eventBus.$on('sprint_add_task', sid => {
            this.sid = sid
            this.queryParams = {
                task_type: 'task',
                sprint: sid
            }
            this.visible = true
        })
    },
    beforeDestroy() {
        eventBus.$off('sprint_add_task')
    }
}
</script>

<style lang="scss">
.sprint_select_task .ant-drawer-body .drawer_body{
    height: 100%;
}
</style>

<style lang="scss" scoped>
.float_add_sprints{
    --safe-area-inset-bottom: env(safe-area-inset-bottom);
    position: fixed;
    bottom: calc(25px + var(--safe-area-inset-bottom));
    left: 15px;
    right: 15px;
    z-index: 50;
    display: flex;
    align-items: center;
    .filter_slot{
        &::v-deep{
            .ant-btn{
                border-radius: 50%;
                border-color: #ffffff;
                display: flex;
                align-items: center;
                justify-content: center; 
                max-width: 40px;
                box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
            }
        }
    }
}
</style>