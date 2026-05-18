<template>
    <a-drawer
        :title="$t('chat.create_group_chat')"
        placement="right"
        class="create_chat_drawer"
        :width="windowWidth > 960 ? 400 : '100%'"
        :class="isMobile && 'mobile'"
        :zIndex="99999999"
        :visible="visible"
        @close="visible = false">
        <div v-if="!isMobile" class="drawer_footer relative">
            <a-input
                :disabled="disabledInput"
                class="w-full input_name"
                v-model="chatName"
                size="large"
                :placeholder="$t('chat.chat_name')" />
            <a-button
                :loading="createLoader"
                @click="createChat()"
                class="absolute"
                :disabled="disabledBtn"
                type="primary"
                flaticon
                shape="circle"
                icon="fi-rr-plus" />
        </div>
        <div class="contact_search">
            <a-input-search 
                v-model="search"
                :placeholder="$t('chat.contact_name_placeholder')"
                class="w-full"
                @change="onSearchHandler" />
        </div>
        <div class="drawer_scroll">
            <RecycleScroller
                :items="contacts"
                size-field="height"
                :buffer="200"
                class="scroll_list"
                emitUpdate
                :item-size="53"
                key-field="id">
                <template #before>
                    <a-alert 
                        class="mt-0"
                        :message="$t('chat.group_chat_info_message')"
                        banner
                        type="info" />
                </template>
                <template #default="{ item }">
                    <UserCard 
                        checkBoxMode 
                        class="cursor-pointer"
                        :userItem="item"  />
                </template>
                <template #after>
                    <infinite-loading
                        ref="create_chat_inf"
                        @infinite="getContactsList" 
                        v-bind:distance="50" 
                        :identifier="visible+search">
                        <div slot="spinner"> <a-spin
                            size="small"
                            style="margin-top: 10px;" /></div>
                        <div slot="no-more"></div>
                        <div slot="no-results"></div>
                    </infinite-loading>
                </template>
            </RecycleScroller>
        </div>
        <div v-if="isMobile" class="drawer_footer relative">
            <a-input
                :disabled="disabledInput"
                class="w-full input_name"
                v-model="chatName"
                size="large"
                :placeholder="$t('chat.chat_name')" />
            <a-button
                :loading="createLoader"
                @click="createChat()"
                class="absolute"
                :disabled="disabledBtn"
                type="primary"
                flaticon
                shape="circle"
                icon="fi-rr-plus" />
        </div>
    </a-drawer>
</template>

