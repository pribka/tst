<template>
    <div>
        <CardLoading v-if="loading && page === 1" class="mt-3" />
        <div
            v-else
            class="grouped_noty_list mt-1"
            :class="{ mobile: isMobile }">
            <transition-group tag="div" name="noty-read-remove">
                <div
                    v-for="item in list"
                    :key="getGroupKey(item)"
                    class="grouped_noty_item"
                    :class="{ unread: !item.is_read, has_timeline: canLoadGroup(item) && isExpanded(item), expanded: isExpanded(item) }">
                <div class="grouped_noty_head">
                    <div class="grouped_noty_mark">
                        <a-avatar
                            class="noty_avatar"
                            :style="`color: ${getColor(item.color)};backgroundColor: ${getBackground(item.color)}`"
                            :icon="getAvatarIcon(item.icon)"
                            :size="30">
                            <i v-if="getIconClass(item.icon)" :class="getIconClass(item.icon)" />
                        </a-avatar>
                    </div>
                    <div class="grouped_noty_content">
                        <div class="grouped_noty_title">
                            <div class="grouped_noty_title_main">
                                <span>{{ getNotificationTitle(item) }}</span>
                                <a-badge
                                    v-if="getHeaderUnreadCount(item)"
                                    :count="getHeaderUnreadCount(item)"
                                    class="grouped_noty_badge"
                                    :class="{ appear_from_left: shouldAnimateBadge(item) }" />
                            </div>
                            <a-button
                                v-if="isMobile && isExpanded(item) && canReadGroup(item)"
                                shape="circle"
                                icon="fi-rr-check-double"
                                flaticon
                                class="grouped_noty_mobile_read_btn grouped_noty_group_title_btn flex items-center justify-center text-xs"
                                @click="readGroup(item)" />
                            <a-checkbox
                                v-else-if="!isMobile && isExpanded(item) && canReadGroup(item)"
                                class="whitespace-nowrap grouped_noty_group_title_checkbox"
                                @change="readGroup(item)">
                                {{ $t('noty.readGroup') }}
                            </a-checkbox>
                        </div>
                        <div class="grouped_noty_body" :class="{ has_timeline: canLoadGroup(item) && isExpanded(item), expanded: isExpanded(item) }">
                            <div v-if="!isExpanded(item)" class="grouped_noty_message">
                                <div class="grouped_noty_single_content">
                                    <div class="grouped_noty_message_meta">
                                        <span class="grouped_noty_message_date">{{ formatDate(item.created_at) }}</span>
                                        <a-badge
                                            v-if="canReadVisibleGroupItem(item) && isMobile"
                                            status="error"
                                            class="grouped_noty_mobile_unread_dot" />
                                        <a-tag v-if="canReadVisibleGroupItem(item) && !isMobile" color="red">
                                            {{ $t('noty.unread') }}
                                        </a-tag>
                                    </div>
                                    <Messsage :item="item" @read="readNoty(item)" />
                                </div>
                                <div v-if="canReadGroup(item)" class="grouped_noty_single_read">
                                    <a-button
                                        v-if="isMobile"
                                        shape="circle"
                                        :icon="canLoadGroup(item) ? 'fi-rr-check-double' : 'fi-rr-check'"
                                        flaticon
                                        class="grouped_noty_mobile_read_btn flex items-center justify-center text-xs"
                                        @click="canLoadGroup(item) ? readGroup(item) : readNoty(item)" />
                                    <a-checkbox
                                        v-else
                                        class="whitespace-nowrap"
                                        @change="canLoadGroup(item) ? readGroup(item) : readNoty(item)">
                                        {{ canLoadGroup(item) ? $t('noty.readGroup') : $t('noty.read') }}
                                    </a-checkbox>
                                </div>
                            </div>
                            <transition
                                name="group-expand"
                                @enter="onExpandEnter"
                                @after-enter="onExpandAfterEnter"
                                @leave="onExpandLeave">
                                <transition-group
                                    v-if="isExpanded(item)"
                                    tag="div"
                                    name="noty-read-remove"
                                    class="grouped_noty_children">
                                    <div
                                        v-for="child in getChildren(item)"
                                        :key="child.id"
                                        class="grouped_noty_child"
                                        :class="{ unread: !child.is_read }">
                                        <div class="grouped_noty_child_content">
                                            <div class="grouped_noty_child_meta">
                                                <span class="grouped_noty_child_date">{{ formatDate(child.created_at) }}</span>
                                                <a-badge
                                                    v-if="!child.is_read && isMobile"
                                                    status="error"
                                                    class="grouped_noty_mobile_unread_dot" />
                                                <a-tag v-if="!child.is_read && !isMobile" color="red">
                                                    {{ $t('noty.unread') }}
                                                </a-tag>
                                            </div>
                                            <div class="grouped_noty_child_message">
                                                <Messsage :item="child" @read="readNoty(child)" />
                                            </div>
                                        </div>
                                        <div class="grouped_noty_child_read">
                                            <template v-if="!child.is_read">
                                                <a-button
                                                    v-if="isMobile"
                                                    shape="circle"
                                                    icon="fi-rr-check"
                                                    flaticon
                                                    class="grouped_noty_mobile_read_btn flex items-center justify-center text-xs"
                                                    @click="readNoty(child)" />
                                                <a-checkbox
                                                    v-else
                                                    class="whitespace-nowrap"
                                                    @change="readNoty(child)">
                                                    {{ $t('noty.read') }}
                                                </a-checkbox>
                                            </template>
                                        </div>
                                    </div>
                                </transition-group>
                            </transition>
                            <button
                                v-if="canLoadGroup(item)"
                                class="grouped_noty_more"
                                :class="{ sticky: isExpanded(item) }"
                                type="button"
                                :disabled="isGroupLoading(item)"
                                @click="toggleGroup(item)">
                                <span>{{ moreButtonText(item) }}</span>
                                <a-spin v-if="isGroupLoading(item)" size="small" class="ml-2" />
                                <i v-else class="fi fi-rr-angle-small-down ml-2" :class="{ active: isExpanded(item) }" />
                            </button>
                        </div>
                    </div>
                </div>
                </div>
            </transition-group>
            <a-empty
                v-if="!loading && list.length === 0"
                class="mt-4"
                :description="$t('noty.emptyList')" />
            <infinite-loading
                v-if="showInfinity"
                ref="grouped_notify_infinity"
                v-bind:distance="10"
                @infinite="scrollHandler">
                <div slot="spinner">
                    <a-spin
                        class="mt-4"
                        v-show="loading && page > 1 && list.length" />
                </div>
                <div slot="no-more"></div>
                <div slot="no-results"></div>
            </infinite-loading>
        </div>
    </div>
