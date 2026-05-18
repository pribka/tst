import { mapState, mapGetters } from 'vuex'
export default {
    computed: {
        ...mapState({
            activeChat: state => state.chat.activeChat,
            isMobile: state => state.isMobile,
            is_support: state => state.user.user.is_support
        }),
        ...mapGetters({
            getFileList: 'chat/getFileList',
            getFileListSend: 'chat/getFileListSend',
            getFileModal: 'chat/getFileModal',
            getReplyMessage: 'chat/replyMessage',
            getReplyMessageModal: 'chat/replyMessageModal'
        }),
        replyMessageData() {
            return this.getReplyMessage(this.activeChat.chat_uid)
        },
        replyMessageModalData() {
            return this.getReplyMessageModal(this.activeChat.chat_uid)
        },
        fileList() {
            return this.getFileList(this.activeChat.chat_uid)
        },
        message: {
            get() {
                return this.$store.state.chat.message[this.activeChat.chat_uid] ? this.$store.state.chat.message[this.activeChat.chat_uid] : {}
            },
            set(val) {
                console.log(val, 'val')
                this.CHANGE_CHAT_MESSAGE({
                    id: this.activeChat.chat_uid,
                    message: val
                })
            }
        },
        messageModal: {
            get() {
                return this.$store.state.chat.messageModal[this.activeChat.chat_uid] ? this.$store.state.chat.messageModal[this.activeChat.chat_uid] : {}
            },
            set(val) {

                this.CHANGE_CHAT_MESSAGE_MODAL({
                    id: this.activeChat.chat_uid,
                    message: val
                })
            }
        },
        fileModal() {
            return this.getFileModal(this.activeChat.chat_uid)
        },
        checkEmptyMessage() {
            if (!this.fileModal && this.message.text.trim().length > 0) return true
            if (this.fileModal) return true
            return false
        },
        charLength() {
            if (this.message.text) return this.message.text.trim().length
            return 0
        },

        modalCharLength() {
            if (this.messageModal.text) return this.messageModal.text.trim().length
            return 0
        },
        
        maxCharLength() {
            return 4096
        }
    },
}