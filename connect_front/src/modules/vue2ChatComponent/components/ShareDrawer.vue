<template>
    <a-modal
        class="share_select_driwer"
        :class="[showExternalShareActions && 'show_link', isMobile && 'mobile']"
        :width="isMobile ? '100%' : 580"
        :destroyOnClose="true"
        :focusTriggerAfterClose="false"
        :title="useForwarded ? $t('chat.forward') : $t('chat.share')"
        :dialog-style="{ top: isMobile ? '0px' : '20px' }"
        :visible="drawerModalVisible"
        @afterVisibleChange="afterVisibleChange"
        @cancel="close()">
        <div
            v-if="showExternalShareActions"
            class="drawer_share_link" :class="isMobile && 'is_mobile'">
            <div
                v-if="hasShareUrl"
                class="share_btn"
                v-tippy="{ inertia : true, duration : '[600,300]'}"
                :content="$t('chat.copy_link')"
                @click="copyLink()">
                <i class="fi fi-rr-link-alt" />
            </div>
            <div 
                class="share_btn" 
                v-tippy="{ inertia : true, duration : '[600,300]'}" 
                :content="$t('chat.share_email')"
                @click="emailShare()">
                <i class="fi fi-rr-envelope"></i>
            </div>
            <a-popover v-if="!isMobile && hasShareUrl" :getPopupContainer="getPopupContainer">
                <template slot="content">
                    <qr-code :text="shareUrl" style="width: 170px;height: 170px;" />
                </template>
                <div class="share_btn">
                    <i class="fi fi-rr-vector"></i>
                </div>
            </a-popover>
            <div 
                class="share_btn" 
                v-tippy="{ inertia : true, duration : '[600,300]'}" 
                :content="$t('chat.share_telegram')"
                @click="tgShare()">
                <img src="@/assets/images/telegram.svg" />
            </div>
            <div 
                class="share_btn" 
                v-tippy="{ inertia : true, duration : '[600,300]'}" 
                :content="$t('chat.share_whatsapp')"
                @click="wpShare()">
                <img src="@/assets/images/WhatsApp.svg" />
            </div>
        </div>
        <div v-if="drawerModalVisible" class="drawer_body" ref="drawerBody">
            <div class="drawer_scroll infinite-wrapper">
                <div class="drawer_search">
                    <a-input
                        v-model="dialogSearch"
                        allowClear
                        size="large"
                        class="drawer_search_input"
                        :placeholder="$t('chat.search')">
                        <a-icon slot="prefix" type="search" />
                    </a-input>
                </div>
                <div v-if="hasMultipleSelectedTargets" class="drawer_selected">
                    <div class="drawer_selected_list">
                        <button
                            v-for="target in selectedTargetsForView"
                            :key="target.key"
                            type="button"
                            class="drawer_selected_item"
                            @click="removeSelectedTargetItem(target)">
                            <a-avatar
                                :class="target.isPublic && 'drawer_group_avatar'"
                                :size="24"
                                :src="target.avatar || null"
                                :style="target.color ? `backgroundColor:${target.color}!important;color:#fff!important;` : 'backgroundColor: #cccccc'">
                                {{ target.initials }}
                            </a-avatar>
                            <span class="drawer_selected_name" :title="target.name">
                                {{ target.name }}
                            </span>
                            <i class="fi fi-rr-cross-small drawer_selected_remove" />
                        </button>
                    </div>
                </div>
                <div v-if="isSearchMode && filteredDialogList.length" class="drawer_section_title">
                    {{ $t('chat.chats') }}
                </div>
                <ul class="bordered-items">
                    <li 
                        class="flex items-center justify-between py-2 cursor-pointer item truncate"
                        v-for="dialog in filteredDialogList" 
                        :key="dialog.chat_uid">
                        <div class="flex items-center justify-between w-full truncate">
                            <div class="flex items-center mr-2">
                                <a-checkbox 
                                    :ref="'checkbox_'+dialog.chat_uid" 
                                    :id="dialog.chat_uid"
                                    :checked="selectList.includes(dialog.chat_uid)"
                                    @change="changeSelect($event, dialog)"/>
                            </div>
                            <div
                                @click="changeSelectValue(dialog)" 
                                class="flex items-center w-full truncate">
                                <template v-if="dialog.is_public">
                                    <div class="mr-2">
                                        <a-avatar
                                            class="drawer_group_avatar"
                                            :style="dialog.color ? `backgroundColor:${dialog.color}!important;color:#fff!important;` : 'backgroundColor: #cccccc'">
                                            {{ avatarText(dialog) }}
                                        </a-avatar>
                                    </div>
                                    <div class="truncate" :title="dialog.name">
                                        <div class="text-sm flex items-center truncate">
                                            {{dialog.name}}
                                            <a-icon class="ml-1" style="font-size: 11px;" type="team" />
                                        </div>
                                    </div>
                                </template>
                                <template v-else>
                                    <ShareDrawerUser :dialog="dialog" />
                                </template>
                            </div> 
                        </div>
                    </li>
                </ul>
                <template v-if="isSearchMode && showContactSearchSection">
                    <div class="drawer_search_separator">
                        <div class="drawer_search_line" />
                        <div class="drawer_section_title drawer_section_title--contacts">
                            {{ $t('chat.contacts') }}
                        </div>
                    </div>
                    <a-spin
                        v-if="contactSearchLoading"
                        class="drawer_contact_loading"
                        size="small" />
                    <ul v-if="filteredContactList.length" class="bordered-items">
                        <li
                            class="flex items-center justify-between py-2 cursor-pointer item truncate"
                            v-for="contact in filteredContactList"
                            :key="`contact_${contact.id}`">
                            <div class="flex items-center justify-between w-full truncate">
                                <div class="flex items-center mr-2">
                                    <a-checkbox
                                        :checked="isContactSelected(contact.id)"
                                        @change="changeContactSelect($event, contact)" />
                                </div>
                                <div
                                    @click="changeContactSelectValue(contact)"
                                    class="flex items-center w-full truncate">
                                    <div class="mr-2">
                                        <a-avatar
                                            :size="32"
                                            :src="contact.avatar && contact.avatar.path ? contact.avatar.path : null"
                                            :style="contact.color ? `backgroundColor:${contact.color}!important;color:#fff!important;` : 'backgroundColor: #cccccc'">
                                            {{ contactAvatarText(contact) }}
                                        </a-avatar>
                                    </div>
                                    <div class="truncate" :title="contactName(contact)">
                                        <div class="text-sm font-semibold truncate">
                                            {{ contactName(contact) }}
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </li>
                    </ul>
                </template>
                <a-empty
                    v-if="isSearchMode && !contactSearchLoading && !filteredDialogList.length && !filteredContactList.length"
                    class="drawer_search_empty"
                    :description="$t('chat.empty')" />
                <infinite-loading
                    v-if="drawerVisible && infiniteReady && !isSearchMode"
                    :identifier="infiniteIdentifier"
                    @infinite="getDialogkList"
                    :distance="10">
                    <div slot="spinner">
                        <a-spin
                            size="small"
                            style="margin-top: 10px" />
                    </div>
                    <div slot="no-more"></div>
                    <div slot="no-results"></div>
                </infinite-loading>
            </div>
        </div>
        <template #footer>
            <a-button
                @click="handleSendAction()"
                :block="isMobile"
                :size="isMobile ? 'large' : 'default'"
                class="px-6"
                type="primary"
                :loading="createLoader"
                :disabled="!hasSelectedTargets">
                {{ $t('chat.send') }}
            </a-button>
            <a-button
                @click="createChat"
                :class="!isMobile && 'ml-2'"
                :block="isMobile"
                :size="isMobile ? 'large' : 'default'"
                :type="isMobile ? 'ui' : 'link'"
                :ghost="isMobile">
                {{$t('chat.create_chat')}}
            </a-button>
        </template>
        <a-modal
            v-if="!useForwarded"
            class="share_modal"
            :visible="modalVisible"
            :destroyOnClose="true"
            :focusTriggerAfterClose="false"
            @cancel="modalVisible = false">
            <template #title>
                <div v-if="selectedChat" class="flex items-center">
                    <div class="flex items-center truncate">
                        <div class="mr-2">
                            <a-avatar
                                v-if="selectedChat.is_public"
                                class="drawer_group_avatar"
                                :style="selectedChat.color ? `backgroundColor:${selectedChat.color}!important;color:#fff!important;` : 'backgroundColor: #cccccc'">
                                {{ avatarText(selectedChat) }}
                            </a-avatar>
                            <a-avatar
                                v-else-if="selectedChat.recipient && selectedChat.recipient.avatar"
                                :src="selectedChat.recipient.avatar.path" />
                            <a-avatar v-else icon="user" />
                        </div>
                        <div class="truncate">
                            <div class="text-sm font-semibold truncate">
                                {{selectedChat.name}}
                                <template v-if="selectedChat.is_public">
                                    <a-icon class="ml-1" style="font-size: 11px;" type="team" />
                                </template>
                            </div>
                        </div>
                    </div>
                </div>
            </template>
            <div v-if="useForwarded && shareObject" class="share_message mt-2">
                <ChatMessage 
                    :messageItem="shareObject" 
                    shareMessage 
                    :user="user" />
            </div>
            <div v-if="!useForwarded && shareObject">
                <template v-if="shareModel === 'invite_contact_person'">
                    <div class="mb-2 font-semibold">
                        Отправить ссылку на приглашение контактному лицу "{{ shareObject.name }}"
                    </div>
                </template>
                <template v-else>
                    <div class="mb-2 font-semibold">
                        <span v-if="shareModel === 'files.files'">
                            {{$t('chat.give_access_to_files')}}:
                        </span>
                        <span v-else>
                            <span>
                                {{$t('chat.attach')}}
                            </span>
                            <span class="lowercase" v-if="shareModel !== 'workgroups.WorkGroupModel'">
                                {{ shareObject.isSprint ? $t('chat.sprint') : $t(shareModel)}}{{shareObject.name && `: ${shareObject.name}`}}
                            </span>
    
                            <span class="lowercase" v-else>
                                {{shareObject.is_project ? $t('chat.project') : $t('chat.work_group')}}:  {{shareObject.name}}
                            </span>
                        </span>
                    </div>
    
                    <div v-if="shareModel === 'crm.GoodsOrderModel'">
                        <div class="mb-2">
                            {{$t('chat.number')}}: {{ shareObject.counter }}
                        </div>
                        <div v-if="shareObject.contractor" class="mb-2">
                            {{$t('chat.client')}}: {{ shareObject.contractor.name }}
                        </div>
                        <div v-if="shareObject.contract" class="mb-2">
                            {{$t('chat.contract')}}: {{ shareObject.contract.name }}
                        </div>
                        <div v-if="shareObject.execute_status">
                            {{$t('chat.status')}}: {{ shareObject.execute_status.name }}
                        </div>
                    </div>
                    <div v-if="shareModel === 'tasks.TaskModel' && !shareObject.isSprint" class="flex items-center">
                        <a-tag class="ml-1" v-if="shareObject.attachments && shareObject.attachments.length">
                            <a-icon type="paper-clip" />
                            {{shareObject.attachments.length}}
                        </a-tag>
    
                        <template v-else>
                            <a-tag class="m-0">{{$t('chat.no_time_limit')}}</a-tag>
                        </template>
                        <a-tag 
                            v-if="shareObject.status"
                            class="ml-2 mr-0" 
                            :color="shareObject.status.color">
                            {{ shareObject.status.name }}
                        </a-tag>
                    </div>
                    <template v-if="shareModel === 'files.files'">
                        <div class="flex items-center truncate">
                            <div class="mt-2 attached_files">
                                <div 
                                    v-for="(file, index) in [shareObject]" 
                                    :key="index"
                                    class="attached_file">
                                    <a-tooltip :title="`${file.name}.${file.extension}`">
                                        <div class="file_image_wrapper">
                                            <img 
                                                :data-src="file.is_image ? file.path : fileIcon(file)" 
                                                alt=""
                                                class="file_icon lazyload"
                                                :class="file.is_image && 'file_image'">
                                        </div>
                                        <div class="file_name font-light text-center truncate">
                                            {{ file.name }}
                                        </div>
                                    </a-tooltip>
                                </div>
                            </div>
                        </div>
                    </template>
                    <template v-if="shareModel === 'comments'">
                        <component 
                            :is="commentComponent" 
                            :user="user"
                            useShare
                            related_object="share"
                            :item="shareObject" />
                    </template>
                    <div v-if="shareModel === 'meetings.PlannedMeetingModel'">
                        <h3 class="text-base">{{shareObject.name}}</h3>
                        <a-tag class="my-1 mr-1">
                            {{$t('chat.duration')}} {{ shareObject.duration}} {{$t('chat.minutes')}}
                        </a-tag>
                        <div 
                            v-if="shareObject.status === 'online'" 
                            class="online flex items-center">
                            <div class="blob mr-2"></div>
                            {{$t('chat.online')}}
                        </div>
                        <a-tag 
                            v-if="shareObject.status === 'new'"
                            class="ml-1"
                            color="green">
                            {{$t('chat.new')}}
                        </a-tag>
                        <a-tag 
                            v-if="shareObject.status === 'ended'"
                            class="ml-1"
                            color="purple">
                            {{$t('chat.ended')}}
                        </a-tag>
                        <a-tag class="my-1 mr-1">
                            {{$t('chat.participants_count')}} - {{ shareObject.members_count }}
                        </a-tag>
                    </div>
                </template>
            </div>
            <template slot="footer">
                <div class="relative w-full footer_share" ref="footerWrapper">
                    <BalloonEditor 
                        v-model="text"
                        chatEditor 
                        initFocus
                        ref="shareText"
                        class="w-full modal_text"
                        :enterShifthHand="createMessage"
                        :placeholder="$t('chat.enter_your_message')" />
                    <!--<a-textarea
                        
                        name="modalText"
                        ref="shareText"
                        v-model="text"
                        @keydown="inputHandler"
                        :placeholder="$t('chat.enter_your_message')"
                        :auto-size="false" />-->
                    <div class="absolute flex items-center footer_action">
                        <a-dropdown :getPopupContainer="() => $refs.footerWrapper">
                            <a-menu slot="overlay">
                                <a-menu-item 
                                    key="1" 
                                    @click="createMessage(false)"> 
                                    <a-icon type="profile" />{{$t('chat.share_and_stay')}} 
                                </a-menu-item>
                                <a-menu-item 
                                    key="2"
                                    @click="createMessage(true)">
                                    <a-icon type="message" />{{$t('chat.share_and_go_to_chat')}}
                                </a-menu-item>
                            </a-menu>
                            <a-button
                                class="lg:ml-2 send_button"
                                type="primary"
                                :loading="createLoader"
                                flaticon
                                icon="fi-rr-paper-plane-top"
                                @click="createMessage(false)"
                                shape="circle" />
                        </a-dropdown>
                    </div>
                </div>
            </template>
        </a-modal>
    </a-modal>