</template>

<script>
import axiosMain from 'axios'
import { errorHandler } from '@/utils/index.js'
import { getColor, getBackground, getNotificationIconClass } from '../utils'
import eventBus from '@/utils/eventBus'
import notySyncChannel from '@/utils/notySyncChannel'

const isCanceledRequest = error => axiosMain.isCancel?.(error) || error?.code === 'ERR_CANCELED'
const GROUP_EXPAND_MIN_DURATION = 240
const GROUP_EXPAND_MAX_DURATION = 900
const GROUP_EXPAND_PX_PER_MS = 2.6
const GROUP_COLLAPSE_DURATION = 240

export default {
    name: "GroupedNotificationsList",
    components: {
        InfiniteLoading: () => import('vue-infinite-loading'),
        Messsage: () => import('./Message'),
        CardLoading: () => import('./CardLoading.vue')
    },
    props: {
        pageName: {
            type: String,
            required: true
        },
        filters: {
            type: Object,
            default: () => ({})
        },
        filtersKey: {
            type: String,
            default: ''
        },
        suspendFiltersWatcher: {
            type: Boolean,
            default: false
        }
    },
    data() {
        return {
            list: [],
            next: true,
            page: 0,
            loading: false,
            showInfinity: false,
            requestSource: null,
            requestId: 0,
            expandedGroups: {},
            groupLoading: {},
            animatedBadges: {},
            filtersReloadTimer: null,
            notySyncUnsubscribe: null,
            mountedReady: false
        }
    },
    computed: {
        isMobile() {
            return this.$store.state.isMobile
        },
        hideReadNotifications() {
            return !!this.$store.state.user.user?.hide_read_notifications
        }
    },
    watch: {
        filtersKey() {
            if (!this.mountedReady) return
            if (this.suspendFiltersWatcher) return
            this.scheduleFiltersReload()
        }
    },
    methods: {
        getColor,
        getBackground,
        getIconClass: getNotificationIconClass,
        getAvatarIcon(icon) {
            return this.getIconClass(icon) ? null : icon
        },
        scheduleFiltersReload() {
            if (this.filtersReloadTimer)
                clearTimeout(this.filtersReloadTimer)

            this.filtersReloadTimer = setTimeout(() => {
                this.reload()
                this.filtersReloadTimer = null
            }, 1000)
        },
        cancelRequest() {
            this.requestId += 1
            if (this.requestSource) {
                this.requestSource.cancel('Grouped notifications request cancelled')
                this.requestSource = null
            }
        },
        getGroupKey(item) {
            return item?.object_id || item?.id
        },
        canShowSocketNotification(item) {
            if (!item || item.is_mention) return false

            const categoryCode = item?.category?.code
            const singleCategory = this.filters?.event_type__category
            const categoryList = this.filters?.event_type__category__in

            if (singleCategory)
                return categoryCode === singleCategory
            if (Array.isArray(categoryList) && categoryList.length)
                return categoryList.includes(categoryCode)

            return true
        },
        isCategoryMatched(item, categoryCodes = []) {
            if (!Array.isArray(categoryCodes) || !categoryCodes.length) return false
            return categoryCodes.includes(item?.category?.code)
        },
        getSyncReadItem(msg) {
            const id = msg?.id
            const objectId = msg?.objectId
            const listItem = this.list.find(item => item.id === id || (objectId && item.object_id === objectId))
            if (listItem) {
                return {
                    ...listItem,
                    id,
                    object_id: objectId || listItem.object_id
                }
            }

            for (const key of Object.keys(this.expandedGroups)) {
                const child = this.expandedGroups[key].find(item => item.id === id)
                if (child) {
                    return {
                        ...child,
                        object_id: objectId || child.object_id || key
                    }
                }
            }

            return {
                id,
                object_id: objectId || null
            }
        },
        markCategoryRead(categoryCodes = []) {
            this.list = this.list.map(item => {
                if (!this.isCategoryMatched(item, categoryCodes)) return item
                return {
                    ...item,
                    is_read: true,
                    group_unread: 0
                }
            })

            Object.keys(this.expandedGroups).forEach(key => {
                const nextChildren = this.expandedGroups[key].map(item => {
                    if (!this.isCategoryMatched(item, categoryCodes)) return item
                    return {
                        ...item,
                        is_read: true,
                        group_unread: 0
                    }
                })
                this.$set(this.expandedGroups, key, nextChildren)
            })
        },
        removeCategoryNotifications(categoryCodes = []) {
            this.list = this.list.filter(item => !this.isCategoryMatched(item, categoryCodes))

            Object.keys(this.expandedGroups).forEach(key => {
                const nextChildren = this.expandedGroups[key].filter(item => !this.isCategoryMatched(item, categoryCodes))
                if (nextChildren.length)
                    this.$set(this.expandedGroups, key, nextChildren)
                else
                    this.$delete(this.expandedGroups, key)
            })
        },
        onSyncMessage(msg) {
            if (!msg || !msg.type) return

            if (msg.type === 'read_one' && msg.id) {
                if (msg.isMention) return

                const readItem = this.getSyncReadItem(msg)
                if (this.hideReadNotifications)
                    this.removeReadNotification(readItem)
                else
                    this.markRead(readItem)
                return
            }

            if (msg.type === 'read_group' && msg.objectId) {
                this.markGroupReadByObjectId(msg.objectId)
                return
            }

            if (msg.type === 'read_all') {
                if (this.hideReadNotifications) {
                    this.list = []
                    this.expandedGroups = {}
                    return
                }
                this.markAllRead()
                return
            }

            if (msg.type === 'read_by_categories' && Array.isArray(msg.category_codes)) {
                if (this.hideReadNotifications)
                    this.removeCategoryNotifications(msg.category_codes)
                else
                    this.markCategoryRead(msg.category_codes)
            }
        },
        applyReadAll(payload = {}) {
            if (payload.isMention) return

            const categoryCodes = Array.isArray(payload.categoryCodes) ? payload.categoryCodes : []
            if (this.hideReadNotifications) {
                if (categoryCodes.length) {
                    this.removeCategoryNotifications(categoryCodes)
                    return
                }

                this.list = []
                this.expandedGroups = {}
                return
            }

            if (categoryCodes.length) {
                this.markCategoryRead(categoryCodes)
                return
            }

            this.markAllRead()
        },
        getMergedGroupFromSocket(currentGroup, notification) {
            const currentTotal = Number(currentGroup?.group_total) || 1
            const currentUnread = Number(currentGroup?.group_unread) || 0
            const nextTotal = Number(notification?.group_total) || currentTotal + 1
            const nextUnread = Number(notification?.group_unread) || currentUnread + (notification?.is_read ? 0 : 1)

            return {
                ...currentGroup,
                ...notification,
                group_total: nextTotal,
                group_unread: nextUnread
            }
        },
        prependExpandedNotification(groupKey, notification) {
            const children = this.expandedGroups[groupKey]
            if (!Array.isArray(children)) return
            if (children.some(item => item.id === notification.id)) return

            this.$set(this.expandedGroups, groupKey, [
                notification,
                ...children
            ])
        },
        onSocketNotification(notification) {
            if (!this.canShowSocketNotification(notification)) return

            const groupKey = this.getGroupKey(notification)
            if (!groupKey) return

            const index = this.list.findIndex(item => this.getGroupKey(item) === groupKey)

            if (index === -1) {
                this.list.unshift({
                    ...notification,
                    group_total: Number(notification?.group_total) || 1,
                    group_unread: Number(notification?.group_unread) || (notification?.is_read ? 0 : 1)
                })
                return
            }

            const currentGroup = this.list[index]
            const wasUnread = Number(currentGroup?.group_unread) > 0
            const nextGroup = this.getMergedGroupFromSocket(currentGroup, notification)
            const hasUnread = Number(nextGroup?.group_unread) > 0

            if (index === 0) {
                this.$set(this.list, index, nextGroup)
            } else {
                this.list.splice(index, 1)
                this.list.unshift(nextGroup)
            }
            if (!wasUnread && hasUnread)
                this.animateBadge(groupKey)
            this.prependExpandedNotification(groupKey, notification)
        },
        getChildren(item) {
            const key = this.getGroupKey(item)
            return this.expandedGroups[key] || []
        },
        isExpanded(item) {
            const key = this.getGroupKey(item)
            return Array.isArray(this.expandedGroups[key])
        },
        isGroupLoading(item) {
            return !!this.groupLoading[this.getGroupKey(item)]
        },
        getUnreadCount(item) {
            return Math.max(0, Number(item?.group_unread) || 0)
        },
        getHeaderUnreadCount(item) {
            if (!this.canLoadGroup(item)) return 0
            return this.getUnreadCount(item)
        },
        shouldAnimateBadge(item) {
            return !!this.animatedBadges[this.getGroupKey(item)]
        },
        animateBadge(groupKey) {
            if (!groupKey) return
            this.$set(this.animatedBadges, groupKey, true)
            setTimeout(() => {
                if (this.animatedBadges[groupKey])
                    this.$delete(this.animatedBadges, groupKey)
            }, 450)
        },
        getNotificationTitle(item) {
            const objectType = item?.group_info?.object_type
            const groupTitle = item?.group_info?.title
            const normalizedObjectType = typeof objectType === 'string' ? objectType.trim() : ''
            const normalizedGroupTitle = typeof groupTitle === 'string' ? groupTitle.trim() : ''

            if (normalizedObjectType && normalizedGroupTitle)
                return `${normalizedObjectType}: ${normalizedGroupTitle}`
            if (normalizedGroupTitle)
                return normalizedGroupTitle

            return item?.icon_name || this.$t('noty.defaultTitle')
        },
        getMoreNotificationsCount(item) {
            if (this.hideReadNotifications)
                return Math.max(0, Number(item?.group_unread) || 0)
            return Math.max(0, Number(item?.group_total) || 0)
        },
        canLoadGroup(item) {
            return !!item?.object_id && this.getMoreNotificationsCount(item) > 1
        },
        canReadSingleGroup(item) {
            return !this.canLoadGroup(item) && !item?.is_read
        },
        canReadGroup(item) {
            return this.getUnreadCount(item) > 0
        },
        canReadVisibleGroupItem(item) {
            return !item?.is_read
        },
        moreButtonText(item) {
            if (this.isExpanded(item))
                return this.$t('noty.hideNotifications')
            const count = this.getMoreNotificationsCount(item)
            return `${this.$t('noty.more')} ${count} ${this.getNotificationWord(count)}`
        },
        getNotificationWord(count) {
            const locale = this.$i18n?.locale
            if (locale === 'ru') {
                const mod10 = count % 10
                const mod100 = count % 100
                if (mod10 === 1 && mod100 !== 11) return 'уведомление'
                if (mod10 >= 2 && mod10 <= 4 && (mod100 < 12 || mod100 > 14)) return 'уведомления'
                return 'уведомлений'
            }
            return this.$t('noty.notifications')
        },
        onExpandEnter(el) {
            const duration = this.getGroupExpandDuration(el.scrollHeight)
            el.style.setProperty('--group-expand-duration', `${duration}ms`)
            el.style.height = '0'
            el.style.overflow = 'hidden'
            el.offsetHeight
            el.style.height = `${el.scrollHeight}px`
        },
        onExpandAfterEnter(el) {
            el.style.height = 'auto'
            el.style.overflow = ''
            el.style.removeProperty('--group-expand-duration')
        },
        onExpandLeave(el) {
            el.style.setProperty('--group-expand-duration', `${GROUP_COLLAPSE_DURATION}ms`)
            el.style.height = `${el.scrollHeight}px`
            el.style.overflow = 'hidden'
            el.offsetHeight
            el.style.height = '0'
        },
        getGroupExpandDuration(height) {
            const duration = Math.round(Number(height) / GROUP_EXPAND_PX_PER_MS)
            return Math.min(
                GROUP_EXPAND_MAX_DURATION,
                Math.max(GROUP_EXPAND_MIN_DURATION, duration)
            )
        },
        formatDate(value) {
            if (!value) return ''
            const current = this.$moment()
            const createdAt = this.$moment(value)
            const days = createdAt.diff(current, 'days')

            if (createdAt.isAfter(current))
                return current.fromNow()

            if(days < -2)
                return createdAt.format('DD.MM.YYYY HH:mm')
            return createdAt.fromNow()
        },
        async getGroupedList() {
            if (this.loading || !this.next) return null

            let source
            const requestId = this.requestId
            const nextPage = this.page + 1

            try {
                this.loading = true
                source = axiosMain.CancelToken.source()
                this.requestSource = source
                this.page = nextPage

                const params = {
                    page_size: 10,
                    page: nextPage,
                    page_name: this.pageName
                }
                if (this.filters && Object.keys(this.filters).length)
                    params.filters = JSON.stringify(this.filters)

                const { data } = await this.$http.get('/notifications/grouped/', {
                    params,
                    cancelToken: source.token
                })

                if (requestId !== this.requestId) return null

                this.next = data?.next || null
                const results = Array.isArray(data?.results) ? data.results : []
                this.mergeList(results)
                return data
            } catch(error) {
                if (isCanceledRequest(error)) return null
                this.page = Math.max(0, nextPage - 1)
                if (error?.response?.status === 404) {
                    this.next = false
                    return { next: null, results: [] }
                }
                errorHandler({ error, show: false })
                throw error
            } finally {
                if (this.requestSource === source) this.requestSource = null
                this.loading = false
            }
        },
        mergeList(results = []) {
            if (!results.length) return

            if (!this.list.length) {
                this.list = results
                return
            }

            const currentMap = new Map(this.list.map(item => [item.id, item]))
            results.forEach(item => {
                if (!item?.id) return
                currentMap.set(item.id, {
                    ...(currentMap.get(item.id) || {}),
                    ...item
                })
            })

            const incomingIds = new Set(results.map(item => item?.id).filter(Boolean))
            this.list = this.list.map(item => incomingIds.has(item.id) ? currentMap.get(item.id) : item)
            results.forEach(item => {
                if (item?.id && !this.list.some(existing => existing.id === item.id))
                    this.list.push(item)
            })
        },
        async toggleGroup(item) {
            const key = this.getGroupKey(item)
            if (!key || this.isGroupLoading(item)) return

            if (this.isExpanded(item)) {
                this.$delete(this.expandedGroups, key)
                return
            }

            try {
                this.$set(this.groupLoading, key, true)
                const { data } = await this.$http.get('/notifications/', {
                    params: {
                        object_id: item.object_id
                    }
                })
                const results = Array.isArray(data?.results) ? data.results : []
                this.$set(this.expandedGroups, key, results)
            } catch(error) {
                errorHandler({ error, show: false })
            } finally {
                this.$delete(this.groupLoading, key)
            }
        },
        readNoty(item) {
            if(!item.is_read) {
                this.$store.dispatch('notifications/readNoty', {
                    id: item.id,
                    isMention: false,
                    categoryCode: item?.category?.code || null,
                    objectId: item?.object_id || null
                }).then(() => {
                    if (this.hideReadNotifications)
                        this.removeReadNotification(item)
                    else
                        this.markRead(item)
                }).catch(() => {})
            }
        },
        readGroup(item) {
            const objectId = item?.object_id
            if (!objectId || !this.canReadGroup(item)) return

            const notificationIds = this.getGroupNotificationIds(item)

            this.$store.dispatch('notifications/readGroupNoty', {
                objectId,
                notificationIds
            }).then(() => {
                if (this.hideReadNotifications)
                    this.removeReadGroup(item)
                else
                    this.markGroupRead(item)
            }).catch(() => {})
        },
        getGroupNotificationIds(item) {
            const groupKey = this.getGroupKey(item)
            const childIds = Array.isArray(this.expandedGroups[groupKey])
                ? this.expandedGroups[groupKey].map(child => child?.id).filter(Boolean)
                : []

            return Array.from(new Set([item?.id, ...childIds].filter(Boolean)))
        },
        removeReadNotification(readItem) {
            const id = readItem?.id
            const objectId = readItem?.object_id
            if (!id) return

            const groupKey = objectId || id
            const isGroupExpanded = Array.isArray(this.expandedGroups[groupKey])
            const children = isGroupExpanded
                ? this.expandedGroups[groupKey].filter(item => item.id !== id)
                : null

            if (children) {
                if (children.length)
                    this.$set(this.expandedGroups, groupKey, children)
                else
                    this.$delete(this.expandedGroups, groupKey)
            }

            this.list = this.list.reduce((acc, item) => {
                const isCurrentGroup = item.id === id || (objectId && item.object_id === objectId)
                if (!isCurrentGroup) {
                    acc.push(item)
                    return acc
                }

                const currentUnread = Number(item.group_unread) || 0
                const currentTotal = Number(item.group_total) || 1
                const nextUnread = Math.max(0, currentUnread - 1)
                const isVisibleCollapsedPreview = !isGroupExpanded && item.id === id && currentTotal > 1
                const nextTotal = isVisibleCollapsedPreview
                    ? currentTotal
                    : Math.max(0, currentTotal - 1)
                const isSingleNotification = currentTotal <= 1
                const shouldRemoveGroup = nextUnread === 0 || nextTotal === 0 || isSingleNotification

                if (!shouldRemoveGroup) {
                    acc.push({
                        ...item,
                        group_total: nextTotal,
                        group_unread: nextUnread,
                        is_read: item.id === id ? true : item.is_read
                    })
                }
                return acc
            }, [])
        },
        removeReadGroup(readItem) {
            const objectId = readItem?.object_id
            if (!objectId) return

            this.$delete(this.expandedGroups, objectId)
            this.list = this.list.filter(item => item.object_id !== objectId)
        },
        markRead(readItem) {
            const id = readItem?.id
            const objectId = readItem?.object_id
            this.list = this.list.map(item => {
                if (item.id === id) {
                    return {
                        ...item,
                        is_read: true,
                        group_unread: Math.max(0, Number(item.group_unread) - 1)
                    }
                }
                if (objectId && item.object_id === objectId && item.id !== id) {
                    return {
                        ...item,
                        group_unread: Math.max(0, Number(item.group_unread) - 1)
                    }
                }
                return {
                    ...item
                }
            })

            Object.keys(this.expandedGroups).forEach(key => {
                const nextChildren = this.expandedGroups[key].map(item => {
                    if (item.id !== id) return item
                    return {
                        ...item,
                        is_read: true
                    }
                })
                this.$set(this.expandedGroups, key, nextChildren)
            })
        },
        markGroupRead(readItem) {
            const objectId = readItem?.object_id
            if (!objectId) return

            this.list = this.list.map(item => {
                if (item.object_id !== objectId) return item
                return {
                    ...item,
                    is_read: true,
                    group_unread: 0
                }
            })

            const groupChildren = this.expandedGroups[objectId]
            if (Array.isArray(groupChildren)) {
                this.$set(this.expandedGroups, objectId, groupChildren.map(item => ({
                    ...item,
                    is_read: true
                })))
            }

            if (this.animatedBadges[objectId])
                this.$delete(this.animatedBadges, objectId)
        },
        markGroupReadByObjectId(objectId) {
            if (!objectId) return

            const groupItem = this.list.find(item => item.object_id === objectId)
            if (!groupItem) return

            if (this.hideReadNotifications)
                this.removeReadGroup(groupItem)
            else
                this.markGroupRead(groupItem)
        },
        markAllRead() {
            this.list = this.list.map(item => ({
                ...item,
                is_read: true,
                group_unread: 0
            }))
            this.animatedBadges = {}

            Object.keys(this.expandedGroups).forEach(key => {
                const nextChildren = this.expandedGroups[key].map(item => ({
                    ...item,
                    is_read: true,
                    group_unread: 0
                }))
                this.$set(this.expandedGroups, key, nextChildren)
            })
        },
        async scrollHandler($state = null) {
            if(!this.loading && this.next) {
                try {
                    const res = await this.getGroupedList()
                    if (!res) {
                        if($state) $state.loaded()
                        return
                    }
                    if(!res.next) {
                        if($state) $state.complete()
                    } else if($state) {
                        $state.loaded()
                    }
                } catch(error) {
                    if($state) $state.complete()
                }
            } else if($state) {
                $state.complete()
            }
        },
        async reload() {
            this.cancelRequest()
            this.loading = false
            this.showInfinity = false
            this.page = 0
            this.next = true
            this.list = []
            this.expandedGroups = {}

            await this.$nextTick()
            await this.scrollHandler()
            this.showInfinity = true
        }
    },
    async mounted() {
        await this.scrollHandler()
        this.showInfinity = true
        this.mountedReady = true
        eventBus.$on('NOTIFICATION_NEW_MESSAGE', this.onSocketNotification)
        this.notySyncUnsubscribe = notySyncChannel.subscribe(this.onSyncMessage)
    },
    beforeDestroy() {
        if (this.filtersReloadTimer)
            clearTimeout(this.filtersReloadTimer)
        if (this.notySyncUnsubscribe)
            this.notySyncUnsubscribe()
        this.cancelRequest()
        this.showInfinity = false
        eventBus.$off('NOTIFICATION_NEW_MESSAGE', this.onSocketNotification)
    }
}
</script>

