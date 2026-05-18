<template>
    <ActivityDrawer v-model="visible" @afterVisibleChange="afterVisibleChange">
        <ActivityItem v-if="reactions && reactions.length">
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
            v-if="item.reactions && item.reactions.length"
            icon="fi-rr-smile"
            @click="openReactionModal()">
            {{ $t('chat.reactions') }}
        </ActivityItem>
        <ActivityItem v-if="reply" key="reply" @click="openResponseForm()">
            <i class="fi fi-rr-undo mr-2" />
            {{ $t('comment.reply') }}
        </ActivityItem>
        <ActivityItem v-if="canManageOwnComment" key="edit" @click="openEdit()">
            <i class="fi fi-rr-edit mr-2" />
            {{ $t('comment.edit') }}
        </ActivityItem>
        <ActivityItem v-if="openCheck" key="open" @click="openComment(item.id)">
            <i class="fi fi-rr-comment-alt-dots mr-2" />
            {{ $t('comment.openComment') }}
        </ActivityItem>
        <ActivityItem v-if="addTaskCheck" key="task" @click="addTask()">
            <i class="fi fi-rr-list-check mr-2" />
            {{ $t('comment.addTask') }}
        </ActivityItem>
        <ActivityItem v-if="item.task_count" key="task_reason" @click="openTaskModal()">
            <i class="fi fi-rr-link-alt mr-2" />
            {{ $t('comment.task_reason') }}
        </ActivityItem>
        <ActivityItem v-if="copyCheck" key="copy" @click="copyItem()">
            <i class="fi fi-rr-copy-alt mr-2" />
            {{ $t('comment.copy') }}
        </ActivityItem>
        <ActivityItem v-if="shareCheck" key="share" @click="share()">
            <i class="fi fi-rr-share mr-2" />
            {{ $t('comment.share') }}
        </ActivityItem>

        <template v-if="myComment">
            <ActivityItem v-if="viewCount && viewUsers && viewUsers.length" key="views" @click="openViewsModal()">
                <i class="fi fi-rr-eye mr-2" />
                <a-spin :spinning="viewLoading" size="small">
                    {{ viewCountText }}
                </a-spin>
            </ActivityItem>
            <ActivityItem v-else key="empty_views">
                <i class="fi fi-rr-eye mr-2" />
                <a-spin :spinning="viewLoading" size="small">
                    {{ viewCountText }}
                </a-spin>
            </ActivityItem>
        </template>

        <ActivityItem v-if="canManageOwnComment" key="delete" @click="removeHandler()">
            <div class="text-red-500 flex items-center">
                <i class="fi fi-rr-trash mr-2" />
                {{ $t('comment.delete') }}
            </div>
        </ActivityItem>
    </ActivityDrawer>
</template>

<script>
import { ActivityItem, ActivityDrawer } from '@/components/ActivitySelect'
import { errorHandler } from '@/utils/index.js'
import { declOfNum } from '@/utils/utils.js'
export default {
    components: {
        ActivityItem, 
        ActivityDrawer
    },
    props: {
        openReactionModal: {
            type: Function,
            default: () => {}
        },
        reactions: {
            type: Array,
            default: () => []
        },
        selectReaction: {
            type: Function,
            default: () => {}
        },
        isMyReaction: {
            type: Function,
            default: () => {}
        },
        item: {
            type: Object,
            required: true
        },
        myComment: {
            type: Boolean,
            default: false
        },
        viewCount: {
            type: Number,
            default: 0
        },
        openTaskModal: {
            type: Function,
            default: () => {}
        },
        openResponseForm: {
            type: Function,
            default: () => {}
        },
        openEdit: {
            type: Function,
            default: () => {}
        },
        openViewsModal: {
            type: Function,
            default: () => {}
        },
        openComment: {
            type: Function,
            default: () => {}
        },
        addTask: {
            type: Function,
            default: () => {}
        },
        share: {
            type: Function,
            default: () => {}
        },
        removeHandler: {
            type: Function,
            default: () => {}
        },
        reply: {
            type: Boolean,
            default: true
        },
        user: {
            type: Object,
            required: true
        },
        openCheck: {
            type: Boolean,
            default: true
        },
        addTaskCheck: {
            type: Boolean,
            default: true
        },
        shareCheck: {
            type: Boolean,
            default: true
        },
        copyCheck: {
            type: Boolean,
            default: true
        }
    },
    computed: {
        isOwnComment() {
            const authorId = this.item?.author?.id
            const userId = this.user?.id
            if (!authorId || !userId)
                return false
            return String(userId) === String(authorId)
        },
        canManageOwnComment() {
            return this.isOwnComment && !this.item?.is_system
        },
        viewCountText() {
            if(this.viewLoading)
                return this.$t('comment.view4')
            if(!this.viewUsers?.length)
                return this.$t('comment.no_view')
            return `${this.viewCount} ${declOfNum(this.viewCount, [this.$t('comment.view1'), this.$t('comment.view2'), this.$t('comment.view3')])}`
        },
    },
    data() {
        return {
            visible: false,
            viewUsers: [],
            viewLoading: false
        }
    },
    methods: {
        async getViewUser() {
            if(!this.viewUsers?.length && this.myComment) {
                try {
                    this.viewLoading = true
                    const { data } = await this.$http.get('/viewers/', {
                        params: {
                            related_object: this.item.id,
                            page_size: 31
                        }
                    })

                    if(data?.results?.length) {
                        this.viewUsers = data.results.filter(
                            u => u.id !== this.user.id
                        )
                    }
                } catch(error) {
                    errorHandler({ error })
                } finally {
                    this.viewLoading = false
                }
            }
        },
        afterVisibleChange(vis) {
            if(vis) {
                this.$store.dispatch('comments/getReactions')
                this.getViewUser()
            }
        },
        openDrawer() {
            this.visible = true
        },
        copyItem() {
            try {
                navigator.clipboard.writeText(this.item.text_clear)
                this.$message.info(this.$t('comment.messageCopied'))
            } catch(e) {
                console.log(e)
                this.$message.error(this.$t('comment.copyError'))
            }
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
