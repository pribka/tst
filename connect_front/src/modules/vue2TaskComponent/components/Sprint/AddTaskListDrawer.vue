<template>

    <DrawerTemplate
        :width="drawerWidth"
        class="task_add_select_drawer"
        v-model="visible"
        :closable="false"
        :title="$t('Add task to sprint')"
        destroyOnClose
        @afterVisibleChange="afterVisibleChange"
        @close="visible = false">
        <div ref="drawerBody">
            <div v-if="!isMobile" class="mb-2">
                <PageFilter 
                    :model="model"
                    :key="pageName"
                    size="large"
                    :getPopupContainer="getPopupContainer"
                    :page_name="pageName"/>
            </div>
            <a-spin 
                v-if="task"
                :spinning="listLoading" 
                :style="isMobile && 'min-height: 90vh;'"
                class="w-full">
                <SprintSelectCard 
                    v-for="sprint in sprintList" 
                    :key="sprint.id" 
                    bgNegative
                    :task="task"
                    :closeDrawer="closeDrawer"
                    :sprint="sprint" />
            </a-spin>
            <div class="flex justify-end pt-1">
                <a-pagination
                    :current="page"
                    :show-size-changer="pageSizeOptions.length > 1"
                    :page-size.sync="pageSize"
                    :defaultPageSize="Number(pageSize)"
                    :pageSizeOptions="pageSizeOptions"
                    :total="count"
                    hideOnSinglePage
                    show-less-items
                    @showSizeChange="sizeSwicth"
                    @change="changePage">
                    <template slot="buildOptionText" slot-scope="props">
                        {{ props.value }}
                    </template>
                </a-pagination>
            </div>
            <div 
                v-if="isMobile"
                class="float_add">
                <div class="filter_slot">
                    <PageFilter 
                        :model="model"
                        :key="pageName"
                        size="large"
                        :getPopupContainer="getPopupContainer"
                        :page_name="pageName"/>
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
        SprintSelectCard: () => import('./SprintSelectCard.vue'),
        PageFilter: () => import('@/components/PageFilter'),
        DrawerTemplate: () => import('@/components/DrawerTemplate.vue')
    },
    computed: {
        isMobile() {
            return this.$store.state.isMobile
        },
        windowWidth() {
            return this.$store.state.windowWidth
        },
        drawerWidth() {
            if(this.windowWidth > 795)
                return 795
            else {
                return '100%'
            }
        },
    },
    data() {
        return {
            task: null,
            model: 'tasks.TaskSprintModel',
            visible: false,
            sprintList: [],
            count: 0,
            page: 1,
            pageName: 'sprint_list_select',
            pageSize: 15,
            listLoading: false,
            pageSizeOptions: ['15', '30', '50']
        }
    },
    methods: {
        closeDrawer() {
            this.visible = false
        },
        sizeSwicth(current, pageSize) {
            this.page = 1
            this.pageSize = Number(pageSize)
            this.getSprints()
        },
        changePage(page) {
            this.page = page
            this.getSprints()
        },
        getPopupContainer() {
            return this.$refs.drawerBody
        },
        afterVisibleChange(vis) {
            if(!vis) {
                this.sprintList = []
                this.count = 0
                this.page = 1
                this.task = null
            } else {
                this.getSprints()
            }
        },
        async getSprints(){
            try{
                this.listLoading = true
                const params = { 
                    page: this.page,
                    page_name: this.pageName,
                    page_size: this.pageSize,
                    for_set_task: this.task.id
                }
                const { data } = await this.$http(`/tasks/sprint/list/`, { params })
                if(data) {
                    this.sprintList = data.results
                    this.count = data.count
                }
            }
            catch(error) {
                errorHandler({error, show: false})
            }
            finally{
                this.listLoading = false
            }
        },
        resetList() {
            this.page = 1
            this.count = 0
            this.getSprints()
        }
    },
    mounted() {
        eventBus.$on('task_add_sprint', task => {
            this.task = task
            this.visible = true
        })
        eventBus.$on(`update_filter_${this.model}_${this.pageName}`, () => {
            this.resetList()
        })
    },
    beforeDestroy() {
        eventBus.$off('task_add_sprint')
        eventBus.$off(`update_filter_${this.model}_${this.pageName}`)
    }
}
</script>

<style lang="scss" scoped>
.task_add_select_drawer{
    &::v-deep{
        .ant-drawer-wrapper-body,
        .ant-drawer-content{
            overflow: initial;
        }
        .ant-drawer-body{
            padding: 0px;
            display: flex;
            flex-direction: column;
            height: 100%;
        }
        .drawer_header{
            padding: 10px 15px;
            border-bottom: 1px solid var(--border2);
            height: 48px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            @media (min-width: 768px) {
                padding: 10px 30px;
            }
        }
        .drawer_body{
            overflow-y: auto;
            flex-grow: 1;
            padding: 20px 15px;
            @media (min-width: 768px) {
                padding: 20px 30px;
            }
        }
    }
}
</style>