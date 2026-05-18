<template>
    <div
        class="comment"
        :class="[myComment && 'my', item.newComment && 'new', item.shaking && 'shaking', isMobile && 'mobile', isSystemComment && 'system']">
        <div ref="commentItem" class="comment_item">
            <Profiler
                v-if="item.author && !isSystemComment"
                :user="item.author"
                showAvatar
                :class="myComment ? `ml-${isMobile ? 1 : 3}` : `mr-${isMobile ? 1 : 3}`"
                :getPopupContainer="getPopupContainer"
                :showUserName="false"
                initStatus />
            <div class="comment_item__body" :class="[isMobile && 'select-none', isSystemComment && 'comment_item__body--system']">
                <div class="flex" :class="myComment && 'flex-row-reverse'">
                    <div>
                        <div class="flex" :class="myComment && 'justify-end'">
                            <a-spin :spinning="loading">
                                <a-dropdown
                                    :trigger="isMobile ? [] : ['contextmenu']"
                                    :visible="ctxDropdownVisible"
                                    :disabled="useShare"
                                    overlayClassName="comment_drop_menu"
                                    @visibleChange="onCtxVisibleChange">
                                    <div
                                        ref="bodyWrap"
                                        class="body_wrap"
                                        v-touch:longtap="longtapHandler"
                                        v-element-visibility="onElementVisibility"
                                        @contextmenu="onDropdownContextmenu">
                                        <div :class="myComment && 'flex justify-end'">
                                            <Profiler
                                                v-if="item.author && !isSystemComment"
                                                :user="item.author"
                                                :getPopupContainer="getPopupContainer"
                                                nameClass="font-semibold truncate text-xs"
                                                :showAvatar="false" />
                                            <div
                                                v-else-if="isSystemComment"
                                                class="comment_system_label">
                                                {{ $t('comment.system_comment') }}
                                            </div>
                                        </div>

                                        <template v-if="item.parent">
                                            <div
                                                v-if="item.parent.attachments && item.parent.attachments.length"
                                                class="res_comment">
                                                <Profiler
                                                    v-if="item.parent.author"
                                                    :user="item.parent.author"
                                                    :avatarSize="22"
                                                    initStatus
                                                    :getPopupContainer="getPopupContainer"
                                                    nameClass="font-semibold truncate text-xs"
                                                    @click="openComment(item.parent.id, item.id)" />
                                                <div
                                                    v-else
                                                    class="comment_system_label comment_system_label--reply"
                                                    @click="openComment(item.parent.id, item.id)">
                                                    {{ $t('comment.system_comment') }}
                                                </div>
                                                <div @click="openComment(item.parent.id, item.id)">
                                                    <TextViewer
                                                        v-if="item.parent.text"
                                                        collapsible
                                                        overlayColor="#dee6f5"
                                                        :body="item.parent.text" />
                                                </div>
                                                <div ref="lght_wrap_parent" class="comment_files mt-2">
                                                    <CommentFile
                                                        v-for="file in item.parent.attachments"
                                                        :key="file.id"
                                                        :file="file"
                                                        :comment-id="item.parent.id" />
                                                </div>
                                            </div>
                                            <div
                                                v-else
                                                class="res_comment"
                                                @click="openComment(item.parent.id, item.id)">
                                                <Profiler
                                                    v-if="item.parent.author"
                                                    :user="item.parent.author"
                                                    :avatarSize="22"
                                                    initStatus
                                                    :getPopupContainer="getPopupContainer"
                                                    nameClass="font-semibold truncate text-xs" />
                                                <div
                                                    v-else
                                                    class="comment_system_label comment_system_label--reply">
                                                    {{ $t('comment.system_comment') }}
                                                </div>
                                                <TextViewer
                                                    v-if="item.parent.text"
                                                    collapsible
                                                    overlayColor="#dee6f5"
                                                    :body="item.parent.text" />
                                            </div>
                                        </template>

                                        <TextViewer
                                            v-if="item.text"
                                            class="comment_text"
                                            :body="item.text" />

                                        <div
                                            v-if="item.attachments && item.attachments.length"
                                            ref="lght_wrap"
                                            :class="item.text && 'mt-2'"
                                            class="comment_files">
                                            <CommentFile
                                                v-for="file in item.attachments"
                                                :key="file.id"
                                                :file="file"
                                                :comment-id="item.id" />
                                        </div>

                                        <!-- ✅ PRIVACY BADGE -->
                                        <div v-if="useVisibility">
                                            <div
                                                v-if="typeof item.is_personal === 'boolean'"
                                                class="comment_vis_badge"
                                                :class="item.is_personal ? 'private' : 'public'">
                                                <i
                                                    class="fi mr-1"
                                                    :class="item.is_personal ? 'fi-rr-lock' : 'fi-rr-globe'" />
                                                {{ item.is_personal ? $t('comment.private') : $t('comment.public') }}
                                            </div>
                                        </div>


                                        <div class="flex items-center justify-between mt-1 gap-2" :class="myComment && 'justify-end'">
                                            <div class="font-light">
                                                {{ date }}
                                            </div>
                                            <div class="flex items-center gap-2">
                                                <transition name="slide-fade">
                                                    <div
                                                        v-if="item.is_updated"
                                                        v-tippy
                                                        :content="`${$t('comment.updated')}: ${$moment(item.updated_at).format('DD.MM.YYYY HH:mm')}`"
                                                        class="comment_updated">
                                                        {{ $t('comment.updated') }}
                                                    </div>
                                                </transition>

                                                <template v-if="isMobile">
                                                    <div
                                                        v-if="item.task_count"
                                                        class="flex items-center cursor-pointer"
                                                        style="color: var(--gray);"
                                                        @click="openTaskModal()">
                                                        <i class="fi fi-rr-list-check mr-1" />
                                                        {{ item.task_count }}
                                                    </div>
                                                </template>
                                                <template v-else>
                                                    <component
                                                        v-if="item.task_count"
                                                        :is="popupTaskComp"
                                                        :getPopupContainer="getPopupContainer"
                                                        :item="item"
                                                        ref="viewTaskPopup">
                                                        <div
                                                            class="flex items-center cursor-pointer"
                                                            style="color: var(--gray);"
                                                            @click="openTaskModal()">
                                                            <i class="fi fi-rr-list-check mr-1" />
                                                            {{ item.task_count }}
                                                        </div>
                                                    </component>
                                                </template>

                                                <template v-if="isMobile">
                                                    <div
                                                        v-if="myComment && viewCount"
                                                        class="flex items-center cursor-pointer"
                                                        style="color: var(--gray);"
                                                        @click="openViewsModal()">
                                                        <i class="fi fi-rr-eye mr-1" />
                                                        {{ viewCount }}
                                                    </div>
                                                </template>
                                                <template v-else>
                                                    <component
                                                        v-if="myComment && viewCount"
                                                        :is="popupViewComp"
                                                        :getPopupContainer="getPopupContainer"
                                                        :item="item"
                                                        ref="viewPopup">
                                                        <div
                                                            class="flex items-center cursor-pointer"
                                                            style="color: var(--gray);"
                                                            @click="openViewsModal()">
                                                            <i class="fi fi-rr-eye mr-1" />
                                                            {{ viewCount }}
                                                        </div>
                                                    </component>
                                                </template>

                                                <a-dropdown
                                                    v-if="!useShare && !isMobile"
                                                    placement="bottomRight"
                                                    :trigger="[]"
                                                    overlayClassName="comment_drop_menu"
                                                    :visible="btnDropdownVisible">
                                                    <a-button
                                                        type="ui_ghost"
                                                        size="small"
                                                        shape="circle"
                                                        flaticon
                                                        icon="fi-rr-menu-dots-vertical"
                                                        @click.stop="onMenuBtnClick($event)"/>
                                                    <a-menu
                                                        slot="overlay"
                                                        @click.native.stop="onOverlayMenuClick">
                                                        <a-menu-item
                                                            v-if="reactions && reactions.length"
                                                            key="reactions"
                                                            class="reactions_menu grid grid-cols-5 gap-4">
                                                            <div
                                                                v-for="smile in reactions"
                                                                :key="smile.code"
                                                                :title="smile.name"
                                                                class="cursor-pointer reaction_option"
                                                                :class="{ active: isMyReaction(smile) }"
                                                                @click="selectReaction(smile)">
                                                                {{ smile.icon }}
                                                            </div>
                                                        </a-menu-item>
                                                        <a-menu-item v-if="item.text_clear" key="copy_btn" class="flex items-center" @click="copyText">
                                                            <i class="fi fi-rr-copy mr-2" />
                                                            {{ $t('comment.copy_text') }}
                                                        </a-menu-item>
                                                        <a-menu-item v-if="canReply" key="reply_btn" class="flex items-center" @click="openResponseForm()">
                                                            <i class="fi fi-rr-undo mr-2" />
                                                            {{ $t('comment.reply') }}
                                                        </a-menu-item>
                                                        <a-menu-item v-if="canManageOwnComment" key="edit_btn" class="flex items-center" @click="openEdit()">
                                                            <i class="fi fi-rr-edit mr-2" />
                                                            {{ $t('comment.edit') }}
                                                        </a-menu-item>
                                                        <a-menu-item v-if="openCheck" key="open_btn" class="flex items-center" @click="openComment(item.id)">
                                                            <i class="fi fi-rr-comment-alt-dots mr-2" />
                                                            {{ $t('comment.open') }}
                                                        </a-menu-item>
                                                        <a-menu-item v-if="addTaskCheck" key="task_btn" class="flex items-center" @click="addTask()">
                                                            <i class="fi fi-rr-list-check mr-2" />
                                                            {{ $t('comment.add_task') }}
                                                        </a-menu-item>

                                                        <a-menu-item v-if="item.task_count" key="task_reasin" class="flex items-center" @click="openTaskModal()">
                                                            <i class="fi fi-rr-link-alt mr-2" />
                                                            {{ $t('comment.task_reason') }}
                                                        </a-menu-item>

                                                        <a-menu-item v-if="shareCheck" key="share_btn" class="flex items-center" @click="share()">
                                                            <i class="fi fi-rr-share mr-2" />
                                                            {{ $t('comment.share') }}
                                                        </a-menu-item>
                                                        <template v-if="myComment">
                                                            <a-sub-menu v-if="viewCount && viewUsers && viewUsers.length" key="views">
                                                                <template #title>
                                                                    <div class="flex items-center" @click="openViewsModal()">
                                                                        <i class="fi fi-rr-eye mr-2" />
                                                                        {{ viewCountText }}
                                                                    </div>
                                                                </template>
                                                                <a-menu-item v-for="userItem in viewUsers" :key="userItem.id" @click="openViewsModal()">
                                                                    <div class="flex items-center truncate" :title="userItem.full_name">
                                                                        <div class="mr-2">
                                                                            <a-avatar
                                                                                :size="18"
                                                                                :key="userItem.id"
                                                                                avResize
                                                                                :src="userItem.avatar && userItem.avatar.path ? userItem.avatar.path : ''"
                                                                                icon="user" />
                                                                        </div>
                                                                        <div class="truncate">
                                                                            {{ userItem.full_name }}
                                                                        </div>
                                                                    </div>
                                                                </a-menu-item>
                                                                <a-menu-item
                                                                    v-if="viewUsers.length > 1"
                                                                    class="flex items-center justify-between"
                                                                    @click="openViewsModal()">
                                                                    {{ $t('comment.view_all') }}
                                                                    <i class="fi fi-rr-arrow-small-right ml-1" />
                                                                </a-menu-item>
                                                            </a-sub-menu>
                                                            <a-menu-item v-else key="empty_views" class="flex items-center">
                                                                <a-spin :spinning="viewLoading" size="small" class="mr-2">
                                                                    <i class="fi fi-rr-eye" />
                                                                </a-spin>
                                                                {{ viewCountText }}
                                                            </a-menu-item>
                                                        </template>
                                                        <template v-if="canManageOwnComment">
                                                            <a-menu-divider />
                                                            <a-menu-item
                                                                key="delete_btn"
                                                                class="flex items-center text-red-500"
                                                                @click="removeHandler()">
                                                                <i class="fi fi-rr-trash mr-2" />
                                                                {{ $t('comment.delete') }}
                                                            </a-menu-item>
                                                        </template>
                                                    </a-menu>
                                                </a-dropdown>
                                            </div>
                                        </div>

                                        <div
                                            v-if="!useShare && commentReactions.length"
                                            class="flex items-center mt-2 justify-start">
                                            <transition-group
                                                name="reaction"
                                                tag="div"
                                                class="flex flex-wrap gap-1 comment_reaction">
                                                <template v-if="isMobile">
                                                    <div
                                                        v-for="react in commentReactions"
                                                        class="comment_reaction__item"
                                                        :key="react.reaction.id"
                                                        :class="{ active: react.my_reaction }"
                                                        @click="selectReaction(react.reaction)">
                                                        <span>{{ react.reaction.icon }}</span> {{ react.users_count }}
                                                    </div>
                                                </template>

                                                <template v-else>
                                                    <a-popover
                                                        v-for="react in commentReactions"
                                                        :key="react.reaction.id"
                                                        :visible="openedReactionId === react.reaction.id"
                                                        transitionName=""
                                                        trigger="hover"
                                                        destroyTooltipOnHide
                                                        :getPopupContainer="getPopupContainer"
                                                        overlayClassName="reactions_popover"
                                                        :mouseEnterDelay="0.2"
                                                        :placement="reactionPlacement(react.reaction.id)"
                                                        autoAdjustOverflow
                                                        @visibleChange="v => onReactVisibleChange(v, react.reaction.id)">
                                                        <div
                                                            class="comment_reaction__item"
                                                            :class="{ active: react.my_reaction }"
                                                            @click="selectReaction(react.reaction)">
                                                            <span>{{ react.reaction.icon }}</span> {{ react.users_count }}
                                                        </div>
                                                        <template slot="content">
                                                            <div :style="`min-height: ${reactHeightCheck(react.users_count)}px;`">
                                                                <ReactUserList
                                                                    v-if="openedReactionId === react.reaction.id"
                                                                    :reaction="react"
                                                                    :ref="`reactUserList_${react.reaction.id}`"
                                                                    :relatedId="item.id" />
                                                            </div>
                                                        </template>
                                                    </a-popover>
                                                </template>
                                            </transition-group>
                                        </div>
                                    </div>

                                    <a-menu v-if="!isMobile" slot="overlay" @click.native="ctxDropdownVisible = false">
                                        <a-menu-item
                                            v-if="reactions && reactions.length"
                                            key="reactions"
                                            class="reactions_menu grid grid-cols-5 gap-4">
                                            <div
                                                v-for="smile in reactions"
                                                :key="smile.code"
                                                :title="smile.name"
                                                class="cursor-pointer reaction_option"
                                                :class="{ active: isMyReaction(smile) }"
                                                @click="selectReaction(smile)">
                                                {{ smile.icon }}
                                            </div>
                                        </a-menu-item>
                                        <a-menu-item v-if="item.text_clear" key="copy_ctx" class="flex items-center" @click="copyText">
                                            <i class="fi fi-rr-copy mr-2" />
                                            {{ $t('comment.copy_text') }}
                                        </a-menu-item>
                                        <a-menu-item v-if="canReply" key="reply_ctx" class="flex items-center" @click="openResponseForm()">
                                            <i class="fi fi-rr-undo mr-2" />
                                            {{ $t('comment.reply') }}
                                        </a-menu-item>
                                        <a-menu-item v-if="canManageOwnComment" key="edit_ctx" class="flex items-center" @click="openEdit()">
                                            <i class="fi fi-rr-edit mr-2" />
                                            {{ $t('comment.edit') }}
                                        </a-menu-item>
                                        <a-menu-item v-if="openCheck" key="open_ctx" class="flex items-center" @click="openComment(item.id)">
                                            <i class="fi fi-rr-comment-alt-dots mr-2" />
                                            {{ $t('comment.open') }}
                                        </a-menu-item>
                                        <a-menu-item v-if="addTaskCheck" key="task_ctx" class="flex items-center" @click="addTask()">
                                            <i class="fi fi-rr-list-check mr-2" />
                                            {{ $t('comment.add_task') }}
                                        </a-menu-item>
                                        <a-menu-item v-if="item.task_count" key="task_reasin" class="flex items-center" @click="openTaskModal()">
                                            <i class="fi fi-rr-link-alt mr-2" />
                                            {{ $t('comment.task_reason') }}
                                        </a-menu-item>
                                        <a-menu-item v-if="shareCheck" key="share_ctx" class="flex items-center" @click="share()">
                                            <i class="fi fi-rr-share mr-2" />
                                            {{ $t('comment.share') }}
                                        </a-menu-item>
                                        <template v-if="myComment">
                                            <a-sub-menu v-if="viewCount && viewUsers && viewUsers.length" key="views">
                                                <template #title>
                                                    <div class="flex items-center" @click="openViewsModal()">
                                                        <i class="fi fi-rr-eye mr-2" />
                                                        {{ viewCountText }}
                                                    </div>
                                                </template>
                                                <a-menu-item v-for="userItem in viewUsers" :key="userItem.id" @click="openViewsModal()">
                                                    <div class="flex items-center truncate" :title="userItem.full_name">
                                                        <div class="mr-2">
                                                            <a-avatar
                                                                :size="18"
                                                                :key="userItem.id"
                                                                avResize
                                                                :src="userItem.avatar && userItem.avatar.path ? userItem.avatar.path : ''"
                                                                icon="user" />
                                                        </div>
                                                        <div class="truncate">
                                                            {{ userItem.full_name }}
                                                        </div>
                                                    </div>
                                                </a-menu-item>
                                                <a-menu-item
                                                    v-if="viewUsers.length > 1"
                                                    class="flex items-center justify-between"
                                                    @click="openViewsModal()">
                                                    {{ $t('comment.view_all') }}
                                                    <i class="fi fi-rr-arrow-small-right ml-1" />
                                                </a-menu-item>
                                            </a-sub-menu>
                                            <a-menu-item v-else key="empty_views" class="flex items-center">
                                                <a-spin :spinning="viewLoading" size="small" class="mr-2">
                                                    <i class="fi fi-rr-eye" />
                                                </a-spin>
                                                {{ viewCountText }}
                                            </a-menu-item>
                                        </template>
                                        <template v-if="canManageOwnComment">
                                            <a-menu-divider />
                                            <a-menu-item
                                                key="delete_ctx"
                                                class="flex items-center text-red-500"
                                                @click="removeHandler()">
                                                <i class="fi fi-rr-trash mr-2" />
                                                {{ $t('comment.delete') }}
                                            </a-menu-item>
                                        </template>
                                    </a-menu>
                                </a-dropdown>
                            </a-spin>
                        </div>

                        <transition name="slide">
                            <div
                                v-if="!useShare && canReply && (!responseForm || isMobile)"
                                class="body_actions"
                                :class="myComment && 'justify-end'">
                                <div
                                    class="act_btn"
                                    @click="openResponseForm()">
                                    {{ $t('comment.reply') }}
                                </div>
                            </div>
                        </transition>
                    </div>
                    <div class="dummy_body" :class="myComment ? 'mr-3' : 'ml-3'"></div>
                </div>
            </div>
        </div>

        <transition v-if="!useShare" name="slide">
            <div v-if="responseForm || editData" class="res_form">
                <div v-if="!isMobile" class="res_form__label gray ml-2">
                    <template v-if="responseForm">
                        <i class="fi fi-rr-undo mr-2" />
                        {{ $t('comment.reply_to') }}
                    </template>
                    <template v-if="editData">
                        <i class="fi fi-rr-edit mr-2" />
                        {{ $t('comment.edit_comment') }}
                    </template>
                </div>
                <CommentInput
                    :related_object="related_object"
                    :model="model"
                    :modal="modal"
                    :mentionsData="mentionsData"
                    :showUsers="showUsers"
                    :editData="editData"
                    :getModalContainer="getModalContainer"
                    :closeEditorFunc="closeEditorFunc"
                    :blockLeft="blockLeft"
                    :showEmoji="showEmoji"
                    :setBlockLeft="setBlockLeft"
                    :pushNewComment="pushNewComment"
                    :updateComment="updateComment"
                    :showFileUpload="showFileUpload"
                    :parent="item" />
            </div>
        </transition>

        <component
            :is="actionComponents"
            ref="comment_actions"
            :openResponseForm="openResponseForm"
            :openEdit="openEdit"
            :reactions="reactions"
            :isMyReaction="isMyReaction"
            :selectReaction="selectReaction"
            :openComment="openComment"
            :addTask="addTask"
            :viewCount="viewCount"
            :openReactionModal="openReactionModal"
            :share="share"
            :openTaskModal="openTaskModal"
            :openViewsModal="openViewsModal"
            :myComment="myComment"
            :shareCheck="shareCheck"
            :addTaskCheck="addTaskCheck"
            :openCheck="openCheck"
            :user="user"
            :removeHandler="removeHandler"
            :reply="canReply"
            :item="item" />

        <component
            ref="userViewsModal"
            :is="userViewsModalComp"
            :item="item" />
        <component
            ref="taskViewsModal"
            :is="taskViewsModalComp"
            :item="item" />

        <component
            :is="reactionModal"
            ref="reactionModal"
            :item="item" />
    </div>
