<template>
    <div class="chat_message" :class="[isMe && 'is_me', message.reply && 'is_reply', isMobile && 'mobile_message']">
        <div>
            <div class="chat_message__bubble">
                <div class="message_header flex items-center">
                    <span class="mr-2">
                        <template v-if="isSupport">
                            <template v-if="message.author">
                                {{  message.author.full_name }}
                            </template>
                            <template v-else>
                                <template v-if="ticket.contact_person">
                                    {{ ticket.contact_person.name }}
                                </template>
                                <template v-else>
                                    {{ ticket.channel ? ticket.channel.name : $t('helpdesk.contact_person') }}
                                </template>
                            </template>
                        </template>
                        <template v-else>
                            {{ $t('helpdesk.your_message') }}
                        </template>
                    </span>
                    <div class="message_date">
                        {{ formattedDate }}
                    </div>
                </div>
                <div v-if="message.reply" class="message_reply">
                    <div class="message_reply__label">{{ $t('helpdesk.reply_to_message') }}:</div>
                    <TextViewer 
                        :body="message.reply.text"
                        collapsible 
                        toggleButtonColor="#416ce9"
                        overlayColor="#e8ecfa" />
                </div>
                <TextViewer v-if="message.text" class="message_text" :body="message.text" />
                <div 
                    v-if="audioFilesList && audioFilesList.length" 
                    class="mt-2">
                    <AudioMessage 
                        v-for="audio in audioFilesList" 
                        :key="audio.id" 
                        :audio="audio"
                        :onLoaded="onAudioLoaded"
                        :onPlayStart="onAudioPlay" />
                </div>
                <div 
                    v-if="videoFilesList && videoFilesList.length" 
                    class="mt-2">
                    <VideoMessage 
                        v-for="video in videoFilesList" 
                        :key="video.id" 
                        :video="video"
                        :onLoaded="onVideoLoaded"
                        :onPlayStart="onVideoPlay" />
                </div>
                <div 
                    v-if="filesList && filesList.length" 
                    class="mt-2 flex flex-wrap">
                    <MessageFile 
                        v-for="file in filesList" 
                        :key="file.id" 
                        :file="file"
                        :id="message.id" />
                </div>
            </div>
            <div v-if="actions && actions.create_message && isActive" class="flex items-center gap-3 mt-2">
                <div v-if="isActions" class="message_btn" @click="setReplace(message)">
                    {{ $t('helpdesk.reply_to_message') }}
                </div>
            </div>
        </div>
        <div v-if="isMe && message.author" class="ml-2">
            <a-avatar 
                :src="message.author.avatar ? message.author.avatar.path : null" 
                icon="user"
                :size="24" />
        </div>
    </div>
</template>

<script>
import { mapState } from 'vuex'
import { audioFormats, videoFormats } from '../../../../../utils/utils.js'
export default {
    props: {
        message: { type: Object, required: true },
        ticket: { type: Object, required: true },
        setReplace: { type: Function, default: () => {} },
        isActive: { type: Boolean, default: false },
        actions: { type: Object, default: () => null },
        onAudioLoaded: { type: Function, default: () => {} },
        onAudioPlay: { type: Function, default: () => {} },
        onVideoLoaded: { type: Function, default: () => {} },
        onVideoPlay: { type: Function, default: () => {} }
    },
    components: {
        MessageFile: () => import('../../../../MessageFile.vue'),
        AudioMessage: () => import('../../../../AudioMessage.vue'),
        VideoMessage: () => import('../../../../VideoMessage.vue'),
        TextViewer: () => import('@apps/CKEditor/TextViewer.vue')
    },
    computed: {
        ...mapState({
            user: state => state.user.user
        }),
        audioFilesList() {
            if (this.message.attachments?.length) {
                return this.message.attachments.filter(f => 
                    audioFormats.some(ext => f.extension.includes(ext))
                )
            }
            return []
        },
        videoFilesList() {
            if (this.message.attachments?.length) {
                return this.message.attachments.filter(f => 
                    videoFormats.some(ext => f.extension.includes(ext))
                )
            }
            return []
        },
        filesList() {
            if (this.message.attachments?.length) {
                return this.message.attachments.filter(f => 
                    ![...audioFormats, ...videoFormats].some(ext => f.extension.includes(ext))
                )
            }
            return []
        },
        isMobile() { 
            return this.$store.state.isMobile
        },
        isActions() {
            return this.actions.change_status
        },
        isSupport() {
            return this.message.is_help_desk
        },
        isMe() {
            if(this.isSupport)
                return false
            else
                return true
        },
        formattedDate() {
            const msgDate = this.$moment(this.message.created_at)
            const now = this.$moment()

            if (msgDate.isSame(now, 'day')) {
                return `${this.$t('helpdesk.today_at')} ${msgDate.format('HH:mm')}`
            } else if (msgDate.isSame(now.clone().subtract(1, 'day'), 'day')) {
                return `${this.$t('helpdesk.yesterday')} ${msgDate.format('HH:mm')}`
            } else {
                return msgDate.format('DD.MM.YYYY')
            }
        }
    }
}
</script>

<style lang="scss" scoped>
.message_reply{
    background: #e8ecfa;
    padding: 10px;
    border-radius: 8px;
    margin-bottom: 10px;
    &__label{
        font-size: 10px;
        line-height: 10px;
        margin-bottom: 5px;
        color: #888888;
    }
    .message_text{
        font-size: 14px;
        word-break: break-word;
        line-height: 22px;
    }
}
.chat_message{
    padding: 15px;
    display: flex;
    &:not(.mobile_message) {
        padding: 20px;
    }
    &::v-deep{
        .ant-avatar{
            background: #fff;
        }
    }
    .message_btn{
        color: #888888;
        cursor: pointer;
        font-size: 12px;
        transition: all 0.3s cubic-bezier(0.645, 0.045, 0.355, 1);
        line-height: 16px;
        &:hover{
            color: var(--blue);
        }
    }
    &.is_me{
        justify-content: flex-end;
    }
    &__bubble{
        background: #fff;
        border-radius: 8px;
        padding: 15px;
        max-width: 800px;
        min-width: 220px;
        .message_date{
            color: #888888;
        }
        .message_header{
            font-size: 12px;
            margin-bottom: 8px;
        }
        .message_text{
            font-size: 14px;
            word-break: break-word;
            line-height: 22px;
        }
    }
}
</style>