<template>
    <div class="flex items-center justify-between w-full">
        <div class="flex items-center">
            <div class="mr-2">
                <a-avatar 
                    :src="ai_avatar" 
                    avResize
                    shape="square"
                    :size="28" />
            </div>
            <div class="ai_name">{{ ai_name }}</div>
        </div>
        <div class="flex items-center">
            <transition name="slowfade" appear :duration="{ enter: 600, leave: 300 }">
                <a-button 
                    v-if="activeChat && activeMessages && activeMessages.results && activeMessages.results.length"
                    type="ui" 
                    shape="circle" 
                    flaticon 
                    ghost
                    v-tippy="{ 
                        content: $t('ai_assistant.clear_dialog'), 
                        trigger: 'mouseenter', 
                        hideOnClick: true, 
                        inertia: true, 
                        duration: [200,200], 
                        interactive: false, 
                        placement: 'top'
                    }"
                    icon="fi-rr-trash"
                    @click="dialogClear()" />
            </transition>
        </div>
    </div>
</template>

<script>
import { vars } from '../utils.js'
import { mapState } from 'vuex'
export default {
    props: {
        footerInputFocus: {
            type: Function,
            default: () => {}
        }
    },
    data() {
        return {
            ai_name: vars.ai_name,
            ai_placeholder: vars.ai_placeholder,
            ai_avatar: vars.ai_avatar
        }
    },
    computed: {
        ...mapState({
            activeChat: state => state.ai.activeChat,
            chatMessages: state => state.ai.chatMessages
        }),
        activeMessages() {
            if(this.activeChat && this.chatMessages?.[this.activeChat.id]) {
                return this.chatMessages[this.activeChat.id]
            }
            return null
        },
    },
    methods: {
        dialogClear() {
            this.$confirm({
                title: this.$t('ai_assistant.clear_dialog_confirm'),
                content: '',
                okText: this.$t('ai_assistant.clear'),
                okType: 'danger',
                zIndex: 2000,
                closable: true,
                maskClosable: true,
                cancelText: this.$t('Close'),
                onOk: () => {
                    return new Promise((resolve, reject) => {
                        this.$http.post(`/chat_ai/chats/${this.activeChat.id}/clear-messages/`)
                            .then(() => {
                                this.$store.commit('ai/CLEAR_ACTIVE_CHAT')
                                this.footerInputFocus()
                                resolve()
                            })
                            .catch(e => {
                                console.log(e)
                                reject(e)
                            })
                    })
                }
            })
        }
    }
}
</script>

<style lang="scss" scoped>
.slowfade-enter-active,
.slowfade-leave-active {
  transition: opacity .4s ease, transform .4s ease;
}

.slowfade-enter,
.slowfade-leave-to {
  opacity: 0;
  transform: translateX(8px);
}
.ai_name{
    color: #2D2D2D;
    font-size: 16px;
    font-weight: 600;
    line-height: 100%;
}
</style>