<style lang="scss" scoped>
.grouped_noty_list{
    width: 100%;
    min-height: 0;
    &.mobile{
        min-height: 90vh;
    }
}
.noty-read-remove-leave-active {
    transition: transform .24s ease, opacity .24s ease;
}
.noty-read-remove-leave-to {
    opacity: 0;
    transform: translateX(80px);
}
.grouped_noty_item{
    padding: 15px 0;
    border-bottom: 1px solid var(--border2);
}
.grouped_noty_head{
    display: flex;
    align-items: flex-start;
}
.grouped_noty_mark{
    position: relative;
    width: 45px;
    flex-shrink: 0;
    align-self: stretch;
    padding-top: 0;
    z-index: 1;
    &::v-deep{
        .ant-avatar{
            position: relative;
            z-index: 2;
        }
        .noty_avatar{
            display: inline-flex;
            align-items: center;
            justify-content: center;
            .ant-avatar-string{
                position: static;
                display: flex;
                align-items: center;
                justify-content: center;
                width: 100%;
                height: 100%;
                line-height: 1!important;
                transform: none!important;
            }
            .fi{
                display: inline-flex;
                align-items: center;
                justify-content: center;
                font-size: 14px;
                line-height: 1;
            }
        }
    }
}
.grouped_noty_content{
    width: 100%;
    min-width: 0;
}
.grouped_noty_title{
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 16px;
    color: #30323a;
    font-size: 15px;
    font-weight: 600;
    line-height: 1.35;
    min-height: 30px;
}
.grouped_noty_title_main{
    display: flex;
    align-items: center;
    min-width: 0;
    gap: 8px;
}
.grouped_noty_group_title_checkbox{
    flex-shrink: 0;
    color: #4c4f58;
    font-size: 15px;
    font-weight: 400;
    line-height: 1.45;
}
.grouped_noty_badge{
    flex-shrink: 0;
    &.appear_from_left{
        animation: grouped-badge-from-left .36s cubic-bezier(.2, .8, .2, 1) both;
    }
}
.grouped_noty_date,
.grouped_noty_child_date,
.grouped_noty_message_date{
    flex-shrink: 0;
    color: #8d96aa;
    font-size: 14px;
    font-weight: 500;
    opacity: 1;
}
.grouped_noty_body{
    position: relative;
    &.has_timeline{
        padding-left: 0;
    }
}
.grouped_noty_message{
    position: relative;
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    gap: 16px;
    color: #4c4f58;
    font-size: 15px;
    line-height: 1.45;
}
.grouped_noty_single_content{
    min-width: 0;
    flex: 1;
}
.grouped_noty_single_read{
    display: flex;
    justify-content: flex-end;
    flex-shrink: 0;
    min-width: 130px;
}
.grouped_noty_mobile_read_btn{
    min-width: 32px;
    max-width: 32px;
    width: 32px;
    min-height: 32px;
    max-height: 32px;
    height: 32px;
    padding: 0!important;
    line-height: 32px!important;
    flex-shrink: 0;
}
.grouped_noty_children{
    position: relative;
    &::before{
        content: '';
        position: absolute;
        top: -14px;
        left: -30px;
        width: 2px;
        height: 24px;
        border-radius: 2px;
        background: #e3e7ee;
        transform-origin: top;
        animation: timeline-line-in .24s ease both;
    }
}
.grouped_noty_child{
    position: relative;
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    gap: 16px;
    padding: 0 0 18px;
    color: #4c4f58;
    font-size: 15px;
    line-height: 1.45;
    &::before{
        content: '';
        position: absolute;
        top: 10px;
        left: -30px;
        width: 16px;
        height: 2px;
        border-radius: 2px;
        background: #e3e7ee;
        transform-origin: left;
        animation: timeline-branch-in .2s ease both;
    }
    &:not(:last-child)::after{
        content: '';
        position: absolute;
        top: 10px;
        bottom: -10px;
        left: -30px;
        width: 2px;
        border-radius: 2px;
        background: #e3e7ee;
        transform-origin: top;
        animation: timeline-line-in .24s ease both;
    }
    &:last-child{
        padding-bottom: 0;
    }
}
.grouped_noty_child_content{
    min-width: 0;
    flex: 1;
}
.grouped_noty_child_meta,
.grouped_noty_message_meta{
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 5px;
    &::v-deep{
        .ant-tag{
            font-size: 11px;
            line-height: 20px;
            padding: 0 6px;
            margin: 0;
        }
    }
}
.grouped_noty_mobile_unread_dot{
    flex-shrink: 0;
}
.grouped_noty_child_message{
    min-width: 0;
}
.grouped_noty_child_read{
    display: flex;
    justify-content: flex-end;
    flex-shrink: 0;
    min-width: 130px;
}
@media (max-width: 991px) {
    .grouped_noty_single_read,
    .grouped_noty_child_read{
        align-self: flex-start;
        min-width: 32px;
        margin-top: 2px;
    }
}
.grouped_noty_more{
    display: inline-flex;
    align-items: center;
    padding: 4px 8px 4px 8px;
    margin-left: -8px;
    margin-top: 10px;
    border: 0;
    background: #fff;
    color: var(--primaryColor);
    font-size: 15px;
    line-height: 1.2;
    min-height: 29px;
    cursor: pointer;
    user-select: none;
    border-radius: 30px;
    &.sticky{
        position: sticky;
        bottom: 0;
        z-index: 3;
        box-shadow: 0 0 0 1px #e6e6e8;
    }
    &:disabled{
        cursor: default;
        opacity: .7;
    }
    .fi{
        transition: transform .2s ease;
        &.active{
            transform: rotate(180deg);
        }
    }
}
.date-fade-enter-active,
.date-fade-leave-active {
    transition: all .2s ease;
}
.date-fade-enter,
.date-fade-leave-to {
    opacity: 0;
    transform: translateY(-4px);
}
.group-expand-enter-active,
.group-expand-leave-active {
    transition: height var(--group-expand-duration, .24s) ease;
    overflow: hidden;
}
.group-expand-enter,
.group-expand-leave-to {
    height: 0;
}
@keyframes timeline-line-in {
    from {
        opacity: 0;
        transform: scaleY(0);
    }
    to {
        opacity: 1;
        transform: scaleY(1);
    }
}
@keyframes timeline-branch-in {
    from {
        opacity: 0;
        transform: scaleX(0);
    }
    to {
        opacity: 1;
        transform: scaleX(1);
    }
}
@keyframes grouped-badge-from-left {
    from {
        opacity: 0;
        transform: translateX(-16px) scale(.8);
    }
    70% {
        opacity: 1;
        transform: translateX(2px) scale(1.04);
    }
    to {
        opacity: 1;
        transform: translateX(0) scale(1);
    }
}
</style>
