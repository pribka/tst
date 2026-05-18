<template>
    <div class="pin_messages px-2 lg:px-3 flex items-center justify-between">
        <div class="w-full truncate flex items-center">
            <div class="spin_slide" v-if="loading">
                <a-spin size="small" />
            </div>
            <swiper
                class="swiper swiper_thumbs"
                style="width: 10px;"
                :options="swiperOptionThumbs"
                :ref="`pin_thumb_${chatData.chat_uid}`">
                <swiper-slide
                    v-for="(mess, index) in currentPin.results"
                    class="thumb"
                    :key="`${mess.message_uid}_`+index">
                </swiper-slide>
            </swiper>
            <div class="w-full truncate">
                <swiper
                    class="swiper"
                    :options="swiperOption"
                    :ref="`pin_slide_${chatData.chat_uid}`"
                    @slideChange="onSlideChange">
                    <swiper-slide
                        v-for="(mess, index) in currentPin.results"
                        :key="mess.id">
                        <div class="cursor-pointer truncate select-none" @click="itemHandler(mess, index)">
                            <label class="text-xs font-semibold block cursor-pointer">
                                {{ $t('chat.pinned_message', {index: index+1}) }}
                            </label>
                            <div class="truncate text-xs pn_message" v-if="isMessageText(mess)">
                                <TextViewer :body="replacePinMessage(mess)" />
                            </div>
                            <template v-else>
                                <template v-if="mess.share">
                                    <div class="reply_text text-sm">{{ getSharePreviewText(mess.share) }}</div>
                                </template>
                                <div v-else class="reply_text text-sm">{{ getMessageFallbackText(mess) }}</div>
                            </template>
                        </div>
                    </swiper-slide>
                </swiper>
            </div>
        </div>
        <div>
            <a-badge
                :count="currentPin.count"
                class="pin_count cursor-pointer"
                @click="openPinDrawer()">
                <a-button
                    :loading="pinLoader"
                    type="ui"
                    ghost
                    v-tippy
                    :content="$t('chat.pinned_messages')"
                    shape="circle"
                    size="large"
                    flaticon
                    icon="fi-rr-thumbtack" />
            </a-badge>
        </div>
        <PinDrawer
            :currentPin="currentPin"
            :messageSearch="messageSearch"
            :chatData="chatData" />
    </div>
</template>

