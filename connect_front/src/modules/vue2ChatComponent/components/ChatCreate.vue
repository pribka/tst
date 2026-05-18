<template>
    <a-modal 
        :title="$t('chat.create_group_chat')" 
        :visible="visible"
        @cancel="visible = false">
        <div ref="wrapRef">
            <a-form-model 
                ref="formRef"
                :model="form"
                :rules="rules">
                <a-form-model-item prop="name" :label="$t('chat.chat_name')">
                    <a-input
                        v-model="form.name"
                        size="large"
                        :placeholder="$t('chat.chat_name')" />
                </a-form-model-item>
                <a-form-model-item prop="members" class="mb-0" :label="$t('chat.participants2')">
                    <UserDrawer 
                        id="chatCreate"
                        multiple
                        :getContainer="getContainer"
                        :changeMetadata="changeMetadata"
                        :metadata="{ key: 'members', value: form.metadata }"
                        v-model="form.members" />
                </a-form-model-item>
            </a-form-model>
        </div>
        <template #footer>
            <div class="flex gap-2" :class="isMobile ? 'flex-col w-full' : 'items-center'">
                <a-button
                    :block="isMobile"
                    :loading="createLoader"
                    @click="submit"
                    size="large"
                    type="primary"
                    htmlType="submit">
                    {{$t('chat.create_chat')}}
                </a-button>
                <a-button
                    :block="isMobile"
                    @click="visible = false"
                    size="large"
                    type="ui_ghost"
                    htmlType="submit">
                    {{$t('Close')}}
                </a-button>
            </div>
        </template>
    </a-modal>
</template>

<script>
import { mapState} from 'vuex'
import eventBus from '@/utils/eventBus'
import Vue from 'vue'
import { errorHandler } from '@/utils/index.js'
let timeout;
export default {
    name: "ChatCreate",
    components: {
        UserDrawer: () => import('@apps/DrawerSelect/index.vue')
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
            if(this.selectedContacts.length > 1 && this.form.name.length)
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
            search: '',
            form: { 
                name: '', 
                members: [], 
                metadata: { 
                    members: [] 
                } 
            },
            rules: {
                name: [
                    { required: true, message: this.$t('chat.field_require'), trigger: 'blur' },
                    { min: 3, message: this.$t('chat.field_min_require', {min: 3}), trigger: 'blur' },
                    { max: 64, message: this.$t('chat.field_max_require', {max: 64}), trigger: 'blur' },
                ],
                members: [
                    { required: true, message: this.$t('chat.field_require'), trigger: 'blur' },
                    { validator: (rule, value) => {
                        if (value && value.length < 2)
                            return Promise.reject(this.$t('chat.need_two_users'));
                        return Promise.resolve();
                    }, 
                    },
                ],
            }
        }
    },
    methods: {
        getContainer() {
            return this.$refs.wrapRef
        },
        changeMetadata({key, value}) {
            Vue.set(this.form.metadata, key, value)
        },

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
        async submit() {
            await this.$refs.formRef.validate(async (valid) =>  {
                if (valid) {
                    await this.createChat()
                } else {
                    console.error(this.$t('chat.fields_required'));
                }
            });
        },
        async createChat() {
            let chat = {
                members: [],
                name: '',
                is_public: false
            }
            this.form.members.forEach(item => {
                let member = { user: item.id }
                
                if(this.form.members.length > 1) {
                    member.is_moderator = false
                    if(this.moderate.length) {
                        const find = this.moderate.find(elem => elem === item)
                        if(find) member.is_moderator = true
                    } 
                }
                if (this.$store.state.user.user.id !== item.id)
                    chat.members.push(member)
            })
            if(this.form.members.length > 1) {
                chat.is_public = true
                chat.name = this.form.name
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
                   
            } catch(error) {
                errorHandler({error})
            } finally {
                this.createLoader = false
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
            this.form = {
                name: '', 
                members: [], 
                metadata: { members: [] } 
            }
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
                } catch(error) {
                    errorHandler({error, show: false})
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