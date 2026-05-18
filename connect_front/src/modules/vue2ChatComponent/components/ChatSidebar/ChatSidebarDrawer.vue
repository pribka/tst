<template>
    <div>
        <a-button
            :type="isMobile ? 'link' : 'ui'"
            icon="fi-rr-menu-burger"
            ghost
            flaticon
            shape="circle"
            @click="visible = true" />

        <a-drawer
            placement="right"
            class="chat_sidebar_drawer"
            :class="isMobile && 'chat_sidebar_drawer_mobile'"
            :width="isMobile ? '100%' : 460"
            v-model="visible"
            :zIndex="700"
            :title="$t('chat.chat_information')"
            :destroyOnClose="true"
            @close="visible = false">
            <div class="drawer_body">
                <div 
                    v-if="taskCount"
                    class="sidebar_drawer_link flex items-center"
                    @click="openSidebarChild('task_list')">
                    <span>{{ $t('chat.chat_tasks') }}</span> 
                    <a-badge 
                        class="ml-2 badge_right" 
                        :count="taskCount"/>
                </div>
                <div 
                    class="sidebar_drawer_link flex items-center"
                    @click="openSidebarChild('chat_files')">
                    <span>{{ $t('chat.chat_files') }}</span> 
                    <a-badge 
                        class="ml-2 badge_right" 
                        :count="fileCount"
                        showZero/>
                </div>
                <div
                    v-if="projectId" 
                    class="sidebar_drawer_link flex items-center"
                    @click="openSidebarChild('project_files')">
                    <span>{{ $t('chat.project_files') }}</span> 
                    <a-badge 
                        class="ml-2 badge_right" 
                        :count="projectFileCount"
                        showZero/>
                </div>
                <div class="mt-8">
                    <Info />
                </div>
            </div>
        </a-drawer>

        <a-drawer
            placement="right"
            class="chat_task_drawer"
            :class="isMobile && 'chat_task_drawer_mobile'"
            :width="widthDrawer"
            :visible="sidebarChildVisible"
            :zIndex="700"
            :title="$t(`chat.${innerDrawerTitle}`)"
            :destroyOnClose="true"
            @close="sidebarChildVisible = false">
            <div class="drawer_body">
                <div
                    class="drawer_wrapper"
                    :class="active === 'task_kanban' && 'kanban_wrapper'">
                    <component
                        :active="active"
                        :is="activeTab"
                        :id="activeChat.chat_uid"
                        
                        :sourceId="fileSourceId"
                        :isFounder="true"
                        :isStudent="true"    />
                </div>
            </div>
        </a-drawer>
    </div>
</template>

