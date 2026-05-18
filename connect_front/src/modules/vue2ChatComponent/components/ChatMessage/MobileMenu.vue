<template>
    <ActivityDrawer 
        v-model="visible" 
        :visibleChange="visibleChange">
        <ActivityItem v-if="actionLoading">
            <span class="flex justify-center">
                <a-spin size="small" />
            </span>
        </ActivityItem>
        <template v-if="actions">
            <ActivityItem v-if="useReact && reactions && reactions.length">
                <div class="reactions_menu flex items-center flex-wrap gap-x-4 gap-y-2">
                    <div
                        v-for="smile in reactions"
                        :key="smile.code"
                        :title="smile.name"
                        class="cursor-pointer reaction_option"
                        :class="{ active: isMyReaction(smile) }"
                        @click="selectReaction(smile)">
                        {{ smile.icon }}
                    </div>
                </div>
            </ActivityItem>
            <ActivityItem 
                v-if="messageItem.reactions && messageItem.reactions.length"
                icon="fi-rr-smile"
                @click="openReactionModal()">
                {{ $t('chat.reactions') }}
            </ActivityItem>
            <ActivityItem
                v-if="showViewsAction && messageViewsCount"
                icon="fi-rr-eye"
                @click="openViewsModal()">
                <a-spin :spinning="messageViewsLoading" size="small">
                    {{ messageViewsText }}
                </a-spin>
            </ActivityItem>
            <ActivityItem
                v-else-if="showViewsAction"
                icon="fi-rr-eye">
                <a-spin :spinning="messageViewsLoading" size="small">
                    {{ messageViewsText }}
                </a-spin>
            </ActivityItem>
            <ActivityItem 
                v-if="messageItem.text"
                icon="fi-rr-copy"
                @click="copyMessage()">
                {{ $t('chat.copy_message_text') }}
            </ActivityItem>
            <template v-if="!pinMessageOn">
                <ActivityItem 
                    v-if="actions.reply && actions.reply.availability"
                    icon="fi-rr-comment" 
                    @click="replyMethod()">
                    {{$t('chat.to_answer')}}
                </ActivityItem>
                <ActivityItem 
                    icon="fi-rr-undo" 
                    @click="() => { visible = false; forwardMessage() }">
                    {{ $t('chat.forward') }}
                </ActivityItem>
                <ActivityItem 
                    v-if="!messageItem.forwarded && actions.edit && actions.edit.availability"
                    icon="fi-rr-edit" 
                    @click="() => { visible = false; editMessage() }">
                    {{ $t('chat.edit') }}
                </ActivityItem>
                <ActivityItem 
                    v-if="actions.add_task && actions.add_task.availability"
                    icon="fi-rr-checkbox" 
                    @click="createTask()">
                    {{$t('chat.set_task')}}
                </ActivityItem>

                <ActivityItem 
                    v-if="actions.create_help_desk_ticket && actions.create_help_desk_ticket.availability"
                    icon="fi-rr-comment-xmark" 
                    @click="сreateATicket()">
                    {{$t('helpdesk.create_ticket')}}
                </ActivityItem>

                <ActivityItem 
                    v-if="actions.add_order && actions.add_order.availability && messageItem.message_author && user && messageItem.message_author.id !== user.id"
                    icon="fi-rr-shopping-cart-check" 
                    @click="openOrderDrawer()">
                    {{$t('chat.set_order')}}
                </ActivityItem>
                <ActivityItem 
                    v-if="actions.pin && actions.pin.availability && pinMessageShow && !messageItem.is_pinned"
                    icon="fi-rr-thumbtack"
                    @click="pinMessage()">
                    {{$t('chat.anchor')}}
                </ActivityItem>
            </template>
            <template v-if="actions.pin && actions.pin.availability && messageItem.is_pinned">
                <ActivityItem 
                    v-if="pinMessageShow"
                    icon="fi-rr-comment-xmark"
                    @click="unpinMessage()">
                    {{$t('chat.unpin')}}
                </ActivityItem>
                <ActivityItem 
                    v-if="pinMessageOn"
                    icon="fi-rr-comments"
                    @click="messSearch(messageItem)">
                    {{$t('chat.show_in_chat')}}
                </ActivityItem>
            </template>
            <ActivityItem 
                v-if="deleteBtnShow"
                redLink
                icon="fi-rr-trash"
                @click="deleteMessage()">
                {{$t('chat.remove')}}
            </ActivityItem>
        </template>
    </ActivityDrawer>
