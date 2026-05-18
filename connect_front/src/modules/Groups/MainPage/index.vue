<template>
    <DrawerTemplate
        v-model="visible"
        :width="widthDrawer"
        destroyOnClose
        class="group_drawer"
        :asideColSize="{
            lg: 8,
            xl: 6,
            xxl: 5
        }"
        :contentColSize="{
            lg: 16,
            xl: 18,
            xxl: 19
        }"
        @afterVisibleChange="afterVisibleChange"
        @close="visible = false">
        <a-skeleton 
            v-if="loading"  
            class="ml-2 mt-4" 
            active 
            avatar 
            :paragraph="{ rows: 4 }" 
            :loading="loading" />

        <template #title>
            <div v-if="requestData" class="w-full flex items-center justify-between">
                <div class="group_info flex items-center truncate">
                    <div>
                        <a-avatar 
                            icon="fi-rr-users-alt"
                            flaticon
                            :size="35" 
                            :src="workgroupLogoPath" />
                    </div>
                    <h5 class="drawer_title ml-3">
                        {{requestData.name}}
                    </h5>
                </div>
                <div class="group_buttons flex items-center pl-3">
                    <component 
                        v-if="isMobile"
                        :is="burgerWidget"
                        :requestData="requestData"
                        :is_project="is_project"
                        :isFounder="isFounder"
                        :actions="actions"
                        :isStudent="isStudent"
                        :loadingExit="loadingExit"
                        :loadingJoin="loadingJoin"
                        :disableJoinClub="disableJoinClub"
                        :createChatLoading="createChatLoading"
                        @finishProject="finishProject($event)"
                        @createChat="createChat"
                        @openChat="openChat"
                        @joinGroup="joinGroup"
                        @leaveGroup="leaveGroup"
                        @goToEdit="goToEdit"
                        @shareToChat="shareToChat"
                        @deleteGroup="deleteGroup" />
                    <template v-else>
                        <template v-if="joinInit">
                            <!--<a-button
                                v-if="actions && actions.create_chat && !requestData.with_chat"
                                class="ml-2"
                                :loading="createChatLoading"
                                type="ui"
                                @click="createChat">
                                {{ $t('wgr.create_chat')  }}
                            </a-button>
                            <a-button
                                v-if="actions?.open_chat?.availability && requestData.with_chat && requestData.linked_chat"
                                class="ml-2"
                                type="ui"
                                @click="openChat">
                                {{ $t('wgr.open_chat') }}
                            </a-button>-->
                            <a-button
                                v-if="actions && actions.edit"
                                type="ui"
                                class="ml-2"
                                ghost
                                shape="circle"
                                icon="fi-rr-edit"
                                flaticon
                                @click="goToEdit" />
                            <a-button
                                class="ml-2"
                                type="ui"
                                icon="fi-rr-share"
                                shape="circle"
                                ghost
                                flaticon
                                @click="shareToChat" />
                            <a-button 
                                v-if="actions && actions.delete"
                                class="ml-2"
                                type="ui"
                                ghost
                                icon="fi-rr-trash"
                                shape="circle"
                                flaticon
                                @click="deleteGroup()"/>
                            <a-button
                                v-if="isStudent && !isFounder"
                                @click="leaveGroup"
                                class="ml-2"
                                icon="fi-rr-exit"
                                ghost
                                flaticon
                                type="ui"
                                :loading="loadingExit">
                                {{ $t("wgr.exit") }}
                            </a-button>
                        </template>
                    </template>
                </div>
            </div>
        </template>

        <template #tabs>
            <template v-if="requestData && requestData.id">
                <template v-if="isMobile">
                    <div class="tab_wrapper">
                        <a-tabs 
                            v-model="active"
                            @change="changeTab">
                            <a-tab-pane
                                v-for="tab in currentMenuRoutes"
                                :key="tab.name">
                                <template #tab>
                                    <div class="flex">
                                        <span>{{$t('wgr.'+tab.menuName)}}</span>
                                    </div>
                                </template>
                            </a-tab-pane>
                        </a-tabs>
                    </div>
                </template>
                <template v-else>
                    <div class="page_switch">
                        <a-menu
                            mode="horizontal"
                            v-model="activeMenu"
                            :defaultSelectedKeys="defaultActive"
                            @click="handleClickMenu">
                            <template v-for="item in currentMenuRoutes" >
                                <template v-if="item.child && item.child.length">
                                    <a-sub-menu 
                                        v-if="item.child" 
                                        :key="item.name"
                                        @titleClick="titleClick($event, item)">
                                        <template slot="title">
                                            <span>{{$t('wgr.'+item.menuName)}}</span>
                                        </template>
                                        <a-menu-item 
                                            v-for="child in item.child" 
                                            :key="child.name">
                                            <span>{{$t('wgr.'+child.menuName)}}</span>
                                        </a-menu-item>
                                    </a-sub-menu>
                                </template>
                                <template v-else>
                                    <a-menu-item 
                                        class="h-full"
                                        :key="item.name">
                                        <div 
                                            class="h-full flex items-center"
                                            v-if="badgeShow">
                                            <a-badge
                                                class="tab_badge"
                                                :count="fileCount(item.name)" :overflow-count="99">
                                                <span>{{$t('wgr.'+item.name)}}</span>
                                            </a-badge>
                                        </div>
                                        <span v-else>
                                            {{$t('wgr.'+item.menuName)}}
                                        </span>
                                    </a-menu-item>
                                </template>
                            </template>
                        </a-menu>
                    </div>
                </template>
            </template>
        </template>
        <template v-if="requestData && requestData.id"  #aside>
            <div v-if="showSidebar" class="flex_basis">
                <About 
                    :actions="actions"
                    :requestData="requestData"
                    :createChatLoading="createChatLoading"
                    :createChat="createChat"
                    :openChat="openChat"
                    :changeTab="changeTab"
                    :updatePartisipants="updatePartisipants" />
            </div>
        </template>
        <template v-if="!loading">
            <template v-if="requestData">
                <template v-if="isStudent || isFounder">
                    <Kanban
                        :id="id"
                        :actions="actions"
                        :is_project="is_project"
                        v-if="active === 'kanban'" />
                    <!--<Calendar
                        :id="id"
                        :isStudent="isStudent" 
                        :isFounder="isFounder" 
                        :is_project="is_project"
                        v-if="active === 'calendar'" />
                    <News 
                        :id="id" 
                        :actions="actions"
                        v-if="active === 'news'"/>-->
                    <Tasks 
                        :isStudent="isStudent" 
                        :isFounder="isFounder" 
                        :actions="actions"
                        :id="id" 
                        :requestData="requestData"
                        v-if="active === 'tasks'"/>
                    <!--<Analytics 
                        :id="id"
                        :is_project="is_project"
                        :requestData="requestData"
                        v-if="active === 'analytics'"/>
                    <Sprint
                        :id="id"
                        :actions="actions"
                        :is_project="is_project"
                        v-if="active === 'sprint'"/>
                    <template v-if="active === 'about'">
                        <About 
                            :id="id"
                            :is_project="is_project"
                            :updatePartisipants="updatePartisipants"
                            :changeTab="changeTab"
                            :actions="actions"
                            :createChatLoading="createChatLoading"
                            :createChat="createChat"
                            :openChat="openChat"
                            :requestData="requestData"/>
                    </template>
                    <Files
                        v-if="isStudent && active === 'group_files'" 
                        :id="id" 
                        :isFounder="isFounder" 
                        :isStudent="isStudent" 
                        :actions="actions"
                        :key="groupFilesKey"/>
                    <Files
                        v-if="isStudent && active === 'chat_files'" 
                        active="chat_files"
                        :id="this.requestData.linked_chat_id" 
                        :isFounder="isFounder" 
                        :isStudent="isStudent"
                        :actions="actions"
                        :key="chatFilesKey"/>-->
                    <!-- WARNING -->
                    <Tasks 
                        :isStudent="isStudent" 
                        :isFounder="isFounder" 
                        :id="id" 
                        :requestData="requestData"
                        :actions="actions"
                        taskType="interest"
                        :key="interestKey"
                        v-if="active === 'interest'"/>
                    <!-- WARNING END -->

                    <Participants 
                        v-if="active === 'participants'"
                        :isStudent="isStudent" 
                        :isFounder="isFounder" 
                        :getRoles="getRoles"
                        :id="id"
                        :updatePartisipants="updatePartisipants"
                        :actions="actions"  />

                </template>
                <template v-else>
                    <a-result 
                        v-if="!loading && !isStudent && requestData.public_or_private"
                        status="403" 
                        :title="$t('wgr.closed_group')" 
                        :sub-title="$t('wgr.no_partisipants_group')">
                        <template #extra>
                            <a-button 
                                type="primary" 
                                icon="message"
                                @click="chatAuthor()">
                                {{ $t('wgr.author_chat') }}
                            </a-button>
                        </template>
                    </a-result>
                    <template v-if="!loading && !requestData.public_or_private">
                        <a-result 
                            v-if="!isStudent || !isFounder"
                            status="404" 
                            :title="$t('wgr.group_info_hide')" 
                            :sub-title="$t('wgr.group_info_hide_desc')" />
                    </template>
                </template>
            </template>
        </template>
        <template #footer>
            <component 
                :is="footerWidget"
                :requestData="requestData"
                :id="id" />
        </template>
    </DrawerTemplate>
