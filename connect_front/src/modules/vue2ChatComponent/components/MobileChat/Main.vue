<template>
    <div class="contact_page">
        <Sidebar />
        <div class="float_add">
            <a-button 
                flaticon
                shape="circle"
                size="large"
                type="primary"
                icon="fi-rr-edit"
                @click="$store.commit('chat/TOGGLE_CREATE_CHAT', true)" />
        </div>
    </div>
</template>

<script>
import Sidebar from '../Sidebar'
import { errorHandler } from '@/utils/index.js'
import { mapMutations, mapActions, mapState } from 'vuex'
export default {
    name: "ChatIndex",
    props: {
        task: {
            type: Boolean,
            default: false
        },
        meetings: {
            type: Boolean,
            default: false
        }
    },
    components: {
        Sidebar
    },
    metaInfo() {
        return {
            htmlAttrs: {
                class: 'bg_white'
            }
        }
    },
    computed: {
        ...mapState({
            isMobile: state => state.isMobile,
            activeChat: state=> state.chat.activeChat,
            chatList: state => state.chat.chatList
        })
    },
    created() {
        this.SET_ACTIVE_CHAT(null)
    },
    methods: {
        ...mapActions({
            getCurrentChat: 'chat/getCurrentChat',
            getPrivateChat: 'chat/getPrivateChat',
        }),
        ...mapMutations({
            SET_ACTIVE_CHAT: 'chat/SET_ACTIVE_CHAT'
        }),
        async getMessageCount() {
            try {
                await this.$store.dispatch('chat/getMessageCount')
            } catch(error) {
                errorHandler({error, show: false})
            }
        },
        async getPinMessages() {
            try {
                await this.$store.dispatch('chat/getPinMessage', {
                    page_size: 10
                })
            } catch(e) {

            }
        }
    },
    mounted() {
        this.getMessageCount()
        if(this.isMobile && this.$route.query?.chat_id)
            this.$router.push({ name: 'chat-body', params: { id: this.$route.query.chat_id } })
    }
}
</script>

<style lang="scss" scoped>
.contact_page{
    height: 100%;
}
</style>