</template>

<script>
import { ActivityItem, ActivityDrawer } from '@/components/ActivitySelect'
import { onLongPress } from '@vueuse/core'
import { mapState } from 'vuex'
export default {
    components: {
        ActivityItem,
        ActivityDrawer
    },
    props: {
        useReact: {
            type: Boolean,
            default: false
        },
        messageItem: {
            type: Object,
            require: true
        },
        pinMessageOn: {
            type: Boolean,
            default: false
        },
        deleteBtnShow: {
            type: Boolean,
            default: false
        },
        pinMessageShow: {
            type: Boolean,
            default: false
        },
        replyMethod: {
            type: Function,
            default: () => {}
        },
        openReactionModal: {
            type: Function,
            default: () => {}
        },
        getMessageViews: {
            type: Function,
            default: () => {}
        },
        openViewsModal: {
            type: Function,
            default: () => {}
        },
        createTask: {
            type: Function,
            default: () => {}
        },
        editMessage: {
            type: Function,
            default: () => {}
        },
        pinMessage: {
            type: Function,
            default: () => {}
        },
        сreateATicket: {
            type: Function,
            default: () => {}
        },
        deleteMessage: {
            type: Function,
            default: () => {}
        },
        unpinMessage: {
            type: Function,
            default: () => {}
        },
        forwardMessage: {
            type: Function,
            default: () => {}
        },
        messSearch: {
            type: Function,
            default: () => {}
        },
        messageRef: {
            type: HTMLElement,
            required: true
        },
        isScrolling: {
            type: Boolean,
            default: false
        },
        openOrderDrawer: {
            type: Function,
            default: () => {}
        },
        copyMessage: {
            type: Function,
            default: () => {}
        },
        selectReaction: {
            type: Function,
            default: () => {}
        },
        showViewsAction: {
            type: Boolean,
            default: false
        },
        messageViewsCount: {
            type: Number,
            default: 0
        },
        messageViewsLoading: {
            type: Boolean,
            default: false
        },
        messageViewsText: {
            type: String,
            default: ''
        }
    },
    computed: {
        ...mapState({
            config: state => state.config.config,
            user: state => state.user.user,
            reactions: state => state.chat.reactions
        })
    },
    data() {
        return {
            visible: false,
            menuLoading: false,
            actions: null,
            actionLoading: false,
        }
    },
    methods: {
        isMyReaction(smile) {
            const reactions = this.messageItem.reactions || []
            return reactions.some(
                r => r.my_reaction && r.reaction.id === smile.id
            )
        },
        visibleChange(vis) {
            if(!vis) {
                this.actions = null
            } else {
                this.$store.dispatch('chat/getReactions')
                this.getMessageViews()
            }
        },
        async getActions() {
            try {
                this.actionLoading = true
                const { data } = await this.$http.get('/chat/message/action_info/', {
                    params: {
                        message: this.messageItem.message_uid,
                        chat: this.messageItem.chat || this.messageItem.chat_uid
                    }
                })
                if(data?.actions) {
                    this.actions = data.actions
                }
            } catch(e) {
                console.log(e)
            } finally {
                this.actionLoading = false
            }
        },
        openMobileMenu() {
            this.getActions()
            this.visible = true
        }
    }
}
</script>

<style lang="scss" scoped>
.reaction_option{
    font-size: 18px;
    width: 34px;
    height: 34px;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 50%;
    transition: all 0.3s cubic-bezier(0.645, 0.045, 0.355, 1);
    transform: scale(1);
    &:hover{
        transform: scale(1.1);
    }
    &.active{
        background: #dfedff;
        transform: scale(1.1);
    }
}
</style>