</template>

<script>
import { mapActions,  mapMutations, mapState } from 'vuex'
import { clearTabQuery } from '@/utils/routerUtils.js'
import eventBus from "@/utils/eventBus"
import { errorHandler } from '@/utils/index.js'
export default {
    name: "GroupViewDrawer",
    components: {
        DrawerTemplate: () => import("@/components/DrawerTemplate.vue"),
        //News: () => import('./PagesSwitch/News.vue'),
        Tasks: () => import('./PagesSwitch/Tasks/index.vue'),
        Kanban: () => import('./PagesSwitch/Kanban.vue'),
        About: () => import('./modules/About'),
        //Calendar: () => import('./PagesSwitch/Calendar.vue'),
        //Analytics: () => import('./PagesSwitch/Analytics.vue'),
        //Sprint: () => import('./PagesSwitch/Sprint.vue'),
        //Files: () => import('./modules/Files.vue'),
        Participants: () => import('./modules/Participants.vue'),
    },
    data(){
        return{
            menuProject:  [] ,
            visible: false,
            active: 'participants',
            activeMenu: ['participants'],
            defaultActive: ['participants'],
            joinInit: false,
            loading: false,

            loadingJoin: false,
            loadingExit: false,
            createChatLoading: false,
            requestData: { social_links: [] },

            dialogJoin: false,
            disableJoinClub: false,

            roles: [],

            isFounder: false,
            isStudent: false,

            mainKey: this.getKey(),
            eventKey: this.getKey(),
            galeryKey: this.getKey(),
            groupFilesKey: this.getKey(),
            chatFilesKey: this.getKey(),
            membersKey: this.getKey(),
            interestKey: this.getKey(),
            groupFileCount: 0,
            chatFileCount: 0,
            actions: null,
            pendingChatNavigation: null
        }
    },
    watch: {
        '$route.query.viewGroup'() {
            if(this.$route.query.viewGroup)
                this.startView()
        },
        '$route.query'(val){
            if(!val.viewGroup){
                this.visible = false
            }
        }
    },

    computed:{
        ...mapState({
            windowWidth: state => state.windowWidth
        }),
        workgroupLogoPath() {
            return this.requestData?.workgroup_logo?.path || null
        },
        footerWidget() {
            if (this.isMobile) {
                if (this.active === 'participants' && this.actions?.add_member) {
                    return () => import('../components/MemberListAdd.vue')
                }
            }
            return null
        },

        currentMenuRoutes() {
            let tabs = this.requestData?.tabs || []

            tabs.forEach((item, index) => {
                if(item.onlyMobile && !this.isMobile)
                    tabs.splice(index, 1)
                if(item.onlyDesktop && this.isMobile)
                    tabs.splice(index, 1)
            })

            if(this.id === '59449eea-4536-11ed-bca7-4216f3de51df') {
                tabs = tabs.concat({
                    name: 'interest',
                    menuName: "interest",
                    icon: "interest"
                })
            }

            return tabs
        },
        id() {
            const query =  Object.assign({}, this.$route.query)
            if(query.viewGroup) return this.$route.query.viewGroup
            return null
        },
        is_project() {
            return this.requestData.is_project
        },
        widthDrawer() {
            if(this.windowWidth > 1200)
                return this.windowWidth - 250
            else
                return '100%'
        },
        showSidebar() {
            if(this.active === 'kanban' || this.active === 'gant' || this.active === 'tasks' || this.isMobile || this.active === 'calendar')
                return false
            else
                return true
        },
        isMobile() {
            return this.$store.state.isMobile
        },
        burgerWidget() {
            if(this.isMobile)
                return () => import('./modules/BurgerMobile.vue' )
            return false
        },
        tableMembers() {
            return this.$store.state.projects.tables?.[`project_members_${this.requestData.id}`]?.results
        },
        startDate() {
            return this.$moment().startOf('day').toISOString()
        },
        endDate() {
            return this.$moment().endOf('week').toISOString()
        }
    },
    methods:{
        ...mapActions({
            getInfos: "workgroups/getInfo",
            getRolesS: "workgroups/getRoles",
            joinGroupS: "workgroups/joinGroup",
            leaveGroupS: "workgroups/leaveGroup",
            finishedDate: "workgroups/finishedDate",
            addNewChat: 'workgroups/addNewChat'

        }),
        ...mapMutations({
            setLoading: "workgroups/setLoading"
        }),
        afterVisibleChange(vis) {
            if(!vis) {
                if(this.pendingChatNavigation) {
                    const query = clearTabQuery({
                        ...this.$route.query,
                        filters: undefined,
                        tab: undefined,
                        viewGroup: undefined
                    })
                    
                    this.$router.replace({query}).then(() => {
                        this.clearComponentState()
                        this.$router.push(this.pendingChatNavigation)
                        this.pendingChatNavigation = null
                    }).catch(() => {
                        this.clearComponentState()
                        this.$router.push(this.pendingChatNavigation)
                        this.pendingChatNavigation = null
                    })
                } else {
                    this.close()
                }
                this.actions = null
            }
        },
        badgeShow() {
            return ((isStudent || isFounder) && item.name === 'group_files' && groupFileCount) || ((isStudent || isFounder) && item.name === 'chat_files' && chatFileCount)
        },
        fileCount(name) {
            if(name==='group_files') {
                return this.groupFileCount
            } else if (name==='chat_files') {
                return this.chatFileCount
            } else {
                return 0
            }
        },
        shareToChat(){
            let is_project =  this.requestData.is_project
            this.$store.commit('share/SET_SHARE_PARAMS', {
                model: 'workgroups.WorkGroupModel',
                shareId: this.requestData.id,
                object: this.requestData,
                shareUrl: `${window.location.origin}/?viewGroup=${ this.requestData.id}`,
                shareTitle: `${is_project ? this.$t('wgr.project'): this.$t('wgr.group_share')} - ${ this.requestData.name}`
            })
        
        },
        deleteGroup() {
            this.$confirm({
                title: this.$t('wgr.warning'),
                content: this.$t('wgr.delete_confirm_text', { type: this.is_project ? this.$t('wgr.project_label') :  this.$t('wgr.group_label') }),
                zIndex: 2200,
                cancelText: this.$t('wgr.close'),
                okText: this.$t('wgr.delete'),
                okType: 'danger',
                onOk: () => {
                    return new Promise((resolve, reject) => {
                        this.$http.post(`/work_groups/workgroups/${this.requestData.id}/delete/`).
                            then(() => {
                                this.$message.success(`${this.is_project ? this.$t('wgr.project_delete') : this.$t('wgr.group_delete')}`)
                                if(this.is_project) {
                                    eventBus.$emit('update_list_project')
                                    eventBus.$emit('project_deleted', this.requestData.id)
                                } else {
                                    eventBus.$emit('update_list_group')
                                } 
                                this.close2()
                                resolve()
                            })
                            .catch((error) => {
                                errorHandler({error})
                                reject()
                            })
                    })
                },
                onCancel() {}
            })
        },
        updatePartisipants(users) {
            this.requestData.members_count = users
            if(this.tableMembers) {
                const workgroup_members = this.tableMembers.filter(item => item.member !== undefined && item.member !== null)
                this.$set(this.requestData, 'workgroup_members', workgroup_members)
            }
        },
        chatAuthor() {
            this.pendingChatNavigation = {name: 'chat', query: {user: this.requestData.founder.id}}
            this.visible = false
        },
        openChat(){
            if(this.isMobile)
                this.pendingChatNavigation = {name: 'chat-body', params: {id: this.requestData.linked_chat}}
            else
                this.pendingChatNavigation = {name: 'chat', query: {chat_id: this.requestData.linked_chat}}
            this.visible = false
        },
        async createChat(){
            try{ 
                this.createChatLoading = true
                const res = await this.addNewChat({data: {with_chat: true}, id: this.id})
                if(res?.chat_uid) {
                    const self = this
                    this.requestData.with_chat = true
                    this.requestData.linked_chat = res.chat_uid
                    this.$success({
                        title: this.$t('wgr.chat_created'),
                        okText: this.$t('wgr.open_chat'),
                        okType: 'success',
                        closable: true,
                        maskClosable: true,
                        cancelText: this.$t('wgr.close'),
                        onOk() {
                            if(self.isMobile)
                                self.pendingChatNavigation = {name: 'chat-body', params: {id: res.chat_uid}}
                            else
                                self.pendingChatNavigation = {name: 'chat', query: {chat_id: res.chat_uid}}
                            self.visible = false
                        },
                        onCancel(){}
                    })
                }
            } 
            catch(error){
                errorHandler({error})
            }
            finally{
                this.createChatLoading = false
            }
        },
        getKey() {
            return  Math.floor(Math.random() * 99999)
        },
        close2() {
            eventBus.$emit('update_workgroup_data')
            const query = clearTabQuery({
                ...this.$route.query,
                filters: undefined,
                tab: undefined,
                viewGroup: undefined
            })

            this.$router.replace({query})
            this.isFounder = false
            this.isStudent = false
            this.active = 'participants'
            this.activeMenu = ['participants']
            this.requestData = { social_links: [] }
            this.joinInit = false
            this.visible = false
        },
        clearComponentState() {
            this.groupFileCount = 0
            this.chatFileCount = 0
            this.isFounder = false
            this.isStudent = false
            this.joinInit = false
            this.active = 'participants'
            this.activeMenu = ['participants']
            this.requestData = { social_links: [] }
        },
        close(){
            const query = clearTabQuery({
                ...this.$route.query,
                filters: undefined,
                tab: undefined,
                viewGroup: undefined
            })

            this.$router.replace({query})
            this.clearComponentState()
        },

        async getTabAttachments(groupId = this.id) {
            try {
                if(!groupId) {
                    return
                }
                if(this.isStudent || this.isFounder) {
                    const groupAttachmentsCount = await this.$http(
                        `attachments/${ groupId }/aggregate/`)
                    this.groupFileCount = groupAttachmentsCount.data.files
                    if(this.requestData.with_chat) {
                        const chatAttachmentsCount = await this.$http(
                            `attachments/${ this.requestData.linked_chat_id }/aggregate/`)
                        this.chatFileCount = chatAttachmentsCount.data.files
                    }                          
                }
            } catch(e) {

            }
        },

        async startView(){
            try{
                const groupId = this.id
                if(!groupId) {
                    return
                }
                const query = {...this.$route.query}
                if (query.tab) {
                    if(this.isMobile) {
                        if(query.tab === 'gant' || query.tab === 'sprint') {
                            delete query.tab
                            this.$router.replace({query})
                        }
                        if(query.tab) {
                            this.active = query.tab
                            this.activeMenu = [query.tab]
                        }
                    } else {
                        if(query.tab === 'about') {
                            delete query.tab
                            this.$router.replace({query})
                        }
                        if(query.tab) {
                            this.active = query.tab
                            this.activeMenu = [query.tab]
                        }
                    }
                }
                this.loading = true
                this.setLoading(true)
                this.visible = true
                const res = await this.getInfos(groupId)
                if(this.id !== groupId) {
                    return
                }
                this.requestData = res
                await this.getRoles(groupId)
                if(this.id !== groupId) {
                    return
                }
                await this.getActions(groupId)
                if(this.id !== groupId) {
                    return
                }
                this.getTabAttachments(groupId)
            }
            catch(error){
                errorHandler({error})
                this.visible = false
            }
            finally{
                this.loading = false
                this.setLoading(false)
            }


        },
        setRouterTab(val) {
            let query = JSON.parse(JSON.stringify(this.$route.query))
            query.tab = val
            this.$router.push({query}).catch(e=>{})
        },
        // Меню и переход на нужный таб
        handleClickMenu(e){
            this.active = e.key
            this.setRouterTab(e.key)
        },
        titleClick(e, item) {
            this.activeMenu = [item.mainPage]
            this.active = item.mainPage
            this.setRouterTab(item.mainPage)
        },
        // Заершить продолжить проект
        finishProject(val){
            try{
                if(val){
                    this.finishedDate({id: this.id, date: null})
                    this.requestData.finished = false
                    this.requestData.finishedDate = null
                } else {
                    this.finishedDate({id: this.id, date: this.$moment()})
                    this.requestData.finished = true
                    this.requestData.finishedDate = this.$moment()

                }
            }
            catch(error){
                errorHandler({error})
            }

        },



        // Отправть запрос на вступление

        async  joinGroup(){
            try{
                this.loadingjoin = true
                await this.joinGroupS({id: this.id, member_visible: true})
                this.$message.success(this.$t('wgr.you_partisipants'))
                this.isStudent = true
                this.membersKey += 1
            }
            catch(error){
                errorHandler({error})
            } finally {
                this.loadingjoin = false
            }

        },

        // Выйти из группы
        async leaveGroup(){
            try{
                this.loadingExit = true
                await this.leaveGroupS(this.id)
                this.membersKey += 1
                this.$message.warning(this.$t('wgr.you_not_member_group'))
                this.isStudent = false;
                this.loadingExit = false
            }
            catch(error){
                errorHandler({error})
            }
        },

        // Получение экшенов
        async getActions(groupId = this.id) {
            try {
                if(!groupId) {
                    return
                }
                const url = `work_groups/workgroups/${groupId}/action_info/`
                const { data } = await this.$http.get(url)
                if(data?.actions) {
                    this.actions = data.actions
                }
            } catch(e) {
                console.log(e)
            }
        },

        // Получение ролей
        async getRoles(groupId = this.id) {
            try{
                if(!groupId) {
                    return
                }
                const res = await this.getRolesS(groupId);
                if (res[0].id) {
                    this.roles = res;
                    res.forEach((item) => {
                        if (['FOUNDER', 'MODERATOR'].includes(item.membership_role.code)) {
                            this.isFounder = true; 
                            this.isStudent = true;
                        } else if (['MEMBER'].includes(item.membership_role.code)) {
                            this.isFounder = false; 
                            this.isStudent = true;
                        }
                    });
                }
            }
            catch(error){
                errorHandler({error, show: false})
            } finally {
                this.joinInit = true
            }
        },

        // Кнопка редактировать группу
        goToEdit() {
            const query = JSON.parse(JSON.stringify(this.$route.query))
            query.updateGroup = this.id
            this.$router.replace({
                query
            })
            this.visible = false
        },

        changeTab(tabName) {
            this.active = tabName
            this.activeMenu = [tabName]
            this.setRouterTab(tabName)
        },
    },
    created() {

        if(this.isMobile) {
            this.defaultActive = ['about']
            this.activeMenu = ['about']
            this.active = 'about'
        }

        const query = this.$route.query
        if(query.viewGroup)
            this.startView()

    },
}
</script>

