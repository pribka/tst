<template>
    <div
        class="flex items-start mt-3 msg_item"
        :class="messageItem.forwarded && 'msg_forwarded'"
        :ref="`message_${messageItem.message_uid}`"
        :data-created="messageItem.created || ''"
        :id="`message_${ messageItem.message_uid }`">
        <div
            class="flex justify-between w-full"
            :class="myMessage && 'flex-row-reverse'">
            <a-dropdown
                :trigger="isMobile && !useDesktopMessageMenu ? [] : ['contextmenu']"
                class="message_context"
                v-model="ctxDropdownVisible"
                @visibleChange="visibleChangeContext"
                :disabled="isViewContext">
                <div
                    class="flex"
                    :class="myMessage && 'flex-row-reverse'">
                    <div
                        v-if="messageItem.message_author && !forwarded"
                        class="flex items-end"
                        :class="myMessage ? 'ml-1 lg:ml-3' : 'mr-1 lg:mr-3'">
                        <template v-if="activeChat.is_public && !myMessage">
                            <Profiler 
                                :getPopupContainer="getPopupContainer"
                                :user="messageItem.message_author">
                                <a-avatar
                                    v-if="authorAvatar"
                                    :key="authorId"
                                    :style="avatarColor"
                                    :size="windowWidth > 864 ? 34 : 28"
                                    :src="authorAvatar" />
                                <a-avatar
                                    v-else
                                    :style="avatarColor"
                                    :size="windowWidth > 864 ? 34 : 28">
                                    {{ avatarText }}
                                </a-avatar>
                            </Profiler>
                        </template>
                        <template v-else>
                            <a-avatar
                                v-if="authorAvatar"
                                :key="authorId"
                                :style="avatarColor"
                                :size="windowWidth > 864 ? 34 : 28"
                                :src="authorAvatar" />
                            <a-avatar
                                v-else
                                :style="avatarColor"
                                :size="windowWidth > 864 ? 34 : 28">
                                {{ avatarText }}
                            </a-avatar>
                        </template>
                    </div>
                    <div
                        class="bubble"
                        :ref="`mb_${messageItem.message_uid}`"
                        :class="[bubbleBackground, isDelete, (textLength || fileExchangePreviewUrl) && 'large_message', expand && 'show', isMobile && !useDesktopMessageMenu && 'mobile', messageItem.is_system && 'is_system', fileExchangePreviewUrl && 'file_exchange_message']"
                        v-touch:longtap="longtapHandler">
                        <div
                            class="mb-1 user_name text-xs flex item-center font-semibold">
                            <template v-if="messageItem.message_author">
                                <i 
                                    v-if="messageItem.forwarded" 
                                    v-tippy
                                    :content="$t('chat.forwared_message')"
                                    class="fi fi-rr-undo mr-2" />
                                <div v-if="forwarded" class="flex items-center gap-1 mr-1">
                                    <span>{{ $t('chat.forwared_from') }}</span>
                                    <a-avatar
                                        v-if="authorAvatar"
                                        :key="authorId"
                                        :style="avatarColor"
                                        :size="14"
                                        :src="authorAvatar" />
                                    <a-avatar
                                        v-else
                                        :style="avatarColor"
                                        :size="14">
                                        {{ avatarText }}
                                    </a-avatar>
                                </div>
                                <template v-if="messageItem.message_author.last_name || messageItem.message_author.first_name">
                                    {{messageItem.message_author.last_name || ""}} {{messageItem.message_author.first_name || ""}}
                                </template>
                                <template v-else>{{messageItem.message_author.full_name}}</template>
                            </template>
                            <template v-if="messageItem.is_system">
                                <div v-if="messageItem.is_ai_message" class="flex items-center">
                                    <span class="mr-1 inline-block" style="min-width: 18px;">
                                        <img src="@/assets/svg/ai_icons.svg" style="max-width: 18px;" />
                                    </span>
                                    <i class="title-systemic">
                                        {{$t('chat.ai_system')}}
                                    </i>
                                </div>
                                <span v-else class="title-systemic">
                                    <i>
                                        {{$t('chat.systemic2')}}
                                    </i>
                                </span>
                            </template>
                        </div>
                        <SharedObject
                            v-if="!messageItem.is_deleted && messageItem.share"
                            :myMessage="myMessage"
                            :message="messageItem" />
                        <div v-if="messageItem.message_forwarded" class="mb-2 forwarded_wrapper">
                            <ChatMessage 
                                :messageItem="messageItem.message_forwarded" 
                                shareMessage 
                                forwarded
                                :user="user" />
                        </div>
                        <div
                            class="cursor-pointer reply_message truncate w-full mt-2 mb-2 pt-1 pb-1 pr-2"
                            v-if=" messageItem.message_reply && !messageItem.is_deleted"
                            @click="messSearch(messageItem.message_reply)">
                            <template v-if="messageItem.message_reply.message_author">
                                <div class="reply_chat_author truncate">
                                    {{messageItem.message_reply.message_author.full_name}}
                                    {{messageItem.message_reply.message_author.id === activeChat.chat_author.id ? ` - ${$t('chat.owner')}` : ''}}
                                </div>
                            </template>
                            <template v-if="messageItem.message_reply.text.length">
                                <TextViewer 
                                    :body="messageItem.message_reply.text" 
                                    collapsible 
                                    :collapseHandler="resizeEvent"
                                    :toggleButtonColor="myMessage ? '#fff' : '#416ce9'"
                                    :overlayColor="myMessage ? '#416ce9' : '#f2f2f2'" />
                            </template>
                            <template v-else>
                                <template v-if="messageItem.message_reply.share">
                                    <div class="reply_text text-sm">
                                        {{ replySharePreviewText }}
                                    </div>
                                </template>
                                <div
                                    v-else
                                    class="reply_text text-sm">
                                    {{ replyMessageFallbackText }}
                                </div>
                            </template>
                        </div>

                        <FileExchangeLinkPreview
                            v-if="fileExchangePreviewUrl"
                            :url="fileExchangePreviewUrl" />
                        <a
                            v-if="videoPreview && videoPreview.thumbnailUrl && !fileExchangePreviewUrl"
                            :href="videoPreview.url"
                            target="_blank"
                            rel="noopener noreferrer"
                            class="youtube-preview"
                            :class="myMessage && 'youtube-preview_my'">
                            <div class="youtube-preview__thumb">
                                <img
                                    :src="videoPreview.thumbnailUrl"
                                    :alt="videoPreview.title">
                                <span class="youtube-preview__play">
                                    <i class="fi fi-rr-play"></i>
                                </span>
                            </div>
                            <div class="youtube-preview__meta">
                                <div class="youtube-preview__title">
                                    {{ videoPreview.title }}
                                </div>
                                <div class="youtube-preview__link">
                                    {{ videoPreview.displayUrl }}
                                </div>
                            </div>
                        </a>
                        <div
                            v-else-if="videoPreview && videoPreview.embedUrl && !fileExchangePreviewUrl"
                            class="video-preview"
                            :class="myMessage && 'video-preview_my'">
                            <div class="video-preview__frame">
                                <iframe
                                    :src="videoPreview.embedUrl"
                                    :title="videoPreview.title"
                                    frameborder="0"
                                    allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share"
                                    allowfullscreen />
                            </div>
                            <a
                                :href="videoPreview.url"
                                target="_blank"
                                rel="noopener noreferrer"
                                class="video-preview__link">
                                {{ videoPreview.displayUrl }}
                            </a>
                        </div>
                        <TextViewer
                            v-if="!fileExchangePreviewUrl"
                            :body="messageBody" />

                        <div
                            v-if="fileExchangePreviewUrl"
                            class="text_expand">
                            <span
                                class="btn"
                                @click="toggleExpand">
                                {{ expand ? $t('collapse') : $t('uncover') }}
                            </span>
                        </div>

                        <ChatMessageFiles
                            v-if="showFiles"
                            :message="messageItem" />

                        <div class="flex items-center text-xs mt-1" :class="messageReactions.length ? 'justify-between' : 'justify-end'">
                            <transition-group
                                v-if="!shareMessage && messageReactions.length"
                                name="reaction"
                                tag="div"
                                class="flex flex-wrap gap-1 message_reaction">
                                <template v-if="isMobile && !useDesktopMessageMenu">
                                    <div
                                        v-for="react in messageReactions" 
                                        class="message_reaction__item"
                                        :key="react.reaction.id"
                                        :class="{ active: react.my_reaction }"
                                        @click="selectReaction(react.reaction)">
                                        <span>{{ react.reaction.icon }}</span> {{ react.users_count }}
                                    </div>
                                </template>
                                <template v-else>
                                    <a-popover 
                                        v-for="react in messageReactions" 
                                        :key="react.reaction.id"
                                        :visible="openedReactionId === react.reaction.id"
                                        transitionName=""
                                        destroyTooltipOnHide
                                        overlayClassName="reactions_popover"
                                        :mouseEnterDelay="0.2"
                                        :placement="reactionPlacement(react.reaction.id)"
                                        autoAdjustOverflow
                                        @visibleChange="v => onReactVisibleChange(v, react.reaction.id)">
                                        <div
                                            class="message_reaction__item"
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
                                                    :messageItem="messageItem" />
                                            </div>
                                        </template>
                                    </a-popover>
                                </template>
                            </transition-group>
                            <div v-else></div>

                            <div class="flex items-center ml-2">
                                <component
                                    :ref="`mobile_menu_${messageItem.message_uid}`"
                                    :is="menuComponent"
                                    :useReact="useReact"
                                    :openReactionModal="openReactionModal"
                                    :messageItem="messageItem"
                                    :deleteBtnShow="deleteBtnShow"
                                    :сreateATicket="сreateATicket"
                                    :pinMessageOn="pinMessageOn"
                                    :pinMessageShow="pinMessageShow"
                                    :replyMethod="replyMethod"
                                    :editMessage="editMessage"
                                    :createTask="createTask"
                                    :pinMessage="pinMessage"
                                    :forwardMessage="forwardMessage"
                                    :selectReaction="selectReaction"
                                    :copyMessage="copyMessage"
                                    :isScrolling="isScrolling"
                                    :deleteMessage="deleteMessage"
                                    :unpinMessage="unpinMessage"
                                    :openOrderDrawer="createOrder"
                                    :messSearch="messSearch"
                                    :showViewsAction="showViewsAction"
                                    :messageViewsCount="normalizedMessageViewsCount"
                                    :messageViewsLoading="messageViewsLoading"
                                    :messageViewsText="messageViewsText"
                                    :getMessageViews="getMessageViews"
                                    :openViewsModal="openViewsModal"
                                    :messageRef="$refs[`mb_${messageItem.message_uid}`]" />

                                <span class="flex items-center cursor-default" style="opacity: 0.6;">
                                    <transition name="u-slide-fade">
                                        <span v-if="messageItem.updated" class="mr-1" v-tippy :content="`${$t('chat.updated')}: ${$moment(messageItem.updated).format('DD.MM.YYYY HH:mm')}`">
                                            {{ $t('chat.updated') }}
                                        </span>
                                    </transition>
                                    {{messageDate}}
                                    <template v-if="myMessage">
                                        <i class="ml-2 fi" :class="isReaded ? 'fi-rr-check-double' : 'fi-rr-check'"></i>
                                    </template>
                                </span>
                                <div
                                    v-if="windowWidth > 864 && menuLoading"
                                    class="ml-3">
                                    <a-spin size="small" />
                                </div>
                            </div>
                        </div>
                    </div>
                    <div v-if="!shareMessage && !messageItem.is_system && (useDesktopMessageMenu || !isMobile) && !isViewContext" :class="btnDropdownVisible && 'active'" class="message_dots">
                        <a-dropdown v-model="btnDropdownVisible" :getPopupContainer="getPopupContainer" :trigger="['click']" @visibleChange="visibleChangeButton">
                            <div
                                :class="[myMessage ? 'mr-2' : 'ml-2']"
                                @click.stop="openMenu">
                                <div class="message_dots__btn">
                                    <i class="fi fi-rr-menu-dots-vertical" />
                                </div>
                            </div>
                            <a-menu slot="overlay">
                                <a-menu-item key="loading" v-if="actionLoading">
                                    <a-spin size="small" />
                                </a-menu-item>
                                <template v-else>
                                    <template v-if="actions">
                                        <a-menu-item
                                            v-if="useReact && reactions && reactions.length"
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
                                        <template v-if="!pinMessageOn">
                                            <a-menu-item
                                                v-if="actions.reply && actions.reply.availability"
                                                key="1"
                                                class="flex items-center"
                                                @click="replyMethod()">
                                                <i class="fi fi-rr-comment mr-2"></i>
                                                {{$t('chat.to_answer')}}
                                            </a-menu-item>
                                            <a-menu-item
                                                key="forward"
                                                class="flex items-center"
                                                @click="forwardMessage()">
                                                <i class="fi fi-rr-undo mr-2" />
                                                {{ $t('chat.forward') }}
                                            </a-menu-item>
                                            <a-menu-item
                                                v-if="!messageItem.forwarded && actions.edit && actions.edit.availability"
                                                key="edit"
                                                class="flex items-center"
                                                @click="editMessage()">
                                                <i class="fi fi-rr-edit mr-2" />
                                                {{ $t('chat.edit') }}
                                            </a-menu-item>
                                            <a-menu-item
                                                v-if="actions.add_task && actions.add_task.availability && isSupportChat"
                                                key="3"
                                                class="flex items-center"
                                                @click="createTask()">
                                                <i class="fi fi-rr-checkbox mr-2"></i>
                                                {{$t('chat.set_task')}}
                                            </a-menu-item>
                                            <a-menu-item
                                                v-if="actions.add_order && actions.add_order.availability && messageItem.message_author && user && messageItem.message_author.id !== user.id"
                                                key="8"
                                                class="flex items-center"
                                                @click="createOrder()">
                                                <i class="fi fi-rr-shopping-cart-check mr-2"></i>
                                                {{$t('chat.set_order')}}
                                            </a-menu-item>
                                            <a-menu-item
                                                v-if="actions.pin && actions.pin.availability && pinMessageShow && !messageItem.is_pinned"
                                                key="5"
                                                class="flex items-center"
                                                @click="pinMessage()">
                                                <i class="fi fi-rr-thumbtack mr-2"></i>
                                                {{$t('chat.anchor')}}
                                            </a-menu-item>
                                            <a-menu-item
                                                v-if="actions.copy_text && actions.copy_text.availability && messageItem.text"
                                                key="9"
                                                class="flex items-center"
                                                @click="copyMessage()">
                                                <i class="fi fi-rr-copy mr-2"></i>
                                                {{$t('chat.copy_to_clipboard')}}
                                            </a-menu-item>
                                            <a-menu-item
                                                key="13"
                                                v-if="actions.create_help_desk_ticket && actions.create_help_desk_ticket.availability"
                                                class="flex items-center"
                                                @click="сreateATicket()">
                                                <i class="fi fi-rr-comment-alt-dots mr-2"></i>
                                                {{$t('helpdesk.create_ticket')}}
                                            </a-menu-item>
                                        </template>
                                        <template v-if="actions.pin && actions.pin.availability && messageItem.is_pinned">
                                            <a-menu-item
                                                v-if="pinMessageShow"
                                                key="6"
                                                class="flex items-center"
                                                @click="unpinMessage()">
                                                <i class="fi fi-rr-comment-xmark mr-2"></i>
                                                {{$t('chat.unpin')}}
                                            </a-menu-item>
                                            <a-menu-item
                                                v-if="pinMessageOn"
                                                key="7"
                                                class="flex items-center"
                                                @click="messSearch(messageItem)">
                                                <i class="fi fi-rr-comments mr-2"></i>
                                                {{$t('chat.show_in_chat')}}
                                            </a-menu-item>
                                        </template>
                                        <template v-if="showViewsAction">
                                            <a-sub-menu
                                                v-if="normalizedMessageViewsCount && messageViewsUsers.length"
                                                class="message_views_submenu"
                                                key="views">
                                                <template #title>
                                                    <div class="flex items-center" @click.stop="openViewsModal()">
                                                        <i class="fi fi-rr-eye mr-2" />
                                                        {{ messageViewsText }}
                                                    </div>
                                                </template>
                                                <a-menu-item
                                                    v-for="userItem in messageViewsUsers"
                                                    :key="userItem.id"
                                                    @click="openViewsModal()">
                                                    <div class="message_views_user flex items-center" :title="userItem.full_name">
                                                        <div class="mr-2">
                                                            <a-avatar
                                                                :size="18"
                                                                :key="userItem.id"
                                                                avResize
                                                                :src="userItem.avatar && userItem.avatar.path ? userItem.avatar.path : ''"
                                                                icon="user" />
                                                        </div>
                                                        <div class="message_views_user__name truncate">
                                                            {{ userItem.full_name }}
                                                        </div>
                                                    </div>
                                                </a-menu-item>
                                                <a-menu-item
                                                    v-if="messageViewsUsers.length > 1"
                                                    class="flex items-center justify-between"
                                                    @click="openViewsModal()">
                                                    {{ $t('comment.view_all') }}
                                                    <i class="fi fi-rr-arrow-small-right ml-1" />
                                                </a-menu-item>
                                            </a-sub-menu>
                                            <a-menu-item v-else key="empty_views" class="flex items-center">
                                                <a-spin :spinning="messageViewsLoading" size="small" class="mr-2">
                                                    <i class="fi fi-rr-eye" />
                                                </a-spin>
                                                {{ messageViewsText }}
                                            </a-menu-item>
                                        </template>
                                        <a-menu-item
                                            key="2"
                                            class="text-red-500 flex items-center"
                                            v-if="deleteBtnShow"
                                            @click="deleteMessage()">
                                            <i class="fi fi-rr-trash mr-2"></i>
                                            {{$t('chat.remove')}}
                                        </a-menu-item>
                                    </template>
                                </template>
                            </a-menu>
                        </a-dropdown>
                    </div>
                </div>
                <a-menu slot="overlay">
                    <a-menu-item key="loading" v-if="actionLoading">
                        <a-spin size="small" />
                    </a-menu-item>
                    <template v-else>
                        <template v-if="actions">
                            <a-menu-item
                                v-if="useReact && reactions && reactions.length"
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
                            <template v-if="!pinMessageOn">
                                <a-menu-item
                                    v-if="actions.reply && actions.reply.availability"
                                    key="1"
                                    class="flex items-center"
                                    @click="replyMethod()">
                                    <i class="fi fi-rr-comment mr-2"></i>
                                    {{$t('chat.to_answer')}}
                                </a-menu-item>
                                <a-menu-item
                                    key="forward"
                                    class="flex items-center"
                                    @click="forwardMessage()">
                                    <i class="fi fi-rr-undo mr-2" />
                                    {{ $t('chat.forward') }}
                                </a-menu-item>
                                <a-menu-item
                                    v-if="!messageItem.forwarded && actions.edit && actions.edit.availability"
                                    key="edit"
                                    class="flex items-center"
                                    @click="editMessage()">
                                    <i class="fi fi-rr-edit mr-2" />
                                    {{ $t('chat.edit') }}
                                </a-menu-item>
                                <a-menu-item
                                    v-if="actions.add_task && actions.add_task.availability && isSupportChat"
                                    key="3"
                                    class="flex items-center"
                                    @click="createTask()">
                                    <i class="fi fi-rr-checkbox mr-2"></i>
                                    {{$t('chat.set_task')}}
                                </a-menu-item>
                                <a-menu-item
                                    v-if="actions.add_order && actions.add_order.availability && messageItem.message_author && user && messageItem.message_author.id !== user.id"
                                    key="8"
                                    class="flex items-center"
                                    @click="createOrder()">
                                    <i class="fi fi-rr-shopping-cart-check mr-2"></i>
                                    {{$t('chat.set_order')}}
                                </a-menu-item>
                                <a-menu-item
                                    v-if="actions.pin && actions.pin.availability && pinMessageShow && !messageItem.is_pinned"
                                    key="5"
                                    class="flex items-center"
                                    @click="pinMessage()">
                                    <i class="fi fi-rr-thumbtack mr-2"></i>
                                    {{$t('chat.anchor')}}
                                </a-menu-item>
                                <a-menu-item
                                    v-if="actions.copy_text && actions.copy_text.availability && messageItem.text"
                                    key="9"
                                    class="flex items-center"
                                    @click="copyMessage()">
                                    <i class="fi fi-rr-copy mr-2"></i>
                                    {{$t('chat.copy_to_clipboard')}}
                                </a-menu-item>
                                <a-menu-item
                                    key="13"
                                    v-if="actions.create_help_desk_ticket && actions.create_help_desk_ticket.availability"
                                    class="flex items-center"
                                    @click="сreateATicket()">
                                    <i class="fi fi-rr-comment-alt-dots mr-2"></i>
                                    {{$t('helpdesk.create_ticket')}}
                                </a-menu-item>
                            </template>
                            <template v-if="actions.pin && actions.pin.availability && messageItem.is_pinned">
                                <a-menu-item
                                    v-if="pinMessageShow"
                                    key="6"
                                    class="flex items-center"
                                    @click="unpinMessage()">
                                    <i class="fi fi-rr-comment-xmark mr-2"></i>
                                    {{$t('chat.unpin')}}
                                </a-menu-item>
                                <a-menu-item
                                    v-if="pinMessageOn"
                                    key="7"
                                    class="flex items-center"
                                    @click="messSearch(messageItem)">
                                    <i class="fi fi-rr-comments mr-2"></i>
                                    {{$t('chat.show_in_chat')}}
                                </a-menu-item>
                            </template>
                            <template v-if="showViewsAction">
                                <a-sub-menu
                                    v-if="normalizedMessageViewsCount && messageViewsUsers.length"
                                    class="message_views_submenu"
                                    key="views">
                                    <template #title>
                                        <div class="flex items-center" @click.stop="openViewsModal()">
                                            <i class="fi fi-rr-eye mr-2" />
                                            {{ messageViewsText }}
                                        </div>
                                    </template>
                                    <a-menu-item
                                        v-for="userItem in messageViewsUsers"
                                        :key="userItem.id"
                                        @click="openViewsModal()">
                                        <div class="message_views_user flex items-center" :title="userItem.full_name">
                                            <div class="mr-2">
                                                <a-avatar
                                                    :size="18"
                                                    :key="userItem.id"
                                                    avResize
                                                    :src="userItem.avatar && userItem.avatar.path ? userItem.avatar.path : ''"
                                                    icon="user" />
                                            </div>
                                            <div class="message_views_user__name truncate">
                                                {{ userItem.full_name }}
                                            </div>
                                        </div>
                                    </a-menu-item>
                                    <a-menu-item
                                        v-if="messageViewsUsers.length > 1"
                                        class="flex items-center justify-between"
                                        @click="openViewsModal()">
                                        {{ $t('comment.view_all') }}
                                        <i class="fi fi-rr-arrow-small-right ml-1" />
                                    </a-menu-item>
                                </a-sub-menu>
                                <a-menu-item v-else key="empty_views" class="flex items-center">
                                    <a-spin :spinning="messageViewsLoading" size="small" class="mr-2">
                                        <i class="fi fi-rr-eye" />
                                    </a-spin>
                                    {{ messageViewsText }}
                                </a-menu-item>
                            </template>
                            <a-menu-item
                                key="2"
                                class="text-red-500 flex items-center"
                                v-if="deleteBtnShow"
                                @click="deleteMessage()">
                                <i class="fi fi-rr-trash mr-2"></i>
                                {{$t('chat.remove')}}
                            </a-menu-item>
                        </template>
                    </template>
                </a-menu>
            </a-dropdown>
        </div>
        <component
            :is="orderDriwer"
            page_name="crm.order_create_page_chat"
            :injectContractor="injectContractor"
            :injectContractorFilter="injectContractorFilter"
            ref="orderDrawer" />
        <component 
            :is="reactionModal" 
            ref="reactionModal"
            :messageItem="messageItem" />
        <component
            :is="messageViewsModal"
            ref="messageViewsModal"
            :messageUid="messageItem.message_uid"
            :viewCount="normalizedMessageViewsCount" />
        <a-modal
            v-if="fileExchangePreviewUrl"
            :visible="expand"
            :title="$t('chat.send_via_exchange')"
            :footer="null"
            :width="isMobile ? '100%' : 920"
            :wrapClassName="isMobile ? 'file_exchange_preview_modal_mobile' : ''"
            :bodyStyle="{ padding: 0, height: isMobile ? 'calc(100vh - 55px)' : '85vh' }"
            centered
            destroyOnClose
            @cancel="toggleExpand">
            <iframe
                :src="fileExchangePreviewEmbedUrl"
                class="file_exchange_preview_modal__frame"
                frameborder="0"
                allow="clipboard-write"
                scrolling="yes" />
        </a-modal>
    </div>
