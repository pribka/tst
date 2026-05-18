<template>
    <div>
        <FileAttach
            ref="fileAttach"
            :attachmentFiles="files"
            :maxMBSize="50"
            :class="files.length && 'ml-5 mb-1'" />
        <div v-if="replaceMessage" class="chat_replace" :class="isMobile && 'mobile_chat_replace'">
            <div class="replace_message truncate">
                <div class="replace_message__label">{{ $t('helpdesk.reply_to_message') }}:</div>
                <div v-html="replaceMessageFormatted" class="message_text truncate" />
            </div>
            <a-button
                type="ui"
                flaticon
                ghost
                class="ml-2 close_btn"
                size="large"
                icon="fi-rr-cross-small"
                @click="setReplace(null)" />
        </div>
        <div class="chat_footer" :class="[replaceMessage && 'top_pd', isMobile ? 'mobile_footer' : 'desc_footer']">
            <div class="message_input_wrapper" :class="isMobile && 'w-full'">
                <div class="editor_wrap" :class="isMobile && 'w-full'" ref="editorWrap">
                    <Editor
                        v-model="message.text"
                        ref="editor"
                        :editorClassName="isMobile ? 'w-full' : ''"
                        commentEditor
                        :placeholder="$t('helpdesk.enter_message')"
                        :enterShifthHand="sendMessage"
                        initFocus />
                </div>
                <div v-if="!isMobile" class="input_actions pl-1 flex items-end" :class="isMobile ? 'pr-1' : 'pr-2'">
                    <div class="flex gap-1 pb-1">
                        <a-button
                            v-if="actions && actions.edit && actions.edit.availability"
                            shape="circle"
                            ghost
                            type="ui"
                            @click="openFileModal">
                            <i class="fi flaticon fi-rr-clip"></i>
                        </a-button>
                        <Emoji
                            v-if="!isMobile"
                            class="act_btn"
                            @click="selectEmoji" />
                    </div>
                </div>
            </div>
            <div :class="isMobile ? 'flex flex-col gap-1 mobile_actions' : 'ml-2'">
                <a-button
                    v-if="isMobile && actions && actions.edit && actions.edit.availability"
                    shape="circle"
                    ghost
                    type="ui"
                    @click="openFileModal">
                    <i class="fi flaticon fi-rr-clip"></i>
                </a-button>
                <a-button
                    type="primary"
                    flaticon
                    class="send_btn"
                    :loading="loading"
                    size="large"
                    icon="fi-rr-paper-plane-top"
                    @click="sendMessage()" />
            </div>
        </div>
    </div>
</template>

<script>
import Emoji from '@/components/Emoji'
import FileAttach from '@apps/vue2Files/components/FileAttach'
import Editor from '@apps/CKEditor/index.vue'

