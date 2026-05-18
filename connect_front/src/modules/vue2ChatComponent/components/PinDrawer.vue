<template>
    <a-drawer
        :title="$t('chat.pinned_messages')"
        :width="windowWidth > 680 ? 680 : windowWidth"
        :destroyOnClose="true"
        placement="right"
        :class="isMobile && 'mobile'"
        class="drawer_style pin_chat_wrapper"
        :visible="visible"
        @close="onClose">
        <div class="drawer_body">
            <template v-if="!startLoader">
                <ChatMessage
                    v-for="(item, index) in currentPin.results"
                    :key="`${ item.id }_${ index }`"
                    :user="user"
                    :replySearch="messageSearch"
                    :pinMessageOn="true"
                    :messageItem="item" />
            </template>
            <div
                class="flex justify-center pt-4"
                v-if="loadingButton && currentPin.next">
                <a-button
                    @click="getPin()"
                    :loading="loading">
                    {{$t('chat.load_more')}}
                </a-button>
            </div>
            <infinite-loading
                @infinite="getPin"
                :identifier="`${ chatData.id }_pin`"
                v-bind:distance="50">
                <div slot="spinner">
                    <a-spin v-if="!loadingButton" />
                </div>
                <div slot="no-more"></div>
                <div slot="no-results"></div>
            </infinite-loading>
        </div>
        <div class="drawer_footer flex items-center">
            <a-button
                v-if="canUnpinAll"
                :loading="removeLoader"
                :block="isMobile"
                type="primary"
                :size="isMobile ? 'large' : 'default'"
                class="mr-1 lg:mr-2"
                @click="removeAllPin()">
                {{$t('chat.unpin_all')}}
            </a-button>
            <a-button 
                :block="isMobile" 
                type="ui"
                ghost
                :size="isMobile ? 'large' : 'default'"
                @click="onClose()">
                {{$t('close')}}
            </a-button>
        </div>
    </a-drawer>
</template>

<script>
import ChatEventBus from '../utils/ChatEventBus'
import {mapMutations, mapState} from 'vuex'
export default {
    name: "ChatPinDrawer",
    components: {
        ChatMessage: () => import('./ChatMessage'),
        InfiniteLoading: () => import('vue-infinite-loading')
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
    computed: {
        ...mapState({
            user: state => state.user.user,
            windowWidth: state => state.windowWidth,
            activeChat: state => state.chat.activeChat,
            isMobile: state => state.isMobile
        }),
        canUnpinAll() {
            const chat = this.activeChat?.chat_uid === this.chatData?.chat_uid
                ? this.activeChat
                : this.chatData

            const isModerator = typeof chat?.is_moderator === 'string'
                ? chat.is_moderator.trim().toLowerCase() === 'true'
                : Boolean(chat?.is_moderator)

            return Boolean(isModerator || chat?.chat_author?.id === this.user?.id)
        }
    },
    watch: {
        'currentPin.results': {
            handler: function(val) {
                if(val.length < this.currentPin.count) {
                    //this.getPin()
                    this.loadingButton = true
                }
            },
            deep: true
        }
    },
    data() {
        return {
            visible: false,
            loading: false,
            startLoader: false,
            removeLoader: false,
            loadingButton: false
        }
    },
    methods: {
        ...mapMutations({
            unpinAll: 'chat/UNPIN_ALL'
        }),
        async removeAllPin() {
            try {
                this.removeLoader = true
                this.$socket.client.emit("chat_unpin_all_message", {chat_uid: this.activeChat.chat_uid})
                this.unpinAll({chat_uid: this.activeChat.chat_uid})
            } catch(e) {
                console.log(e)
                this.$message.error(this.$t('error'))
            } finally {
                this.visible = false
                this.removeLoader = false
            }
        },
        async getPinMessages() {
            try {
                this.startLoader = true
                await this.$store.dispatch('chat/getPinMessage', {
                    page_size: 10
                })
            } catch(e) {
                console.log(e)
            } finally {
                this.loading = false
                this.startLoader = false
            }
        },
        onClose() {
            this.visible = false
        },
        async getPin($state) {
            if(!this.loading && this.currentPin.next) {
                try {
                    this.loading = true
                    const res = await this.$store.dispatch('chat/getPinMessageScroll')
                    if(!res.next) {
                        if($state)
                            $state.complete()
                    } else {
                        if($state)
                            $state.loaded()
                    }
                } catch(e) {
                    console.log(e)
                    if($state)
                        $state.complete()
                } finally {
                    this.loading = false
                }
            } else {
                if($state)
                    $state.complete()
            }
            if(this.loadingButton)
                this.loadingButton = false
        }
    },
    mounted() {
        // console.log("pin Drawer", this.chatData)
        ChatEventBus.$on('OPEN_PIN_DRAWER', () => {
            this.visible = true
        })
        ChatEventBus.$on('CLOSE_PIN_DRAWER', () => {
            this.visible = false
        })
    },
    beforeDestroy() {
        ChatEventBus.$off('OPEN_PIN_DRAWER')
        ChatEventBus.$off('CLOSE_PIN_DRAWER')
    }
}
</script>
<style scoped>
.drawer_footer{
          position: absolute;
          bottom: 0;
          width: 100%;
          border-top: 1px solid #e8e8e8;
          padding: 10px 16px;
          text-align: right;
          left: 0;
          background: #fff;
          border-radius: 0 0 4px 4px;
        
}
</style>

<style lang="scss" scoped>
.pin_chat_wrapper{
    &::v-deep{
        .ant-drawer-body,
        .ant-drawer-content,
        .ant-drawer-wrapper-body{
            overflow: hidden;
        }
        .ant-drawer-body{
            padding: 0px;
            height: calc(100% - 40px);
        }
        .drawer_body{
            height: calc(100% - 53px);
            overflow-y: auto;
            padding: 15px;
            background-color: #f2f2f2;
            background-image: url('~@apps/vue2ChatComponent/assets/chat_bg.png');
        }
    }
    &.mobile{
        .drawer_body{
            height: calc(100% - 100px);
        }
        .drawer_footer{
            height: 100px;
            display: block;
            padding-top: 5px;
            padding-bottom: 5px;
            .ant-btn{
                &:last-child{
                    margin-top: 5px;
                }
            }
        }
    }
}
</style>
