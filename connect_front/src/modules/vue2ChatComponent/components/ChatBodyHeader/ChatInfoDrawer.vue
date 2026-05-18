<template>
    <DrawerTemplate
        placement="right"
        class="chat_info_drawer"
        :width="drawerWidth"
        v-model="visible"
        destroyOnClose
        @afterVisibleChange="afterVisibleChange"
        @close="visible = false">
        <template #title>
            <div class="head_wrap flex items-center justify-between truncate w-full">
                <div class="flex items-center truncate w-full">
                    <div class="awatar_wrapper pr-2">
                        <template v-if="activeChat.is_public">
                            <a-avatar
                                v-if="activeChat.is_support"
                                class="chat_info_drawer__avatar--group"
                                src="/img/support_avatar.jpg"
                                :size="32" />
                            <a-avatar
                                v-else
                                class="chat_info_drawer__avatar--group"
                                :style="activeChat.color ? `backgroundColor:${activeChat.color}!important;color:#fff!important;` : 'backgroundColor: #cccccc'"
                                :size="32">
                                {{ avatarText }}
                            </a-avatar>
                        </template>
                        <a-avatar
                            v-else
                            :size="32"
                            :style="activeChat.color ? `backgroundColor:${activeChat.color}!important;color:#fff!important;` : 'backgroundColor: #cccccc'"
                            :src="activeChat.recipient && activeChat.recipient.avatar && activeChat.recipient.avatar.path ? activeChat.recipient.avatar.path : null">
                            {{ avatarText }}
                        </a-avatar>
                    </div>
                    <div class="name truncate w-full">
                        <div class="truncate w-full">{{ chatName }}</div>
                        <div v-if="activeChat && activeChat.is_public && !activeChat.is_support" class="member">{{ chatMember }}</div>
                    </div>
                </div>
                <div v-if="isUserSupport" class="actions">
                    <template v-if="activeChat && activeChat.is_public">
                        <template v-if="isModerator || isAuthor">
                            <a-button
                                v-tippy="!isMobile ? { inertia : true, duration : '[600,300]'} : { touch: false }"
                                :content="!isMobile && $t('chat.edit')"
                                @click="changeChatName()"
                                icon="fi-rr-edit"
                                shape="circle"
                                ghost
                                flaticon
                                type="ui" />

                            <UserDrawer
                                id="add_chat_users"
                                :metadata="{ key: 'users', value: addUsersForm.metadata }"
                                :changeMetadata="changeMetadata"
                                :submitHandler="addUsers"
                                v-model="addUsersForm.users"
                                multiple
                                inputSize="large"
                                :title="$t('chat.add_user')"
                                @change="userChange">
                                <template #openButton>
                                    <a-button
                                        v-tippy="!isMobile ? { inertia : true, duration : '[600,300]'} : { touch: false }"
                                        :content="!isMobile && $t('chat.add_user')"
                                        icon="fi-rr-user-add"
                                        shape="circle"
                                        class="ml-1"
                                        ghost
                                        flaticon
                                        type="ui" />
                                </template>
                            </UserDrawer>

                            <a-button
                                v-if="isAuthor"
                                v-tippy="!isMobile ? { inertia : true, duration : '[600,300]'} : { touch: false }"
                                :content="!isMobile && $t('chat.remove')"
                                @click="showDeleteModal()"
                                icon="fi-rr-trash"
                                shape="circle"
                                class="ml-1"
                                ghost
                                flaticon
                                type="ui" />
                        </template>
                    </template>
                </div>
            </div>
        </template>
        <template #tabs>
            <a-tabs v-model="tab" class="header_tab" :class="isMobile && 'px-3'" :showContent="false">
                <a-tab-pane v-if="isUserSupport" key="members">
                    <span slot="tab">
                        {{$t('chat.participants')}}
                    </span>
                </a-tab-pane>
                <a-tab-pane key="task_list">
                    <span slot="tab">
                        <div class="flex items-center">
                            {{$t('chat.chat_tasks')}} <a-badge class="ml-1" :count="taskCount" />
                        </div>
                    </span>
                </a-tab-pane>
                <a-tab-pane key="chat_files">
                    <span slot="tab">
                        <div class="flex items-center">
                            {{$t('chat.chat_files')}} <a-badge class="ml-1" :count="fileCount" />
                        </div>
                    </span>
                </a-tab-pane>
                <a-tab-pane v-if="projectId" key="project_files">
                    <span slot="tab">
                        <div class="flex items-center">
                            {{$t('chat.project_files')}} <a-badge class="ml-1" :count="projectFileCount" />
                        </div>
                    </span>
                </a-tab-pane>
                <a-tab-pane key="help_desk_list">
                    <span slot="tab">
                        <div class="flex items-center">
                            {{$t('chat.ticket_tasks')}} <a-badge class="ml-1" :count="ticketCount" />
                        </div>
                    </span>
                </a-tab-pane>
            </a-tabs>
        </template>
        <a-tabs v-if="visible" class="body_tabs" :activeKey="tab" :showBar="false">
            <a-tab-pane v-if="isUserSupport" key="members" tab="">
                <div v-if="loading" class="flex justify-center">
                    <a-spin />
                </div>
                <div
                    v-if="members && members.results"
                    class="chat_members">
                    <div
                        v-for="item in members.results"
                        :key="item.id"
                        class="item">
                        <UserCard
                            :userItem="item.user"
                            :showUserInfo="activeChat.is_public"
                            :info="item" />
                    </div>
                </div>
                <infinite-loading
                    @infinite="getMembers"
                    :identifier="activeChat.chat_uid"
                    v-bind:distance="20">
                    <div slot="spinner"></div>
                    <div slot="no-more"></div>
                    <div slot="no-results"></div>
                </infinite-loading>
            </a-tab-pane>
            <a-tab-pane key="chat_files" tab="" class="padding_tab">
                <component
                    :active="tab"
                    :is="activeTab"
                    :id="activeChat.chat_uid"
                    :sourceId="fileSourceId"
                    useIconButton
                    :isFounder="true"
                    :isStudent="true" />
            </a-tab-pane>
            <a-tab-pane v-if="projectId" key="project_files" tab="" class="padding_tab">
                <component
                    :active="tab"
                    :is="activeTab"
                    :id="activeChat.chat_uid"
                    :sourceId="fileSourceId"
                    useIconButton
                    :isFounder="true"
                    :isStudent="true" />
            </a-tab-pane>
            <a-tab-pane key="task_list" tab="" class="padding_tab flex flex-col">
                <component
                    :active="tab"
                    :is="activeTab"
                    :id="activeChat.chat_uid"
                    :sourceId="fileSourceId"
                    :activeChat="activeChat"
                    :isFounder="true"
                    :isStudent="true" />
            </a-tab-pane>
            <a-tab-pane key="help_desk_list" tab="" class="padding_tab flex flex-col">
                <HelpDeskTable :isUserSupport="isUserSupport" style="height: 75vh;" :chat_uid="activeChat.chat_uid"/>
            </a-tab-pane>
        </a-tabs>

        <a-modal
            :title="$t('chat.change_chat_name')"
            @cancel="changeName = false"
            destroyOnClose
            :visible="changeName">
            <a-form-model
                ref="nameForm"
                :model="form"
                :rules="rules">
                <a-form-model-item ref="name" prop="name">
                    <div class="textarea_wrapper">
                        <a-textarea
                            v-model="form.name"
                            class="textarea_input"
                            ref="descriptionTextArea"
                            :maxLength="descriptionMaxCount"
                            :placeholder="$t('chat.press_chat_name')"
                            @input="adjustHeight" />
                        <div class="description_length">
                            {{form.name.length}}/{{ descriptionMaxCount }}
                        </div>
                    </div>
                </a-form-model-item>
            </a-form-model>
            <template slot="footer">
                <div :class="!isMobile && 'flex items-center justify-end'" class="w-full">
                    <a-button
                        key="back"
                        :block="isMobile ? true : false"
                        type="ui"
                        ghost
                        :size="isMobile ? 'large' : 'default'"
                        @click="changeName = false">
                        {{$t('chat.close')}}
                    </a-button>
                    <a-button
                        :loading="nameLoading"
                        key="submit"
                        :class="isMobile && 'mt-2'"
                        :size="isMobile ? 'large' : 'default'"
                        :block="isMobile ? true : false"
                        :style="!isMobile && 'margin-left: 5px;'"
                        type="primary"
                        @click="submitForm()">
                        {{$t('chat.save')}}
                    </a-button>
                </div>
            </template>
        </a-modal>
        <!--<AddMemberSidebar/>-->
    </DrawerTemplate>