<script>
import { mapState} from 'vuex'
import UserCard from './UserCard'
import InfiniteLoading from 'vue-infinite-loading'
import eventBus from '@/utils/eventBus'
import { RecycleScroller } from 'vue-virtual-scroller'
import 'vue-virtual-scroller/dist/vue-virtual-scroller.css'
let timeout;
export default {
    name: "ChatCreate",
    components: {
        UserCard,
        InfiniteLoading,
        RecycleScroller
    },
    computed: {
        visible: {
            get() {
                return this.$store.state.chat.createChat
            },
            set(val) {
                this.$store.commit('chat/TOGGLE_CREATE_CHAT', val)
            }
        },
        ...mapState({
            activeChat: state => state.chat.activeChat,
            contacts: state => state.chat.contactList,
            allContactStatus: state => state.chat.allContactStatus,
            selectedContacts: state => state.chat.selectedContacts,
            contactListNext: state => state.chat.contactListNext,
            moderate: state => state.chat.moderate,
            windowWidth: state => state.windowWidth,
            isMobile: state => state.isMobile,
            user: state => state.user.user
        }),
        disabledBtn() {
            if(this.selectedContacts.length > 1 && this.chatName.length)
                return false
            else
                return true
        },
        disabledInput() {
            if(this.selectedContacts.length > 1)
                return false
            else
                return true
        },
    },
    data() {
        return {
            loading: false,
            createLoader: false,
            page: 0,
            chatName: '',
            search: ''
        }
    },
    methods: {
        onSearchHandler() {
            clearTimeout(timeout)
            if(this.search?.length > 1 || !this.search?.length) {
                timeout = setTimeout(() => {
                    this.$store.commit('chat/SET_CONTACT_LIST_PAGE', 0)
                    this.$store.commit('chat/CLEAR_CONTACT_LIST')

                    this.$nextTick(() => {
                        this.$refs['create_chat_inf'].stateChanger.reset()
                    })
                }, 700)
            }
        },
        async createChat() {
            if(this.chatName.length >= 3) {
                let chat = {
                    members: [],
                    name: '',
                    is_public: false
                }
                this.selectedContacts.forEach(item => {
                    let member = {user: item}
                    if(this.selectedContacts.length > 1) {
                        if(this.moderate.length) {
                            const find = this.moderate.find(elem => elem === item)
                            if(find)
                                member.is_moderator = true
                            else
                                member.is_moderator = false
                        } else {
                            member.is_moderator = false
                        }
                    }
                    chat.members.push(member)
                })
                if(this.selectedContacts.length > 1) {
                    chat.is_public = true
                    chat.name = this.chatName
                } else
                    chat.name = chat.members[0].user
                try {
                    this.createLoader = true
                    await this.createNewChat(chat)
                    setTimeout(() => {
                        this.$store.commit('chat/setSidebarActiveTab', 1)
                        if(this.activeChat) 
                            this.setQueryId(this.activeChat)  
                        this.clearPopup()
                        this.visible = false
                    }, 300);
                   
                } catch(e) {
                } finally {
                    this.createLoader = false
                }
            } else {
                /*this.$vs.notify({
                    text: this.$t('chat_name_min'),
                    color: 'warning'
                })*/
            }
        },
        createNewChat(chat) {
            this.$socket.client.emit("create", chat)
            eventBus.$emit('update_list_share_drawer')
        },
      
        setQueryId(data) {
            if(this.isMobile) {
                this.$router.push({
                    name: 'chat-body',
                    params: {
                        id: data.chat_uid
                    }
                })
            } else {
                let query = Object.assign({}, this.$route.query)
                if (query?.chat_id !== data.chat_uid) {
                    query.chat_id = data.chat_uid
                    this.$router.push({ query })
                }
            }
        },
        clearPopup() {
            this.chatName = ''
            this.$store.commit('chat/SET_SELECTED_CONTACTS', [])
            this.$store.commit('chat/SET_MODERATE', [])
            this.popupActive = false
        },
        async getContactsList($state = null) {
            if(!this.loading && this.visible && this.contactListNext) {
                try {
                    this.loading = true
                  
                    this.page = this.page+1
                    const res = await this.$store.dispatch('chat/getSidebarContact', {
                        all: true, 
                        search: this.search,
                        user: this.user
                    })
                    if(!res.next) {
                        if($state)
                            $state.complete()
                    } else {
                        if($state)
                            $state.loaded()
                    }
                } catch(e) {
                    console.error(e)
                } finally {
                    this.loading = false
                }
            } else {
                if($state)
                    $state.complete()
            }
        }
    }
}
</script>

<style lang="scss">
.create_chat_drawer{
    .ant-drawer-wrapper-body,
    .ant-drawer-content{
        overflow: hidden;
    }
    .ant-drawer-body{
        padding: 0px;
        height: calc(100% - 40px);
    }
    .contact_search{
        border-bottom: 1px solid var(--border2);
        input{
            &.ant-input{
                border-radius: 0px;
                border: 0px;
                height: 40px;
            }
        }
    }
    .drawer_scroll{
        height: calc(100% - 80px);
        overflow: hidden;
        .scroll_list{
            height: 100%;
        }
    }
    .drawer_footer{
        border-bottom: 1px solid var(--border2);
        input{
            &.ant-input{
                border-radius: 0px;
                border: 0px;
            }
        }
        .ant-btn{
            right: 10px;
            top: 3px;
        }
    }
    &.mobile{
        .drawer_scroll{
            height: calc(100% - 88px);
        }
        .drawer_footer{
            height: 48px;
            border-top: 1px solid var(--border2);
            border-bottom: 0px;
            .ant-input-lg{
                height: 48px;
            }
            .ant-btn{
                top: 5px;
            }
            .input_name{
                padding-right: 50px;
            }
        }
    }
}
</style>