</template>

<script>
import eventBus from '@/utils/eventBus'
import eventBusLoc from './eventBus.js'
import { vElementVisibility } from '@vueuse/components'
import { errorHandler } from '@/utils/index.js'
import { itemProps } from './initProps.js'
import { declOfNum } from '@/utils/utils.js'
import { mapState } from 'vuex'

export default {
    components: {
        CommentInput: () => import('./CommentInput'),
        CommentFile: () => import('./CommentFIle'),
        TextViewer: () => import('@apps/CKEditor/TextViewer.vue'),
        ReactUserList: () => import('./ReactUserList.vue')
    },
    directives: {
        ElementVisibility: vElementVisibility
    },
    props: { ...itemProps },
    computed: {
        ...mapState({
            reactions: state => state.comments.reactions
        }),
        reactionModal() {
            if(this.isMobile && !this.useShare)
                return () => import('./ReactionModal.vue')
            return null
        },
        userViewsModalComp() {
            if(this.viewCount && this.isMobile && !this.useShare)
                return () => import('./UserViewsModal.vue')
            return null
        },
        taskViewsModalComp() {
            if(this.item.task_count && this.isMobile && !this.useShare)
                return () => import('./TaskViewsModal.vue')
            return null
        },
        viewCount() {
            const count = this.item.viewer_count - 1
            if (count < 0)
                return 0
            return count
        },
        viewCountText() {
            if (this.viewLoading)
                return this.$t('comment.view4')
            if (!this.viewUsers?.length)
                return this.$t('comment.no_view')
            return `${this.viewCount} ${declOfNum(this.viewCount, [this.$t('comment.view1'), this.$t('comment.view2'), this.$t('comment.view3')])}`
        },
        date() {
            return this.$moment(this.item.created_at).format(this.commentDateTimeFormat || 'HH:mm')
        },
        isSystemComment() {
            return Boolean(this.item?.is_system)
        },
        isOwnComment() {
            const authorId = this.item?.author?.id
            const userId = this.user?.id
            if (!authorId || !userId)
                return false
            return String(userId) === String(authorId)
        },
        canManageOwnComment() {
            return this.isOwnComment && !this.isSystemComment
        },
        canReply() {
            return this.reply && !this.isSystemComment
        },
        myComment() {
            if(this.useShare)
                return false
            if (!this.modal && !this.blockLeft)
                return this.isOwnComment
            return false
        },
        commentReactions() {
            return this.item.reactions || []
        },
        isMobile() {
            return this.$store.state.isMobile
        },
        actionComponents() {
            if(this.isMobile && !this.useShare)
                return () => import('./MobileMenuActions.vue')
            return null
        },
        popupViewComp() {
            if (this.viewCount && !this.isMobile)
                return () => import('./UserViewsPopup.vue')
            return null
        },
        popupTaskComp() {
            if (this.item.task_count && !this.isMobile)
                return () => import('./TaskViewPopup.vue')
            return null
        }
    },
    data() {
        return {
            lgObserver: null,
            showCommentForm: false,
            loading: false,
            showAnswer: false,
            responseForm: false,
            state: false,
            editData: null,
            copySource: 'item',
            ctxDropdownVisible: false,
            btnDropdownVisible: false,
            lg: null,
            lgWrapInst: null,
            lgParentWrapInst: null,
            moWrap: null,
            moParentWrap: null,
            lazyHandler: null,
            viewUsers: [],
            viewLoading: false,
            openedReactionId: null,
            popoverLockedUntil: 0
        }
    },
    created () {
        if (this.item.newComment) {
            setTimeout(() => {
                this.updateNewComment(this.item.id)
            }, 1000)
        }
    },
    methods: {
        openReactionModal() {
            if (this.$refs.reactionModal)
                this.$refs.reactionModal.openModal()
        },
        lockPopover(ms = 400) {
            this.popoverLockedUntil = Date.now() + ms
            this.openedReactionId = null
        },
        isPopoverLocked() {
            return Date.now() < this.popoverLockedUntil
        },
        reactHeightCheck(count) {
            if (count >= 2)
                return 60
            if (count >= 3)
                return 70
            if (count >= 4)
                return 100
            if (count >= 5)
                return 120
            if (count >= 6)
                return 150
            return 40
        },
        reactionPlacement(id) {
            const ref = this.$refs.bodyWrap
            const el = Array.isArray(ref) ? ref[0] : ref

            return this.isNearBottom(el) ? 'top' : 'bottom'
        },
        isNearBottom(el) {
            if (!el) return false

            const rect = el.getBoundingClientRect()
            const viewportHeight = window.innerHeight

            return viewportHeight - rect.bottom < 180
        },
        onReactVisibleChange(visible, id) {
            if (this.isPopoverLocked()) return

            this.openedReactionId = visible ? id : null
        },
        isMyReaction(smile) {
            const reactions = this.item.reactions || []
            return reactions.some(
                r => r.my_reaction && r.reaction.id === smile.id
            )
        },
        async selectReaction(reaction) {
            this.lockPopover(500)

            const myReaction = (this.item.reactions || []).find(r => r.my_reaction)
            const openReaction = this.openedReactionId
            this.openedReactionId = null

            const nextReaction =
                myReaction && String(myReaction.reaction.id) === String(reaction.id)
                    ? null
                    : reaction

            const prevSnapshot = this.item.reactions ? this.item.reactions.slice() : []

            this.$emit('reaction-change', {
                commentId: this.item.id,
                nextReaction,
                prevSnapshot,
                openReaction
            })

            this.ctxDropdownVisible = false
            this.btnDropdownVisible = false

            try {
                await this.$http.post(`/reactions/related_object/${this.item.id}/set/`, {
                    reaction: nextReaction ? nextReaction.id : null
                })

                if (openReaction && nextReaction) this.openedReactionId = openReaction

                await this.$nextTick()

                const rid = reaction && reaction.id ? reaction.id : null
                const ref = rid ? this.$refs[`reactUserList_${rid}`] : null
                const comp = Array.isArray(ref) ? ref[0] : ref
                if (comp && typeof comp.reloadList === 'function')
                    comp.reloadList()
            } catch (error) {
                this.$emit('reaction-rollback', {
                    commentId: this.item.id,
                    prevSnapshot
                })
                errorHandler({ error })
            }
        },
        openViewsModal() {
            this.$nextTick(() => {
                this.ctxDropdownVisible = false
                this.btnDropdownVisible = false

                if (this.isMobile) {
                    if (this.$refs.userViewsModal)
                        this.$refs.userViewsModal.openModal()
                } else {
                    if (this.$refs.viewPopup)
                        this.$refs.viewPopup.openPopup()
                }
            })
        },
        openTaskModal() {
            this.$nextTick(() => {
                this.ctxDropdownVisible = false
                this.btnDropdownVisible = false

                if (this.isMobile) {
                    if (this.$refs.taskViewsModal)
                        this.$refs.taskViewsModal.openModal()
                } else {
                    if (this.$refs.viewTaskPopup)
                        this.$refs.viewTaskPopup.openPopup()
                }
            })
        },
        async getViewUser() {
            if (!this.viewUsers?.length && this.myComment && this.viewCount) {
                try {
                    this.viewLoading = true
                    const { data } = await this.$http.get('/viewers/', {
                        params: {
                            related_object: this.item.id,
                            page_size: 5
                        }
                    })

                    if (data?.results?.length) {
                        this.viewUsers = data.results.filter(
                            u => u.id !== this.user.id
                        )
                    }
                } catch (error) {
                    errorHandler({ error })
                } finally {
                    this.viewLoading = false
                }
            }
        },
        menuVisibleChange(v) {
            if (v)
                this.getViewUser()
        },
        onCtxVisibleChange(v) {
            this.ctxDropdownVisible = v
            if (v) {
                this.$store.dispatch('comments/getReactions')
                this.getViewUser()
                this.btnDropdownVisible = false
            }
        },
        async getLG() {
            if (this.lg) return this.lg
            if (typeof window !== 'undefined' && (window.lightGallery || window.lightgallery))
                this.lg = window.lightGallery || window.lightgallery
            else {
                const mod = await import('lightgallery.js')
                this.lg = mod.default || mod
            }
            return this.lg
        },
        destroyLG(refName) {
            const wrap = this.$refs[refName]
            if (!wrap) return
            const instKey = refName === 'lght_wrap' ? 'lgWrapInst' : 'lgParentWrapInst'
            const inst = this[instKey]
            if (inst && inst.destroy) {
                try { inst.destroy(true) } catch (e) {}
                this[instKey] = null
            }
        },
        async ensureLG(refName) {
            await this.$nextTick()
            const wrap = this.$refs[refName]
            if (!wrap) return
            const items = wrap.querySelectorAll('.lht_l')
            if (!items || !items.length) return
            const LG = await this.getLG()
            this.destroyLG(refName)
            const instKey = refName === 'lght_wrap' ? 'lgWrapInst' : 'lgParentWrapInst'
            this[instKey] = LG(wrap, {
                selector: '.lht_l',
                thumbnail: true,
                rotateLeft: true,
                rotateRight: true,
                fullScreen: true,
                animateThumb: true,
                showThumbByDefault: true,
                download: true,
                flipHorizontal: false,
                flipVertical: false,
                zoom: true,
                speed: 300,
                enableZoomAfter: 300
            })
        },
        scheduleLGInit() {
            this.ensureLG('lght_wrap')
            this.ensureLG('lght_wrap_parent')
        },
        attachObservers() {
            const w1 = this.$refs.lght_wrap
            const w2 = this.$refs.lght_wrap_parent
            if (w1 && !this.moWrap) {
                this.moWrap = new MutationObserver(this.scheduleLGInit)
                this.moWrap.observe(w1, { childList: true, subtree: true })
            }
            if (w2 && !this.moParentWrap) {
                this.moParentWrap = new MutationObserver(this.scheduleLGInit)
                this.moParentWrap.observe(w2, { childList: true, subtree: true })
            }
            if (!this.lazyHandler) {
                this.lazyHandler = e => {
                    const t = e && e.target
                    if (!t) return
                    const w = this.$refs.lght_wrap
                    const wp = this.$refs.lght_wrap_parent
                    if ((w && w.contains(t)) || (wp && wp.contains(t))) this.scheduleLGInit()
                }
                document.addEventListener('lazyloaded', this.lazyHandler, true)
            }
        },
        detachObservers() {
            if (this.moWrap) {
                this.moWrap.disconnect()
                this.moWrap = null
            }
            if (this.moParentWrap) {
                this.moParentWrap.disconnect()
                this.moParentWrap = null
            }
            if (this.lazyHandler) {
                document.removeEventListener('lazyloaded', this.lazyHandler, true)
                this.lazyHandler = null
            }
        },
        longtapHandler() {
            if (this.isMobile) {
                this.$nextTick(() => {
                    this.$refs.comment_actions.openDrawer()
                })
            }
        },
        onOverlayMenuClick() {
            this.btnDropdownVisible = false
            this.ctxDropdownVisible = false
        },
        handleDocClick(e) {
            if (!this.btnDropdownVisible && !this.ctxDropdownVisible) return

            const bodyWrap = this.$refs.bodyWrap
            const target = e.target

            const clickedInsideBody =
                bodyWrap && bodyWrap.contains(target)

            const clickedInsideDropdown =
                target.closest('.ant-dropdown') ||
                target.closest('.ant-dropdown-menu')

            if (!clickedInsideBody && !clickedInsideDropdown) {
                this.btnDropdownVisible = false
                this.ctxDropdownVisible = false
            }
        },
        onMenuBtnClick(e) {
            if (this.isMobile) return
            try {
                const inReply = e && e.target && e.target.closest && e.target.closest('.res_comment')
                this.copySource = inReply ? 'parent' : 'item'
            } catch (err) {
                this.copySource = 'item'
            }
            this.btnDropdownVisible = !this.btnDropdownVisible
            if (this.btnDropdownVisible) {
                this.$store.dispatch('comments/getReactions')
                this.getViewUser()
                this.ctxDropdownVisible = false
            }
        },
        openEdit() {
            if (!this.canManageOwnComment)
                return
            this.closeMainInput()
            this.responseForm = false
            this.editData = this.item
        },
        onElementVisibility(e) {
            if (this.item.newVisible) {
                if (e) {
                    this.toggleNewCommentCount('min', this.item.id)
                } else {
                    this.toggleNewCommentCount('add')
                }
            }
            this.state = e
        },
        openComment(id, cid = null) {
            if (!this.modal)
                this.closeMainInput()
            eventBusLoc.$emit(`open_comment_detail_${this.related_object}`, id, cid)
        },
        getPopupContainer() {
            return this.$refs.commentItem
        },
        openResponseForm() {
            if (!this.canReply)
                return
            eventBus.$emit('CLOSE_RES_FORM')
            this.closeMainInput()
            this.editData = null
            this.responseForm = true
        },
        closeEditorFunc() {
            this.responseForm = false
            this.editData = null
        },
        share() {
            this.$store.commit('share/SET_SHARE_PARAMS', {
                model: 'comments',
                shareId: this.item.id,
                object: this.item,
                bodySelector: this.bodySelector
            })
        },
        escapeHtml(value) {
            return String(value || '')
                .replace(/&/g, '&amp;')
                .replace(/</g, '&lt;')
                .replace(/>/g, '&gt;')
                .replace(/"/g, '&quot;')
                .replace(/'/g, '&#39;')
        },
        buildCommentDescription() {
            const baseText = this.item.text || ''
            const attachments = Array.isArray(this.item.attachments) ? this.item.attachments : []

            if (!attachments.length) return baseText

            const attachmentsHtml = attachments
                .map(file => {
                    const filePath = file?.path
                    if (!filePath) return ''

                    const safePath = this.escapeHtml(filePath)

                    if (file?.is_image) {
                        const alt = this.escapeHtml(file?.name || 'image')
                        return `<figure class="image"><a class="lht_l" href="${safePath}" target="_blank"><img src="${safePath}" alt="${alt}"></a></figure>`
                    }

                    const fileName = this.escapeHtml(file?.name || this.$t('file'))
                    return `<p><a href="${safePath}" target="_blank" rel="noopener noreferrer">${fileName}</a></p>`
                })
                .filter(Boolean)
                .join('')

            return `${baseText}${attachmentsHtml}`
        },
        addTask() {
            this.$store.commit('task/SET_TASK_DRAWER_ZINDEX', this.extendDrawerZIndex + 100)
            let form = {
                description: this.buildCommentDescription(),
                operator: this.item.author,
                attachments: this.item.attachments,
                reason_model: 'comments',
                reason: this.item.id,
                reason_parent: this.related_object
            }
            this.$store.commit('task/SET_TASK_TYPE', 'task')
            eventBus.$emit(this.isMobile ? 'ADD_WATCH' : 'add_task_modal_watch', { type: 'add_task', data: form })
        },
        async removeHandler() {
            if (!this.canManageOwnComment)
                return
            try {
                this.loading = true
                await this.deleteComment(this.item.id)
            } catch (error) {
                errorHandler({ error })
            } finally {
                this.loading = false
            }
        },
        onDropdownContextmenu(e) {
            try {
                const inReply = e && e.target && e.target.closest && e.target.closest('.res_comment')
                this.copySource = inReply ? 'parent' : 'item'
            } catch (err) {
                this.copySource = 'item'
            }
        },
        getCopyPlainText() {
            const src = this.copySource === 'parent' ? this.item.parent : this.item
            return src && src.text_clear ? String(src.text_clear) : ''
        },
        async copyText() {
            const text = this.getCopyPlainText()
            try {
                if (navigator.clipboard && navigator.clipboard.writeText) {
                    await navigator.clipboard.writeText(text)
                } else {
                    const ta = document.createElement('textarea')
                    ta.value = text
                    ta.setAttribute('readonly', '')
                    ta.style.position = 'absolute'
                    ta.style.left = '-9999px'
                    document.body.appendChild(ta)
                    ta.select()
                    document.execCommand('copy')
                    document.body.removeChild(ta)
                }
                this.$message.success(this.$t('comment.copied') || 'Скопировано')
            } catch (e) {
                this.$message.error(this.$t('comment.copy_failed') || 'Не удалось скопировать')
            }
        }
    },
    mounted() {
        eventBus.$on('CLOSE_RES_FORM', () => {
            this.responseForm = false
        })
        this.$nextTick(() => {
            this.scheduleLGInit()
            this.attachObservers()
        })
        document.addEventListener('click', this.handleDocClick, true)
    },
    beforeDestroy() {
        eventBus.$off('CLOSE_RES_FORM')
        this.detachObservers()
        this.destroyLG('lght_wrap')
        this.destroyLG('lght_wrap_parent')
        document.removeEventListener('click', this.handleDocClick, true)
        if (this.lgObserver) this.lgObserver.disconnect()
        this.lgObserver = null
    },
    updated() {
        this.scheduleLGInit()
    }
}
</script>

<style lang="scss">
.comment_drop_menu{
    .ant-dropdown-menu-submenu-arrow{
        top: 9px;
    }
    .ant-dropdown-menu-submenu-popup{
        max-width: 230px;
    }
}
</style>

<style lang="scss" scoped>
.reaction-enter-active,
.reaction-leave-active {
    transition: all 0.18s ease
}
.comment.system {
    .comment_item {
        align-items: flex-start;
    }
    .body_wrap {
        background: #e7f5ff;
    }
}
.comment_item__body--system {
    width: 100%;
}
.comment_system_label {
    font-size: 12px;
    font-weight: 600;
    color: var(--gray);
}
.comment_system_label--reply {
    cursor: pointer;
}
.reaction-enter,
.reaction-leave-to {
    opacity: 0;
    transform: scale(0.7)
}
.reaction-enter-to,
.reaction-leave {
    opacity: 1;
    transform: scale(1)
}

.comment_reaction{
    &__item{
        background: rgba(0, 0, 0, 0.1);
        padding: 0px 10px;
        border-radius: 10px;
        display: flex;
        align-items: center;
        min-height: 18px;
        cursor: pointer;
        span{
            font-size: 16px;
            margin-right: 5px;
            transition: all 0.3s cubic-bezier(0.645, 0.045, 0.355, 1);
        }
        &:hover{
            span{
                transform: scale(1.2)
            }
        }
        &.active{
            columns: var(--blue);
            background: #dee6f5;
        }
    }
}

.reactions_menu{
    &.ant-dropdown-menu-item{
        position: absolute;
        top: -85px;
        background: #fff!important;
        border-radius: 12px;
        left: 0px;
        box-shadow: 0px 8px 16px 0px rgba(0, 0, 0, 0.0784313725);
        user-select: none;
        text-align: center;
        .reaction_option{
            font-size: 18px;
            width: 24px;
            height: 24px;
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
    }
}

.dummy_body{
    min-width: 32px;
}

.comment{
    &:not(:last-child){
        margin-bottom: 18px;
    }
    &.mobile{
        .body_wrap{
            transition: all 0.5s cubic-bezier(0.645, 0.045, 0.355, 1);
            &.touch{
                box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
                transform: scale(0.97);
            }
        }
    }
    .res_form{
        &__label{
            margin-bottom: 5px;
            display: flex;
            align-items: center;
        }
    }
    &.my{
        .comment_item{
            flex-direction: row-reverse;
        }
    }
    &.new{
        .body_wrap{
            background: #edece0;
        }
    }
    .comment_updated{
        font-size: 10px;
        margin-left: 5px;
        color: var(--gray);
    }

    /* ✅ badge */
    .comment_vis_badge{
        display: inline-flex;
        align-items: center;
        width: fit-content;
        font-size: 10px;
        padding: 2px 8px;
        border-radius: 999px;
        margin-top: 6px;
        user-select: none;
        background: rgba(0, 0, 0, 0.06);
        color: var(--gray);

        &.private{
            background: rgba(0, 0, 0, 0.06);
        }
        &.public{
            background: rgba(28, 101, 192, 0.10);
        }
    }

    .slide-fade-enter-active {
        transition: all .3s ease;
    }
    .slide-fade-leave-active {
        transition: all .8s cubic-bezier(1.0, 0.5, 0.8, 1.0);
    }
    .slide-fade-enter, .slide-fade-leave-to{
        transform: translateX(10px);
        opacity: 0;
    }
    .slide-enter-active {
        transition-duration: 0.2s;
        transition-timing-function: ease-in;
    }
    .slide-leave-active {
        transition-duration: 0.2s;
        transition-timing-function: cubic-bezier(0, 1, 0.5, 1);
    }
    .slide-enter-to,
    .slide-leave {
        max-height: 100px;
        overflow: hidden;
    }
    .slide-enter,
    .slide-leave-to {
        overflow: hidden;
        max-height: 0;
    }
    &.shaking{
        .body_wrap{
            animation-fill-mode: both;
            animation-duration: 0.7s;
            animation-name: shakeX;
            animation-delay: 0s;
            transition: all 0.7s cubic-bezier(0.645, 0.045, 0.355, 1);
        }
    }
}

.comment_item{
    display: flex;
    align-items: flex-start;
    &::v-deep{
        .ck_text_viewer{
            .ck-table,
            table{
                min-width: 100%!important;
            }
        }
    }
    &__body{
        width: 100%;
        .body_actions{
            display: flex;
            padding: 0 15px;
            .act_btn{
                cursor: pointer;
                color: var(--gray);
                transition: all 0.3s cubic-bezier(0.645, 0.045, 0.355, 1);
                &:hover{
                    color: var(--blue);
                }
            }
        }
        .body_wrap{
            border-radius: 15px;
            background: #eef2f5;
            padding: 10px 15px;
            margin-bottom: 8px;
            transition: all 0.7s cubic-bezier(0.645, 0.045, 0.355, 1);
            .comment_text{
                word-break: break-word;
                &::v-deep{
                    pre{
                        white-space: pre-wrap;
                    }
                    figure{
                        &.media{
                            width: 250px;
                        }
                    }
                }
            }
            .res_comment{
                background: var(--primaryHover);
                border-radius: 0 var(--borderRadius) var(--borderRadius) 0;
                margin-bottom: 10px;
                padding: 10px;
                border-left: 4px solid var(--blue);
                cursor: pointer;
                word-break: break-word;
                &::v-deep{
                    .ck_text_viewer{
                        .ck-table,
                        table{
                            min-width: 100%!important;
                        }
                        pre{
                            white-space: pre-wrap;
                        }
                        figure{
                            &.media{
                                width: 250px;
                            }
                        }
                    }
                }
            }
            .comment_files{
                display: flex;
                flex-wrap: wrap;
                align-items: flex-start;
                gap: 6px;
            }
            &::v-deep{
                .user_profile{
                    margin-bottom: 6px;
                    color: #000000;
                }
            }
        }
    }
}

@keyframes shakeX {
    from,
    to {
        transform: translate3d(0, 0, 0);
    }
    10%,
    30%,
    50%,
    70%,
    90% {
        transform: translate3d(-3px, 0, 0);
    }
    20%,
    40%,
    60%,
    80% {
        transform: translate3d(3px, 0, 0);
    }
}
</style>
