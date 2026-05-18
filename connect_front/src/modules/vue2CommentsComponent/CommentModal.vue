<template>
    <a-modal 
        v-model="visible" 
        title=""
        :width="600"
        :dialog-style="{ top: isMobile ? '0px' : '20px' }"
        class="comment_modal"
        ref="commentModal"
        :afterClose="afterClose">
        <template #footer>
            <div class="w-full relative">
                <CommentInput
                    v-if="allowComments && comment"
                    :related_object="related_object"
                    :model="model"
                    :createFounder="createFounder"
                    :oneUpload="oneUpload"
                    :parent="comment"
                    modal
                    :mentionsData="mentionsData"
                    :blockLeft="blockLeft"
                    :setBlockLeft="setBlockLeft"
                    :getModalContainer="getInModalContainer"
                    :inputPlaceholder="$t('comment.reply_to_comment')"
                    :showEmoji="showEmoji"
                    :showFileUpload="showFileUpload"
                    :pushNewComment="pushNewComment"
                    :showUsers="showUsers" />
                <transition v-if="list.results.length" name="slide-up-fade">
                    <div 
                        v-if="!inputVisible" 
                        class="new_comment">
                        <a-badge 
                            :count="newComment"
                            :number-style="{
                                backgroundColor: '#1c65c0'
                            }">
                            <a-button
                                shape="circle"
                                flaticon
                                icon="fi-rr-angle-small-up"
                                @click="parentTopScroll()" />
                        </a-badge>
                    </div>
                </transition>
            </div>
        </template>
        <template #closeIcon>
            <a-button 
                type="ui" 
                ghost 
                flaticon 
                shape="circle"
                icon="fi-rr-cross" />
        </template>
        <a-spin :spinning="detailLoading" class="w-full">
            <template v-if="comment">
                <div 
                    class="current_comment" 
                    ref="currentComment" 
                    v-element-visibility="onElementVisibility">
                    <CommentItem 
                        :item="comment" 
                        :user="user"
                        :commentDateTimeFormat="commentDateTimeFormat"
                        modal
                        :mentionsData="mentionsData"
                        :deleteComment="deleteCurrentComment"
                        :setBlockLeft="setBlockLeft"
                        :openCheck="false"
                        :extendDrawerZIndex="1050"
                        :reply="false"
                        :related_object="related_object"
                        :model="model"
                        @reaction-change="onReactionChangeModal"
                        @reaction-rollback="onReactionRollbackModal" />
                </div>
                <div
                    v-if="list.results.length"
                    class="pt-6">
                    <div 
                        v-for="(group, index) in sortedList" 
                        :key="index" 
                        class="comment_group">
                        <GroupLabel :group="group" />
                        <transition-group name="comment_list" tag="div">
                            <CommentItem
                                v-for="item in group.data"
                                :key="item.id"
                                :user="user"
                                :item="item"
                                :commentDateTimeFormat="commentDateTimeFormat"
                                :reply="false"
                                :mentionsData="mentionsData"
                                :setBlockLeft="setBlockLeft"
                                :blockLeft="blockLeft"
                                :extendDrawerZIndex="1050"
                                :toggleNewCommentCount="toggleNewCommentCount"
                                :updateNewComment="updateNewComment"
                                :deleteComment="deleteComment"
                                :related_object="related_object"
                                :pushNewComment="pushNewComment"
                                :model="model"
                                @reaction-change="onReactionChangeModal"
                                @reaction-rollback="onReactionRollbackModal" />
                        </transition-group>
                    </div>
                </div>
                <infinite-loading 
                    ref="comment_m_infinity"
                    @infinite="getCommentInfinite"
                    :identifier="comment.id"
                    v-bind:distance="10">
                    <div 
                        slot="spinner"
                        class="flex items-center justify-center mt-3">
                        <a-spin />
                    </div>
                    <div slot="no-more"></div>
                    <div slot="no-results"></div>
                </infinite-loading>
            </template>
        </a-spin>
    </a-modal>
</template>

