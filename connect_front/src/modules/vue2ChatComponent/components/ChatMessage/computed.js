import { mapState } from 'vuex'

export default {
    computed: {
        ...mapState({
            activeChat: state => state.chat.activeChat,
            windowWidth: state => state.windowWidth,
            isMobile: state => state.isMobile
            // user: state => state.user.user
        }),
        useDesktopMessageMenu() {
            if (this.$route?.name !== 'chat-window')
                return false
            if (typeof window === 'undefined')
                return false

            const hasTouchPoints = navigator.maxTouchPoints > 0 || navigator.msMaxTouchPoints > 0
            const coarsePointer = typeof window.matchMedia === 'function'
                ? window.matchMedia('(pointer: coarse)').matches
                : false
            const touchCapable = 'ontouchstart' in window || hasTouchPoints || coarsePointer

            return !touchCapable
        },
        menuComponent() {
            if(this.isMobile && !this.useDesktopMessageMenu)
                return () => import('./MobileMenu.vue')
            else
                return null
        },
        isViewContext() {
            if(this.shareMessage)
                return true
            if(this.messageItem.is_system)
                return true
            if (!this.messageItem.is_system || (this.messageItem.is_system && this.messageItem.share)) return false

            return true
        },
        bubbleBackground() {
            if(this.messageItem.is_ai_message)
                return 'bg_purple'
            if (!this.shareMessage && this.myMessage) 
                return 'bg_primary'
            return 'bg_gray'
        },
        deleteBtnShow() {
            return !this.messageItem.is_system && this.actions?.delete?.availability ? true : false
        },
        textLength() {
            if (this.messageItem.text.length > 300)
                return true
            else
                return false
        },
        textReplace() {
            const urlRegex = /(\b(https?|ftp|file):\/\/[-A-Z0-9+&@#\/%?=~_|!:,.;]*[-A-Z0-9+&@#\/%=~_|])/ig;
            return this.messageItem.text.replace(urlRegex, (url) => {
                return '<a target="_blank" class="m_link" href="' + url + '">' + url + '</a>';
            })
        },
        messageDate() {
            const yesterday = this.$moment(this.messageItem.created).add(14, 'hour').unix(),
                current = this.$moment().unix();

            if (yesterday > current)
                return this.$moment(this.messageItem.created).format('HH:mm')
            else
                return this.$moment(this.messageItem.created).format('DD.MM.YYYY HH:mm')
        },
        isDelete() {
            if (this.messageItem.is_deleted)
                return 'delete_message'
            else
                return ''
        },
        messageBg() {
            if (this.activeChat.chat_author) {
                if (this.user.id === this.activeChat.chat_author.id)
                    return 'bg_primary text-white'
                else
                    return 'border border-solid border-transparent bg_white'
            } else
                return 'delete_message'
        },
        myMessage() {
            if(this.shareMessage)
                return false
            if (this.messageItem.message_author)
                if (this.user.id === this.messageItem.message_author.id)
                    return true
                else
                    return false
            else
                return false
        },
        pinMessageShow() {
            if (this.activeChat.is_public) {
                if (this.activeChat.chat_author && this.user.id === this.activeChat.chat_author.id || this.activeChat.is_moderator) {
                    return true
                }
                else
                    return false
            } else
                return true
        }
    }
}
