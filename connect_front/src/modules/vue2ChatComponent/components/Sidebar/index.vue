<template>
    <div class="chat_aside">
        <div class="hfl aside_wrapper">
            <Header />
            <div v-show="!searchStart" class="chat_aside__body" :style="{'--tab-w': tabWidth}">
                <a-tabs v-model="activeTab">
                    <a-tab-pane :key="1">
                        <span slot="tab" class="sidebar_tab_label" :title="$t('chat.chats')">
                            <i class="fi fi-rr-comments mr-1"></i>
                            <span class="sidebar_tab_text">{{ $t('chat.chats') }}</span>
                        </span>
                        <ChatList />
                    </a-tab-pane>
                    <a-tab-pane :key="2">
                        <span slot="tab" class="sidebar_tab_label" :title="$t('chat.contacts')">
                            <i class="fi fi-rr-comment-user mr-1"></i>
                            <span class="sidebar_tab_text">{{ $t('chat.contacts') }}</span>
                        </span>
                        <ContactList />
                    </a-tab-pane>

                    <!-- Показываем только если есть контакты HelpDesk -->
                    <a-tab-pane v-if="hasHelpDesk" :key="3">
                        <span slot="tab" class="sidebar_tab_label" :title="$t('chat.сonsultants')">
                            <i class="fi fi-rr-comment-alt-dots mr-1"></i>
                            <span class="sidebar_tab_text" style="max-width: 80px;">{{ $t('chat.сonsultants') }}</span>
                        </span>
                        <ChatHelpDeskList />
                    </a-tab-pane>
                </a-tabs>
            </div>
            <div v-if="searchStart" class="search_res">
                <div
                    v-for="(item) in listSearch"
                    :key="`chat_${item.id}`"
                    class="sidebar_item"
                    @click="clearSearch(item)">
                    <ChatContact
                        v-if="item.type === 'chat.ChatModel'"
                        :chat="item" />
                    <UserCard
                        v-else
                        :select="true"
                        :userItem="item"/>
                </div>
                <a-empty :description="$t('chat.empty')" class="mt-4" v-show="listSearch.length === 0 && !searchLoading" />
                <a-spin  v-show="searchLoading"  style="margin-top: 15px; margin-left: 46%" />
            <!-- <infinite-loading
                @infinite="getListSearch"
                v-bind:distance="20">
                <div slot="spinner">

                </div>
                <div slot="no-more"></div>
                <div slot="no-results"></div>
            </infinite-loading> -->

            </div>

        </div>
    </div>
</template>

