<template>
    <a-drawer
        :title="$t('chat.group_chat_add')"
        placement="right"
        class="group_chat_drawer"
        :class="isMobile && 'mobile'"
        :width="isMobile ? '100%' : 380"
        :visible="popupActive"
        :afterVisibleChange="afterVisibleChange"
        @close="popupActive = false">
        <div v-if="!isMobile" class="drawer_footer relative">
            <a-input
                v-model="search"
                @input="memberSearch"
                :placeholder="$t('chat.press_user_name')"
                class="input_search"
                size="large">
                <a-icon slot="prefix" type="search" />
            </a-input>
            <a-button
                @click="addUser()"
                class="absolute"
                type="primary"
                :disabled="selectedContacts.length ? false : true"
                shape="circle"
                icon="plus" />
        </div>
        <div class="drawer_scroll">
            <RecycleScroller
                :items="list.results"
                size-field="height"
                :buffer="200"
                class="scroll_list"
                emitUpdate
                :item-size="53"
                key-field="id">
                <template #before>
                    <a-empty 
                        v-if="empty" 
                        class="mt-3"
                        :description="$t('no_data')" />
                </template>
                <template #default="{ item }">
                    <UserCard 
                        :clickSelect="true" 
                        :userItem="item" 
                        class="cursor-pointer"
                        :checkBoxMode="true" 
                        :selectModerLength="0" />
                </template>
                <template #after>
                    <infinite-loading 
                        @infinite="getContactsList" 
                        ref="userInfinity"
                        v-bind:distance="10" 
                        :identifier="popupActive">
                        <div slot="spinner"><a-spin class="mt-1" /></div>
                        <div slot="no-more"></div>
                        <div slot="no-results"></div>
                    </infinite-loading>
                </template>
            </RecycleScroller>
        </div>
        <div v-if="isMobile" class="drawer_footer relative">
            <a-input
                v-model="search"
                @input="memberSearch"
                :placeholder="$t('chat.press_user_name')"
                class="input_search"
                size="large">
                <a-icon slot="prefix" type="search" />
            </a-input>
            <a-button
                @click="addUser()"
                class="absolute"
                type="primary"
                :disabled="selectedContacts.length ? false : true"
                shape="circle"
                icon="plus" />
        </div>
    </a-drawer>
</template>

<script>
import {mapMutations, mapState} from 'vuex'
let searchId
import { RecycleScroller } from 'vue-virtual-scroller'
import 'vue-virtual-scroller/dist/vue-virtual-scroller.css'
export default {
    name: "ChatAddMemberSidebar",
    components: {
        UserCard: () => import('../UserCard.vue'),
        InfiniteLoading: () => import('vue-infinite-loading'),
        RecycleScroller
    },
    data() {
        return {
            loading: false,
            page: 0,
            empty: false,
            search: '',
            list: {
                results: [],
                next: true,
                count: 0
            }
        }
    },
    computed: {
        ...mapState({
            addMembersList: state => state.chat.contactsGroup,
            activeChat: state => state.chat.activeChat,
            moderate: state => state.chat.moderate,
            windowWidth: state => state.windowWidth,
            contactGroupNext: state=> state.chat.contactGroupNext,
            selectedContacts: state => state.chat.selectedContacts,
            isMobile: state => state.isMobile
        }),
        popupActive: {
            get() {
                return this.$store.state.chat.addMemberPopup
            },
            set(val) {
                this.$store.commit('chat/SET_ADD_MEMBER_POPUP', val)
            }
        }
    },
    methods: {
        ...mapMutations({
            clearMemberSideBar: "chat/clearMemberSideBar",
            addUserCount: 'chat/addUserCount'
        }),
        memberSearch(e) {
            clearTimeout(searchId)
            
            searchId = setTimeout(() => {
                this.$nextTick(() => {
                    this.page = 0
                    this.empty = false
                    this.list = {
                        results: [],
                        next: true,
                        count: 0
                    }
                })
                this.$refs.userInfinity.stateChanger.reset()
            }, 500)
        },
        afterVisibleChange(vis) {
            if(!vis) {
                this.page = 0
                this.empty = false
                this.search = ''
                this.list = {
                    results: [],
                    next: true,
                    count: 0
                }
            }
        },
        async getContactsList($state = null) {
            if(!this.loading && this.list.next) {
                try {
                    this.loading = true
                    this.page += 1
                    const { data } = await this.$http.get('/chat/users/', {
                        params: {
                            page: this.page,
                            page_size: 15,
                            search: this.search,
                            chat: this.activeChat.chat_uid
                        }
                    })

                    if(data) {
                        this.list.count = data.count
                        this.list.next = data.next
                    }

                    if(data?.results?.length)
                        this.list.results = this.list.results.concat(data.results)

                    if(this.page === 1 && !this.list.results.length) {
                        this.empty = true
                    }
                        
                    if(this.list.next)
                        $state.loaded()
                    else
                        $state.complete()
                } catch(e) {
                    console.log(e)
                } finally {
                    this.loading = false
                }
            }
        },
        async addUser(){
            if(this.selectedContacts.length > 0){ 
                let chat = {
                    members: [],
                    chat_uid: this.activeChat.chat_uid
                }
                this.selectedContacts.forEach(item => {
                    let member = {user: item}
              
                    if(this.moderate.length) {
                        const find = this.moderate.find(elem => elem === item)
                        if(find)
                            member.is_moderator = true
                        else
                            member.is_moderator = false
                    } else {
                        member.is_moderator = false
                    }
                
                    chat.members.push(member)
                })
                if(this.selectedContacts.length > 1) {
                    chat.is_public = true
                    chat.name = this.chatName
                } else
                    chat.name = chat.members[0].user
                try {
                    this.loading = true
                    
                    // this.addUserCount()
                    this.$socket.client.emit('chat_add_user', chat)
                    this.clearMemberSideBar()
                   
                    this.$emit('add')
           
                    this.popupActive = false
                
                  
                } catch(e) {
                    console.error(e)
                } finally {
                    this.loading = false
                }
            }
            
        }
    }
}
</script>

<style lang="scss" scoped>
.group_chat_drawer{
    &::v-deep{
        .ant-drawer-wrapper-body,
        .ant-drawer-content{
            overflow: hidden;
        }
        .ant-drawer-body{
            height: calc(100% - 40px);
            .drawer_scroll{
                height: calc(100% - 56px);
            }
        }
    }
    &.mobile{
        &::v-deep{
            .drawer_footer{
                border-top: 1px solid var(--borderColor);
                border-bottom: 0px;
            }
        }
    }
}
</style>