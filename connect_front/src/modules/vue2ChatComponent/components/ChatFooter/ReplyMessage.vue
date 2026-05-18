<template>
    <transition name="slide-fade">
        <div
            v-if="replyMessage"
            class="truncate reply_nav lg:px-4 py-1 w-full">
            <div class="flex truncate reply_nav__wrapper">
                <div class="mr-3 blue_color text-lg">
                    <i class="fi fi-rr-undo"></i>
                </div>
                <div class="replay_nav_body truncate w-full pr-2">
                    <div class="text-xs font-semibold">
                        {{replyMessage.message_author.full_name}}
                    </div>
                <div
                    v-if="isMessageText"
                    class="replay_nav_text truncate text-sm ">
                        <TextViewer :body="replyMessageText" />
                    </div>
                    <template v-else>
                        <template v-if="replyMessage.share">
                            <div class="text-sm truncate">
                                {{ replySharePreviewText }}
                            </div>
                        </template>
                        <div v-else class="text-sm truncate">
                            {{ replyFallbackText }}
                        </div>
                    </template>
                </div>
            </div>
            <div>
                <a-button
                    @click="replyRemove"
                    type="ui"
                    ghost
                    style="max-width: 36px;padding: 0px;"
                    shape="circle"
                    flaticon
                    size="large"
                    icon="fi-rr-circle-xmark" />
            </div>
        </div>
    </transition>
</template>

<script>
import { mapState, mapGetters, mapMutations } from 'vuex'
import { clearMessageHtml } from '../../utils/index.js'
import { isVoiceMessageFile } from '@/utils/voice'
import { getChatSharePreviewText } from '@/utils/chatPreview'
export default {
    name: "ChatReplyMessage",
    components: {
        TextViewer: () => import('@apps/CKEditor/TextViewer.vue')
    },
    computed: {
        ...mapState({
            activeChat: state => state.chat.activeChat
        }),
        ...mapGetters({
            getReplyMessage: 'chat/replyMessage'
        }),
        replyMessage() {
            return this.getReplyMessage(this.activeChat.chat_uid)
        },
        replyPreviewMessage() {
            return this.replyMessage?.message_forwarded || this.replyMessage
        },
        replyMessageText() {
            const reply = this.replyPreviewMessage

            if (reply?.is_deleted) {
                return this.$t('chat.deleted_message_text')
            }

            if (!reply?.text) return ''
            return clearMessageHtml(reply.text)
        },
        isMessageText() {
            if (this.replyPreviewMessage?.is_deleted)
                return true
            if(this.replyPreviewMessage?.text?.length)
                return this.replyPreviewMessage.text
            return ""
        },
        replyFallbackText() {
            const attachments = Array.isArray(this.replyPreviewMessage?.attachments) ? this.replyPreviewMessage.attachments : []

            if (attachments.length && attachments.every(item => isVoiceMessageFile(item))) {
                return this.$t('chat.voice_message')
            }

            return this.$t('chat.file_and_image')
        },
        replySharePreviewText() {
            return getChatSharePreviewText(this.replyPreviewMessage?.share, this.$t.bind(this))
        }
    },
    methods: {
        ...mapMutations({
            DELETE_REPLY_MESSAGE: 'chat/DELETE_REPLY_MESSAGE'
        }),
        replyRemove() {
            this.DELETE_REPLY_MESSAGE(this.activeChat.chat_uid)
        }
    }
}
</script>

<style lang="scss" scoped>
.slide-fade-enter-active {
  transition: all .3s ease;
}
.slide-fade-leave-active {
  transition: all .3s cubic-bezier(1.0, 0.5, 0.8, 1.0);
}
.slide-fade-enter, .slide-fade-leave-to{
  transform: translateY(10px);
  opacity: 0;
}
.replay_nav_text{
    &::v-deep{
        .ck_text_viewer,
        .ck_text_viewer_wrap,
        .tv_root{
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }
    }
}
</style>