export default {
    components: {
        Emoji,
        FileAttach,
        Editor
    },
    props: {
        ticket: {
            type: Object,
            required: true
        },
        addNewMessage: {
            type: Function,
            default: () => {}
        },
        replaceMessage: {
            type: Object,
            default: () => null
        },
        setReplace: {
            type: Function,
            default: () => {}
        },
        scrollToBottom: {
            type: Function,
            default: () => {}
        },
        actions: {
            type: Object,
            default: () => null
        }
    },
    computed: {
        replaceMessageFormatted() {
            const raw = this.replaceMessage?.text
            if (!raw) return null

            const doc = new DOMParser().parseFromString(String(raw), 'text/html')
            const text = (doc.body?.textContent || '')
                .replace(/\u00a0/g, ' ')
                .replace(/\s+/g, ' ')
                .trim()

            return text
        },
        isMobile() {
            return this.$store.state.isMobile
        }
    },
    data() {
        return {
            loading: false,
            message: {
                text: "",
                attachments: []
            },
            files: [],
            ro: null,
            heightPollId: null,
            lastHeight: 0,
            debounceId: null
        }
    },
    watch: {
        'message.text'() {
            this.$nextTick(() => this.triggerScrollIfHeightChanged())
        }
    },
    methods: {
        openFileModal() {
            this.$nextTick(() => {
                this.$refs.fileAttach.openFileModal()
            })
        },
        selectEmoji(emoji) {
            if(this.$refs?.editor)
                this.$refs.editor.insertText(emoji.detail.unicode)
            this.inputFocus()
        },
        async sendMessage() {
            if (this.loading) return
            if (!this.message.text && !this.files.length) return
            try {
                this.loading = true
                const queryData = {
                    org_admin: this.ticket.org_admin.id,
                    text: this.message.text,
                    attachments: this.files?.length ? this.files.map(item => item.id) : [],
                    ticket: this.ticket.id
                }
                if (this.replaceMessage) queryData.reply = this.replaceMessage.id
                await this.$http.post('/help_desk/contact_persons/messages/client/create/', queryData)
                this.message = {
                    text: "",
                    attachments: []
                }
                this.files.splice(0)
            } catch(e) {
                console.log(e)
            } finally {
                this.loading = false
            }
        },
        inputFocus() {
            this.$nextTick(() => {
                if (this.$refs.editor) {
                    this.$refs.editor.editorFocus()
                } else if (this.$refs.message_input) {
                    this.$refs.message_input.focus()
                }
            })
        },
        onResizeObserved() {
            if (this.debounceId) clearTimeout(this.debounceId)
            this.debounceId = setTimeout(() => {
                this.triggerScrollIfHeightChanged()
            }, 50)
        },
        triggerScrollIfHeightChanged() {
            const el = this.$refs.editorWrap
            if (!el) return
            const h = el.offsetHeight || 0
            if (h !== this.lastHeight) {
                this.lastHeight = h
                if (typeof this.scrollToBottom === 'function') this.scrollToBottom()
            }
        },
        startHeightObserver() {
            const el = this.$refs.editorWrap
            if (!el) return
            this.lastHeight = el.offsetHeight || 0
            if (window.ResizeObserver) {
                this.ro = new ResizeObserver(() => this.onResizeObserved())
                this.ro.observe(el)
            }
            if (!this.heightPollId) {
                this.heightPollId = setInterval(() => this.triggerScrollIfHeightChanged(), 120)
            }
        },
        stopHeightObserver() {
            if (this.ro) {
                this.ro.disconnect()
                this.ro = null
            }
            if (this.heightPollId) {
                clearInterval(this.heightPollId)
                this.heightPollId = null
            }
            if (this.debounceId) {
                clearTimeout(this.debounceId)
                this.debounceId = null
            }
        }
    },
    mounted() {
        this.inputFocus()
        this.$nextTick(() => this.startHeightObserver())
    },
    beforeDestroy() {
        this.stopHeightObserver()
    }
}
</script>

<style lang="scss" scoped>
.mobile_actions{
  position: absolute;
  right: 5px;
  bottom: 5px;
  z-index: 30;
}
.send_btn{
  &.ant-btn{
    display: flex;
    align-items: center;
    justify-content: center;
    &.ant-btn-lg{
      height: 40px;
    }
  }
}
.chat_replace{
  display: flex;
  .close_btn{
    padding: 0px;
    min-width: 42px!important;
  }
  &:not(.mobile_chat_replace){
    padding: 0 20px;
  }
  .replace_message{
    background: #fff;
    border-bottom: 1px solid #dadada;
    border-radius: 8px 8px 0 0;
    padding: 10px 15px;
    flex: 1;
    &__label{
      color: #888888;
      font-size: 12px;
      line-height: 12px;
      margin-bottom: 5px;
    }
  }
}
.chat_footer{
  display: flex;
  align-items: flex-end;
  &.mobile_footer{
    width: 100%;
    position: relative;
    .message_input_wrapper{
      padding-right: 48px;
    }
  }
  &:not(.mobile_footer){
    padding: 10px 20px;
    .editor_wrap{
      flex: 1;
      min-width: 0;
    }
    .input_actions{
      flex: 0 0 auto;
      shrink: 0;
    }
    .message_input_wrapper{
      flex: 1;
      min-width: 0;
    }
  }
  &.desc_footer{
    @media (max-width: 1190px) {
      .message_input_wrapper{
        display: block;
      }
    }
  }
  &.top_pd{
    padding-top: 0px;
    &::v-deep{
      .ck.ck-toolbar{
        border-radius: 0px;
      }
    }
    .message_input_wrapper{
      border-radius: 0 0 var(--ck-border-radius) var(--ck-border-radius);
    }
  }
  .message_input{
    min-height: 40px!important;
    resize: none;
    border-color: #fff;
    padding-right: 40px;
    &:focus{
      box-shadow: initial;
    }
  }
  &::v-deep{
    .ck.ck-toolbar{
      background: #fff;
      border-bottom: transparent;
      border: 0px;
    }
    .ck-content.ck-editor__editable{
      border: 0px;
      box-shadow: initial!important;
    }
  }
}
.message_input_wrapper{
  position: relative;
  display: flex;
  background: #fff;
  border-radius: var(--ck-border-radius);
}
</style>