</template>

<script>
import eventBus from '@/utils/eventBus'
import ChatEventBus from '../../utils/ChatEventBus'
import { mapMutations, mapState } from 'vuex'
import computedMixin from './computed'
import { errorHandler } from '@/utils/index.js'
import { declOfNum } from '@/utils/utils.js'
import { isVoiceMessageFile } from '@/utils/voice'
import { getChatSharePreviewText } from '@/utils/chatPreview'
export default {
    name: "ChatMessage",
    components: {
        ChatMessageFiles: () => import('./ChatMessageFiles'),
        FileExchangeLinkPreview: () => import('./FileExchangeLinkPreview.vue'),
        SharedObject: () => import('./messages/SharedObject'),
        TextViewer: () => import('@apps/CKEditor/TextViewer.vue'),
        ReactUserList: () => import('./ReactUserList.vue'),
        ChatMessage: () => import('./index.vue')
    },
    mixins: [computedMixin],
    props: {
        messageItem: {
            type: Object,
            require: true
        },
        user: {
            type: Object,
            required: false
        },
        replySearch: {
            type: Function,
            default: () => {}
        },
        pinMessageOn: {
            type: Boolean,
            default: false
        },
        shareMessage: {
            type: Boolean,
            default: false
        },
        isScrolling: {
            type: Boolean,
            default: false
        },
        resizeEvent: {
            type: Function,
            default: () => {}
        },
        useReact: {
            type: Boolean,
            default: false
        },
        forwarded: {
            type: Boolean,
            default: false
        }
    },
    computed: {
        ...mapState({
            config: state => state.config.config,
            reactions: state => state.chat.reactions
        }),
        reactionModal() {
            if(this.isMobile)
                return () => import('./ReactionModal.vue')
            return null
        },
        messageViewsModal() {
            if(this.showViewsAction)
                return () => import('./MessageViewsModal.vue')
            return null
        },
        messageReactions() {
            return this.messageItem.reactions || []
        },
        showViewsAction() {
            return Boolean(this.activeChat?.is_public && this.myMessage)
        },
        normalizedMessageViewsCount() {
            const count = this.messageViewsCount - (this.messageViewsHasCurrentUser ? 1 : 0)
            if (count < 0)
                return 0
            return count
        },
        messageViewsText() {
            if (this.messageViewsLoading)
                return this.$t('comment.view4')
            if (!this.normalizedMessageViewsCount)
                return this.$t('comment.no_view')
            return `${this.normalizedMessageViewsCount} ${declOfNum(this.normalizedMessageViewsCount, [this.$t('comment.view1'), this.$t('comment.view2'), this.$t('comment.view3')])}`
        },
        avatarColor() {
            if(this.messageItem?.message_author?.color)
                return `background: ${this.messageItem.message_author.color}!important;color:#fff!important;position: sticky;bottom: 0px;z-index: 5;`
            return `background: #fff!important;color:var(--text)!important;position: sticky;bottom: 0px;z-index: 5;`
        },
        authorAvatar() {
            const avatar = this.messageItem.message_author?.avatar
            if (this.messageItem.message_author?.avatar?.path?.includes('null.null')) return null
            return avatar?.path || avatar
        },
        isSupportChat() {
            if(this.activeChat?.is_support) {
                if(this.user.is_support) {
                    return true
                } else {
                    return false
                }
            }
            return true
        },
        authorId() {
            return this.messageItem?.message_author.id
        },
        orderDriwer() {
            return () => import('@apps/Orders/views/CreateOrder/OrderDrawer.vue')
        },
        fileExchangePreviewUrl() {
            const normalizedText = this.getNormalizedMessageText()

            if (!normalizedText || this.messageItem.is_deleted || this.showFiles) {
                return ''
            }

            if (!/^https:\/\/files\.gos24\.kz\/\S+$/i.test(normalizedText)) {
                return ''
            }

            return normalizedText
        },
        fileExchangePreviewEmbedUrl() {
            if (!this.fileExchangePreviewUrl) {
                return ''
            }

            try {
                const url = new URL(this.fileExchangePreviewUrl)
                url.searchParams.set('embed', 'chat-preview')
                url.searchParams.set('lang', String(this.$i18n?.locale || 'ru').toLowerCase() === 'kk' ? 'kz' : String(this.$i18n?.locale || 'ru').toLowerCase())
                return url.toString()
            } catch (error) {
                return this.fileExchangePreviewUrl
            }
        },
        showFiles() {
            return this.messageItem?.attachments?.length && !this.messageItem.is_deleted
        },
        videoPreview() {
            if (this.messageItem?.is_deleted || this.showFiles || this.fileExchangePreviewUrl) {
                return null
            }

            const normalizedText = this.getNormalizedMessageText()
            if (!normalizedText) {
                return null
            }

            const urlMatch = normalizedText.match(/https?:\/\/[^\s<>"']+/i)
            if (!urlMatch?.[0]) {
                return null
            }

            return this.getVideoPreviewData(urlMatch[0])
        },
        messageBody() {
            if (this.messageItem?.is_deleted) {
                return this.$t('chat.deleted_message_text')
            }

            return this.messageItem?.text || ''
        },
        replyMessageFallbackText() {
            const attachments = Array.isArray(this.messageItem?.message_reply?.attachments)
                ? this.messageItem.message_reply.attachments
                : []

            if (attachments.length && attachments.every(item => isVoiceMessageFile(item))) {
                return this.$t('chat.voice_message')
            }

            return this.$t('chat.file_and_image')
        },
        replySharePreviewText() {
            return getChatSharePreviewText(this.messageItem?.message_reply?.share, this.$t.bind(this))
        },
        avatarText() {
            const n = this.messageItem.message_author.full_name.split(' ')
            return `${n[0].charAt(0).toUpperCase()}${n[1] ? n[1].charAt(0).toUpperCase() : ''}`
        },
        isReaded() {
            const readedAtDate = this.$moment(this.activeChat.readed_at)
            const messageSentDate = this.$moment(this.messageItem.created)
            const isNotReaded = readedAtDate.isBefore(messageSentDate)
            return !isNotReaded
        }
    },
    data() {
        return {
            expand: false,
            deleteAnimationRunning: false,
            menuLoading: false,
            expandText: this.$t('chat.uncover'),
            visible: false,
            actions: null,
            actionLoading: false,
            injectContractor: {},
            injectContractorFilter: {},
            galleryInstance: null,
            galleryInitialized: false,
            galleryInitTimer: null,
            lg: null,
            lgWrapInst: null,
            moWrap: null,
            lazyHandler: null,
            menuSource: null,
            menuLoaded: false,
            ctxDropdownVisible: false,
            btnDropdownVisible: false,
            openedReactionId: null,
            messageViewsUsers: [],
            messageViewsCount: 0,
            messageViewsLoading: false,
            messageViewsHasCurrentUser: false
        }
    },
    methods: {
        ...mapMutations({
            setReplyMessage: 'chat/setReplyMessage',
            setPin: 'chat/PIN_MESSAGE',
            setUnpin: 'chat/UNPIN_MESSAGE',
            removeMessage: 'chat/removeMessage',
            changeReact: 'chat/MESSAGE_CHANGE_REACT'
        }),
        editMessage() {
            this.closeAllMenu()
            ChatEventBus.$emit('edit_message', this.messageItem)
        },
        openReactionModal() {
            if(this.$refs.reactionModal)
                this.$refs.reactionModal.openModal()
        },
        reactHeightCheck(count) {
            if(count >= 2)
                return 60
            if(count >= 3)
                return 70
            if(count >= 4)
                return 100
            if(count >= 5)
                return 120
            if(count >= 6)
                return 150
        },
        reactionPlacement(id) {
            const ref = this.$refs[`mb_${this.messageItem.message_uid}`]
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
            this.openedReactionId = visible ? id : null
        },
        isMyReaction(smile) {
            const reactions = this.messageItem.reactions || []
            return reactions.some(
                r => r.my_reaction && r.reaction.id === smile.id
            )
        },
        async selectReaction(reaction) {
            if(this.useReact) {
                const reactions = this.messageItem.reactions || []
                const myReaction = reactions.find(r => r.my_reaction)
                const openReaction = this.openedReactionId
                this.openedReactionId = null
                const nextReaction = myReaction && myReaction.reaction.id === reaction.id
                    ? null
                    : reaction

                try {
                    this.changeReact({
                        reaction: nextReaction,
                        chat_uid: this.messageItem.chat || this.messageItem.chat_uid,
                        message: this.messageItem
                    })
                    this.resizeEvent()
                    this.ctxDropdownVisible = false
                    this.btnDropdownVisible = false
                    await this.$http.post(`/reactions/related_object/${this.messageItem.message_uid}/set/`, {
                        reaction: nextReaction ? nextReaction.id : null
                    })
                    if(openReaction && nextReaction)
                        this.openedReactionId = openReaction
                    await this.$nextTick()
                    const ref = this.$refs[`reactUserList_${reaction.id}`]
                    const comp = Array.isArray(ref) ? ref[0] : ref

                    if (comp && typeof comp.reloadList === 'function')
                        comp.reloadList()
                } catch (error) {
                    errorHandler({ error })
                }
            }
        },
        getPopupContainer(trigger) {
            return trigger.parentNode
        },
        closeAllMenu() {
            this.ctxDropdownVisible = false
            this.btnDropdownVisible = false
        },
        openViewsModal() {
            this.closeAllMenu()
            this.$nextTick(() => {
                if (this.$refs.messageViewsModal)
                    this.$refs.messageViewsModal.openModal()
            })
        },
        openMenu() {
            this.ctxDropdownVisible = false
            if (this.btnDropdownVisible && this.menuSource === 'button') {
                this.btnDropdownVisible = false
                this.visible = false
                this.menuSource = null
                return
            }
            this.menuSource = 'button'
            this.btnDropdownVisible = true
            this.visibleChange(true)
        },
        visibleChangeContext(vis) {
            this.ctxDropdownVisible = vis
            this.visibleChange(vis, 'context')
        },
        visibleChangeButton(vis) {
            this.btnDropdownVisible = vis
            this.visibleChange(vis, 'button')
        },
        async copyMessage() {
            try {
                function htmlToText(html) {
                    const doc = new DOMParser().parseFromString(html, 'text/html')
                    return doc.body.textContent || ''
                }

                this.closeAllMenu()

                const html = this.messageItem.text
                const plain = htmlToText(html)

                const item = new ClipboardItem({
                    'text/plain': new Blob([plain], { type: 'text/plain' }),
                    'text/html': new Blob([html], { type: 'text/html' })
                })

                await navigator.clipboard.write([item])

                this.$message.info(this.$t('chat.copied_success'))
            } catch (e) {
                console.log(e)
                this.$message.error(this.$t('chat.copy_error'))
            }
        },
        escapeHtml(value) {
            return String(value || '')
                .replace(/&/g, '&amp;')
                .replace(/</g, '&lt;')
                .replace(/>/g, '&gt;')
                .replace(/"/g, '&quot;')
                .replace(/'/g, '&#39;')
        },
        getNormalizedMessageText() {
            const rawHtml = String(this.messageItem?.text || '').trim()
            if (!rawHtml) {
                return ''
            }

            const doc = new DOMParser().parseFromString(rawHtml, 'text/html')
            return (doc.body.textContent || '')
                .replace(/\u00A0/g, ' ')
                .replace(/\s+/g, ' ')
                .trim()
        },
        getVideoPreviewData(rawUrl) {
            try {
                const sanitizedUrl = String(rawUrl || '').replace(/[),.;!?]+$/, '')
                const url = new URL(sanitizedUrl)
                const hostname = url.hostname.replace(/^www\./i, '').toLowerCase()
                if (hostname === 'youtu.be' || hostname === 'youtube.com' || hostname === 'm.youtube.com' || hostname === 'music.youtube.com') {
                    let videoId = ''

                    if (hostname === 'youtu.be') {
                        videoId = url.pathname.split('/').filter(Boolean)[0] || ''
                    } else if (url.pathname === '/watch') {
                        videoId = url.searchParams.get('v') || ''
                    } else if (url.pathname.startsWith('/shorts/')) {
                        videoId = url.pathname.split('/')[2] || ''
                    } else if (url.pathname.startsWith('/embed/')) {
                        videoId = url.pathname.split('/')[2] || ''
                    }

                    if (!/^[a-zA-Z0-9_-]{11}$/.test(videoId)) {
                        return null
                    }

                    return {
                        service: 'youtube',
                        videoId,
                        url: `https://www.youtube.com/watch?v=${videoId}`,
                        embedUrl: `https://www.youtube.com/embed/${videoId}`,
                        thumbnailUrl: `https://img.youtube.com/vi/${videoId}/hqdefault.jpg`,
                        title: 'YouTube',
                        displayUrl: sanitizedUrl
                    }
                }

                if (hostname === 'vkvideo.ru') {
                    const videoMatch = url.pathname.match(/\/video(-?\d+)_([0-9]+)/i)
                    if (!videoMatch) {
                        return null
                    }

                    const ownerId = videoMatch[1]
                    const videoId = videoMatch[2]

                    return {
                        service: 'vkvideo',
                        videoId: `${ownerId}_${videoId}`,
                        url: sanitizedUrl,
                        embedUrl: `https://vkvideo.ru/video_ext.php?oid=${ownerId}&id=${videoId}&hd=2`,
                        thumbnailUrl: '',
                        title: 'VK Video',
                        displayUrl: sanitizedUrl
                    }
                }

                if (hostname === 'rutube.ru') {
                    const videoMatch = url.pathname.match(/\/video\/([a-z0-9]+)/i)
                    if (!videoMatch) {
                        return null
                    }

                    const videoId = videoMatch[1]

                    return {
                        service: 'rutube',
                        videoId,
                        url: sanitizedUrl,
                        embedUrl: `https://rutube.ru/play/embed/${videoId}`,
                        thumbnailUrl: '',
                        title: 'Rutube',
                        displayUrl: sanitizedUrl
                    }
                }

                if (/(\.|^)yandex\./i.test(hostname)) {
                    const previewMatch = url.pathname.match(/\/video\/preview\/([0-9]+)/i)
                    if (!previewMatch) {
                        return null
                    }

                    const videoId = previewMatch[1]

                    return {
                        service: 'yandex-video',
                        videoId,
                        url: sanitizedUrl,
                        embedUrl: `https://frontend.vh.yandex.ru/player/${videoId}`,
                        thumbnailUrl: '',
                        title: 'Yandex Video',
                        displayUrl: sanitizedUrl
                    }
                }

                if (hostname === 'facebook.com' || hostname === 'm.facebook.com' || hostname === 'web.facebook.com') {
                    let videoId = ''

                    if (url.pathname === '/watch/' || url.pathname === '/watch') {
                        videoId = url.searchParams.get('v') || ''
                    } else {
                        const videoMatch = url.pathname.match(/\/videos\/([0-9]+)/i)
                        const reelMatch = url.pathname.match(/\/reel\/([0-9]+)/i)
                        videoId = videoMatch?.[1] || reelMatch?.[1] || ''
                    }

                    if (!videoId) {
                        return null
                    }

                    return {
                        service: 'facebook',
                        videoId,
                        url: sanitizedUrl,
                        embedUrl: `https://www.facebook.com/plugins/video.php?href=${encodeURIComponent(sanitizedUrl)}&show_text=false&width=560`,
                        thumbnailUrl: '',
                        title: 'Facebook Video',
                        displayUrl: sanitizedUrl
                    }
                }

                return null
            } catch (error) {
                return null
            }
        },
        getAttachmentPath(path) {
            if(!path) return ''
            if(path.includes('chat_attachments'))
                return path

            const chatUid = this.messageItem.chat_uid || this.messageItem.chat
            return path + encodeURIComponent(`&chat_uid=${chatUid}&message_uid=${this.messageItem.message_uid}&target=chat_attachments`)
        },
        buildMessageDescription() {
            const baseText = this.messageItem.text || ''
            const attachments = Array.isArray(this.messageItem.attachments) ? this.messageItem.attachments : []

            if(!attachments.length) return baseText

            const attachmentsHtml = attachments
                .map(file => {
                    const filePath = this.getAttachmentPath(file?.path)
                    if(!filePath) return ''
                    const safePath = this.escapeHtml(filePath)

                    if(file?.is_image) {
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
        async сreateATicket() {
            try {
                this.closeAllMenu()
                const { data } = await this.$http.get('/help_desk/tickets/create_from_chat/', {
                    params: {
                        message_uid: this.messageItem.message_uid
                    }
                })
                eventBus.$emit('helpdesc_add_tickets', {
                    ...data,
                    receipt_date: this.messageItem.created,
                    message_uid: this.messageItem.message_uid,
                    description: this.buildMessageDescription()
                })
            } catch(error) {
                errorHandler({error})
            }
        },
        longtapHandler() {
            if(!this.messageItem.is_system && this.isMobile && !this.useDesktopMessageMenu) {
                this.$nextTick(() => {
                    this.$refs[`mobile_menu_${this.messageItem.message_uid}`]?.openMobileMenu()
                })
            }
        },
        async getMessageViews() {
            if (!this.showViewsAction)
                return

            try {
                this.messageViewsLoading = true
                this.messageViewsUsers = []
                this.messageViewsCount = 0
                this.messageViewsHasCurrentUser = false

                const { data } = await this.$http.get(`/chat/message/${this.messageItem.message_uid}/viewers/`, {
                    params: {
                        page_size: 5
                    }
                })

                this.messageViewsCount = data?.count || 0
                this.messageViewsHasCurrentUser = Boolean((data?.results || []).find(user => user.id === this.user?.id))
                this.messageViewsUsers = (data?.results || []).filter(user => user.id !== this.user?.id)
            } catch (error) {
                this.messageViewsCount = 0
                this.messageViewsUsers = []
                this.messageViewsHasCurrentUser = false
                errorHandler({ error, show: false })
            } finally {
                this.messageViewsLoading = false
            }
        },
        async visibleChange(vis, source = null) {
            this.visible = vis
            if (source)
                this.menuSource = vis ? source : null
            if ((this.btnDropdownVisible && vis && source !== 'button') || this.openedReactionId && vis)
                this.ctxDropdownVisible = false
            if (this.ctxDropdownVisible && vis && source !== 'context')
                this.btnDropdownVisible = false
            if (!vis) {
                this.menuSource = null
                return
            }

            this.getMessageViews()

            if (this.menuLoaded) return

            try {
                this.actionLoading = true

                const { data } = await this.$http.get('/chat/message/action_info/', {
                    params: {
                        message: this.messageItem.message_uid,
                        chat: this.messageItem.chat || this.messageItem.chat_uid
                    }
                })

                this.$store.dispatch('chat/getReactions')

                if (data?.actions) {
                    this.actions = data.actions
                    this.menuLoaded = true
                }
            } catch (error) {
                errorHandler({ error, show: false })
            } finally {
                this.actionLoading = false
            }
        },
        forwardMessage() {
            try {
                this.closeAllMenu()

                let object = {...this.messageItem}

                if(this.messageItem.forwarded)
                    object = this.messageItem.message_forwarded

                this.$store.commit('share/SET_SHARE_PARAMS', {
                    useForwarded: true,
                    object
                })
            } catch(error) {
                console.error(error)
            }
        },
        replyMethod() {
            this.closeAllMenu()
            this.setReplyMessage({
                id: this.activeChat.chat_uid,
                mesage: this.messageItem
            })
            ChatEventBus.$emit('inputFocus')
        },
        messSearch(mess) {
            this.menuLoading = true
            this.replySearch(mess)
                .then(() => {
                    ChatEventBus.$emit('SLIDE_TO_PIN', mess)
                    this.menuLoading = false
                })
        },
        async pinMessage() {
            try {
                this.closeAllMenu()
                this.menuLoading = true
                let data = this.messageItem
                data.chat_uid = this.messageItem.chat_uid ? this.messageItem.chat_uid : this.messageItem.chat
                this.$socket.client.emit("chat_pin_message", data)
                this.setPin(data)
                ChatEventBus.$emit('PINNED_MESSAGE', data)
            } catch(error) {
                errorHandler({error})
            } finally {
                this.menuLoading = false
            }
        },
        async unpinMessage() {
            try {
                this.closeAllMenu()
                this.menuLoading = true
                let data = this.messageItem
                data.chat_uid = this.messageItem.chat_uid ? this.messageItem.chat_uid : this.messageItem.chat
                this.$socket.client.emit("chat_unpin_message", this.messageItem)
                this.setUnpin(data)
            } catch(error) {
                errorHandler({error})
            } finally {
                this.menuLoading = false
            }
        },
        async sendMessage() {
            try{
                this.closeAllMenu()
                this.menuLoading = true
                const res = await this.$store.dispatch('chat/getUserChat', this.messageItem.message_author.id)
                if(res) {
                    this.$router.push({name: 'chat', query: {id: res.id}})
                    this.$store.commit('chat/SET_OPEN_DIALOG', res)
                }
            } catch(error) {
                errorHandler({error})
            } finally {
                this.menuLoading = false
            }
        },
        createOrder() {
            this.closeAllMenu()
            if(this.messageItem.text) {
                this.injectContractor['comment'] = this.messageItem.text
            }
            this.injectContractorFilter = {
                profiles: this.messageItem.message_author.id
            }
            this.$nextTick(() => {
                if(this.$refs['orderDrawer']) {
                    this.$refs['orderDrawer'].toggleDrawer()
                }
            })
        },
        async createTask() {
            this.closeAllMenu()
            let visors = []
            const messageDescription = this.buildMessageDescription()
            if(this.activeChat.is_public) {
                try {
                    this.menuLoading = true
                    const {data} = await this.$http.get('/chat/member/list/', {
                        params: {
                            chat: this.activeChat.chat_uid
                        }
                    })
                    if(data && data.results.length) {
                        data.results.forEach(({user}) => {
                            visors.push(user)
                        })
                    }
                } catch(error) {
                    errorHandler({error})
                } finally {
                    this.menuLoading = false
                }
            }

            const stripHtml = html => {
                const div = document.createElement('div')
                div.innerHTML = html
                return div.textContent || div.innerText || ''
            }

            let form = {
                name: stripHtml(this.messageItem.text),
                description: messageDescription,
                operator: this.messageItem.chat_author,
                attachments: this.messageItem.attachments,
                reason: this.messageItem.message_uid
            }
            if(this.activeChat.workgroup) {
                if(!this.activeChat.workgroup.is_project) {
                    form.workgroup = {
                        name: this.activeChat.workgroup.name,
                        id: this.activeChat.workgroup.uid
                    }
                }
                if(this.activeChat.workgroup.is_project) {
                    form.project = {
                        name: this.activeChat.workgroup.name,
                        id: this.activeChat.workgroup.uid,
                        dead_line: this.activeChat.workgroup.dead_line || null,
                        date_start_plan: this.activeChat.workgroup.date_start_plan || null
                    }
                }
            }
            if(visors.length)
                form.visors = visors
            if(this.messageItem.text.length > 150) {
                if(this.activeChat?.name)
                    form.name = this.$t('chat.message_task', {chat: this.activeChat.name})
                else
                    form.name = this.$t('chat.message_task_empty')
            } else
                form.name = stripHtml(this.messageItem.text)
            eventBus.$emit(this.isMobile ? 'ADD_WATCH' : 'add_task_modal_watch', {type: 'add_task', data: form})
        },
        async deleteMessage() {
            try {
                if (this.deleteAnimationRunning) return
                this.closeAllMenu()
                await this.runDeleteAnimation()
                const data = {chat_uid: this.activeChat.chat_uid, message_uid: this.messageItem.message_uid}
                this.$socket.client.emit('chat_delete_message', data)
                this.removeMessage(data)
            } catch(error) {
                errorHandler({error})
            }
        },
        runDeleteAnimation() {
            if (this.shareMessage || this.forwarded) {
                return Promise.resolve()
            }

            const bubbleRef = this.$refs[`mb_${this.messageItem.message_uid}`]
            const bubble = Array.isArray(bubbleRef) ? bubbleRef[0] : bubbleRef

            if (!bubble) {
                return Promise.resolve()
            }

            this.deleteAnimationRunning = true
            bubble.classList.add('bubble--deleting')

            return new Promise(resolve => {
                window.setTimeout(resolve, 260)
            }).finally(() => {
                this.deleteAnimationRunning = false
            })
        },
        async galleryInit() {
            this.$nextTick(async () => {
                if(this.galleryInitTimer) {
                    clearTimeout(this.galleryInitTimer)
                    this.galleryInitTimer = null
                }
                this.galleryInitTimer = setTimeout(async () => {
                    const lightboxWrap = this.$refs[`message_${this.messageItem.message_uid}`]
                    const lightbox = lightboxWrap ? lightboxWrap.querySelectorAll('.ch_lght') : null
                    if(!lightbox?.length) {
                        this.destroyGallery()
                        return
                    }
                    try {
                        const [{default: lightGallery}, {default: lgThumbnail}, {default: lgFullscreen}, {default: lgZoom}, {default: lgRotate}] = await Promise.all([
                            import('lightgallery.js'),
                            import('lg-thumbnail.js'),
                            import('lg-fullscreen.js'),
                            import('lg-zoom.js'),
                            import('lg-rotate.js')
                        ])
                        if(this.galleryInstance && this.galleryInstance.destroy) {
                            this.galleryInstance.destroy()
                            this.galleryInstance = null
                            this.galleryInitialized = false
                        }
                        this.galleryInstance = lightGallery(lightboxWrap, {
                            selector: ".ch_lght",
                            thumbnail: true,
                            animateThumb: true,
                            rotateLeft: true,
                            rotateRight: true,
                            actualSize: false,
                            flipHorizontal: false,
                            flipVertical: false,
                            fullScreen: this.isMobile ? false : true,
                            showThumbByDefault: this.isMobile ? false : true,
                            download: this.isMobile ? false : true,
                            speed: 300,
                            plugins: [lgThumbnail, lgFullscreen, lgZoom, lgRotate]
                        })
                        this.galleryInitialized = true
                    } catch(e) {
                        console.log('lightgallery init error', e)
                        this.destroyGallery()
                    }
                }, 80)
            })
        },
        destroyGallery() {
            try {
                if(this.galleryInitTimer) {
                    clearTimeout(this.galleryInitTimer)
                    this.galleryInitTimer = null
                }
                if(this.galleryInstance && typeof this.galleryInstance.destroy === 'function') {
                    this.galleryInstance.destroy()
                }
                this.galleryInstance = null
                this.galleryInitialized = false
            } catch(e) {
                console.log(e)
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
            const inst = this.lgWrapInst
            if (inst && inst.destroy) {
                try { inst.destroy(true) } catch(e) {}
                this.lgWrapInst = null
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
            this.lgWrapInst = LG(wrap, {
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
            this.ensureLG(`message_${this.messageItem.message_uid}`)
        },
        attachObservers() {
            const wrap = this.$refs[`message_${this.messageItem.message_uid}`]
            if (wrap && !this.moWrap) {
                this.moWrap = new MutationObserver(() => this.scheduleLGInit())
                this.moWrap.observe(wrap, { childList: true, subtree: true })
            }
            if (!this.lazyHandler) {
                this.lazyHandler = e => {
                    const t = e && e.target
                    if (!t) return
                    const wrap2 = this.$refs[`message_${this.messageItem.message_uid}`]
                    if (wrap2 && wrap2.contains(t)) this.scheduleLGInit()
                }
                document.addEventListener('lazyloaded', this.lazyHandler, true)
            }
        },
        detachObservers() {
            if (this.moWrap) {
                this.moWrap.disconnect()
                this.moWrap = null
            }
            if (this.lazyHandler) {
                document.removeEventListener('lazyloaded', this.lazyHandler, true)
                this.lazyHandler = null
            }
        },
        toggleExpand() {
            this.expand = !this.expand
        }
    },
    mounted() {
        if(this.messageItem.attachments?.length)
            this.galleryInit()
        this.$nextTick(() => {
            this.scheduleLGInit()
            this.attachObservers()
        })
    },
    watch: {
        'messageItem.attachments'(val) {
            this.$nextTick(() => {
                if(val && val.length)
                    this.galleryInit()
                else
                    this.destroyGallery()
            })
        }
    },
    updated() {
        this.scheduleLGInit()
    },
    beforeDestroy() {
        this.destroyGallery()
        this.detachObservers()
        this.destroyLG(`message_${this.messageItem.message_uid}`)
    }
}
</script>

<style lang="scss" scoped>
.u-slide-fade-enter-active {
    transition: all .3s ease;
}
.u-slide-fade-leave-active {
    transition: all .8s cubic-bezier(1.0, 0.5, 0.8, 1.0);
}
.u-slide-fade-enter, .u-slide-fade-leave-to{
    transform: translateX(10px);
    opacity: 0;
}
.reaction-enter-active,
.reaction-leave-active {
    transition: all 0.18s ease
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
.message_reaction{
    &__item{
        background: rgba(0, 0, 0, 0.1);
        padding: 3px 10px;
        border-radius: 10px;
        display: flex;
        align-items: center;
        min-height: 22px;
        cursor: pointer;
        &.active{

        }
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
    }
}
.msg_forwarded{
    .forwarded_wrapper{
        .bubble{
            background: #e8ecfa;
        }
    }
    .bg_primary{
        .forwarded_wrapper{
            .bubble{
                &::v-deep{
                    a{
                        color: var(--blue)!important;
                    }
                }
            }
        }
    }
}
.bubble{
    &.bg_purple{
        border: 1px solid #f1dcff;
        background: linear-gradient(135deg, rgb(249, 239, 255) 46%, rgb(240, 216, 255) 100%);
    }
    &.bg_primary{
        .message_reaction__item{
            &.active{
                background: rgba(255, 255, 255, 0.2);
            }
        }
    }
    &.bg_gray{
        .message_reaction__item{
            &.active{
                background: #e8ecfa;
                color: var(--blue);
            }
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
.message_dots{
    display: flex;
    align-items: flex-end;
    height: 100%;
    padding-bottom: 5px;
    opacity: 0;
    transition: all 0.3s cubic-bezier(0.645, 0.045, 0.355, 1);
    &::v-deep{
        .ant-dropdown-trigger{
            position: sticky;
            bottom: 0;
            z-index: 5;
        }
    }
    &.active{
        opacity: 1;
    }
    &__btn{
        background: #fff;
        width: 25px;
        height: 25px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        cursor: pointer;
    }
}
.message_context,
.message_dots{
    &::v-deep{
        .message_views_submenu{
            > .ant-menu-submenu-title{
                display: flex;
                align-items: center;
                min-height: 40px;
                padding-top: 0;
                padding-bottom: 0;
            }
            .ant-menu-submenu-arrow{
                top: 50%;
                transform: translateY(-50%);
            }
        }
    }
}
.message_views_user{
    max-width: 250px;
    min-width: 0;
    &__name{
        max-width: calc(250px - 26px);
        min-width: 0;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
    }
}
.msg_item{
    &:hover{
        .message_dots{
            opacity: 1;
        }
    }
}
.bubble{
    transition: transform 0.26s ease, opacity 0.26s ease;
    transform-origin: center center;
    will-change: transform, opacity;
    &.bubble--deleting{
        transform: scale(0);
        opacity: 0;
    }
    &.file_exchange_message{
        max-width: 520px;
        width: min(520px, calc(100vw - 92px));
        overflow: visible;
        &.large_message{
            &:not(.show){
                .file-exchange-preview{
                    max-height: none;
                    overflow: visible;
                }
            }
        }
    }
    &.mobile{
        -webkit-user-select: none;
        -khtml-user-select: none;
        -moz-user-select: none;
        -ms-user-select: none;
        user-select: none;
    }
}

.youtube-preview{
    display: block;
    margin-bottom: 10px;
    overflow: hidden;
    border: 1px solid rgba(255, 255, 255, 0.12);
    border-radius: 16px;
    background: #ffffff;
    color: inherit;
    text-decoration: none;
    box-shadow: 0 8px 24px rgba(17, 24, 39, 0.08);
    transition: transform 0.2s ease, box-shadow 0.2s ease;
    &:hover{
        transform: translateY(-1px);
        box-shadow: 0 12px 28px rgba(17, 24, 39, 0.12);
        color: inherit;
    }
    &__thumb{
        position: relative;
        aspect-ratio: 16 / 9;
        background: #111827;
        img{
            width: 100%;
            height: 100%;
            object-fit: cover;
            display: block;
        }
    }
    &__play{
        position: absolute;
        left: 50%;
        top: 50%;
        transform: translate(-50%, -50%);
        width: 56px;
        height: 56px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        background: rgba(255, 0, 0, 0.9);
        color: #fff;
        font-size: 22px;
        box-shadow: 0 8px 20px rgba(0, 0, 0, 0.22);
    }
    &__meta{
        padding: 12px 14px;
    }
    &__title{
        font-weight: 600;
        font-size: 14px;
        line-height: 1.35;
    }
    &__link{
        margin-top: 4px;
        font-size: 12px;
        line-height: 1.35;
        color: #6b7280;
        word-break: break-word;
    }
    &_my{
        border-color: rgba(255, 255, 255, 0.22);
        background: rgba(255, 255, 255, 0.12);
        .youtube-preview__link{
            color: rgba(255, 255, 255, 0.72);
        }
    }
}

.video-preview{
    margin-bottom: 10px;
    overflow: hidden;
    border: 1px solid rgba(255, 255, 255, 0.12);
    border-radius: 16px;
    background: #ffffff;
    box-shadow: 0 8px 24px rgba(17, 24, 39, 0.08);
    &__frame{
        position: relative;
        aspect-ratio: 16 / 9;
        background: #111827;
        iframe{
            display: block;
            width: 100%;
            height: 100%;
        }
    }
    &__link{
        display: block;
        padding: 10px 14px 12px;
        font-size: 12px;
        line-height: 1.35;
        color: #6b7280;
        word-break: break-word;
    }
    &_my{
        border-color: rgba(255, 255, 255, 0.22);
        background: rgba(255, 255, 255, 0.12);
        .video-preview__link{
            color: rgba(255, 255, 255, 0.72);
        }
    }
}

::v-deep(.file_exchange_preview_modal__frame){
    display: block;
    width: 100%;
    height: 100%;
    border: 0;
    background: #fff;
}

::v-deep(.file_exchange_preview_modal_mobile .ant-modal){
    top: 0;
    width: 100% !important;
    max-width: 100%;
    margin: 0;
    padding-bottom: 0;
}

::v-deep(.file_exchange_preview_modal_mobile .ant-modal-content){
    min-height: 100vh;
    border-radius: 0;
}

::v-deep(.file_exchange_preview_modal_mobile .ant-modal-body){
    padding: 0 !important;
}

.title-systemic{
    font-weight: 400;
    color: #888888;
}
</style>
