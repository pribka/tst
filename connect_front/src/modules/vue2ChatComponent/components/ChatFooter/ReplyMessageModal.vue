<template>
    <transition name="slide">
        <div
            v-if="replyMessage"
            class="reply_modal flex items-center justify-between reply_nav absolute px-4 py-1 w-full">
            <div class="replay_nav_body w-full pr-2">
                <div class="text-xs font-semibold">
                    {{replyMessage.message_author.full_name}}
                </div>
                <div
                    v-if="isMessageText"
                    class="replay_nav_text text-sm">
                    <TextViewer :body="replyMessageText" />
                </div>
                <template v-else>
                    <template v-if="replyMessage.share">
                        <div class="text-sm">
                            {{ replySharePreviewText }}
                        </div>
                    </template>
                    <div v-else class="text-sm">
                        {{ replyFallbackText }}
                    </div>
                </template>
            </div>
            <a-button
                @click="replyRemove"
                type="link"
                class="text-current"
                size="large"
                icon="close-circle" />
        </div>
    </transition>
</template>

<script>
import { mapState, mapGetters, mapMutations } from 'vuex'
import { clearMessageHtml } from '../../utils/index.js'
import { isVoiceMessageFile } from '@/utils/voice'
import { getChatSharePreviewText } from '@/utils/chatPreview'
export default {
    components: {
        TextViewer: () => import('@apps/CKEditor/TextViewer.vue')
    },
    computed: {
        ...mapState({
            activeChat: state => state.chat.activeChat
        }),
        ...mapGetters({
            getReplyMessage: 'chat/replyMessageModal'
        }),
        replyMessage() {
            return this.getReplyMessage(this.activeChat.chat_uid)
        },
        replyMessageText() {
            const reply = this.replyMessage
            if(reply.message_forwarded) {
                if (!reply?.message_forwarded?.text) return ''
                return clearMessageHtml(reply.message_forwarded.text)
            } else {
                if (!reply?.text) return ''
                return clearMessageHtml(reply.text)
            }
        },
        isMessageText() {
            if(this.replyMessage.message_forwarded?.text?.length)
                return this.replyMessage.message_forwarded.text
            if(this.replyMessage?.text?.length)
                return this.replyMessage.text
            return ""
        },
        replyFallbackText() {
            const attachments = Array.isArray(this.replyMessage?.attachments) ? this.replyMessage.attachments : []

            if (attachments.length && attachments.every(item => isVoiceMessageFile(item))) {
                return this.$t('chat.voice_message')
            }

            return this.$t('chat.file_and_image')
        },
        replySharePreviewText() {
            return getChatSharePreviewText(this.replyMessage?.share, this.$t.bind(this))
        }
    },
    methods: {
        ...mapMutations({
            DELETE_REPLY_MESSAGE: 'chat/DELETE_REPLY_MESSAGE_MODAL'
        }),
        replyRemove() {
            this.DELETE_REPLY_MESSAGE(this.activeChat.chat_uid)
        }
    }
}
</script>

<style lang="scss" scoped>
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

<style lang="scss">
.ant-modal-footer{
    .reply_nav{
        &.reply_modal{
            position: relative;
            bottom: initial;
            left: initial;
            margin-bottom: 5px;
            padding-left: 0px;
            padding-right: 0px;
            backdrop-filter: initial;
            .replay_nav_body{
                text-align: left;
            }
        }
    }
}
</style>
