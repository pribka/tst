<template>
    <div class="comment_block"
         :ref="commentBlockRefName"
         v-element-visibility="onCommentBlockVisibility"
         :class="mainClass || 'w-full'">
        <CommentInput
            v-if="allowComments"
            ref="mainInput"
            :related_object="related_object"
            :model="model"
            :mentionsData="mentionsData"
            :createFounder="createFounder"
            :oneUpload="oneUpload"
            :showEmoji="showEmoji"
            :showFileUpload="showFileUpload"
            :pushNewComment="pushNewComment"
            :blockLeft="blockLeft"
            :setBlockLeft="setBlockLeft"
            :getModalContainer="getModalContainer"
            :showUsers="showUsers"
            :useVisibility="useVisibility"
            :defaultPublic="defaultPublic"
            v-element-visibility="onElementVisibility" />
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
                        :mentionsData="mentionsData"
                        @reaction-change="onCommentReactionChange"
                        @reaction-rollback="onCommentReactionRollback"
                        :bodySelector="bodySelector"
                        :addTaskCheck="addTaskCheck"
                        :toggleNewCommentCount="toggleNewCommentCount"
                        :showEmoji="showEmoji"
                        :updateNewComment="updateNewComment"
                        :shareCheck="shareCheck"
                        :setBlockLeft="setBlockLeft"
                        :useVisibility="useVisibility"
                        :deleteComment="deleteComment"
                        :blockLeft="blockLeft"
                        :closeMainInput="closeMainInput"
                        :showFileUpload="showFileUpload"
                        :extendDrawerZIndex="extendDrawerZIndex"
                        :showUsers="showUsers"
                        :getModalContainer="getModalContainer"
                        :related_object="related_object"
                        :pushNewComment="pushNewComment"
                        :updateComment="updateComment"
                        :model="model" />
                </transition-group>
            </div>
        </div>
        <template v-if="commentLimit">
            <div
                v-if="list.count > limitCount && list.next"
                class="flex justify-center">
                <a-button
                    type="ui"
                    ghost
                    :loading="loading"
                    @click="getCommentLimit()">
                    {{ $t('comment.loadMore', { count: list.count - visibleComment }) }}
                </a-button>
            </div>
        </template>
        <infinite-loading
            v-else
            ref="comment_infinity"
            @infinite="getCommentInfinite"
            v-bind:distance="10">
            <div
                slot="spinner"
                class="flex items-center justify-center mt-3">
                <a-spin />
            </div>
            <div slot="no-more"></div>
            <div slot="no-results"></div>
        </infinite-loading>
        <CommentModal
            :model="model"
            :related_object="related_object"
            :commentDateTimeFormat="commentDateTimeFormat"
            :pPushNewComment="pushNewComment"
            :pDeleteComment="deleteComment"
            :allowComments="allowComments"
            :createFounder="createFounder"
            :oneUpload="oneUpload"
            :blockLeft="blockLeft"
            :mentionsData="mentionsData"
            :setBlockLeft="setBlockLeft"
            :spliceComment="spliceComment"
            :showUsers="showUsers"
            :showEmoji="showEmoji"
            :getModalContainer="getModalContainer"
            :showFileUpload="showFileUpload" />
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

