<template>
    <DrawerTemplate
        ref="drawerTemplate"
        v-model="visible"
        :wrapClassName="`ai_drawer ${isMobile && 'mob_drawer'}`"
        @afterVisibleChange="afterVisibleChange"
        :width="drawerWidth"
        @close="visible = false">
        <template #title>
            <Header :footerInputFocus="footerInputFocus" />
        </template>
        <div class="flex flex-col h-full">
            <div class="body_head pb-2">
                {{ $t('ai_assistant.ai_bot_desc', { name: ai_name }) }}
            </div>
            <div class="body_main flex-grow flex flex-col">
                <Body v-if="activeChat" ref="body" :actionHandler="actionHandler" />
                <div v-if="chatLoading" class="chat_loading_overlay">
                    <div class="chat_loading_overlay__badge">
                        <a-spin size="small" />
                    </div>
                </div>
                <template v-if="!chatLoading">
                    <Footer 
                        v-if="online"
                        ref="chatFooter"
                        :addNewMessage="addNewMessage" 
                        :visible="visible" 
                        :scrollToBottom="scrollToBottom" />
                    <OfflineFooter v-else />
                </template>
            </div>
        </div>
    </DrawerTemplate>
</template>

<script>
import { vars } from '../utils.js'
import { clearTabQuery } from '@/utils/routerUtils.js'
import { mapState } from 'vuex'
import { mobileModuleCheck } from '@/utils/index.js'
export default {
    components: {
        DrawerTemplate: () => import("@/components/DrawerTemplate.vue"),
        Header: () => import('./Header.vue'),
        Body: () => import("./Body.vue"),
        Footer: () => import("./Footer.vue"),
        OfflineFooter: () => import('./OfflineFooter.vue')
    },
    sockets: {
        connect() {
            this.reconcilePendingMessages()
        },
        notify(payload) {
            const eventPayload = this.resolveAiEventPayload(payload)
            if (eventPayload?.event_type !== 'ai_chat_event')
                return

            this.$store.commit('ai/APPLY_AI_EVENT', eventPayload)

            if (this.activeChat?.id && `${this.activeChat.id}` === `${eventPayload.chat_id}`) {
                this.addNewMessage({
                    id: eventPayload.assistant_message_id,
                    is_bot: true
                })
            }
        }
    },
    data() {
        return {
            visible: false,
            drawerWidth: 680,
            ai_name: vars.ai_name,
            ai_placeholder: vars.ai_placeholder,
            ai_avatar: vars.ai_avatar,
            ai_desc: vars.ai_desc,
            reconcileTimer: null
        }
    },
    computed: {
        ...mapState({
            online: state => state.online,
            isMobile: state => state.isMobile,
            activeChat: state => state.ai.activeChat
        }),
        chatLoading() {
            return this.$store.state.ai.chatLoading
        }
    },
    methods: {
        resolveAiEventPayload(payload) {
            if (payload?.event_type === 'ai_chat_event')
                return payload

            if (payload?.data?.event_type === 'ai_chat_event')
                return payload.data

            if (payload?.data?.message?.event_type === 'ai_chat_event')
                return payload.data.message

            if (payload?.message?.event_type === 'ai_chat_event')
                return payload.message

            return null
        },
        actionHandler(message) {
            this.$nextTick(() => {
                this.$refs.chatFooter.actionHandler(message)
            })
        },
        footerInputFocus() {
            this.$nextTick(() => {
                this.$refs.chatFooter.inputFocus()
            })
        },
        scrollToBottom() {
            this.$nextTick(() => {
                if(this.$refs.body) {
                    this.$refs.body.scrollToBottom()
                }
            })
        },
        addNewMessage(data) {
            this.$nextTick(() => {
                if(this.$refs.body) {
                    this.$refs.body.addNewMessage(data)
                }
            })
        },
        reconcilePendingMessages() {
            if (!this.activeChat?.id)
                return Promise.resolve([])

            return this.$store.dispatch('ai/reconcilePendingMessages', {
                chatId: this.activeChat.id
            }).catch(error => {
                console.error(error)
                return []
            })
        },
        startReconcileLoop() {
            if (this.reconcileTimer || !this.visible || !this.online)
                return

            this.reconcilePendingMessages()
            this.reconcileTimer = setInterval(() => {
                this.reconcilePendingMessages()
            }, 5000)
        },
        stopReconcileLoop() {
            if (!this.reconcileTimer)
                return

            clearInterval(this.reconcileTimer)
            this.reconcileTimer = null
        },
        syncReconcileLoop() {
            if (this.visible && this.online && this.activeChat?.id) {
                this.startReconcileLoop()
            } else {
                this.stopReconcileLoop()
            }
        },
        closeDrawer() {
            const query = clearTabQuery({ ...this.$route.query })
            if(query.ai_chat) {
                delete query.ai_chat
                this.$router.push({query})
            }
        },
        afterVisibleChange(vis) {
            if(vis) {

            } else {
                this.closeDrawer()
            }
        },
        getChat() {
            try {
                this.$store.dispatch('ai/getChat')
            } catch(e) {
                console.error(e)    
            }
        }
    },
    beforeDestroy() {
        this.stopReconcileLoop()
    },
    mounted() {
        if(this.$route.query.ai_chat) {
            this.visible = true
            // if(mobileModuleCheck()) {
            //     this.visible = true
            // } else {
            //     this.closeDrawer()
            // }
        }

        this.getChat()
        this.syncReconcileLoop()
    },
    watch: {
        '$route.name'() {
            this.visible = false
        },
        visible() {
            this.syncReconcileLoop()
        },
        online() {
            this.syncReconcileLoop()
        },
        'activeChat.id'() {
            this.syncReconcileLoop()
            this.reconcilePendingMessages()
        },
        '$route.query': {
            handler: function (val, oldVal) {
                if(val.ai_chat) {
                    this.visible = true
                    // if(mobileModuleCheck()) {
                    //     this.visible = true
                    // } else {
                    //     this.closeDrawer()
                    // }
                }
                this.syncReconcileLoop()
            },
            deep: true
        }
    },
}
</script>

<style lang="scss" scoped>
.body_head{
    color: #888888;
    font-size: 12px;
    line-height: 16px;
    
}
.body_main{
    background: #f7f9fc;
    overflow: hidden;
    position: relative;
}
.chat_loading_overlay{
    position: absolute;
    top: 12px;
    left: 0;
    right: 0;
    height: 0;
    z-index: 3;
    display: flex;
    justify-content: center;
    pointer-events: none;
}
.chat_loading_overlay__badge{
    width: 40px;
    height: 40px;
    border-radius: 50%;
    background: #ffffff;
    box-shadow: 0 6px 18px rgba(31, 57, 104, 0.12);
    display: flex;
    align-items: center;
    justify-content: center;
}
.ai_drawer{
    &::v-deep{
        &.drawer_wrap{
            &.ant-drawer{
                .ant-drawer-body{
                    .drawer_body{
                        overflow: hidden;
                        &.padding{
                            padding-top: 0px;
                        }
                    }
                }
            }
        }
    }
    &:not(.mob_drawer){
        .body_main{
            border-radius: 8px;
        }
    }
    &.mob_drawer{
        &::v-deep{
            .body_head{
                padding-left: 15px;
                padding-right: 15px;
            }
            .ant-drawer-body .drawer_body.padding{
                padding: 0px;
            }
        }
    }
}
</style>