<style>
@media  (max-width: 800px) {
    .flex_basis {
        flex-basis: auto;
    }
    .flex_order {
        order: 1;
    }
    .mobile_dummy {
        padding-top: 30px;
    }
}

</style>

<style lang="scss">
.workgroup_drawer_collapse {
    margin: 0 -15px;
    .ant-collapse-header {
        font-weight: 500;
    }
    .ant-collapse-content-box {
        padding-top: 5px;
        padding: 15px;
    }
}

.group_drawer{
    .about_card_mobile{
        border: none;
        .ant-card-head {
            padding: 0;
            border: none;
        }
        .ant-card-body {
            padding: 0;
        }
    }
    .group_content{
        overflow-y: auto;
        &.mobile_wrap{
            height: calc(100% - 96px);
        }
        &.full_wrap{
            height: calc(100% - 104px);
        }
        .group_cont_wrap{
            padding: 30px 30px 20px 30px;
            &.grp_calendar_page,
            &.grp_kanbam_page,
            &.grp_gant_page{
                height: 100%;
                .ant-row-flex{
                    height: 100%;
                }
                .ant-col{
                    height: 100%;
                }
            }
            &.grp_calendar_page,
            &.grp_kanbam_page{
                padding: 0px;
            }
        }
    }
    .ant-drawer-header{
        display: none;
    }
    .ant-drawer-wrapper-body,
    .ant-drawer-content{
        overflow: hidden;
    }
    .ant-drawer-body{
        height: 100%;
        padding: 0px;
        overflow-y: hidden;
        .drawer_body{
            height: 100%;
        }
    }
    .group_header{
        .ant-avatar{
            border: 1px solid var(--border2);
        }
    }
}
.group_drawer_mobile {
    .group_content{
        .group_cont_wrap{
            padding: 15px;
        }
    }
    .tab_wrapper {
        .ant-tabs-bar {
            margin-bottom: 0;
        }
        .ant-tabs-tab {
            padding: 10px 16px;
        }

    }
    .group_header {
        padding: 10px 15px;
    }
    .ant-result-image {
        position: relative;
        height: 150px;
        width: 150px;
        svg {
            position: absolute;
            top: 0;
            left: 0;
            transform: scale(0.5) translate(-50%, -50%);
        }
    }
}
</style>