<script>
import {mapState, mapMutations, mapActions} from 'vuex'
import { errorHandler } from '@/utils/index.js'
export default {
    name: "ChatSidebar",
    components: {
        ContactList: () => import('./ContactList'),
        ChatList: () => import('./ChatList'),
        Header: () => import('./Header'),
        ChatContact: () => import('../ChatContact.vue'),
        ChatHelpDeskList: () => import("./ChatHelpDeskList.vue"),
        UserCard: () => import('../UserCard.vue')
    },
    computed: {
        ...mapState({
            listSearch: state=> state.chat.searchResult,
            searchStart: state=> state.chat.searchStart,
            chatList: state => state.chat.chatList,
            isMobile: state => state.isMobile,

            // добавили список helpdesk из стора
            helpDeskList: state => state.chat.helpDeskList,
            helpDeskPage: state => state.chat.helpDeskPage
        }),
        isStandaloneChatWindow() {
            return this.$route?.name === 'chat-window'
        },
        hasSeededStandaloneHelpDeskList() {
            return this.isStandaloneChatWindow && this.helpDeskPage > 0 && this.helpDeskList.length > 0
        },
        // индикатор наличия контактов HelpDesk
        hasHelpDesk() {
            return Array.isArray(this.helpDeskList) && this.helpDeskList.length > 0
        },
        // ширина вкладок: 3 вкладки = 33.333%, 2 вкладки = 50%
        tabWidth() {
            return this.hasHelpDesk ? '33.3333%' : '50%'
        },
        searchLoading:{
            get(){
                return this.$store.state.chat.searchLoading
            },

            set(value){
                this.$store.commit('chat/setValueState', {name: 'searchLoading', value})
            }
        },
        activeTab:{
            get(){
                return this.$store.state.chat.sidebarActiveTab
            },

            set(val){
                this.$store.commit('chat/setSidebarActiveTab', val)
            }
        },
    },
    async mounted() {
        if (this.hasSeededStandaloneHelpDeskList) return

        try {
            await this.getSidebarHelpDesk({ all: false })
        } catch (error) {
            errorHandler({ error, show: false })
        }
    },
    watch: {
        // если вкладка консультантов исчезла, а активна была 3-я — вернёмся на 1-ю
        hasHelpDesk(newVal) {
            if (!newVal && this.activeTab === 3) {
                this.activeTab = 1
            }
        }
    },
    methods: {
        ...mapActions({
            getSidebarHelpDesk: 'chat/getSidebarHelpDesk',
            getCurrentChat: 'chat/getCurrentChat',
            getPrivateChat: 'chat/getPrivateChat',
        }),
        ...mapMutations({
            createVirtualChat: 'chat/CREATE_VIRTUAL_CHAT',
        }),
        async createChat(item){
            const privateChat = await this.getPrivateChat(item.id)
            const isStandaloneChatWindow = this.$route?.name === 'chat-window'

            if(!privateChat?.chat_uid){
                item['chat_author'] = this.$store.state.user.user
                this.createVirtualChat(item)

                if(this.isMobile) {
                    if (isStandaloneChatWindow) {
                        this.$router.push({
                            name: 'chat-window',
                            params: {
                                id: item.id
                            }
                        })
                        return
                    }
                    this.$router.push({
                        name: 'chat-body',
                        params: {
                            id: item.id
                        }
                    })
                }
            } else {
                const chatUid = privateChat.chat_uid

                if(this.isMobile) {
                    if (isStandaloneChatWindow) {
                        this.$router.push({
                            name: 'chat-window',
                            params: {
                                id: chatUid
                            }
                        })
                        this.$store.commit('chat/setSidebarActiveTab', 1)
                        return
                    }
                    this.$router.push({
                        name: 'chat-body',
                        params: {
                            id: chatUid
                        }
                    })
                } else {
                    const chat = await this.getCurrentChat(chatUid)
                    if (!chat || chat.chat_uid !== chatUid) return

                    if(
                        this.$store.state.chat.activeChat &&
                        !this.$store.state.chat.activeChat.is_public &&
                        this.$store.state.chat.activeChat.recipient?.id
                    ) {
                        this.$socket.client.emit('chat_status_user', {
                            chat_uid: this.$store.state.chat.activeChat.chat_uid,
                            user_uid: this.$store.state.chat.activeChat.recipient.id
                        })
                    }

                    const query = JSON.parse(JSON.stringify(this.$route.query || {}))
                    if(query.chat_id !== chatUid) {
                        query.chat_id = chatUid
                        this.$router.push({ query })
                    }
                }

                this.$store.commit('chat/setSidebarActiveTab', 1)
            }
        },
        clearSearch(item){
            if(item.type === "users.ProfileModel") {
                this.createChat(item)
            }
            this.$store.commit('chat/CLEAR_SEARCH_RESULT')
            this.$store.commit('chat/setValueState', {name: 'searchText', value: ""})
            this.$store.commit('chat/setValueState', {name: 'searchStart', value: false})
            this.searchLoading = false
        }
    }

}
</script>

<style lang="scss">
.search_res{
    padding-left: 15px;
    padding-right: 15px;
}
.chat_aside{
    .ant-tabs-tab{
        width: var(--tab-w, 50%);
        padding-top: 10px;
        padding-bottom: 10px;
        min-width: 0;
    }
    .sidebar_tab_label{
        display: flex;
        align-items: center;
        justify-content: center;
        min-width: 0;
        gap: 4px;
    }
    .sidebar_tab_text{
        min-width: 0;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
    }
}
</style>