</template>

<script>
import { filesFormat } from '@/utils'
import {mapState} from 'vuex'
import {statusList} from '@/utils/localeData'
import eventBus from '@/utils/eventBus'
const key = 'shareCreateKey'
export default {
    name: "ChatShareDrawer",
    components: {
        InfiniteLoading: () => import('vue-infinite-loading'),
        ShareDrawerUser: () => import('./ShareDrawerUser.vue'),
        QrCode: () => import('vue-qrcode-component'),
        BalloonEditor: () => import('@apps/CKEditor/BalloonEditor.vue'),
        ChatMessage: () => import('./ChatMessage/index.vue')
    },
    data() {
        return {
            statusList,
            dialogList: [],
            activeDrop: true,
            scrollStatus: true,
            skipNextDialogFetch: false,
            page: 0,
            drawerVisible: false,
            drawerModalVisible: false,
            infiniteReady: false,
            infiniteIdentifier: 0,
            loading: false,
            createLoader: false,
            modalVisible: false,
            selectedChat: null,
            selectList: [],
            selectUserList: [],
            selectedUserMap: {},
            selectedTargetsOrder: [],
            selectedIdList: [],
            text: '',
            showMobileShare: false,
            dialogSearch: '',
            contactSearchList: [],
            contactSearchLoading: false,
            contactSearchRequestId: 0,
            contactSearchTimer: null,
        }
    },
    computed: {
        ...mapState({
            windowWidth: state => state.windowWidth,
            shareModel: state => state.share.shareModel,
            useForwarded: state => state.share.useForwarded,
            messageText: state => state.share.messageText,
            shareId: state => state.share.shareId,
            shareObject: state => state.share.shareObject,
            chatMessage: state => state.chat.chatMessage,
            user: state => state.user.user,
            bodySelector: state => state.share.bodySelector,
            shareUrl: state => state.share.shareUrl,
            shareTitle: state => state.share.shareTitle,
            isMobile: state => state.isMobile,
            chatList: state => state.chat.chatList,
            chatListNext: state => state.chat.chatListNext,
            chatListPage: state => state.chat.chatListPage
        }),
        statusType() {
            const status = this.statusList.find(elem => elem.name === this.shareObject.status)
            if(status)
                return status.color
            else
                return 'blue'
        },
        commentComponent() {
            if(this.shareModel === 'comments')
                return () => import('@apps/vue2CommentsComponent/CommentItem.vue')
            return null
        },
        storeVisible: {
            get() {
                return this.$store.state.share.visible
            },
            set(val) {
                this.$store.commit('share/SET_VISIBLE', val)
            }
        },
        checkFileType() {
            if(this.shareObject.is_image)
                return 'file-image'
            if(this.shareObject.is_doc)
                return 'file-text'
            if(this.shareObject.is_video)
                return 'video-camera'
            if(this.shareObject.is_audio)
                return 'audio'

            return 'file'
        },
        searchQuery() {
            return String(this.dialogSearch || '').trim().toLowerCase()
        },
        hasShareUrl() {
            return Boolean(String(this.shareUrl || '').trim())
        },
        forwardedShareText() {
            if (!this.useForwarded) return ''

            const messageText = String(this.shareObject?.text || '').trim()
            if (messageText) return messageText

            const sharedObjectName = String(this.shareObject?.share?.name || '').trim()
            if (sharedObjectName) return sharedObjectName

            return ''
        },
        forwardedAttachmentLinks() {
            if (!this.useForwarded) return []

            const attachments = Array.isArray(this.shareObject?.attachments) ? this.shareObject.attachments : []
            if (!attachments.length) return []

            const chatUid = this.shareObject?.chat_uid || this.shareObject?.chat || ''
            const messageUid = this.shareObject?.message_uid || ''
            const links = []

            attachments.forEach((file) => {
                const rawPath = String(file?.path || file?.file?.path || '').trim()
                if (!rawPath) return

                const link = this.buildForwardedAttachmentShareLink(rawPath, chatUid, messageUid)
                if (!link) return

                if (!links.includes(link)) {
                    links.push(link)
                }
            })

            return links
        },
        externalShareTitle() {
            return String(this.shareTitle || this.$t('chat.forward') || '').trim()
        },
        externalShareBody() {
            if (this.hasShareUrl) {
                const title = String(this.shareTitle || '').trim()
                if (title) {
                    return `${title} - ${this.shareUrl}`
                }
                return String(this.shareUrl || '')
            }

            const plainMessageText = this.stripHtmlToPlainText(this.forwardedShareText)
            const attachmentLinksText = this.forwardedAttachmentLinks.join('\n')

            if (plainMessageText && attachmentLinksText) {
                return `${plainMessageText}\n\n${attachmentLinksText}`
            }

            return plainMessageText || attachmentLinksText
        },
        showExternalShareActions() {
            if (this.hasShareUrl) return true
            return Boolean(this.externalShareBody)
        },
        isSearchMode() {
            return this.searchQuery.length > 0
        },
        hasSelectedTargets() {
            return this.selectList.length > 0 || this.selectUserList.length > 0
        },
        selectedTargetsForView() {
            return this.selectedTargetsOrder
                .map((target) => {
                    if (target.type === 'chat') {
                        const dialog = this.findDialogByUid(target.id)
                        if (!dialog) return null

                        return {
                            key: `chat_${target.id}`,
                            type: 'chat',
                            id: String(target.id),
                            name: String(dialog?.name || ''),
                            isPublic: !!dialog?.is_public,
                            avatar: dialog?.recipient?.avatar?.path || null,
                            color: dialog?.color || null,
                            initials: this.avatarText(dialog)
                        }
                    }

                    const contact = this.selectedUserMap[target.id] || this.contactSearchList.find(item => String(item?.id || '') === String(target.id))
                    if (!contact) return null

                    return {
                        key: `user_${target.id}`,
                        type: 'user',
                        id: String(target.id),
                        name: this.contactName(contact),
                        avatar: contact?.avatar?.path || null,
                        color: contact?.color || null,
                        initials: this.contactAvatarText(contact)
                    }
                })
                .filter(Boolean)
        },
        selectedTargetsCount() {
            return this.selectedTargetsForView.length
        },
        hasMultipleSelectedTargets() {
            return this.selectedTargetsCount >= 2
        },
        filteredDialogList() {
            if (!this.isSearchMode) {
                return this.dialogList
            }

            const selectedChatIds = new Set(this.selectList.map(item => String(item)))

            return this.dialogList.filter((dialog) => {
                const chatUid = String(dialog?.chat_uid || '')
                if (!chatUid) return false

                if (selectedChatIds.has(chatUid)) {
                    return true
                }

                const name = String(dialog?.name || '').toLowerCase()
                return name.includes(this.searchQuery)
            })
        },
        filteredContactList() {
            if (!this.isSearchMode) {
                return []
            }

            const selectedContactIds = new Set(this.selectUserList.map(item => String(item)))
            const existingPrivateChatUsers = new Set(
                this.dialogList
                    .filter(dialog => !dialog?.is_public && dialog?.recipient?.id)
                    .map(dialog => String(dialog.recipient.id))
            )

            const contactMap = new Map()

            this.contactSearchList.forEach((contact) => {
                const contactId = String(contact?.id || '')
                if (!contactId || contactMap.has(contactId)) return
                contactMap.set(contactId, contact)
            })

            Object.keys(this.selectedUserMap || {}).forEach((id) => {
                const contactId = String(id || '')
                if (!contactId || contactMap.has(contactId)) return
                const selectedContact = this.selectedUserMap[contactId]
                if (selectedContact) {
                    contactMap.set(contactId, selectedContact)
                }
            })

            return Array.from(contactMap.values()).filter((contact) => {
                const contactId = String(contact?.id || '')
                if (!contactId) return false
                if (String(this.user?.id || '') === contactId) return false

                const isSelected = selectedContactIds.has(contactId)
                if (!isSelected && existingPrivateChatUsers.has(contactId)) {
                    return false
                }

                if (isSelected) {
                    return true
                }

                const contactName = this.contactName(contact).toLowerCase()
                return contactName.includes(this.searchQuery)
            })
        },
        showContactSearchSection() {
            return this.contactSearchLoading || this.filteredContactList.length > 0
        }
    },
    watch: {
        modalVisible(val) {
            if(!val)
                this.text = ''
            else {
                this.$nextTick(() => {
                    if (this.messageText) {
                        this.text = this.messageText
                    }

                    requestAnimationFrame(() => {
                        const editorElement = this.$refs.shareText?.$el?.querySelector?.('[contenteditable="true"], textarea, input')

                        if (editorElement && typeof editorElement.focus === 'function') {
                            editorElement.focus()
                        }
                    })
                })
            }
        },
        storeVisible(val) {
            if(!val) {
                this.drawerModalVisible = false
                this.clear()
            } else {
                this.openDrawerModal()
            }
        },
        searchQuery(val) {
            this.handleSearchQueryChange(val)
        }
    },
    mounted(){
        if (this.storeVisible) {
            this.openDrawerModal()
        }

        this.$nextTick(() => {
            this.drawerVisible = true
        })
        eventBus.$on("update_list_share_drawer", ()=>{
            if(this.storeVisible){ 
                this.initializeDialogList(true)
                this.getDialogkList()
            }
        })

        if(this.isMobile && navigator.share) {
            this.showMobileShare = true
        }
    },
    beforeDestroy() {
        if (this.contactSearchTimer) {
            clearTimeout(this.contactSearchTimer)
            this.contactSearchTimer = null
        }
    },
    
    methods: {
        openDrawerModal() {
            this.blurActiveElement()
            requestAnimationFrame(() => {
                this.dialogSearch = ''
                this.resetContactSearch()
                this.initializeDialogList()
                this.infiniteReady = false
                this.drawerModalVisible = true
            })
        },
        handleSearchQueryChange(query) {
            if (this.contactSearchTimer) {
                clearTimeout(this.contactSearchTimer)
                this.contactSearchTimer = null
            }

            if (!query || query.length < 2) {
                this.resetContactSearch()
                return
            }

            this.contactSearchTimer = setTimeout(() => {
                this.fetchContactsBySearch(query)
            }, 300)
        },
        resetContactSearch() {
            this.contactSearchRequestId += 1
            this.contactSearchLoading = false
            this.contactSearchList = []
        },
        async fetchContactsBySearch(query) {
            const requestId = ++this.contactSearchRequestId
            this.contactSearchLoading = true

            try {
                const { data } = await this.$http.get('/chat/users/', {
                    params: {
                        page: 1,
                        page_size: 20,
                        all: false,
                        search: query
                    }
                })

                if (requestId !== this.contactSearchRequestId) return

                const uniqueById = new Map()
                const results = Array.isArray(data?.results) ? data.results : []
                results.forEach((item) => {
                    const itemId = String(item?.id || '')
                    if (!itemId || uniqueById.has(itemId)) return
                    uniqueById.set(itemId, item)
                })

                this.contactSearchList = Array.from(uniqueById.values())
            } catch (e) {
                if (requestId !== this.contactSearchRequestId) return
                this.contactSearchList = []
            } finally {
                if (requestId === this.contactSearchRequestId) {
                    this.contactSearchLoading = false
                }
            }
        },
        blurActiveElement() {
            const activeElement = document.activeElement

            if (activeElement && typeof activeElement.blur === 'function') {
                activeElement.blur()
            }
        },
        findDialogByUid(chatUid) {
            const uid = String(chatUid || '')
            if (!uid) return null

            const fromDialogList = this.dialogList.find(item => String(item?.chat_uid || '') === uid)
            if (fromDialogList) return fromDialogList

            return this.chatList.find(item => String(item?.chat_uid || '') === uid) || null
        },
        addSelectedTarget(type, id) {
            const targetId = String(id || '')
            if (!targetId) return

            const exists = this.selectedTargetsOrder.some(item => item.type === type && String(item.id) === targetId)
            if (!exists) {
                this.selectedTargetsOrder.push({ type, id: targetId })
            }
        },
        removeSelectedTarget(type, id) {
            const targetId = String(id || '')
            this.selectedTargetsOrder = this.selectedTargetsOrder.filter(item => !(item.type === type && String(item.id) === targetId))
        },
        rememberSelectedContact(contact) {
            const contactId = String(contact?.id || '')
            if (!contactId) return

            this.$set(this.selectedUserMap, contactId, { ...contact, id: contactId })
        },
        removeChatSelection(chatUid) {
            const uid = String(chatUid || '')
            if (!uid) return

            this.selectList = this.selectList.filter(item => String(item) !== uid)

            const dialog = this.findDialogByUid(uid)
            if (dialog?.id) {
                this.selectedIdList = this.selectedIdList.filter(item => String(item) !== String(dialog.id))
            }

            this.removeSelectedTarget('chat', uid)
        },
        removeUserSelection(userId) {
            const uid = String(userId || '')
            if (!uid) return

            this.selectUserList = this.selectUserList.filter(item => String(item) !== uid)
            if (this.selectedUserMap[uid]) {
                this.$delete(this.selectedUserMap, uid)
            }

            this.removeSelectedTarget('user', uid)
        },
        removeSelectedTargetItem(target) {
            if (target?.type === 'chat') {
                this.removeChatSelection(target.id)
                return
            }

            this.removeUserSelection(target.id)
        },
        contactName(contact) {
            return String(contact?.full_name || contact?.name || '')
        },
        contactAvatarText(contact) {
            const name = this.contactName(contact)
            if (!name) return ''

            const chunks = name.split(' ').filter(Boolean)
            if (!chunks.length) return ''

            return chunks
                .slice(0, 3)
                .map(item => item.charAt(0).toUpperCase())
                .join('')
        },
        isContactSelected(contactId) {
            return this.selectUserList.includes(String(contactId))
        },
        avatarText(dialog) {
            if(dialog) {
                if(dialog.is_public) {
                    return dialog.name.charAt(0).toUpperCase()
                } else {
                    const n = dialog.name.split(' ')
                    return `${n[0].charAt(0).toUpperCase()}${n[1] ? n[1].charAt(0).toUpperCase() : ''}${n[2] ? n[2].charAt(0).toUpperCase() : ''}`
                }
            }
            return ''
        },
        mobileShare() {
            const shareData = {
                text: this.externalShareBody
            }
            if (this.hasShareUrl) {
                shareData.url = this.shareUrl
            }

            navigator.share(shareData)
                .then(() => console.log('Share success'))
                .catch((error) => console.log('Error sharing', error))
        },
        openExternalWindow(url) {
            const popup = window.open(url, '_blank')
            if (popup && typeof popup.focus === 'function') {
                popup.focus()
            }
        },
        stripHtmlToPlainText(htmlText) {
            if (!htmlText) return ''

            const normalizedHtml = String(htmlText)
                .replace(/<br\s*\/?>/gi, '\n')
                .replace(/<\/(p|div|li|h1|h2|h3|h4|h5|h6)>/gi, '\n')

            const container = document.createElement('div')
            container.innerHTML = normalizedHtml

            return String(container.textContent || container.innerText || '')
                .replace(/\u00A0/g, ' ')
                .replace(/[ \t]+\n/g, '\n')
                .replace(/\n{3,}/g, '\n\n')
                .replace(/[ \t]{2,}/g, ' ')
                .trim()
        },
        toAbsoluteShareUrl(filePath) {
            const value = String(filePath || '').trim()
            if (!value) return ''

            if (typeof window === 'undefined') {
                return value
            }

            try {
                return new URL(value, window.location.origin).toString()
            } catch (e) {
                return value
            }
        },
        buildForwardedAttachmentShareLink(filePath, chatUid, messageUid) {
            let nextPath = String(filePath || '').trim()
            if (!nextPath) return ''

            const hasChatAttachmentMarker = nextPath.includes('chat_attachments')
            const hasQueryMeta = /chat_uid=|%26chat_uid%3D/i.test(nextPath)

            if (!hasChatAttachmentMarker && chatUid && messageUid && !hasQueryMeta) {
                nextPath += encodeURIComponent(`&chat_uid=${chatUid}&message_uid=${messageUid}&target=chat_attachments`)
            }

            return this.toAbsoluteShareUrl(nextPath)
        },
        emailShare() {
            if (!this.externalShareBody) return

            this.openExternalWindow(`mailto:?subject=${encodeURIComponent(this.externalShareTitle)}&body=${encodeURIComponent(this.externalShareBody)}`)
        },
        wpShare() {
            if (!this.externalShareBody) return

            this.openExternalWindow(`https://wa.me/?text=${encodeURIComponent(this.externalShareBody)}`)
        },
        tgShare() {
            if (!this.externalShareBody) return

            const shareUrl = this.hasShareUrl
                ? this.shareUrl
                : (typeof window !== 'undefined' ? window.location.origin : '')
            const shareText = this.hasShareUrl
                ? this.externalShareTitle
                : this.externalShareBody

            this.openExternalWindow(`https://t.me/share/url?url=${encodeURIComponent(shareUrl)}&text=${encodeURIComponent(shareText)}`)
        },
        vbShare() {
            if (!this.externalShareBody) return

            this.openExternalWindow(`viber://forward?text=${encodeURIComponent(this.externalShareBody)}`)
        },
        copyLink() {
            if (!this.hasShareUrl) return

            try {
                navigator.clipboard.writeText(this.shareUrl)
                this.$message.success(this.$t('chat.linkCopied'))
            } catch(e) {
                this.$message.error('Ошибка копирования ссылки')
                console.log(e)
            }
        },
        getPopupContainer() {
            return this.$refs.drawerBody
        },
        openShareConfirmModal() {
            this.blurActiveElement()
            this.modalVisible = true
        },
        handleSendAction() {
            if (this.useForwarded) {
                this.createMessage(false)
                return
            }

            this.openShareConfirmModal()
        },
        initializeDialogList(forceReset = false) {
            const hasCachedChatList = Array.isArray(this.chatList) && this.chatList.length > 0

            if (forceReset) {
                this.dialogList = []
                this.page = 0
                this.scrollStatus = true
                this.skipNextDialogFetch = false
            }

            if (!hasCachedChatList) {
                return
            }

            this.dialogList = this.chatList.slice()
            this.page = this.chatListPage || 0
            this.scrollStatus = Boolean(this.chatListNext)
            this.skipNextDialogFetch = this.page > 0
        },
        afterVisibleChange(val) {
            if(val) {
                this.$nextTick(() => {
                    this.infiniteIdentifier += 1
                    this.infiniteReady = true
                    this.drawerVisible = true
                })
            } else {
                this.drawerVisible = false
                this.infiniteReady = false
            }
        },
        changeSelectValue(dialog){
            if (this.useForwarded) {
                this.selectedChat = dialog
                const isSelected = this.selectList.includes(dialog.chat_uid)
                if (isSelected) {
                    this.removeChatSelection(dialog.chat_uid)
                } else {
                    this.selectList.push(dialog.chat_uid)
                    this.addSelectedTarget('chat', dialog.chat_uid)
                    if (dialog?.id && !this.selectedIdList.includes(dialog.id)) {
                        this.selectedIdList.push(dialog.id)
                    }
                }
                return
            }

            if (!this.selectList.includes(dialog.chat_uid)) {
                this.selectList.push(dialog.chat_uid)
            }
            this.addSelectedTarget('chat', dialog.chat_uid)
            this.selectedChat = dialog

            if (dialog?.id && !this.selectedIdList.includes(dialog.id)) {
                this.selectedIdList.push(dialog.id)
            }
            

            if(this.$refs.sharingOldSelector)
                this.$refs.sharingOldSelector.saveSelect(dialog)
            this.openShareConfirmModal()
        },
        changeSelect(val, dialog){
            let value = val.target.checked
            if(value){
                if (!this.selectList.includes(val.target.id)) {
                    this.selectList.push(val.target.id)
                }
                this.addSelectedTarget('chat', val.target.id)

                if (dialog?.id && !this.selectedIdList.includes(dialog.id)) {
                    this.selectedIdList.push(dialog.id)
                }
            } else {
                this.selectList = this.selectList.filter(el=> el !== val.target.id)
                this.selectedIdList = this.selectedIdList.filter(el=> el !== dialog.id)
                this.removeSelectedTarget('chat', val.target.id)
            }

            if(this.dialogList.length) {
                const find = this.dialogList.find(f => f.chat_uid === val.target.id)
                if(find && this.$refs.sharingOldSelector)
                    this.$refs.sharingOldSelector.saveSelect(find)
            }
        },
        changeContactSelectValue(contact) {
            const contactId = String(contact?.id || '')
            if (!contactId) return

            if (this.useForwarded) {
                this.selectedChat = {
                    name: this.contactName(contact),
                    recipient: contact,
                    is_public: false
                }
                const isSelected = this.selectUserList.includes(contactId)
                if (isSelected) {
                    this.removeUserSelection(contactId)
                } else {
                    this.selectUserList.push(contactId)
                    this.rememberSelectedContact(contact)
                    this.addSelectedTarget('user', contactId)
                }
                return
            }

            if (!this.selectUserList.includes(contactId)) {
                this.selectUserList.push(contactId)
            }
            this.rememberSelectedContact(contact)
            this.addSelectedTarget('user', contactId)

            this.selectedChat = {
                name: this.contactName(contact),
                recipient: contact,
                is_public: false
            }

            this.openShareConfirmModal()
        },
        changeContactSelect(val, contact) {
            const checked = !!val?.target?.checked
            const contactId = String(contact?.id || '')
            if (!contactId) return

            if (checked) {
                if (!this.selectUserList.includes(contactId)) {
                    this.selectUserList.push(contactId)
                }
                this.rememberSelectedContact(contact)
                this.addSelectedTarget('user', contactId)
            } else {
                this.removeUserSelection(contactId)
            }
        },
        createPrivateChat(userId) {
            this.$socket.client.emit("create", {
                is_public: false,
                members: [
                    { user: userId }
                ]
            })
        },
        sleep(ms = 200) {
            return new Promise(resolve => setTimeout(resolve, ms))
        },
        async waitPrivateChat(userId, maxAttempts = 25) {
            for (let attempt = 0; attempt < maxAttempts; attempt += 1) {
                await this.sleep(220)
                const chat = await this.$store.dispatch('chat/getPrivateChat', userId)
                if (chat?.chat_uid) {
                    return chat.chat_uid
                }
            }
            return null
        },
        async resolveUserTargetChat(userId) {
            const existingChat = await this.$store.dispatch('chat/getPrivateChat', userId)
            if (existingChat?.chat_uid) {
                return existingChat.chat_uid
            }

            this.createPrivateChat(userId)
            return this.waitPrivateChat(userId)
        },
        async resolveSelectedTargetsToChats() {
            const targetChatIds = Array.from(new Set(this.selectList))
            const userIds = Array.from(new Set(this.selectUserList))

            for (const userId of userIds) {
                const chatUid = await this.resolveUserTargetChat(userId)
                if (chatUid && !targetChatIds.includes(chatUid)) {
                    targetChatIds.push(chatUid)
                }
            }

            return targetChatIds
        },
        createChat(){
            this.$store.commit('chat/TOGGLE_CREATE_CHAT', true)
        },
        async createMessage(value) {
            try {
                this.createLoader = true
                const targetChatIds = await this.resolveSelectedTargetsToChats()
                if (!targetChatIds.length) {
                    this.$message.warning(this.$t('chat.empty'))
                    return
                }

                targetChatIds.forEach(el => {
                    const queryParams = this.createMessageParams(el)
                    this.$socket.client.emit("message", queryParams)
                    // this.$store.commit('chat/ADD_MESSAGE_BY_ID', {chat_uid: this.selectList[0], value: queryParams})
                });

                if(this.shareModel === 'tasks.TaskModel')
                    this.$message.success(this.$t('chat.task_sent'))
                if(this.shareModel === 'files.files') {
                    this.$message.success(this.$t('chat.file_sent'))
                    targetChatIds.forEach(chatId => {
                        this.$store.commit('files/CLEAR_ALL', chatId)
                    })

                }
                if(this.shareModel === 'comments')
                    this.$message.success(this.$t('chat.comments_sent'))

                if(value){ 
                    this.createLoader = true
                    setTimeout(async() => {
                        const firstTargetChatId = targetChatIds[0]
                        if(this.isMobile) {
                            if(this.$route.name === 'chat-body') {
                                if(this.$route.params?.id !== firstTargetChatId) {
                                    this.$router.replace({
                                        params: {
                                            id: firstTargetChatId
                                        }
                                    })
                                    try {
                                        this.$message.loading({ content: `${this.$t('chat.loading')}...`, key })
                                        await this.$store.dispatch('chat/getCurrentChat', firstTargetChatId)
                                    } finally {
                                        this.$message.destroy()
                                    }
                                    const find = this.dialogList.find(f => f.chat_uid === firstTargetChatId)
                                    if(find) {
                                        if(!find.is_public)
                                            this.$socket.client.emit('chat_status_user', {chat_uid: find.chat_uid, user_uid: find.recipient.id})
                                    }
                                }                           
                            } else {
                                this.$router.push({
                                    name: 'chat-body',
                                    params: {
                                        id: firstTargetChatId
                                    }
                                })
                            }
                        } else {
                            if(this.$route.name !=='chat' && this.$route.query.chat_id !== firstTargetChatId)
                                this.$router.push({name: 'chat', query: {chat_id: firstTargetChatId}})  
                            if(this.$route.name ==='chat' && this.$route.query.chat_id !== firstTargetChatId) {
                                try {
                                    this.$message.loading({ content: `${this.$t('chat.loading')}...`, key })
                                    await this.$store.dispatch('chat/getCurrentChat', firstTargetChatId)
                                } finally {
                                    this.$message.destroy()
                                }
                                const find = this.dialogList.find(f => f.chat_uid === firstTargetChatId)
                                if(find) {
                                    if(!find.is_public)
                                        this.$socket.client.emit('chat_status_user', {chat_uid: find.chat_uid, user_uid: find.recipient.id})
                                }
                                this.$router.replace({query: {chat_id: firstTargetChatId}})  
                            }
                        }
                        this.createLoader = false
                        this.close()
                    }, 10);
                } else {
                    this.close()
                }
            } catch(e) {
                console.log(e)
                // this.$message.error(this.$t('error') + e)
            } finally {
                this.createLoader = false
            }
        },
        createMessageParams(chat) {
            const messageParams = {
                text: this.text,
                chat: chat                    
            }
            let shareParams = {}

            if(this.useForwarded) {
                messageParams.message_forwarded = this.shareObject
                messageParams.forwarded = true
                messageParams.is_deleted = false
                messageParams.is_ai_message = false
                messageParams.is_pinned = false
                messageParams.is_system = false
                messageParams.is_updated = false
                messageParams.mentions = []
                messageParams.message_author = {...this.user}
                messageParams.message_reply = null
                messageParams.share = null
                messageParams.attachments = []
            } else {
                shareParams = {
                    share_id: this.shareId,
                    ...this.shareObject,
                    type: this.shareModel
                }

                const isFile = this.shareModel === 'files.files'
                if(isFile) {
                    messageParams.attachments = [shareParams]
                } else {
                    messageParams.share = shareParams
                }
            }

            return messageParams
        },
        clear() {
            this.drawerVisible = false
            this.infiniteReady = false
            this.dialogSearch = ''
            this.resetContactSearch()
            this.text = ''
            this.selectedChat = null
            this.dialogList = []
            this.scrollStatus = true
            this.skipNextDialogFetch = false
            this.page = 0
            this.selectList = []
            this.selectUserList = []
            this.selectedUserMap = {}
            this.selectedTargetsOrder = []
            this.$store.commit('share/CLEAR_PARAMS')
        },
        selectDialog(dialog) {
            this.selectedChat = dialog
            this.openShareConfirmModal()
        },
        close() {
            this.blurActiveElement()
            this.modalVisible = false
            this.drawerModalVisible = false
            this.storeVisible = false
            this.selectList = []
            this.selectUserList = []
            this.selectedUserMap = {}
            this.selectedTargetsOrder = []
            this.selectedIdList.splice(0)
            if (this.contactSearchTimer) {
                clearTimeout(this.contactSearchTimer)
                this.contactSearchTimer = null
            }
        },
        async getDialogkList($state = null) {
            if (this.loading) return

            if (!this.dialogList.length) {
                this.initializeDialogList()
            }

            if (this.skipNextDialogFetch) {
                this.skipNextDialogFetch = false
                if ($state) $state.loaded()
                return
            }

            if (!this.scrollStatus) {
                if ($state) $state.complete()
                return
            }

            try {
                this.loading = true
                const nextPage = this.page + 1

                const params = {
                    page_size: 20,
                    page: nextPage,
                    display: 'short'
                }

                const { data } = await this.$http.get('/chat/list/', { params })

                if (data?.results?.length) {
                    this.page = nextPage
                    const nextResults = data.results.filter(item => !this.dialogList.some(dialog => dialog.chat_uid === item.chat_uid))
                    this.dialogList = this.dialogList.concat(nextResults)
                }

                if (!data?.next) {
                    this.scrollStatus = false
                    if ($state) $state.complete()
                } else {
                    if ($state) $state.loaded()
                }
            } catch (e) {
                this.scrollStatus = false
                if ($state) $state.complete()
            } finally {
                this.loading = false
            }
        },
        fileIcon(file) {
            // if(this.isFolder)
            //     return require(`@/assets/images/files/folder.svg`)

            const extension = filesFormat.find(format => format === file.extension)
            if(extension)
                return require(`@/assets/images/files/${extension}.svg`)
            else
                return require(`@/assets/images/files/file.svg`)
        },
    }
}
</script>