<script>
import { mapState, mapGetters } from 'vuex'
import { declOfNum } from '../../utils'
export default {
    name: "ChatSidebar",
    components: {
        Info: () => import('./Info.vue')
    },
    computed: {
        ...mapState({
            activeChat: state => state.chat.activeChat,
            sidebarTasks: state => state.chat.sidebarTasks,
            windowWidth: state => state.windowWidth,
            isMobile: state => state.isMobile
        }),
        ...mapGetters({
            chatMembers: 'chat/chatMembers'
        }),
        activeTab() {
            if(this.active === 'task_list')
                return () => import('./Tasks.vue')
            if(this.active === 'task_kanban')
                return () => import('./Kanban.vue')
            if(['project_files', 'chat_files'].includes(this.active))
                return () => import('@apps/vue2Files')
            return () => import('./Tasks.vue')
        },
        fileSourceId() {
            switch (this.active) {
            case 'chat_files':
                return this.activeChat.id
            case 'project_files':
                return this.activeChat.workgroup.uid
            default:
                return 0
            }
        },
        projectId() {
            return this.activeChat?.workgroup?.uid
        },
        visible: {
            get() {
                return this.sidebarTasks
            },
            set(val) {
                this.$store.commit('chat/TOGGLE_TASKS_SIDEBAR', val)
            }
        },
        widthDrawer() {
            if(this.windowWidth > 1200)
                return this.windowWidth - 250
            else
                return this.windowWidth
        },
        isMobile() {
            return this.$store.state.isMobile
        },
        taskCount() {
            return this.count?.total 
        },
        fileCount() {
            return this.fileAggregate?.files
        },
        projectFileCount() {
            return this.projectFileAggregate?.files
        },
        innerDrawerTitle() {
            return this.$t(this.active)
        }
    },
    data(){
        return{
            changeName: false,
            nameLoading: false,
            active: 'task_list',
            activeMenu: ['task_list'],
            defaultActive: ['task_list'],
            count: 0,
            countLoader: false,
            rules: {
                name: [
                    { required: true, message: this.$t('chat.field_require'), trigger: 'blur' },
                    { min: 3, max: 30, message: this.$t('chat.field_min_require', {min: 3}), trigger: 'blur' },
                ],
            },
            form: {
                name: ''
            },
            sidebarChildVisible: false,
            fileAggregate: null,
            projectFileAggregate: null
        }
    },
    async created() {
        await this.getTaskCount()
        await this.getFileCount()
        if(this.projectId)
            await this.getProjectFileCount()
    },
    methods: {
        async getTaskCount() {
            try {
                this.countLoader = true
                const { data } = await this.$http.get('/chat/task/list/', {
                    params: {
                        chat: this.activeChat.chat_uid,
                        task_type: 'task'
                    }
                })
                if(data)
                    this.count = data
            } catch(e) {
                console.log(e)
            } finally {
                this.countLoader = false
            }
        },
        async getFileCount() {
            try {
                this.countLoader = true
                const { data } = await this.$http.get(`attachments/${this.activeChat.id}/aggregate/`)
                if(data)
                    this.fileAggregate = data
            } catch(e) {
                console.log(e)
            } finally {
                this.countLoader = false
            }
        },
        async getProjectFileCount() {
            try {
                this.countLoader = true
                const { data } = await this.$http.get(`attachments/${this.projectId}/aggregate/`)
                if(data)
                    this.projectFileAggregate = data
            } catch(e) {
                console.log(e)
            } finally {
                this.countLoader = false
            }
        },
        handleClickMenu(e){
            this.active = e.key
        },
        openSidebarChild(child) {
            this.sidebarChildVisible = true
            this.active = child
        }
    }
}
</script>

<style lang="scss">
.badge_right {
    margin-left: auto;
    margin-right: 0;
}
.chat_sidebar_drawer{
    .ant-drawer-body{
        padding: 0px;
        overflow: hidden;
        height: calc(100% - 40px);
    }
    .ant-drawer-wrapper-body{
        overflow: hidden;
    }
}

.chat_task_drawer{
    .ant-drawer-body{
        padding: 0px;
        overflow: hidden;
        height: calc(100% - 40px);
    }
    .ant-drawer-wrapper-body{
        overflow: hidden;
    }
}
.chat_task_count{
    .ant-badge-count{
        top: 5px;
    }
}
</style>

<style lang="scss" scoped>
.chat_sidebar_drawer {
    .drawer_body {
        height: 100%;
        padding: 30px;
        overflow-y: auto;
    }
    .sidebar_drawer_link {
        padding: 10px 20px;
        border-radius: 15px;
        border: 1px solid var(--border3);
        transition: background-color 0.2s ease-in-out;
        cursor: pointer;
        &:not(:last-child) {
            margin-bottom: 10px;
        }
        &:hover {
            background-color: var(--bgColor2);
        }
    }
}

.chat_task_drawer{
    .drawer_body{
        height: 100%;

    }
    .drawer_wrapper{
        height: calc(100% - 48px);
        overflow-y: auto;
        &:not(.kanban_wrapper){
            padding: 30px;
            @media (max-width: 900px) {
                padding: 15px;
            }
        }
    }

}
.chat_task_drawer_mobile {

    .drawer_wrapper{
        &:not(.kanban_wrapper){
            padding: 15px;
        }
    }
}
</style>