<script>
import eventBus from './eventBus.js'
import { mapState } from 'vuex'
import { vElementVisibility } from '@vueuse/components'
import { errorHandler } from '@/utils/index.js'
import { modalProps } from './initProps.js'
export default {
    components: {
        CommentItem: () => import('./CommentItem.vue'),
        GroupLabel: () => import('./GroupLabel.vue'),
        InfiniteLoading: () => import('vue-infinite-loading'),
        CommentInput: () => import('./CommentInput.vue')
    },
    props: {...modalProps},
    directives: {
        ElementVisibility: vElementVisibility
    },
    computed: {
        ...mapState({
            user: state => state.user.user
        }),
        sortedList() {
            const list = [...this.list.results].map(item => {
                return {
                    ...item,
                    key: this.$moment(item.created_at).format('YYYY-MM-DD')
                }
            })

            const res = list.reduce((accumulator, currentValue, currentIndex, array, key = currentValue.key) => {
                const keyObjectPosition = accumulator.findIndex((item) => item.key === key)
                if (keyObjectPosition >= 0) {
                    accumulator[keyObjectPosition].data.push(currentValue)
                    return accumulator    
                } else {
                    return accumulator.concat({ data: [currentValue], key: key })
                }
            }, [])

            return res
        },
        isMobile() {
            return this.$store.state.isMobile
        }
    },
    data() {
        return {
            visible: false,
            loading: false,
            comment: null,
            detailLoading: false,
            page: 0,
            inputVisible: true,
            slice_count: 0,
            newComment: 0,
            list: {
                results: [],
                count: 0,
                next: true
            }
        }
    },
    sockets: {
        comment_reaction({ data }) {
            if (!this.visible || !data) return
            const commentId = data?.comment
            if (!commentId) return
            const fresh = Array.isArray(data.reactions) ? data.reactions : []

            if (this.comment && this.comment.id === commentId) {
                const next = this.mergeReactionsPreserveMy(this.comment.reactions, fresh)
                this.$set(this.comment, 'reactions', next)
                return
            }

            const idx = this.list.results.findIndex(c => c.id === commentId)
            if (idx === -1) return
            const next = this.mergeReactionsPreserveMy(this.list.results[idx].reactions, fresh)
            this.$set(this.list.results[idx], 'reactions', next)
        },
        create_comment({ data }) {
            if(this.visible && this.comment?.id === data.parent?.id) {
                this.pushNewComment({
                    ...data,
                    newComment: this.user?.id === data.author?.id ? false : true,
                    newVisible: this.user?.id === data.author?.id ? false : true
                })
            }
        },
        update_comment({data}) {
            if(this.visible && this.comment) {
                this.updateComment(data)
                if(this.comment.id === data.id) {
                    this.comment = data
                }
            }
        },
        delete_comment({ data }) {
            if(this.visible && this.comment) {
                this.deleteCommentHandler(data)
                if(this.comment.id === data) {
                    this.visible = false
                    this.$message.info('Данный комментарий удален')
                }
            }
        }
    },
    methods: {
        hasCommentById(id) {
            if (!id) return false
            return this.list.results.some(item => String(item.id) === String(id))
        },
        mergeUniqueById(target = [], incoming = []) {
            const map = new Map()

            target.forEach(item => {
                if (item && item.id != null) {
                    map.set(String(item.id), item)
                }
            })

            incoming.forEach(item => {
                if (!item || item.id == null) return
                map.set(String(item.id), item)
            })

            return Array.from(map.values())
        },
        mergeReactionsPreserveMy(oldReactions, freshReactions) {
            const old = Array.isArray(oldReactions) ? oldReactions : []
            const fresh = Array.isArray(freshReactions) ? freshReactions : []

            const oldMap = {}
            old.forEach(r => {
                const rid = r?.reaction?.id
                if (rid != null) oldMap[String(rid)] = this.isMyFlag(r.my_reaction)
            })

            return fresh.map(r => {
                const rid = r?.reaction?.id
                return {
                    ...r,
                    my_reaction: rid != null ? oldMap[String(rid)] === true : false
                }
            })
        },
        isMyFlag(v) {
            return v === true || v === 1 || v === '1' || v === 'true'
        },
        onReactionChangeModal({ commentId, nextReaction }) {
            if (this.comment && this.comment.id === commentId) {
                const next = this.computeNextReactions(this.comment.reactions, nextReaction)
                this.$set(this.comment, 'reactions', next)
                return
            }

            const idx = this.list.results.findIndex(c => c.id === commentId)
            if (idx === -1) return

            const cur = this.list.results[idx]
            const next = this.computeNextReactions(cur.reactions, nextReaction)
            this.$set(this.list.results[idx], 'reactions', next)

            eventBus.$emit('comment_reaction_local', { commentId, nextReaction })
        },

        onReactionRollbackModal({ commentId, prevSnapshot }) {
            if (this.comment && this.comment.id === commentId) {
                this.$set(this.comment, 'reactions', prevSnapshot)
                return
            }
            const idx = this.list.results.findIndex(c => c.id === commentId)
            if (idx === -1) return
            this.$set(this.list.results[idx], 'reactions', prevSnapshot)

            eventBus.$emit('comment_reaction_rollback', { commentId, prevSnapshot })
        },

        computeNextReactions(currentReactions, nextReaction) {
            const reactions = Array.isArray(currentReactions) ? currentReactions : []
            let next = reactions.slice()

            const myIndex = next.findIndex(r => r.my_reaction)

            // снять реакцию
            if (nextReaction === null) {
                if (myIndex !== -1) {
                    const item = next[myIndex]
                    if ((item.users_count || 1) > 1) {
                        next[myIndex] = { ...item, users_count: item.users_count - 1, my_reaction: false }
                    } else {
                        next.splice(myIndex, 1)
                    }
                }
                return next
            }

            if (myIndex !== -1) {
                const myItem = next[myIndex]
                if (String(myItem.reaction.id) === String(nextReaction.id)) {
                    return next
                }

                if ((myItem.users_count || 1) > 1) {
                    next[myIndex] = { ...myItem, users_count: myItem.users_count - 1, my_reaction: false }
                } else {
                    next.splice(myIndex, 1)
                }
            }

            // добавить/увеличить новую
            const existIndex = next.findIndex(r => String(r.reaction.id) === String(nextReaction.id))
            if (existIndex !== -1) {
                const item = next[existIndex]
                next[existIndex] = { ...item, users_count: (item.users_count || 0) + 1, my_reaction: true }
            } else {
                next.push({ my_reaction: true, users_count: 1, reaction: nextReaction })
            }

            return next
        },
        onElementVisibility(e) {
            this.inputVisible = e
        },
        getInModalContainer() {
            return document.body
        },
        toggleNewCommentCount(type, id = null) {
            if(type === 'add') {
                this.newComment += 1
            }
            if(type === 'min') {
                if(this.newComment > 0)
                    this.newComment -= 1
                if(id) {
                    const index = this.list.results.findIndex(f => f.id === id)
                    if(index !== -1)
                        this.$delete(this.list.results[index], 'newVisible')
                }
            }
        },
        updateNewComment(id) {
            const index = this.list.results.findIndex(f => f.id === id)
            if(index !== -1) {
                this.$delete(this.list.results[index], 'newComment')
            }
        },
        updateComment(data) {
            if(this.list.results.length) {
                const index = this.list.results.findIndex(f => f.id === data.id)
                if(index !== -1)
                    this.$set(this.list.results, index, data)
            }
        },
        deleteCommentHandler(id) {
            const index = this.list.results.findIndex(f => f.id === id)
            if(index !== -1) {
                this.list.results.splice(index, 1)
                this.list.count -= 1
                if(this.slice_count > 0)
                    this.slice_count -= 1
            }
            const cParent = this.list.results.filter(f => f.parent?.id === id)
            if(cParent?.length) {
                cParent.forEach(item => {
                    const cIndex = this.list.results.findIndex(f => f.id === item.id)
                    if(cIndex !== -1) {
                        this.$set(this.list.results[cIndex].parent, 'text', 'Комментарий удалён')
                    }
                })
            }
        },
        async deleteCurrentComment(id) {
            try {
                await this.$http.post('/comments/delete/', { id })
            } catch(error) {
                errorHandler({error})
            }
        },
        async deleteComment(id) {
            this.$confirm({
                title: this.$t('comment.comment_remove_message'),
                okText: this.$t('remove'),
                cancelText: this.$t('cancel'),
                onOk: async () => {
                    try {
                        await this.$http.post('/comments/delete/', { id })
                        /*if(data === 'ok') {
                            this.list.count -= 1
                            const index = this.list.results.findIndex(f => f.id === id)
                            if(index !== -1) {
                                this.list.results.splice(index, 1)
                            }
                            this.spliceComment(id)
                        }*/
                    } catch(error) {
                        errorHandler({error})
                    }
                }
            })
        },
        pushNewComment(data) {
            if (!data?.id) return

            const nextItem = {
                ...data,
                created_at: this.$moment(data.created_at).add(-1, 'seconds').format()
            }

            const index = this.list.results.findIndex(item => String(item.id) === String(data.id))
            if (index !== -1) {
                this.$set(this.list.results, index, {
                    ...this.list.results[index],
                    ...nextItem
                })
                return
            }

            this.list.results.unshift(nextItem)
            this.list.count += 1
            this.slice_count += 1
        },
        clear() {
            this.inputVisible = true
            this.comment = null
            this.list = {
                results: [],
                count: 0,
                next: true
            }
            this.slice_count = 0
            this.page = 0
            this.newComment = 0
        },
        afterClose() {
            this.clear()
        },
        async getComment(id, cid = null) {
            try {
                this.detailLoading = true
                const { data } = await this.$http.get(`/comments/${id}/`)
                if(data) {
                    this.comment = data
                }
            } catch(error) {
                if(error?.detail === 'Страница не найдена.') {
                    this.visible = false
                    this.$message.info('Данный комментарий удален')
                    if(cid)
                        eventBus.$emit('set_comment_shaking', cid)
                }
                console.log(error)
            } finally {
                this.detailLoading = false
            }
        },
        async getCommentInfinite($state) {
            if(!this.loading && this.list.next) {
                try {
                    this.loading = true
                    this.page += 1

                    const params = {
                        page: this.page,
                        page_size: 15,
                        reverse: true,
                        parent: this.comment.id
                    }

                    if(this.slice_count)
                        params.slice_count = this.slice_count
                    if(this.model)
                        params.model = this.model
                    if(this.related_object)
                        params.related_object = this.related_object

                    const { data } = await this.$http.get('/comments/', { params })

                    if(data) {
                        this.list.count = data.count
                        this.list.next = data.next
                    }

                    if(data?.results?.length)
                        this.list.results = this.mergeUniqueById(this.list.results, data.results)
                        
                    if(this.list.next)
                        $state.loaded()
                    else
                        $state.complete()
                } catch(e) {
                    console.log(e)
                } finally {
                    this.loading = false
                }
            } else {
                $state.complete()
            }
        },
        parentTopScroll() {
            if(this.$refs.commentModal?.$el?.children?.length) {
                const modalScroll = this.$refs.commentModal.$el.children[1]
                if(modalScroll)
                    modalScroll.scroll({top:0, behavior:'smooth'})
            }
        }
    },
    mounted() {
        eventBus.$on(`open_comment_detail_${this.related_object}`, (id, cid = null) => {
            if(this.comment?.id === id) {
                if(cid && this.list.results.length) {
                    const index = this.list.results.findIndex(f => f.id === cid)
                    if(index !== -1) {
                        if(this.list.results[index].shaking) {
                            this.$delete(this.list.results[index], 'shaking')
                            setTimeout(() => {
                                this.$set(this.list.results[index], 'shaking', true)
                            }, 5)
                        } else {
                            this.$set(this.list.results[index], 'shaking', true)
                        }
                    }
                }
            } else {
                if(!this.visible)
                    this.visible = true
                if(this.comment)
                    this.clear()
                this.getComment(id, cid)
            }
        })
    },
    beforeDestroy() {
        eventBus.$off(`open_comment_detail_${this.related_object}`)
    }
}
</script>