<style lang="scss">
.footer_share{
    textarea{
        resize: none;
    }
    .footer_action{
        right: 15px;
        top: 50%;
        margin-top: -16px;
    }
    .send_chat_btn{
        &.ant-btn-loading{
            img{
                display: none;
            }
        }
    }
    
}
.ant-dropdown{
        z-index: 99999;
}
.send_button{
                display: flex;
                align-items: center;
                justify-content: center;
                .feather{
                    margin-top: 2px;
                    margin-right: 2px;
                }
            }
.share_select_driwer{
    .ant-modal{
        max-width: calc(100vw - 24px);
        padding-bottom: 0;
    }
    .ant-modal-content{
        display: flex;
        flex-direction: column;
        max-height: calc(100vh - 40px);
    }
    .ant-modal-body{
        display: flex;
        flex: 1 1 auto;
        flex-direction: column;
        min-height: 0;
        overflow: hidden;
    }
    .drawer_search{
        position: sticky;
        top: 0;
        z-index: 2;
        background: #fff;
        padding: 8px 0;
    }
    .drawer_search_input{
        width: 100%;
    }
    .drawer_selected{
        padding-top: 8px;
        padding-bottom: 8px;
    }
    .drawer_selected_list{
        display: flex;
        flex-wrap: wrap;
        gap: 5px;
    }
    .drawer_selected_item{
        border: 1px solid var(--border2);
        border-radius: 999px;
        background: #fff;
        display: inline-flex;
        align-items: center;
        max-width: 100%;
        gap: 6px;
        padding: 2px 8px 2px 2px;
        cursor: pointer;
    }
    .drawer_group_avatar{
        border-radius: 12px;
    }
    .drawer_selected_name{
        max-width: 190px;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
        font-size: 12px;
        line-height: 1.2;
        color: var(--textColor);
    }
    .drawer_selected_remove{
        font-size: 12px;
        color: var(--gray);
        line-height: 1;
    }
    .drawer_search_empty{
        margin-top: 14px;
    }
    .drawer_section_title{
        padding-top: 10px;
        padding-bottom: 6px;
        font-size: 12px;
        font-weight: 600;
        color: var(--gray);
    }
    .drawer_search_separator{
        margin-top: 6px;
    }
    .drawer_search_line{
        width: 100%;
        height: 1px;
        background: var(--border2);
    }
    .drawer_section_title--contacts{
        padding-top: 8px;
        padding-bottom: 6px;
    }
    .drawer_contact_loading{
        display: block;
        margin: 6px auto 8px;
    }
    .drawer_body{
        display: flex;
        flex-direction: column;
        flex: 1 1 auto;
        min-height: 0;
    }
    .drawer_scroll{
        flex: 1 1 auto;
        min-height: 0;
        overflow-y: auto;
        overflow-x: hidden;
        -webkit-overflow-scrolling: touch;
    }
    .ant-drawer-content,
    .ant-drawer-wrapper-body{
        overflow: hidden;
    }
    &.show_link{
        .drawer_share_link{
            height: 50px;
            padding: 5px 0px;
            display: flex;
            flex: 0 0 auto;
            align-items: center;
            .share_btn{
                cursor: pointer;
                width: 35px;
                height: 35px;
                display: flex;
                align-items: center;
                justify-content: center;
                background: #eff2f5;
                border-radius: 50%;
                img{
                    max-width: 18px;
                    height: auto;
                }
                &:not(:last-child){
                    margin-right: 8px;
                }
            }
        }
        .drawer_body{
            display: flex;
            flex-direction: column;
            flex: 1 1 auto;
            min-height: 0;
        }
    }
    &:not(.show_link) {
        .drawer_body{
            display: flex;
            flex-direction: column;
            flex: 1 1 auto;
            min-height: 0;
        }
    }
    .ant-drawer-body{
        padding: 0px;
        height: calc(100% - 40px);
        .drawer_footer{
            padding: 0 15px;
            display: flex;
            align-items: center;
            border-top: 1px solid var(--border2);
            height: 40px;
        }
    }
    &.mobile{
        .ant-modal{
            max-width: 100vw;
            margin: 0;
        }
        .ant-modal-content{
            max-height: 100vh;
            border-radius: 0;
        }
        .ant-drawer-content-wrapper{
            height: 100%!important;
        }
        &.show_link{
            .drawer_body{
                flex: 1 1 auto;
                min-height: 0;
            }
        }
        &:not(.show_link) {
            .drawer_body{
                flex: 1 1 auto;
                min-height: 0;
            }
        }
        .drawer_share_link{
            border-bottom: 0px;
            border-top: 1px solid var(--border2);
            &.is_mobile{
                border-top: 0px;
            }
        }
        .drawer_footer{
            height: 10px;
            display: block;
            padding-top: 5px;
            padding-bottom: 5px;
            border-top: 0px;
            .ant-btn{
                &:last-child{
                    margin-top: 5px;
                }
            }
        }
    }
}
</style>


