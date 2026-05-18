<template>
    <div class="message_files reply_message lg:pt-3 pb-1 lg:pb-3 pr-2 mb-2 mt-2">
        <div class="text-xs mb-1"><a-icon type="paper-clip" /> {{$t('chat.attached_file')}}</div>
        <div class="file_list_item">
            <div class="res_img_wrapper cursor-pointer" @click="$store.commit('chat/SET_SELECT_IMG', message.share)" v-if="message.share.is_image">
                <img class="img_resp lazyload" :data-src="message.share.path" :alt="message.share.name" />
            </div>
            <div v-else-if="isShareVideo" class="media_wrapper media_wrapper--video">
                <video
                    class="media_player media_player--video"
                    controls
                    preload="metadata"
                    :src="message.share.path"></video>
            </div>
            <div v-else-if="isShareAudio" class="media_wrapper media_wrapper--audio">
                <VoiceMessagePlayer
                    v-if="isVoiceShare"
                    :src="message.share.path"
                    :chat-uid="resolvedChatUid"
                    :message-uid="message?.message_uid" />
                <audio
                    v-else
                    v-sync-media="{
                        chatUid: resolvedChatUid,
                        messageUid: message?.message_uid
                    }"
                    class="media_player media_player--audio"
                    controls
                    preload="metadata"
                    :src="message.share.path"></audio>
            </div>
            <div class="file_wrapper" v-else>
                <a
                    v-if="useOnlyofficePreview"
                    class="doc_file_message"
                    href="#"
                    @click.prevent="openPreview">
                    <a-icon type="file" class="mr-2" />
                    {{message.share.name ? message.share.name : $t('file')}}
                </a>
                <a v-else class="doc_file_message" download :href="message.share.path">
                    <a-icon type="file" class="mr-2" />
                    {{message.share.name ? message.share.name : $t('file')}}
                </a>
            </div>
        </div>
    </div>
</template>

<script>
import { isOnlyofficePreviewable, openOnlyofficePreview } from '@/utils/onlyoffice'
import { isVoiceMessageFile } from '@/utils/voice'
import { bindMediaElement, unbindMediaElement } from '@/utils/voicePlayback'

const AUDIO_EXTENSIONS = new Set(['aac', 'flac', 'm4a', 'mp3', 'oga', 'ogg', 'wav', 'weba'])
const VIDEO_EXTENSIONS = new Set(['avi', 'm4v', 'mkv', 'mov', 'mp4', 'mpeg', 'mpg', 'ogv', 'webm'])

export default {
    directives: {
        syncMedia: {
            inserted(el, binding) {
                bindMediaElement(el, binding.value || {})
            },
            unbind(el) {
                unbindMediaElement(el)
            }
        }
    },
    components: {
        VoiceMessagePlayer: () => import('@/components/VoiceMessagePlayer')
    },
    props: {
        message: {
            type: Object,
            required: true
        }
    },
    computed: {
        shareExtension() {
            return String(this.message?.share?.extension || this.message?.share?.ext || '')
                .toLowerCase()
                .replace(/^\./, '')
        },
        isShareAudio() {
            return !!this.message?.share?.is_audio || AUDIO_EXTENSIONS.has(this.shareExtension)
        },
        isVoiceShare() {
            return isVoiceMessageFile(this.message?.share)
        },
        isShareVideo() {
            if (this.isShareAudio || this.isVoiceShare) {
                return false
            }
            return !!this.message?.share?.is_video || VIDEO_EXTENSIONS.has(this.shareExtension)
        },
        useOnlyofficePreview() {
            return !!this.message?.share?.id && isOnlyofficePreviewable(this.message?.share)
        },
        resolvedChatUid() {
            const chatUid = this.message?.chat_uid || this.message?.chat || ''

            if (chatUid && typeof chatUid === 'object') {
                return chatUid.chat_uid || chatUid.uid || chatUid.id || ''
            }

            return chatUid
        }
    },
    methods: {
        openPreview() {
            openOnlyofficePreview(this.$store, {
                scope: 'file',
                file_id: this.message?.share?.id
            })
        }
    }
}
</script>

<style lang="scss" scoped>
.res_img_wrapper{
    background: transparent!important;
}

.media_wrapper{
    width: 100%;
    border-radius: 12px;
    overflow: hidden;
    background: #0f172a;
}

.media_wrapper--audio{
    background: rgba(15, 23, 42, 0.04);
    padding: 10px;
    min-width: 340px;
    max-width: min(100%, 420px);

    @media (max-width: 900px) {
        min-width: 0;
        max-width: 100%;
    }
}

.media_player{
    width: 100%;
    display: block;
    outline: none;
}

.media_player--video{
    min-height: 220px;
    max-height: 360px;
    background: #000;
}

.media_player--audio{
    height: 40px;
    min-width: 320px;

    @media (max-width: 900px) {
        min-width: 240px;
    }
}
</style>