</template>

<script>
import { mapMutations, mapState } from 'vuex'
import { declOfNum } from '../../utils'
import { mapActions, mapGetters } from 'vuex'
import { errorHandler } from '@/utils/index.js'
import ChatEventBus from '../../utils/ChatEventBus'
export default {
    name: "ChatInfoDrawer", 
    components: {
        HelpDeskTable: () => import("../ChatSidebar/HelpDeskTable.vue"),
        InfiniteLoading: () => import('vue-infinite-loading'),
        UserCard: () => import('../UserCard.vue'),
        //AddMemberSidebar: () => import('../Sidebar/AddMemberSidebar.vue'),
        UserDrawer: () => import('@apps/DrawerSelect/index.vue'),
        DrawerTemplate: () => import("@/components/DrawerTemplate.vue")
    },
    computed: {
        ...mapState({
            activeChat: state => state.chat.activeChat,
            sidebarInfo: state => state.chat.sidebarInfo,
            user: state => state.user.user,
            isMobile: state => state.isMobile
        }),
        ...mapGetters({
            chatMembers: 'chat/chatMembers'
        }),
        isUserSupport() {
            if(this.activeChat?.is_support) {
                return this.user?.is_support
            }
            return true
        },
        chatName() {
            if(this.activeChat) {
                if(this.user.is_support) {
                    return this.activeChat.name
                } else {
                    if(this.activeChat.is_support)
                        return this.$t('chat.support_name', { name: this.appName })
                }
                return this.activeChat.name
            }
            return ''
        },
        avatarText() {
            if(this.activeChat) {
                if(this.activeChat.is_public) {
                    return this.activeChat.name.charAt(0).toUpperCase()
                } else {
                    const n = this.activeChat.name.split(' ')
                    return `${n[0].charAt(0).toUpperCase()}${n[1] ? n[1].charAt(0).toUpperCase() : ''}${n[2] ? n[2].charAt(0).toUpperCase() : ''}`
                }
            }
            return ''
        },
        visible: {
            get() {
                if(this.sidebarInfo && this.activeChat && this.activeChat.is_public)
                    this.$socket.client.emit('chat_status_user', {chat_uid: this.activeChat.chat_uid})
                return this.sidebarInfo
            },
            set(val) {
                this.$store.commit('chat/TOGGLE_INFO_SIDEBAR', val)
            }
        },
        loading: {
            get(){
                return this.$store.state.chat.loadingInfoChat
            },
            set(val){
                this.$store.commit('chat/SET_LOADING_INFOCHAT', val)
            }
        },
        activeTab() {
            if(this.tab === 'task_list')
                return () => import('../ChatSidebar/Tasks.vue')
            if(['project_files', 'chat_files'].includes(this.tab))
                return () => import('@apps/vue2Files')

            return null
        },
        fileSourceId() {
            switch (this.tab) {
            case 'chat_files':
                return this.activeChat.id || this.activeChat.uid
            case 'project_files':
                return this.activeChat.workgroup.uid
            default:
                return 0
            }
        },
        projectId() {
            return this.activeChat?.workgroup?.uid
        },
        chatMember() {
            return this.activeChat.member_count + ' ' + declOfNum(this.activeChat.member_count, [this.$t('chat.participant'), this.$t('chat.participant2'), this.$t('chat.participant3')])
        },
        members() {
            return this.chatMembers(this.activeChat.chat_uid)
        },
        author() {
            return this.activeChat.chat_author
        },
        isAuthor() {
            if(this.author?.id === this.user.id)
                return true
            else
                return false
        },
        taskCount() {
            return this.tCount?.total
        },
        windowWidth() {
            return this.$store.state.windowWidth
        },
        isModerator() {
            if (typeof this.activeChat?.is_moderator === 'string') {
                return this.activeChat.is_moderator.trim().toLowerCase() === 'true'
            }

            return Boolean(this.activeChat?.is_moderator)
        },
        drawerWidth() {
            if(this.isMobile) {
                return '100%'
            } else {
                return 560
            }
        },
        fileCount() {
            return this.fileAggregate?.files
        },
        projectFileCount() {
            return this.projectFileAggregate?.files
        },
    },
    data(){
        return{
            addUsersForm: {
                metadata: { users: [] },
                users: []
            },
            appName: process.env.VUE_APP_NAME || 'Gos24.КОННЕКТ',
            changeName: false,
            nameLoading: false,
            rules: {
                name: [
                    { required: true, message: this.$t('chat.field_require'), trigger: 'blur' },
                    { min: 3, max: 120, message: this.$t('chat.chat_name_rules', {min: 3, max: 120}), trigger: 'blur' }
                ]
            },
            form: {
                name: ''
            },
            tab: 'members',
            fileAggregate: null,
            projectFileAggregate: null,
            tCount: 0,
            ticketCount: 0,
            descriptionMaxCount: 120
        }
    },
    watch: {
        activeChat(data) {
            if(!data) {
                this.visible = false
            }
        }
    },
    methods: {
        ...mapActions({
            getChatMembers: 'chat/getChatMembers',
        }),
        ...mapMutations({
            renameChat: "chat/RENAME_CHAT",
            deleteChatFromStore: 'chat/DELETE_CHAT'
        }),
        adjustHeight(event) {
            const textarea = event.target;
            textarea.style.height = 'auto'
            const maxHeight = window.innerHeight - 100
            textarea.style.height = `${Math.min(textarea.scrollHeight, maxHeight)}px`
        },
        clearAddUserForm() {
            this.addUsersForm = {
                metadata: { users: [] },
                users: []
            }
        },
        changeMetadata({key, value}) {
            this.$set(this.addUsersForm.metadata, key, value)
        },
        userChange() {
            this.addUsers()
        },
        addUsers() {
            if (this.addUsersForm.users.length === 0)
                return 0

            const chat = {
                members: [],
                chat_uid: this.activeChat.chat_uid
            }
            const chatMembers = this.addUsersForm.users.map(user => ({ user: user.id, is_moderator: false }))
            chat.members.push(...chatMembers)

            if (this.addUsersForm.users.length > 1) {
                chat.is_public = true
                chat.name = this.chatName
            } else {
                chat.name = chat.members[0].user
            }

            try {
                this.$socket.client.emit('chat_add_user', chat)
                this.clearAddUserForm()
            } catch(error) {
                errorHandler({error})
            }
        },
        afterVisibleChange(vis) {
            if(vis) {
                this.getFileCount()
                this.getTaskCount()
                this.getTicketCount()
                if(!this.isUserSupport)
                    this.tab = 'task_list'
                if(this.projectId)
                    this.getProjectFileCount()
            } else {
                this.fileAggregate = null
                this.projectFileAggregate = null
                this.tCount = 0
                this.tab = 'members'
                ChatEventBus.$emit('inputFocus')
            }
        },
        changeChatName() {
            // if(this.activeChat.chat_author.id === this.user.id) {
            this.form.name = JSON.parse(JSON.stringify(this.activeChat.name))
            this.changeName = true
            // }
        },
        async getFileCount() {
            try {
                const { data } = await this.$http.get(`attachments/${this.activeChat.id}/aggregate/`)
                if(data)
                    this.fileAggregate = data
            } catch(error) {
                errorHandler({error, show: false})
            }
        },
        async getProjectFileCount() {
            try {
                const { data } = await this.$http.get(`attachments/${this.projectId}/aggregate/`)
                if(data)
                    this.projectFileAggregate = data
            } catch(error) {
                errorHandler({error, show: false})
            }
        },
        async getTaskCount() {
            try {
                const { data } = await this.$http.get('/chat/task/list/', {
                    params: {
                        chat: this.activeChat.chat_uid,
                        task_type: 'task'
                    }
                })
                if(data)
                    this.tCount = data
            } catch(error) {
                errorHandler({error, show: false})
            }
        },
        async getTicketCount() {
            try {
                const { data } = await this.$http.get('/help_desk/tickets/for_client/list/', {
                    params: {
                        chat: this.activeChat.chat_uid,
                    }
                })
                if(data)
                    this.ticketCount = data.count
            } catch(error) {
                errorHandler({error, show: false})
            }
        },
        submitForm() {
            this.$refs.nameForm.validate(async valid => {
                if (valid) {
                    try {
                        this.nameLoading = true
                        this.$socket.client.emit('chat_rename', {chat_uid: this.activeChat.chat_uid, chat_name: this.form.name})
                        this.renameChat({chat_uid: this.activeChat.chat_uid, chat_name: this.form.name})

                        this.changeName = false
                        this.$message.success(this.$t('chat.name_changed'))

                    } catch(error) {
                        errorHandler({error})
                    } finally {
                        this.nameLoading = false
                    }
                } else
                    return false
            })
        },
        showDeleteModal() {
            const self = this
            this.$confirm({
                title: this.$t('chat.chat_delete'),
                content: this.$t('chat.chat_delete_text'),
                okText: this.$t('chat.yes'),
                okType: 'danger',
                cancelText: this.$t('chat.no'),
                async onOk() {
                    await self.deleteChat()
                },
                onCancel() {

                }
            })
        },
        async deleteChat() {
            try {
                this.$socket.client.emit('chat_delete', { chat_uid: this.activeChat.chat_uid });
                this.visible = false;
                this.deleteChatFromStore(this.activeChat.chat_uid);
                this.$message.success(this.$t('chat.deleted_success'));

                if (this.isMobile) {
                    this.$router.push({
                        name: 'chat-contact'
                    });
                } else {
                    this.$router.replace({ query: {} });
                }
            } catch (error) {
                errorHandler({error})
            }
        },
        async getMembers($state) {
            try{
                this.loading = true
                if(!this.members || this.members.results.length !== this.members?.count) {
                    try {
                        const res = await this.getChatMembers({chat: this.activeChat.chat_uid})
                        if(res.next) {
                            $state.loaded()
                        } else {
                            $state.complete()
                        }
                    } catch(show) {
                        errorHandler({error, show: false})
                    }
                } else {
                    $state.complete()
                }
            }catch(e){}
            finally{
                this.loading = false
            }
        },

        addUser(){
            this.$store.commit('chat/SET_ADD_MEMBER_POPUP', true)
        },

    }
}
</script>

<style lang="scss" scoped>
.body_tabs{
    &::v-deep{
        > .ant-tabs-bar{
            display: none;
        }
        .kanban-card{
            cursor: default;
        }
    }
}
.header_tab{
    &::v-deep{
        > .ant-tabs-content{
            display: none;
        }
    }
}
.textarea_wrapper{
    position: relative;
    .description_length{
        position: absolute;
        bottom: 10px;
        right: 10px;
        z-index: 5;
        color: #888;
        font-size: 13px;
        line-height: 13px;
    }
    .textarea_input{
        margin-bottom: 0px!important;
        padding-bottom: 25px;
    }
}
.head_wrap{
    .chat_info_drawer__avatar--group{
        border-radius: 12px !important;
    }
    ::v-deep(.chat_info_drawer__avatar--group.ant-avatar),
    ::v-deep(.chat_info_drawer__avatar--group img){
        border-radius: 12px !important;
    }
    .member{
        font-size: 12px;
        line-height: 13px;
        color: var(--gray);
    }
    .actions{
        display: flex;
        align-items: center;
    }
}
</style>
