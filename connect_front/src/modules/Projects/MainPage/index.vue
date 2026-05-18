<template>
    <DrawerTemplate
        v-model="visible"
        :title="requestData.name"
        :width="widthDrawer"
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
        :class="isMobile && 'group_drawer_mobile'"
        destroyOnClose
        @afterVisibleChange="afterVisibleChange"
        @close="visible = false">
        <template #title>
            <div class="w-full flex items-center justify-between">
                <div class="group_info flex items-center truncate">
                    <div>
                        <a-avatar
                            icon="fi-rr-users-alt"
                            flaticon
                            :size="35"
                            :src="workgroupLogoPath"/>
                    </div>
                    <h5 class="drawer_title ml-3">
                        {{ requestData.name }}
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
                        @deleteGroup="deleteGroup"/>
                    <template v-else>
                        <template v-if="joinInit">
                            <template v-if="actions && actions.project_finish">
                                <a-button
                                    v-show="isFounder"
                                    v-if="is_project && requestData.finished"
                                    type="primary"
                                    ghost
                                    @click="finishProject(true)">
                                    {{ $t("project.resume_project") }}
                                </a-button>
                                <a-button
                                    v-show="isFounder"
                                    type="success"
                                    ghost
                                    v-if="is_project && !requestData.finished"
                                    @click="finishProject(false)">
                                    {{ $t("project.finished_project") }}
                                </a-button>
                            </template>
                            <a-button
                                v-if="actions && actions.create_chat && !requestData.with_chat"
                                class="ml-2"
                                :loading="createChatLoading"
                                type="ui"
                                @click="createChat">
                                {{ $t("project.create_chat") }}
                            </a-button>
                            <a-button
                                v-if="requestData.with_chat && requestData.linked_chat"
                                class="ml-2"
                                type="ui"
                                @click="openChat">
                                {{ $t("project.open_chat") }}
                            </a-button>
                            <a-button
                                v-if="actions && actions.edit"
                                type="ui"
                                class="ml-2"
                                ghost
                                shape="circle"
                                icon="fi-rr-edit"
                                flaticon
                                @click="goToEdit"/>
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
                                class="ml-2"
                                type="ui"
                                icon="fi-rr-share"
                                shape="circle"
                                ghost
                                flaticon
                                @click="shareToChat"/>
                            <a-button
                                v-if="isStudent && !isFounder"
                                @click="leaveGroup"
                                class="ml-2"
                                icon="fi-rr-exit"
                                ghost
                                flaticon
                                type="ui"
                                :loading="loadingExit">
                                {{ $t("project.exit") }}
                            </a-button>
                        </template>
                    </template>
                </div>
            </div>
        </template>
        <template v-if="requestData && requestData.id"  #aside>
            <div v-if="showSidebar" class="flex_basis">
                <!-- Завершить проект -->
                <a-alert
                    :message="$t('project.project_finished')"
                    class="mb-2"
                    show-icon
                    v-if="requestData.finished"
                    type="success"/>
                <About 
                    :requestData="requestData" 
                    :actions="actions"
                    :active="active"
                    :createChatLoading="createChatLoading"
                    :createChat="createChat"
                    :openChat="openChat"
                    :changeTab="changeTab"
                    :addToMembersList="addToMembersList"
                    :updatePartisipants="updatePartisipants" />
            </div>
        </template>
        <template v-if="requestData && requestData.id && showSidebar" #aside_bottom>
            <AboutCalendar :requestData="requestData" />
        </template>
        <template #tabs>
            <template v-if="requestData && requestData.id">
                <template v-if="isMobile">
                    <div class="tab_wrapper" ref="tabs">
                        <a-tabs v-model="active" @change="changeTab" :getPopupContainer="() => $refs.tabs">
                            <a-tab-pane v-for="tab in mobileCurrentMenuRoutes" :key="tab.name">
                                <template #tab>
                                    <div class="flex">
                                        <span>{{ $t("project." + tab.menuName) }}</span>
                                    </div>
                                </template>
                            </a-tab-pane>
                        </a-tabs>
                    </div>
                </template>
                <template v-else>
                    <div class="page_switch" ref="menu">
                        <a-menu
                            mode="horizontal"
                            v-model="activeMenu"
                            class="module_menu"
                            :defaultSelectedKeys="defaultActive"
                            @click="handleClickMenu">
                            <template v-for="item in currentMenuRoutes">
                                <template v-if="item.child && item.child.length">
                                    <a-sub-menu
                                        v-if="item.child"
                                        :key="item.name"
                                        @titleClick="titleClick($event, item)">
                                        <template slot="title">
                                            <span>{{ $t("project." + item.menuName) }}</span>
                                        </template>
                                        <a-menu-item v-for="child in item.child" :key="child.name">
                                            <span>{{ $t("project." + child.menuName) }}</span>
                                        </a-menu-item>
                                    </a-sub-menu>
                                </template>
                                <template v-else>
                                    <a-menu-item :key="item.name">
                                        <div class="flex items-center" v-if="badgeShow">
                                            <a-badge
                                                class="tab_badge"
                                                :count="fileCount(item.name)"
                                                :overflow-count="99">
                                                <span>{{ $t("project." + item.name) }}</span>
                                            </a-badge>
                                        </div>
                                        <span v-else>
                                            {{ $t("project." + item.menuName) }}
                                        </span>
                                    </a-menu-item>
                                </template>
                            </template>
                        </a-menu>
                    </div>
                </template>
            </template>
        </template>
        <template>
            <a-skeleton
                v-if="loading"
                class="ml-2 mt-4"
                active
                avatar
                :paragraph="{ rows: 4 }"
                :loading="loading"/>
            <template v-else-if="requestData">
                <template v-if="isStudent || isFounder">
                    <component 
                        :is="pageWidget"
                        :getRoles="getRoles"
                        :key="active"
                        :id="active === 'chat_files' ? this.requestData.linked_chat_id : id"
                        :isStudent="isStudent"
                        :isFounder="isFounder"
                        :actions="actions"
                        :is_project="is_project"
                        :requestData="requestData"
                        :refreshProjectContext="refreshProjectContext"
                        :taskType="active === 'interest' ? 'interest' : 'task'"
                        :updatePartisipants="updatePartisipants"
                        :active="active === 'chat_files' ? chat_files : null" />
                    <About
                        v-if="active === 'about'"
                        :id="id"
                        :actions="actions"
                        :changeTab="changeTab"
                        :createChatLoading="createChatLoading"
                        :createChat="createChat"
                        :openChat="openChat"
                        :updatePartisipants="updatePartisipants"
                        key="about_about"
                        :is_project="is_project"
                        :requestData="requestData"/>
                    <template v-if="requestData && requestData.id && active === 'about'">
                        <a-divider class="my-2" />
                        <AboutCalendar :requestData="requestData" />
                    </template>
                </template>
                <template v-else>
                    <a-result
                        v-if="
                            !loading && !isStudent && requestData.public_or_private
                        "
                        status="403"
                        :title="$t('project.closed_group')"
                        :sub-title="$t('project.no_partisipants_group')">
                        <template #extra>
                            <a-button
                                type="primary"
                                icon="message"
                                @click="chatAuthor()">
                                {{ $t("project.author_chat") }}
                            </a-button>
                        </template>
                    </a-result>
                    <template v-if="!loading && !requestData.public_or_private">
                        <a-result
                            v-if="!isStudent || !isFounder"
                            status="404"
                            :title="$t('project.group_info_hide')"
                            :sub-title="$t('project.group_info_hide_desc')" />
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
import { mapActions, mapMutations, mapState } from "vuex"
import eventBus from "@/utils/eventBus"
import { clearTabQuery } from '@/utils/routerUtils.js'
import { errorHandler } from '@/utils/index.js'
export default {
    name: "ProjectViewDrawer",
    components: {
        DrawerTemplate: () => import("@/components/DrawerTemplate.vue"),
        News: () => import('./PagesSwitch/News.vue'),
        Tasks: () => import('./PagesSwitch/Tasks/index.vue'),
        Kanban: () => import('./PagesSwitch/Kanban.vue'),
        About: () => import('./modules/About'),
        Members: () => import('./modules/Members'),
        Calendar: () => import('./PagesSwitch/Calendar.vue'),
        Analytics: () => import('./PagesSwitch/Analytics.vue'),
        Sprint: () => import('./PagesSwitch/Sprint.vue'),
        Files: () => import('./modules/Files.vue'),
        Gantt: () => import('./PagesSwitch/Gantt.vue'),
        Participants: () => import('./modules/Participants.vue'),
        AboutCalendar: () => import('../components/AboutCalendar.vue'),
        Organizations: () => import("./PagesSwitch/Organizations.vue"),
        Meeting: () => import('./PagesSwitch/Meeting.vue')
    },
    data() {
        return {
            menuProject: [],
            visible: false,
            active: "news",
            activeMenu: ["news"],
            defaultActive: ["news"],
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
        };
    },
    watch: {
        "$route.query.viewProject"() {
            if (this.$route.query.viewProject) this.startView();
        },
        "$route.query"(val) {
            if (!val.viewProject) {
                this.visible = false;
            }
        },
    },

    computed: {
        ...mapState({
            windowWidth: (state) => state.windowWidth,
        }),
        mobileCurrentMenuRoutes() {
            return this.currentMenuRoutes.reduce((acc, curr) => {
                if (curr.child) { acc.push(...curr.child) } 
                else { acc.push(curr) }
                return acc
            }, [])
        },
        footerWidget() {
            if (this.isMobile) {
                if (this.active === 'employees' && this.actions?.add_member) {
                    return () => import('../components/MemberListAdd.vue')
                }
            }
            return null
        },
        pageWidget() {
            const c = this.$options.components
            const widgets = {
                gant: c.Gantt,
                gantt: c.Gantt,
                kanban: c.Kanban,
                calendar: c.Calendar,
                news: c.News,
                tasks: c.Tasks,
                analytics: c.Analytics,
                sprint: c.Sprint,
                group_files: c.Files,
                chat_files: c.Files,
                interest: c.Tasks,
                employees: c.Participants,
                organizations: c.Organizations,
                meetings: c.Meeting
            }

            if (['group_files', 'chat_files'].includes(this.active) && !this.isStudent)
                return null

            return widgets[this.active]
        },  
        tabsSettings() {
            return this.requestData.tabs.reduce(
                settings,
                (tab) => ({
                    ...settings,
                    [tab.name]: tab,
                }),
                {}
            );
        },
        workgroupLogoPath() {
            return this.requestData?.workgroup_logo?.path || null;
        },
        currentMenuRoutes() {
            let tabs = this.requestData?.tabs || [];

            tabs.forEach((item, index) => {
                if (item.onlyMobile && !this.isMobile) tabs.splice(index, 1);
                if (item.onlyDesktop && this.isMobile) tabs.splice(index, 1);

                if (item.child) {
                    item.children = item.child;
                }
                item.key = item.name;
            });

            if (this.id === "59449eea-4536-11ed-bca7-4216f3de51df") {
                tabs = tabs.concat({
                    name: "interest",
                    menuName: "interest",
                    icon: "interest",
                });
            }

            return tabs;
        },
        id() {
            const query = Object.assign({}, this.$route.query);
            if (query.viewProject) return this.$route.query.viewProject;
            return 0;
        },
        is_project() {
            return this.requestData.is_project;
        },
        widthDrawer() {
            if (this.windowWidth > 1200) return "95%";
            else return "100%";
        },
        showSidebar() {
            if (
                this.active === "kanban" ||
                this.active === "sprint" ||
        this.active === "gant" ||
        this.active === "tasks" ||
        this.active === "meetings" ||
        this.isMobile ||
        this.active === "calendar"
            )
                return false;
            else return true;
        },
        isMobile() {
            return this.$store.state.isMobile;
        },
        burgerWidget() {
            if (this.isMobile) return () => import("./modules/BurgerMobile.vue");
            return false;
        },
        tableMembers() {
            return this.$store.state.projects.tables?.[`project_members_${this.requestData.id}`]?.results
        }
    },
    methods: {
        ...mapActions({
            getInfos: "projects/getInfo",
            getRolesS: "projects/getRoles",
            joinGroupS: "projects/joinGroup",
            leaveGroupS: "projects/leaveGroup",
            finishedDate: "projects/finishedDate",
            addNewChat: "projects/addNewChat",
        }),
        ...mapMutations({
            setLoading: "projects/setLoading",
        }),
        afterVisibleChange(vis) {
            if(!vis) {
                if(this.pendingChatNavigation) {
                    const query = clearTabQuery({
                        ...this.$route.query,
                        filters: undefined,
                        tab: undefined,
                        viewProject: undefined
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
            return (
                ((isStudent || isFounder) &&
          item.name === "group_files" &&
          groupFileCount) ||
        ((isStudent || isFounder) &&
          item.name === "chat_files" &&
          chatFileCount)
            );
        },
        fileCount(name) {
            if (name === "group_files") {
                return this.groupFileCount;
            } else if (name === "chat_files") {
                return this.chatFileCount;
            } else {
                return 0;
            }
        },
        shareToChat() {
            let is_project = this.requestData.is_project;
            this.$store.commit("share/SET_SHARE_PARAMS", {
                model: "workgroups.WorkGroupModel",
                shareId: this.requestData.id,
                object: this.requestData,
                shareUrl: `${window.location.origin}/?viewProject=${this.requestData.id}`,
                shareTitle: `${
          is_project
              ? this.$t("project.project")
              : this.$t("project.group_share")
        } - ${this.requestData.name}`,
            });
        },
        deleteGroup() {
            this.$confirm({
                title: this.$t("project.warning"),
                content: this.$t("project.delete_confirm_text", {
                    type: this.is_project
                        ? this.$t("project.project_label")
                        : this.$t("project.group_label"),
                }),
                zIndex: 2200,
                cancelText: this.$t("project.close"),
                okText: this.$t("project.delete"),
                okType: "danger",
                onOk: () => {
                    return new Promise((resolve, reject) => {
                        this.$http
                            .post(`/work_groups/workgroups/${this.requestData.id}/delete/`)
                            .then(() => {
                                this.$message.success(
                  `${
                    this.is_project
                        ? this.$t("project.project_delete")
                        : this.$t("project.group_delete")
                  }`
                                );
                                eventBus.$emit("update_filter_workgroups.WorkgroupModel");
                                if (this.is_project) {
                                    eventBus.$emit("update_list_project");
                                    eventBus.$emit("project_deleted", this.requestData.id);
                                } else {
                                    eventBus.$emit("update_list_group");
                                }
                                this.close2();
                                resolve();
                            })
                            .catch((error) => {
                                errorHandler({error})
                                reject();
                            });
                    });
                },
                onCancel() {},
            });
        },
        updatePartisipants(users) {
            this.requestData.members_count = Array.isArray(users) ? users.length : users;
        },
        addToMembersList(users) {
            if (!Array.isArray(users) || !users.length) return

            const founderId = this.requestData?.founder?.member?.id
            const currentMembers = Array.isArray(this.requestData.workgroup_members)
                ? [...this.requestData.workgroup_members]
                : []

            const currentIds = new Set(
                currentMembers
                    .map(item => item?.member?.id)
                    .filter(Boolean)
            )

            const nextMembers = users
                .filter(user => user?.id && user.id !== founderId && !currentIds.has(user.id))
                .map(user => ({
                    id: `local_${user.id}`,
                    default_visor: false,
                    member: user,
                    member_visible: true,
                    membership_request_status: {
                        code: 'MEMBER-APPROVED',
                        name: 'Одобрена'
                    },
                    membership_role: {
                        code: 'MEMBER',
                        name: this.$t('project.participant')
                    }
                }))

            if (!nextMembers.length) return

            this.requestData.workgroup_members = currentMembers.concat(nextMembers)
        },
        chatAuthor() {
            this.pendingChatNavigation = {name: 'chat', query: {user: this.requestData.founder.id}}
            this.visible = false
        },
        openChat() {
            if(this.isMobile)
                this.pendingChatNavigation = {name: 'chat-body', params: {id: this.requestData.linked_chat}}
            else
                this.pendingChatNavigation = {name: 'chat', query: {chat_id: this.requestData.linked_chat}}
            this.visible = false
        },
        async createChat() {
            try {
                this.createChatLoading = true;
                const res = await this.addNewChat({
                    data: { with_chat: true },
                    id: this.id,
                });
                if (res?.chat_uid) {
                    const self = this;
                    this.requestData.with_chat = true;
                    this.requestData.linked_chat = res.chat_uid;
                    this.$success({
                        title: this.$t("project.chat_created"),
                        okText: this.$t("project.open_chat"),
                        okType: "success",
                        closable: true,
                        maskClosable: true,
                        cancelText: this.$t("project.close"),
                        onOk() {
                            if(self.isMobile)
                                self.pendingChatNavigation = {name: 'chat-body', params: {id: res.chat_uid}}
                            else
                                self.pendingChatNavigation = {name: 'chat', query: {chat_id: res.chat_uid}}
                            self.visible = false
                        },
                        onCancel() {},
                    });
                }
            } catch (error) {
                errorHandler({error})
            } finally {
                this.createChatLoading = false;
            }
        },
        getKey() {
            return Math.floor(Math.random() * 99999);
        },
        
        close2() {
            eventBus.$emit("update_workgroup_data");
            const query = clearTabQuery({
                ...this.$route.query,
                filters: undefined,
                tab: undefined,
                viewProject: undefined
            })
            this.$router.replace({ query })

            this.isFounder = false;
            this.isStudent = false;
            this.active = this.isMobile ? "about" : "news";
            this.activeMenu = [this.isMobile ? "about" : "news"];
            this.requestData = { social_links: [] };
            this.visible = false;
            this.joinInit = false
        },
        clearComponentState() {
            this.groupFileCount = 0
            this.chatFileCount = 0
            this.isFounder = false
            this.isStudent = false
            this.joinInit = false
            this.active = this.isMobile ? 'about' : 'news'
            this.activeMenu = [this.isMobile ? 'about' : 'news']
            this.requestData = { social_links: [] }
        },
        close(){
            const query = clearTabQuery({
                ...this.$route.query,
                filters: undefined,
                tab: undefined,
                viewProject: undefined
            })

            this.$router.replace({query})
            this.clearComponentState()
        },

        async getTabAttachments() {
            try {
                if (this.isStudent || this.isFounder) {
                    const groupAttachmentsCount = await this.$http(
            `attachments/${this.id}/aggregate/`
                    );
                    this.groupFileCount = groupAttachmentsCount.data.files;
                    if (this.requestData.with_chat) {
                        const chatAttachmentsCount = await this.$http(
              `attachments/${this.requestData.linked_chat_id}/aggregate/`
                        );
                        this.chatFileCount = chatAttachmentsCount.data.files;
                    }
                }
            } catch (e) {}
        },

        async startView() {
            try {
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
                this.loading = true;
                this.setLoading(true);
                if (this.id !== undefined) {
                    this.visible = true;
                    const res = await this.getInfos(this.id);
                    this.requestData = res;
                    await this.getRoles();
                    await this.getActions();
                    this.getTabAttachments();
                    this.joinInit = true
                }
            } catch (error) {
                if(error?.status === 404) {
                    this.$message.info(this.$t('project.not_found'))
                    this.visible = false
                } else {
                    if (error && error.detail) {
                        if (
                            error.detail === "Не найдено." ||
                error.detail === "Страница не найдена." ||
                error.detail ===
                "У вас недостаточно прав для выполнения данного действия."
                        ) {
                            this.$message.warning(this.$t("project.not_found"));
                            this.close();
                        } else {
                            this.$message.error(this.$t("project.error"));
                        }
                    } else {
                        this.$message.error(this.$t("project.error"));
                    }
                }
                console.log(error);
            } finally {
                this.loading = false;
                this.setLoading(false);
            }
        },
        async refreshProjectContext() {
            if (!this.id) return

            const res = await this.getInfos(this.id)
            this.requestData = res
            await this.getRoles()
            await this.getActions()
        },
        setRouterTab(val) {
            let query = JSON.parse(JSON.stringify(this.$route.query));
            query.tab = val;
            this.$router.push({ query }).catch((e) => {});
        },
        // Меню и переход на нужный таб
        handleClickMenu(e) {
            this.active = e.key;
            this.setRouterTab(e.key);
        },
        titleClick(e, item) {
            this.activeMenu = [item.mainPage];
            this.active = item.mainPage;
            this.setRouterTab(item.mainPage);
        },
        // Заершить продолжить проект
        finishProject(val) {
            this.$confirm({
                title: val ? this.$t('project.project_finish_message2') : this.$t('project.project_finish_message'),
                okText: this.$t('yes'),
                cancelText: this.$t('no'),
                onOk: async () => {
                    try {
                        if (val) {
                            this.finishedDate({ id: this.id, date: null });
                            this.requestData.finished = false;
                            this.requestData.finishedDate = null;
                            this.$message.success(this.$t('project.project_finish2'))
                        } else {
                            this.finishedDate({ id: this.id, date: this.$moment() });
                            this.requestData.finished = true;
                            this.requestData.finishedDate = this.$moment();
                            this.$message.success(this.$t('project.project_finish'))
                        }
                    } catch (error) {
                        errorHandler({error})
                    }
                }
            })
        },

        // Отправть запрос на вступление

        async joinGroup() {
            try {
                this.loadingjoin = true;
                await this.joinGroupS({ id: this.id, member_visible: true });
                this.$message.success(this.$t("project.you_partisipants"));
                this.isStudent = true;
                this.membersKey += 1;
                this.loadingjoin = false;
            } catch (error) {
                errorHandler({error})
            }
        },

        // Выйти из группы
        async leaveGroup() {
            try {
                this.loadingExit = true;
                await this.leaveGroupS(this.id);
                this.membersKey += 1;
                this.$message.warning(this.$t("project.you_not_member_group"));
                this.isStudent = false;
                this.loadingExit = false;
            } catch (error) {
                errorHandler({error})
            }
        },

        // Получение экшенов
        async getActions() {
            try {
                const { data } = await this.$http.get(`/work_groups/workgroups/${this.id}/action_info/`
                );
                if (data?.actions) {
                    this.actions = data.actions;
                }
            } catch (e) {
                console.log(e);
            }
        },

        // Получение ролей
        async getRoles() {
            try {
                const res = await this.getRolesS(this.id);
                if (res[0].id) {
                    this.roles = res;
                    res.forEach((item) => {
                        if (['FOUNDER', 'MODERATOR'].includes(item.membership_role.code)) {
                            this.isFounder = true; 
                            this.isStudent = true;
                        } else if (['MEMBER', 'ORG-COORDINATOR'].includes(item.membership_role.code)) {
                            this.isFounder = false; 
                            this.isStudent = true;
                        }
                    });
                }
            } catch (error) {
                this.$message.error(this.$t("project.error") + error);
            }
        },

        // Кнопка редактировать группу
        goToEdit() {
            eventBus.$emit('edit_project_modal', { id: this.id, source: 'details' })
        },

        async handleProjectUpdated(id) {
            if (String(id) !== String(this.id) || !this.visible) {
                return
            }

            await this.startView()
        },

        changeTab(tabName) {
            this.active = tabName;
            this.activeMenu = [tabName];
            this.setRouterTab(tabName);
        },
    },
    created() {
        if (this.isMobile) {
            this.defaultActive = ["about"];
            this.activeMenu = ["about"];
            this.active = "about";
        }

        const query = this.$route.query;
        if (query.viewProject) this.startView();
        eventBus.$on('project_updated', this.handleProjectUpdated)
    },
    beforeDestroy() {
        eventBus.$off('project_updated', this.handleProjectUpdated)
    },
};
</script>

<style>
@media (max-width: 800px) {
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

<style lang="scss" scoped>
.module_menu{
    &::v-deep{
        .ant-menu-item{
            color: #888888;
            &.ant-menu-item-selected{
                color: var(--text);
                border-color: #fd9907;
            }
            &:hover{
                color: var(--text);
            }
            &:not(.ant-menu-item-selected) {
                &:hover{
                    border-color: transparent;
                }
            }
        }
        .ant-menu-submenu{
            color: #888888;
            &:hover{
                color: var(--text);
                .ant-menu-submenu-title{
                    color: var(--text);
                }
            }
            &:not(.ant-menu-item-selected) {
                &:not(.ant-menu-submenu-active) {
                    &:hover{
                        border-color: transparent;
                    }
                }
            }
            &.ant-menu-submenu-active{
                border-color: transparent;
            }
            &.ant-menu-submenu-selected{
                color: var(--text);
                border-color: #fd9907;
                .ant-menu-submenu-title{
                    color: var(--text);
                }
            }
        }
    }
}
::v-deep.workgroup_drawer_collapse {
  margin: 0 -15px;
  .ant-collapse-header {
    font-weight: 500;
  }
  .ant-collapse-content-box {
    padding-top: 5px;
    padding: 15px;
  }
}

::v-deep.group_drawer {
  .about_card_mobile {
    border: none;
    .ant-card-head {
      padding: 0;
      border: none;
    }
    .ant-card-body {
      padding: 0;
    }
  }
  .group_content {
    overflow-y: auto;
    &.mobile_wrap {
      height: calc(100% - 96px);
    }
    &.full_wrap {
      height: calc(100% - 104px);
    }
    .group_cont_wrap {
      // padding: 30px 30px 20px 30px;
      &.grp_calendar_page,
      &.grp_kanbam_page,
      &.grp_gant_page {
        height: 100%;
        .ant-row-flex {
          height: 100%;
        }
        .ant-col {
          height: 100%;
        }
      }
      &.grp_calendar_page,
      &.grp_kanbam_page {
        padding: 0px;
      }
    }
  }
  .ant-drawer-header {
    display: none;
  }
  .ant-drawer-wrapper-body,
  .ant-drawer-content {
    overflow: hidden;
  }
  .ant-drawer-body {
    height: 100%;
    padding: 0px;
    overflow-y: hidden;
    .drawer_body {
      height: 100%;
    }
  }
  .group_header {
    .ant-avatar {
      border: 1px solid var(--border2);
    }
  }
}
::v-deep.group_drawer_mobile {
  .group_content {
    .group_cont_wrap {
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