<style lang="scss" scoped>
.slide-up-fade-enter-active {
  transition: all .2s ease;
}
.slide-up-fade-leave-active {
  transition: all .1s cubic-bezier(1.0, 0.5, 0.8, 1.0);
}
.slide-up-fade-enter, .slide-up-fade-leave-to {
  transform: translateY(10px);
  opacity: 0;
}
.comment_modal{
    &::v-deep{
        .ant-modal-footer{
            position: sticky;
            bottom: 0px;
            z-index: 900;
            background: #ffffff;
            text-align: left;
            padding: 5px 10px;
            border-top: 1px solid var(--borderColor);
        }
    }
    .comment_group{
        .comment_list-enter-active, .comment_list-leave-active {
            transition: all 0.3s;
        }
        .comment_list-enter, .comment_list-leave-to {
            opacity: 0;
            transform: translateY(30px);
        }
    }
    .new_comment{
        position: absolute;
        top: -50px;
        right: 15px;
        &::v-deep{
            .ant-badge{
                .ant-badge-count{
                    font-size: 10px !important;
                    min-width: 17px;
                    height: 17px;
                    padding: 0 6px;
                    line-height: 17px;
                    right: initial;
                    left: 50%;
                    margin-left: -17px;
                    &.ant-badge-multiple-words{
                        margin-left: -23px;
                    }
                }
            }
        }
    }
}
</style>

<style lang="scss">
.comment_modal {
    @media (max-width: 991.98px) {
        .ant-modal {
            top: 0 !important;
            width: 100vw !important;
            max-width: 100vw !important;
            margin: 0 !important;
            padding-bottom: 0 !important;
        }
        .ant-modal-content {
            min-height: 100vh;
            border-radius: 0 !important;
        }
        .ant-modal-body {
            padding: 12px 12px 0 12px;
        }
        .ant-modal-footer {
            padding-left: 10px !important;
            padding-right: 10px !important;
            padding-top: 5px !important;
            padding-bottom: calc(5px + env(safe-area-inset-bottom, 0px)) !important;
        }
        .ant-modal-close {
            top: 8px;
            right: 8px;
        }
    }
}
</style>
