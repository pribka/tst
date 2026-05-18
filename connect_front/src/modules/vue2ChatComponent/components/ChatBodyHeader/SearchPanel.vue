<!--SearchPanel-->
<template>
    <div class="search_panel px-2 lg:px-3 flex items-center">
        <a-input-search
            :placeholder="$t('chat.message_search_min')"
            :value="value"
            allowClear
            ref="searchInput"
            @change="onChange" />
        <div class="pl-2">
            <a-button
                @click="closeSearch()"
                type="ui"
                ghost
                style="max-width: 36px;padding: 0px;"
                shape="circle"
                flaticon
                size="large"
                icon="fi-rr-circle-xmark" />
        </div>
    </div>
</template>

<script>
import ChatEventBus from '../../utils/ChatEventBus.js'
export default {
    props: {
        activeChat: {
            type: Object,
            required: true
        }
    },
    data() {
        return {
            searchTimer: null,
            onKeydown: null
        }
    },
    computed: {
        chatUid() {
            return this.activeChat?.chat_uid
        },
        value() {
            if (!this.chatUid) return ''
            return this.$store.state.chat.chatSearchTextByChat?.[this.chatUid] || ''
        }
    },
    methods: {
        scheduleSearch(q) {
            if (this.searchTimer) clearTimeout(this.searchTimer)

            this.searchTimer = setTimeout(() => {
                if (!this.chatUid) return
                this.$store.dispatch('chat/searchChatMessages', { chat_uid: this.chatUid, text: q })
            }, 350)
        },
        onChange(e) {
            const text = e?.target?.value || ''
            if (!this.chatUid) return

            this.$store.commit('chat/SET_CHAT_SEARCH_TEXT', { chat_uid: this.chatUid, text })

            const q = text.toString().trim()

            if (!q) {
                if (this.searchTimer) clearTimeout(this.searchTimer)
                this.$store.commit('chat/CLEAR_CHAT_SEARCH', this.chatUid)
                return
            }

            if (q.length < 3) {
                if (this.searchTimer) clearTimeout(this.searchTimer)
                this.$store.commit('chat/SET_CHAT_SEARCH_MESSAGES', { chat_uid: this.chatUid, data: { results: [], next: null } })
                return
            }

            this.scheduleSearch(q)
        },
        closeSearch() {
            if (!this.chatUid) return
            if (this.searchTimer) clearTimeout(this.searchTimer)
            this.$store.commit('chat/TOGGLE_SEARCH_PANEL', { chat_uid: this.chatUid, value: false })
            this.$store.commit('chat/CLEAR_CHAT_SEARCH', this.chatUid)
            ChatEventBus.$emit('inputFocus')
        }
    },
    mounted() {
        this.$nextTick(() => {
            if (this.$refs.searchInput) this.$refs.searchInput.focus()
        })

        this.onKeydown = e => {
            const key = e?.key || e?.code
            if (key === 'Escape' || key === 'Esc') {
                e.preventDefault()
                this.closeSearch()
            }
        }

        document.addEventListener('keydown', this.onKeydown)
    },
    beforeDestroy() {
        if (this.searchTimer) clearTimeout(this.searchTimer)
        if (this.onKeydown) document.removeEventListener('keydown', this.onKeydown)
        this.onKeydown = null
    }
}
</script>

<style lang="scss" scoped>
.search_panel{
    height: 44px;
    border-bottom: 1px solid var(--borderColor);
    overflow: hidden;
    position: relative;
    background-color: #f7f9fc;
    &::v-deep{
        .ant-input{
            border-color: #fff;
        }
    }
}
</style>