<script>
import axiosMain from 'axios'
import { mapState } from 'vuex'
import eventBus from './eventBus'
import gEventBus from '@/utils/eventBus'
import { vElementVisibility } from '@vueuse/components'
import { socketEmitJoin, socketEmitLeave } from '@/utils/socketUtils.js'
import { errorHandler } from '@/utils/index.js'
import { mainProps } from './initProps.js'
export default {
    name: 'Comments',
    components: {
        CommentInput: () => import('./CommentInput.vue'),
        CommentItem: () => import('./CommentItem.vue'),
        InfiniteLoading: () => import('vue-infinite-loading'),
        GroupLabel: () => import('./GroupLabel.vue'),
        CommentModal: () => import('./CommentModal.vue')
    },
    directives: {
        ElementVisibility: vElementVisibility
    },
    props: {...mainProps},
    computed: {
        ...mapState({
            user: state => state.user.user
        }),
        sortedList() {
            const res = [...this.list.results].map(item => {
                return {
                    ...item,
                    key: this.$moment(item.created_at).format('YYYY-MM-DD'),
                    auid: item.author?.id || null
                }
            }).reduce((accumulator, currentValue, currentIndex, array, key = currentValue.key) => {
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
        socketRoomName() {
            const s = this.suffix_socket_name ? `${this.suffix_socket_name}` : ''
            return `detail_${s}${this.related_object}`
        },
        commentBlockRefName() {
            const s = this.suffix_socket_name ? `${this.suffix_socket_name}` : ''
            return `commentBlock_${s}${this.related_object}`
        }
    },
    data() {
        return {
            loading: false,
            scrollParent: null,
            page: 0,
            slice_count: 0,
            newComment: 0,
            visibleComment: 0,
            inputVisible: true,
            blockLeft: false,
            page_size: 15,
            limitLoaded: false,
            limitLoadedNext: false,
            viewersDebounceMs: 600,
            viewersFlushTimer: null,
            viewersRequestSource: null,
            pendingViewerCommentIds: new Set(),
            commentVisibilityInstanceKey: `comment_visibility_${this._uid}`,
            list: {
                results: [],
                count: 0,
                next: true
            }
        }
    },
    created() {
        const blockLeft = localStorage.getItem('blockLeft')
        if(blockLeft)
            this.blockLeft = JSON.parse(blockLeft)
        if(this.commentLimit)
            this.getCommentLimit()

        if(this.initScroll && this.$route.query?.comment && this.page === 0)
            this.getCommentInfinite()
    },
    sockets: {
        comment_reaction({ data }) {
            if(data)
                this.applyCommentReactionSocket(data)
        },
        create_comment({ data }) {
            if(data.related_object === this.related_object) {
                this.pushNewComment({
                    ...data,
                    newComment: this.user?.id === data.author?.id ? false : true,
                    newVisible: this.user?.id === data.author?.id ? false : true
                })
                this.queueViewerComment(data)
            }
        },
        update_comment({data}) {
            if(data.related_object === this.related_object)
                this.updateComment(data)
        },
        delete_comment({ data }) {
            this.spliceComment(data)
        }
    },
    methods: {
        onCommentReactionChange({ commentId, nextReaction }) {
            this.applyCommentReactionLocal({ commentId, reaction: nextReaction })
        },
        onCommentReactionRollback({ commentId, prevSnapshot }) {
            const index = this.list.results.findIndex(c => c.id === commentId)
            if (index === -1) return
            this.$set(this.list.results[index], 'reactions', prevSnapshot)
        },
        applyCommentReactionLocal({ commentId, reaction }) {
            const index = this.list.results.findIndex(c => c.id === commentId)
            if(index === -1) return

            const current = this.list.results[index]
            const reactions = Array.isArray(current.reactions) ? current.reactions : []
            let nextReactions = reactions.slice()

            const myIndex = nextReactions.findIndex(r => r.my_reaction)

            // снять реакцию
            if (reaction === null) {
                if (myIndex !== -1) {
                    const item = nextReactions[myIndex]
                    if (item.users_count > 1) {
                        nextReactions[myIndex] = {
                            ...item,
                            users_count: item.users_count - 1,
                            my_reaction: false
                        }
                    } else {
                        nextReactions.splice(myIndex, 1)
                    }
                }
                this.$set(this.list.results[index], 'reactions', nextReactions)
                return
            }

            // если была моя реакция — убрать её (или оставить, если та же самая)
            if (myIndex !== -1) {
                const myItem = nextReactions[myIndex]

                // повторный клик по той же реакции — считаем как "ничего не делаем"
                // (или если у тебя по UX повторный клик снимает — тогда тут reaction=null вызывай)
                if (String(myItem.reaction.id) === String(reaction.id)) {
                    this.$set(this.list.results[index], 'reactions', nextReactions)
                    return
                }

                if (myItem.users_count > 1) {
                    nextReactions[myIndex] = {
                        ...myItem,
                        users_count: myItem.users_count - 1,
                        my_reaction: false
                    }
                } else {
                    nextReactions.splice(myIndex, 1)
                }
            }

            // добавить/увеличить новую реакцию
            const existIndex = nextReactions.findIndex(r => String(r.reaction.id) === String(reaction.id))
            if (existIndex !== -1) {
                const item = nextReactions[existIndex]
                nextReactions[existIndex] = {
                    ...item,
                    users_count: item.users_count + 1,
                    my_reaction: true
                }
            } else {
                nextReactions.push({
                    my_reaction: true,
                    users_count: 1,
                    reaction
                })
            }

            this.$set(this.list.results[index], 'reactions', nextReactions)
        },
        applyCommentReactionSocket(data) {
            const commentId = data?.comment
            if(!commentId) return

            const index = this.list.results.findIndex(c => c.id === commentId)
            if(index === -1) return

            const oldReactions = Array.isArray(this.list.results[index].reactions)
                ? this.list.results[index].reactions
                : []

            const freshReactions = Array.isArray(data?.reactions) ? data.reactions : []

            // сохраним мой флаг по reaction.id
            const oldMap = {}
            oldReactions.forEach(r => {
                const rid = r?.reaction?.id
                if (rid != null) oldMap[String(rid)] = (r.my_reaction === true || r.my_reaction === 1 || r.my_reaction === '1')
            })

            const nextReactions = freshReactions.map(r => {
                const rid = r?.reaction?.id
                return {
                    ...r,
                    my_reaction: rid != null ? oldMap[String(rid)] === true : false
                }
            })

            this.$set(this.list.results[index], 'reactions', nextReactions)
        },
        setBlockLeft() {
            this.blockLeft = !this.blockLeft
            localStorage.setItem('blockLeft', JSON.stringify(this.blockLeft))
        },
        closeMainInput() {
            this.$refs.mainInput.closeEditorHandler()
        },
        getModalContainer() {
            if(this.modalContainer) {
                if(this.injectContainer) {
                    return this.injectContainerSelector()
                } else
                    return this.$refs[this.commentBlockRefName]
            } else
                return document.body
        },
        onElementVisibility(e) {
            this.inputVisible = e
        },
        onCommentBlockVisibility(visible) {
            this.$store.commit('comments/SET_COMMENT_VISIBILITY', {
                relatedObject: this.related_object,
                instanceKey: this.commentVisibilityInstanceKey,
                visible
            })
        },
        getScrollParent(elm = this.$el) {
            let result;

            if (!result) {
                if (elm.tagName === 'BODY') {
                    result = window;
                } else if (['scroll', 'auto'].indexOf(getComputedStyle(elm).overflowY) > -1) {
                    result = elm;
                } else if (elm.hasAttribute('infinite-wrapper') || elm.hasAttribute('data-infinite-wrapper')) {
                    result = elm;
                }
            }

            return result || this.getScrollParent(elm.parentNode);
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
            if(index !== -1)
                this.$delete(this.list.results[index], 'newComment')
        },
        updateComment(data) {
            if(this.list.results.length) {
                const index = this.list.results.findIndex(f => f.id === data.id)
                if(index !== -1) {
                    const newData = {
                        ...data,
                        reactions: this.list.results[index]?.reactions || []
                    }
                    this.$set(this.list.results, index, newData)
                }
            }
        },
        pushNewComment(data) {
            const find = this.list.results.find(f => f.id === data.id)
            if(find) return
            this.list.results.unshift({
                ...data,
                created_at: this.$moment(data.created_at).add(-1, 'seconds').format()
            })
            this.list.count += 1
            if(this.commentLimit) {
                if(this.limitLoadedNext)
                    this.slice_count += 1
            } else {
                this.slice_count += 1
            }
        },
        queueViewerComment(comment) {
            const commentId = comment?.id
            const authorId = comment?.author?.id
            if (!commentId) return
            if (String(authorId) === String(this.user?.id)) return

            this.pendingViewerCommentIds.add(String(commentId))
            this.scheduleViewersFlush()
        },
        scheduleViewersFlush() {
            if (this.viewersFlushTimer) {
                clearTimeout(this.viewersFlushTimer)
            }

            if (this.viewersRequestSource) {
                this.viewersRequestSource.cancel('Viewers request cancelled')
                this.viewersRequestSource = null
            }

            this.viewersFlushTimer = setTimeout(() => {
                this.viewersFlushTimer = null
                this.flushViewerComments()
            }, this.viewersDebounceMs)
        },
        async flushViewerComments() {
            const ids = Array.from(this.pendingViewerCommentIds)
            if (!ids.length) return

            const source = axiosMain.CancelToken.source()
            this.viewersRequestSource = source
            let shouldRetry = false

            try {
                await this.$http.post('/viewers/', {
                    obj: ids
                }, {
                    cancelToken: source.token
                })

                ids.forEach(id => {
                    this.pendingViewerCommentIds.delete(id)
                })
            } catch(error) {
                const isCanceled = axiosMain.isCancel?.(error) || error?.code === 'ERR_CANCELED'
                shouldRetry = isCanceled
                if (!isCanceled) {
                    errorHandler({ error, show: false })
                }
            } finally {
                if (this.viewersRequestSource === source) {
                    this.viewersRequestSource = null
                }

                if (!this.viewersFlushTimer && this.pendingViewerCommentIds.size && shouldRetry) {
                    this.viewersFlushTimer = setTimeout(() => {
                        this.viewersFlushTimer = null
                        this.flushViewerComments()
                    }, this.viewersDebounceMs)
                }
            }
        },
        spliceComment(id) {
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
                        this.$set(this.list.results[cIndex].parent, 'text', this.$t('comment.commentDeleted')) // Комментарий удалён / Пікір жойылды
                    }
                })
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
                    } catch(error) {
                        errorHandler({error})
                    }
                }
            })
        },
        async getCommentLimit() {
            try {
                this.page += 1
                this.loading = true

                const params = {
                    page: this.page,
                    reverse: true
                }

                if(this.limitLoaded) {
                    if(this.page > 1) {
                        if(this.slice_count)
                            params.slice_count = this.slice_count
                    }
                    params.page_size = 15
                } else {
                    params.page_size = this.limitCount || 2
                }

                if(this.model)
                    params.model = this.model
                if(this.related_object)
                    params.related_object = this.related_object

                const { data } = await this.$http.get('/comments/', { params })

                if(data) {
                    this.list.count = data.count
                    this.list.next = data.next
                }
                if(data?.results?.length) {
                    if(this.limitLoaded && this.page === 1) {
                        if(!this.limitLoadedNext)
                            this.limitLoadedNext = true
                        this.list.results = data.results
                    } else {
                        this.list.results = this.list.results.concat(data.results)
                    }
                    this.visibleComment = this.list.results.length
                }
                if(!this.limitLoaded) {
                    this.page = 0
                    this.limitLoaded = true
                }
            } catch(error) {
                errorHandler({error, show: false})
            } finally {
                this.loading = false
            }
        },
        async getCommentInfinite($state = null) {
            if(!this.loading && this.list.next) {
                try {
                    this.loading = true
                    this.page += 1

                    const params = {
                        page: this.page,
                        page_size: 15,
                        reverse: true
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
                        this.list.results = this.list.results.concat(data.results)

                    if(this.initScroll && this.$route.query?.comment && this.page === 1) {
                        this.$nextTick(() => {
                            const query = JSON.parse(JSON.stringify(this.$route.query))
                            delete query.comment
                            this.$router.replace({query})
                            setTimeout(() => {
                                this.parentTopScroll()
                            }, 300)
                        })
                    }

                    if(this.list.next) {
                        if($state) {
                            this.$nextTick(() => {
                                $state.loaded()
                            })
                        }
                            
                    }
                    else {
                        if($state) {
                            this.$nextTick(() => {
                                $state.complete()
                            })
                        }
                    }
                } catch(error) {
                    errorHandler({error, show: false})
                } finally {
                    this.loading = false
                }
            } else {
                if($state)
                    $state.complete()
            }
        },
        scrollHandler(e) {
            // console.log(e, 'scrollHandler')
        },
        parentTopScroll() {
            if(this.scrollParent) {
                this.newComment = 0
                const obj = this.$refs[this.commentBlockRefName]
                const posX = obj.offsetTop
                this.scrollParent.scrollTop = posX - 100
                // this.scrollParent.scroll({top:0, behavior:'smooth'})
            }
        }
    },
    mounted() {
        this.$store.dispatch('comments/getReactions')
        this.$store.commit('comments/REGISTER_COMMENT_VISIBILITY', {
            relatedObject: this.related_object,
            instanceKey: this.commentVisibilityInstanceKey
        })
        this.scrollParent = this.getScrollParent()
        socketEmitJoin(this.socketRoomName)
        /*setTimeout(() => {
            this.scrollHandler()
            this.scrollParent.addEventListener('scroll', this.scrollHandler, evt3rdArg)
        }, 1)*/

        eventBus.$on('comment_reaction_local', ({ commentId, nextReaction }) => {
            this.applyCommentReactionLocal({ commentId, reaction: nextReaction })
        })

        eventBus.$on('comment_reaction_rollback', ({ commentId, prevSnapshot }) => {
            const index = this.list.results.findIndex(c => c.id === commentId)
            if (index !== -1) this.$set(this.list.results[index], 'reactions', prevSnapshot)
        })

        eventBus.$on('set_comment_shaking', cid => {
            if(cid) {
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
        })
        gEventBus.$on(`comment_task_added_${this.related_object}`, obj => {
            if(obj?.item && this.list?.results?.length) {
                const index = this.list.results.findIndex(f => f.id === obj.item)
                if(index !== -1) {
                    const count = this.list.results[index]?.task_count || 0
                    this.$set(this.list.results[index], 'task_count', count+1)
                }
            }
        })        
    },
    beforeDestroy() {
        if (this.viewersFlushTimer) {
            clearTimeout(this.viewersFlushTimer)
            this.viewersFlushTimer = null
        }
        if (this.viewersRequestSource) {
            this.viewersRequestSource.cancel('Comments component destroyed')
            this.viewersRequestSource = null
        }
        this.pendingViewerCommentIds.clear()
        this.$store.commit('comments/UNREGISTER_COMMENT_VISIBILITY', {
            relatedObject: this.related_object,
            instanceKey: this.commentVisibilityInstanceKey
        })
        socketEmitLeave(this.socketRoomName)
        eventBus.$off('comment_reaction_local')
        eventBus.$off('comment_reaction_rollback')
        eventBus.$off('set_comment_shaking')
        gEventBus.$off(`comment_task_added_${this.related_object}`)
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
.comment_block{
    position: relative;
}
.comment_group{
    &:not(:last-child){
        margin-bottom: 18px;
    }
    .comment_list-item {
        display: inline-block;
        margin-right: 10px;
    }
    .comment_list-enter-active, .comment_list-leave-active {
        transition: all 0.3s;
    }
    .comment_list-enter, .comment_list-leave-to {
        opacity: 0;
        transform: translateY(30px);
    }
}
.new_comment{
    position: sticky;
    bottom: 40px;
    height: 0px;
    z-index: 100;
    display: flex;
    justify-content: flex-end;
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
</style>