<style scoped lang="scss">
.share_message{
    &::v-deep{
        .bubble{
            padding: 10px 15px;
            border-radius: var(--borderRadius2);
            overflow: hidden;
            border-radius: 10px;
            max-width: 500px;
            opacity: 1;
            box-shadow: 0 2px 2px rgba(0, 0, 0, 0.02);
            background: #e7edfc;
            .reply_message{
                border-left: 5px solid;
                border-radius: 5px 5px;
                padding-left: 5px;
                background: rgba(0, 0, 0, 0.1);
                border-color: var(--blue);
            }
        }
    }
}
.modal_text{
    border: 1px solid var(--borderColor)!important;
    box-shadow: initial!important;
    @media (min-width: 768px) {
        padding-right: 60px!important;
    }
    &.ck-focused{
        border-color: var(--blue)!important;
    }
}
    .attached_file {
        position: relative;

        border: 1px solid #d9d9d9;
        border-radius: 4px;
        .file_image_wrapper {
            display: flex;
            align-items: center;
            justify-content: center;
    
            height: 70px;
            
            padding: 8px;
            .file_icon {
                width: 100%;
                max-height: 100%;
                
                object-fit: contain;
            }
            .file_image {
                border: 1px solid var(--borderColor);
                border-radius: 4px;
            }
        }
        .file_name {
            margin-top: 4px;
            padding: 0 8px;

            line-height: 1.1;
        }
    }
</style>