<script>
import { Swiper, SwiperSlide } from 'vue-awesome-swiper'
import 'swiper/css/swiper.css'
import ChatEventBus from '../utils/ChatEventBus'
import { clearMessageHtml } from '../utils/index.js'
import { isVoiceMessageFile } from '@/utils/voice'
import { getChatSharePreviewText } from '@/utils/chatPreview'
export default {
    name: "ChatPinMessage",
    components: {
        Swiper,
        SwiperSlide,
        TextViewer: () => import('@apps/CKEditor/TextViewer.vue'),
        PinDrawer: () => import('./PinDrawer')
    },
    props: {
        chatData: {
            type: Object,
            required: true
        },
        currentPin: {
            type: Object,
            required: true
        },
        messageSearch: {
            type: Function,
            default: () => {}
        }
    },
    data() {
        return {
            swiperOption: {
                autoHeight: true,
                direction: 'vertical',
                slidesPerView: 1,
                mousewheel: true,
                touchRatio: 0,
                draggable: false
            },
            swiperOptionThumbs: {
                autoHeight: true,
                direction: 'vertical',
                spaceBetween: 2,
                slidesPerView: 'auto',
                centeredSlides: true,
                touchRatio: 0,
                slideToClickedSlide: true,
                draggable: false
            },
            pinLoader: false,
            loading: false
        }
    },
    computed: {
        swiper() {
            return this.$refs[`pin_slide_${this.chatData.chat_uid}`].$swiper
        },
        swiperThumb() {
            return this.$refs[`pin_thumb_${this.chatData.chat_uid}`].$swiper
        }
    },
    methods: {
        getPreviewMessage(message) {
            return message?.message_forwarded || message
        },
        isMessageText(message) {
            const previewMessage = this.getPreviewMessage(message)

            if (previewMessage?.is_deleted)
                return true
            if(previewMessage?.text?.length)
                return previewMessage.text
        },
        replacePinMessage(message) {
            const previewMessage = this.getPreviewMessage(message)

            if (previewMessage?.is_deleted) {
                return this.$t('chat.deleted_message_text')
            }

            if(previewMessage?.text) {
                return clearMessageHtml(previewMessage.text)
            }

            return ''
        },
        getMessageFallbackText(message) {
            const previewMessage = this.getPreviewMessage(message)
            const attachments = Array.isArray(previewMessage?.attachments) ? previewMessage.attachments : []

            if (attachments.length && attachments.every(item => isVoiceMessageFile(item))) {
                return this.$t('chat.voice_message')
            }

            return this.$t('chat.file_and_image')
        },
        getSharePreviewText(share) {
            return getChatSharePreviewText(share, this.$t.bind(this))
        },
        async onSlideChange() {
            const length = this.currentPin.results.length-1
            if(length >= 9 && this.currentPin.next && !this.loading) {
                if(this.swiper.activeIndex === length) {
                    try {
                        this.loading = true
                        await this.$store.dispatch('chat/getPinMessageScroll')
                    } catch(e) {

                    } finally {
                        this.swiper.slideTo(this.swiper.activeIndex+1, 0)
                        this.loading = false
                    }
                }
            }
        },
        openPinDrawer() {
            ChatEventBus.$emit('OPEN_PIN_DRAWER')
        },
        itemHandler(mess, index) {
            this.pinLoader = true
            this.messageSearch(mess)
                .then(() => {
                    this.pinLoader = false
                    if(this.currentPin.results.length === index+1)
                        this.swiper.slideTo(0, 300)
                    else
                        this.swiper.slideTo(index+1, 300)
                })
                .catch(()=>{
                    this.pinLoader = false
                })
        }
    },
    mounted() {
        this.$nextTick(() => {
            this.swiper.controller.control = this.swiperThumb
            this.swiperThumb.controller.control = this.swiper
        })
        ChatEventBus.$on('PINNED_MESSAGE', () => {
            try {
                if(this.$refs[`pin_slide_${this.chatData.chat_uid}`] && this.$refs[`pin_slide_${this.chatData.chat_uid}`].$swiper && this.currentPin.results.length > 1)
                    this.$refs[`pin_slide_${this.chatData.chat_uid}`].$swiper.slideTo(0, 300)
            } catch(e) {
                console.log(e)
            }
        })
        ChatEventBus.$on('SLIDE_TO_PIN', (mess) => {
            const index = this.currentPin.results.findIndex(pin => pin.id === mess.id)
            if(index !== -1)
                this.swiper.slideTo(index, 300)
        })
    },
    beforeDestroy() {
        ChatEventBus.$off('PINNED_MESSAGE')
        ChatEventBus.$off('SLIDE_TO_PIN')
    }
}
</script>

<style lang="scss" scoped>
.pn_message{
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
    .pin_messages{
        height: 44px;
        border-bottom: 1px solid var(--borderColor);
        overflow: hidden;
        position: relative;
        background-color: #f7f9fc;
        display: grid;
        grid-template-columns: 1fr 40px;
        .pin_count{
            .ant-badge-count{
                font-size: 8px;
                padding: 0 1px;
                top: 10px;
                right: 10px;
                min-width: 16px;
                height: 16px;
                line-height: 16px;
            }
        }
        .size-text{
                
             @media(min-width: 1900px){
                max-width: 70vw;
            }
            @media(min-width: 1700px){
                max-width: 67vw;
            }
            @media(min-width: 1500px){
                max-width: 63vw;
            }
            @media(min-width: 1300px){
                max-width: 58vw;
            }
            @media(min-width: 1200px){
                max-width: 53vw;
            }
        
        }
        .spin_slide{
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            z-index: 10;
            display: flex;
            align-items: center;
            justify-content: center;
            background: rgba(255, 255, 255, 0.5);
        }
        .swiper_thumbs{
            padding-top: 2px;
            margin-top: -10px;
            .thumb{
                width: 2px;
                height: 15px;
                background: var(--primaryColor);
                border-radius: 1px;
                &:not(.swiper-slide-active){
                    opacity: 0.3;
                }
            }
        }
        .swiper{
            height: 44px;
            .swiper-slide{
                display: flex;
                align-items: center;
            }
        }
    }
</style>
