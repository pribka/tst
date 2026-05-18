<template>
    <div ref="notifyDrawerWrapper">
        <div v-if="!isMobile" class="flex items-center justify-between header_noty__filters">
            <div class="flex items-center">
                <a-button
                    @click="readAllNoty()"
                    type="primary"
                    size="large"
                    icon="fi-rr-check-double"
                    flaticon
                    class="mr-2">
                    {{ readAllButtonText }}
                </a-button>
                <PageFilter
                    :excludeFields="excludeFilters"
                    :model="model"
                    :title="$t('filters')"
                    :getPopupContainer="getPopupContainer"
                    filterButtonSize="large"
                    size="large"
                    :page_name="page_name" />
            </div>
            <div class="grouping_switch flex items-center" @click="toggleGroupNotifications">
                <a-switch
                    class="mr-2"
                    :checked="groupNotifications"
                    :loading="groupNotificationsLoading"
                    @click.native.stop
                    @change="changeGroupNotifications" />
                <span>{{ $t('noty.grouping') }}</span>
            </div>
        </div>
        <div>
            <a-tabs
                :activeKey="activeTab"
                class="notify_tabs"
                @change="onTabChange">
                <div v-if="isMobile" slot="tabBarExtraContent" class="notify_tabs_extra">
                    <a-switch
                        :checked="groupNotifications"
                        :loading="groupNotificationsLoading"
                        @click.native.stop
                        @change="changeGroupNotifications" />
                </div>
                <a-tab-pane key="notifications">
                    <template #tab>
                        <div class="flex items-center select-none">
                            <i class="fi fi-rr-bell mr-2" />
                            <span>{{ $t('noty.tabNotifications') }}</span>
                            <transition name="badge-fade-slide">
                                <a-badge v-if="unreadCount" :count="unreadCount" class="ml-2" />
                            </transition>
                        </div>
                    </template>
                </a-tab-pane>
                <a-tab-pane key="mentions">
                    <template #tab>
                        <div class="flex items-center select-none">
                            <span class="mentions_icon mr-2">@</span>
                            <span>{{ $t('noty.tabMentions') }}</span>
                            <transition name="badge-fade-slide">
                                <a-badge v-if="unreadMentionsCount" :count="unreadMentionsCount" class="ml-2" />
                            </transition>
                        </div>
                    </template>
                </a-tab-pane>
            </a-tabs>
        </div>

        <div v-if="activeTab === 'notifications'" class="category_filter_wrap mt-2">
            <div class="category_filter_head">
                <div class="flex items-center">
                    <span>{{ $t('noty.categoryFilter') }}</span>
                    <a-button
                        class="category_order_settings_btn ml-2"
                        v-tippy
                        :content="$t('noty.changeCategorySortSettings')"
                        type="ui"
                        ghost
                        shape="circle"
                        size="small"
                        flaticon
                        icon="fi-rr-settings"
                        :aria-label="$t('noty.categoryOrderSettings')"
                        @click="openCategoryOrderModal" />
                </div>
                <div>
                    <transition name="slide-right-fade">
                        <a-button
                            v-if="selectedCategoryCodes.length"
                            type="link"
                            size="small"
                            class="p-0"
                            @click="clearCategories">
                            {{ $t('noty.resetCategoryFilter') }}
                        </a-button>
                    </transition>
                </div>
            </div>
            <div v-if="categoriesLoading && !categories.length" class="py-2">
                <a-spin size="small" />
            </div>
            <div
                v-else
                class="category_chips_wrapper"
                @mouseenter="onCategoryWrapperEnter"
                @mouseleave="onCategoryWrapperLeave">
                <a-button
                    v-if="showLeftArrow"
                    class="scroll_arrow left"
                    shape="circle"
                    size="small"
                    type="flat_primary"
                    flaticon
                    icon="fi-rr-angle-small-left"
                    @mouseenter="startHoverScroll('left')"
                    @mouseleave="stopHoverScroll" />
                <a-button
                    v-if="showRightArrow"
                    class="scroll_arrow right"
                    shape="circle"
                    size="small"
                    type="flat_primary"
                    flaticon
                    icon="fi-rr-angle-small-right"
                    @mouseenter="startHoverScroll('right')"
                    @mouseleave="stopHoverScroll" />
                <div ref="categoryChips" class="category_chips" @scroll="onCategoriesScroll">
                    <a-button
                        v-for="category in categories"
                        :key="category.code"
                        :ref="'categoryItem_' + category.code"
                        class="category_chip flex items-center"
                        :type="isSelectedCategory(category.code) ? 'primary' : 'flat_primary'"
                        @click="toggleCategory(category.code)">
                        <span>{{ category.name }}</span>
                        <transition name="badge-fade-slide">
                            <a-badge 
                                v-if="getCategoryUnreadCount(category.code)"
                                :count="getCategoryUnreadCount(category.code)" 
                                :overflow-count="99"
                                :number-style="{
                                    backgroundColor: '#fff',
                                    color: '#000',
                                    boxShadow: 'none'
                                }"
                                class="ml-2" />
                        </transition>
                    </a-button>
                </div>
            </div>
        </div>

        <GroupedList
            v-if="useGroupedNotifications"
            :key="`grouped-${listRenderKey}`"
            ref="groupedList"
            :pageName="page_name"
            :filters="requestFilters"
            :filtersKey="requestFiltersKey"
            :suspendFiltersWatcher="tabSwitching" />
        <DefaultList
            v-else
            :key="`default-${listRenderKey}`"
            ref="defaultList"
            :pageName="page_name"
            :filters="requestFilters"
            :filtersKey="requestFiltersKey"
            :suspendFiltersWatcher="tabSwitching" />

        <div v-if="isMobile" class="float_add">
            <div class="filter_slot">
                <PageFilter
                    :excludeFields="excludeFilters"
                    :model="model"
                    :title="$t('filters')"
                    filterButtonSize="large"
                    :zIndex="6000"
                    size="large"
                    :page_name="page_name" />
            </div>
            <a-button
                flaticon
                shape="circle"
                size="large"
                type="primary"
                icon="fi-rr-check-double"
                @click="readAllNoty()" />
        </div>

        <a-modal
            :visible="categoryOrderModalVisible"
            :title="$t('noty.categoryOrderSettings')"
            :confirm-loading="categoryOrderSaving"
            :width="isMobile ? '100vw' : undefined"
            :wrapClassName="isMobile ? 'category-order-modal-mobile' : 'category-order-modal'"
            :dialog-style="isMobile ? { top: '0', paddingBottom: '0' } : { top: '20px' }"
            @cancel="closeCategoryOrderModal">
            <draggable
                v-model="editableCategories"
                :forceFallback="true"
                ghost-class="ghost"
                draggable=".category_order_item"
                handle=".category_order_handle"
                class="category_order_list"
                @start="categoryOrderDragging = true"
                @end="categoryOrderDragging = false">
                <div
                    v-for="category in editableCategories"
                    :key="category.code"
                    class="category_order_item">
                    <a-button
                        class="category_order_handle select-none"
                        type="ui"
                        ghost
                        shape="circle"
                        flaticon
                        icon="fi-rr-grip-dots-vertical"
                        :aria-label="$t('move')" />
                    <div class="category_order_chip flex items-center">
                        <span>{{ category.name }}</span>
                    </div>
                </div>
            </draggable>
            <template #footer>
                <div :class="isMobile ? 'w-full' : 'flex justify-end'">
                    <a-button
                        :block="isMobile"
                        type="primary"
                        :loading="categoryOrderSaving"
                        @click="saveCategoryOrder">
                        {{ $t('save') }}
                    </a-button>
                </div>
            </template>
        </a-modal>
    </div>
</template>

<script>
import { mapActions, mapState } from 'vuex'
import eventBus from '@/utils/eventBus'
import { errorHandler } from '@/utils/index.js'
import notySyncChannel from '@/utils/notySyncChannel'
import draggable from "vuedraggable"

export default {
    name: "NotificationsList",
    components: {
        PageFilter: () => import('@/components/PageFilter'),
        DefaultList: () => import('./DefaultList.vue'),
        GroupedList: () => import('./GroupedList.vue'),
        draggable
    },
    data() {
        return {
            excludeFilters: ['event_type__icon__exclude', 'event_type__icon'],
            model: "notifications.WebNotificationModel",
            page_name: "page_list_notifications.WebNotificationModel",
            isCategoryWrapperHover: false,
            canScrollLeft: false,
            canScrollRight: false,
            categoryHoverScrollTimer: null,
            categoryHoverScrollDir: null,
            groupNotificationsLoading: false,
            categoryOrderModalVisible: false,
            editableCategories: [],
            categoryOrderSaving: false,
            categoryOrderDragging: false,
            refreshCategoriesTimer: null,
            settingsReloadTimer: null,
            notySyncUnsubscribe: null,
            tabSwitching: false,
            listRenderKey: 0
        }
    },
    computed: {
        ...mapState({
            categories: state => state.notifications.categories,
            categoriesLoading: state => state.notifications.categoriesLoading,
            unreadCount: state => state.notifications.unreadCount,
            unreadMentionsCount: state => state.notifications.unreadMentionsCount,
            unreadByCategory: state => state.notifications.unreadByCategory,
            user: state => state.user.user
        }),
        groupNotifications() {
            return !!this.user?.group_notifications
        },
        useGroupedNotifications() {
            return this.activeTab === 'notifications' && this.groupNotifications
        },
        isMobile() {
            return this.$store.state.isMobile
        },
        showLeftArrow() {
            return !this.isMobile && this.isCategoryWrapperHover && this.canScrollLeft
        },
        showRightArrow() {
            return !this.isMobile && this.isCategoryWrapperHover && this.canScrollRight
        },
        activeTab: {
            get() {
                return this.$store.state.notifications.activeTab
            },
            set(value) {
                this.$store.commit('notifications/SET_ACTIVE_TAB', value)
            }
        },
        selectedCategoryCodes() {
            return this.$store.state.notifications.selectedCategoryCodes
        },
        requestFilters() {
            if (this.activeTab === 'mentions') {
                return {
                    event_type__is_mention: true
                }
            }

            const filters = {
                event_type__is_mention: false
            }

            if (this.selectedCategoryCodes.length === 1) {
                filters.event_type__category = this.selectedCategoryCodes[0]
            } else if (this.selectedCategoryCodes.length > 1) {
                filters.event_type__category__in = this.selectedCategoryCodes
            }

            return filters
        },
        requestFiltersKey() {
            return JSON.stringify(this.requestFilters)
        },
        readAllButtonText() {
            return this.activeTab === 'mentions'
                ? this.$t('noty.readAllMentions')
                : this.$t('noty.readAll')
        }
    },
    watch: {
        categories() {
            this.$nextTick(() => this.updateCategoryArrows())
        },
        activeTab() {
            this.$nextTick(() => this.updateCategoryArrows())
        },
        isMobile() {
            this.$nextTick(() => this.updateCategoryArrows())
        }
    },
    methods: {
        ...mapActions({
            getCategories: "notifications/getCategories",
            refreshCategories: "notifications/refreshCategories",
            readAllNotyy: "notifications/readAllNoty",
        }),
        getPopupContainer() {
            return this.$refs.notifyDrawerWrapper
        },
        getScrollContainer() {
            const el = this.$el
            if (!el) return window

            if (typeof el.closest === 'function') {
                const drawerBody = el.closest('.drawer_body, .ant-drawer-body')
                if (drawerBody) return drawerBody
            }

            return window
        },
        scrollToTop() {
            const container = this.getScrollContainer()

            if (!container) return

            if (container === window) {
                window.scrollTo({ top: 0, behavior: 'auto' })
                return
            }

            if (typeof container.scrollTo === 'function') {
                container.scrollTo({ top: 0, behavior: 'auto' })
                return
            }

            container.scrollTop = 0
        },
        scheduleRefreshCategories() {
            if (this.refreshCategoriesTimer)
                clearTimeout(this.refreshCategoriesTimer)

            this.refreshCategoriesTimer = setTimeout(() => {
                this.refreshCategories().then(() => {
                    this.$nextTick(() => this.updateCategoryArrows())
                }).catch(() => {})
                this.refreshCategoriesTimer = null
            }, 1000)
        },
        scheduleSettingsReload() {
            if (this.settingsReloadTimer)
                clearTimeout(this.settingsReloadTimer)

            this.settingsReloadTimer = setTimeout(() => {
                this.reload()
                this.settingsReloadTimer = null
            }, 800)
        },
        async changeGroupNotifications(value) {
            const previousValue = this.groupNotifications

            try {
                this.groupNotificationsLoading = true
                this.$store.commit('user/SET_USER', {
                    group_notifications: value
                })

                await this.$http.patch('/users/update_profile/', {
                    group_notifications: value
                })
                notySyncChannel.groupNotifications(value)
            } catch(error) {
                this.$store.commit('user/SET_USER', {
                    group_notifications: previousValue
                })
                errorHandler({error})
            } finally {
                this.groupNotificationsLoading = false
            }
        },
        toggleGroupNotifications() {
            if (this.groupNotificationsLoading) return
            this.changeGroupNotifications(!this.groupNotifications)
        },
        onSyncMessage(msg) {
            if (!msg || msg.type !== 'group_notifications') return
            if (this.groupNotifications === !!msg.value) return

            this.$store.commit('user/SET_USER', {
                group_notifications: !!msg.value
            })
        },
        openCategoryOrderModal() {
            this.editableCategories = this.categories.map(category => ({ ...category }))
            this.categoryOrderModalVisible = true
        },
        closeCategoryOrderModal() {
            if (this.categoryOrderSaving) return
            this.categoryOrderModalVisible = false
            this.categoryOrderDragging = false
        },
        async saveCategoryOrder() {
            const orderedCodes = this.editableCategories.map(category => category.code).filter(Boolean)

            try {
                this.categoryOrderSaving = true
                await this.$http.put('/notifications/settings/update_category_order/', {
                    categories: orderedCodes
                })
                this.$store.commit('notifications/SET_NOTIFICATION_CATEGORIES', [...this.editableCategories])
                this.categoryOrderModalVisible = false
                this.$nextTick(() => this.updateCategoryArrows())
            } catch(error) {
                errorHandler({ error })
            } finally {
                this.categoryOrderSaving = false
            }
        },
        onCategoryWrapperEnter() {
            this.isCategoryWrapperHover = true
            this.$nextTick(() => this.updateCategoryArrows())
        },
        onCategoryWrapperLeave() {
            this.isCategoryWrapperHover = false
            this.stopHoverScroll()
        },
        onCategoriesScroll() {
            this.updateCategoryArrows()
        },
        getCategoryScrollEl() {
            return this.$refs.categoryChips
        },
        updateCategoryArrows() {
            const el = this.getCategoryScrollEl()
            if (!el || this.isMobile || this.activeTab !== 'notifications') {
                this.canScrollLeft = false
                this.canScrollRight = false
                return
            }

            const max = el.scrollWidth - el.clientWidth
            if (max <= 0) {
                this.canScrollLeft = false
                this.canScrollRight = false
                return
            }

            const left = el.scrollLeft
            const eps = 1

            this.canScrollLeft = left > eps
            this.canScrollRight = left < max - eps
        },
        startHoverScroll(dir) {
            if (this.isMobile || this.activeTab !== 'notifications') return
            if (!this.isCategoryWrapperHover) return

            const el = this.getCategoryScrollEl()
            if (!el) return

            this.stopHoverScroll()
            this.categoryHoverScrollDir = dir

            const step = 8
            const tick = 16

            this.categoryHoverScrollTimer = setInterval(() => {
                if (!this.isCategoryWrapperHover) {
                    this.stopHoverScroll()
                    return
                }

                const max = el.scrollWidth - el.clientWidth
                if (max <= 0) {
                    this.updateCategoryArrows()
                    this.stopHoverScroll()
                    return
                }

                let next = el.scrollLeft
                if (this.categoryHoverScrollDir === 'left') next = next - step
                if (this.categoryHoverScrollDir === 'right') next = next + step

                if (next < 0) next = 0
                if (next > max) next = max

                el.scrollLeft = next
                this.updateCategoryArrows()

                if (next === 0 || next === max) this.stopHoverScroll()
            }, tick)
        },
        stopHoverScroll() {
            if (this.categoryHoverScrollTimer) {
                clearInterval(this.categoryHoverScrollTimer)
                this.categoryHoverScrollTimer = null
            }
            this.categoryHoverScrollDir = null
        },
        scrollCategoryToStart(code) {
            const container = this.getCategoryScrollEl()
            const refEl = this.$refs['categoryItem_' + code]
            const el = Array.isArray(refEl) ? refEl[0] : refEl
            if (!container || !el) return

            const offset = this.isMobile ? 15 : 30
            const containerRect = container.getBoundingClientRect()
            const elRect = el.$el ? el.$el.getBoundingClientRect() : el.getBoundingClientRect()

            const leftDelta = elRect.left - containerRect.left - offset
            const rightDelta = elRect.right - containerRect.right
            if (leftDelta >= 0 && rightDelta <= 0) return

            const targetLeft = container.scrollLeft + leftDelta
            if (typeof container.scrollTo === 'function') {
                container.scrollTo({ left: targetLeft, behavior: 'smooth' })
            } else {
                container.scrollLeft = targetLeft
            }

            this.$nextTick(() => this.updateCategoryArrows())
        },
        readAllNoty() {
            let payload = {}

            if (this.activeTab === 'mentions') {
                payload = { isMention: true }
            } else {
                const categoryCodes = this.selectedCategoryCodes
                payload = categoryCodes.length
                    ? { categoryCodes }
                    : {}
            }

            this.readAllNotyy(payload).then(() => {
                if (this.useGroupedNotifications && this.$refs.groupedList) {
                    this.$refs.groupedList.applyReadAll(payload)
                    return
                }

                if (this.$refs.defaultList)
                    this.$refs.defaultList.applyReadAll(payload)
            })
        },
        isSelectedCategory(code) {
            return this.selectedCategoryCodes.includes(code)
        },
        onTabChange(key) {
            this.tabSwitching = true
            this.activeTab = key
            this.$nextTick(() => {
                this.reload()
                this.tabSwitching = false
            })
        },
        toggleCategory(code) {
            if (this.activeTab !== 'notifications') return

            const hasCode = this.selectedCategoryCodes.includes(code)
            const nextCodes = hasCode
                ? this.selectedCategoryCodes.filter(item => item !== code)
                : this.selectedCategoryCodes.concat(code)
            this.$store.commit('notifications/SET_SELECTED_CATEGORY_CODES', nextCodes)
            this.$nextTick(() => {
                this.scrollCategoryToStart(code)
            })
        },
        clearCategories() {
            this.$store.commit('notifications/SET_SELECTED_CATEGORY_CODES', [])
        },
        getCategoryUnreadCount(code) {
            if (!code || !this.unreadByCategory) return 0
            return Number(this.unreadByCategory[code]) || 0
        },
        async handleMobileFocus() {
            if (!this.isMobile) return
            if (typeof document !== 'undefined' && document.visibilityState !== 'visible') return

            await this.hardReload({ scrollToTop: true })
        },
        async hardReload({ scrollToTop = false } = {}) {
            this.listRenderKey += 1
            await this.$nextTick()

            if (scrollToTop)
                this.$nextTick(() => this.scrollToTop())
        },
        async reload({ scrollToTop = false } = {}) {
            if (this.useGroupedNotifications) {
                if(this.$refs.groupedList)
                    await this.$refs.groupedList.reload()
                if (scrollToTop)
                    this.$nextTick(() => this.scrollToTop())
                return
            }

            if(this.$refs.defaultList)
                await this.$refs.defaultList.reload()

            if (scrollToTop)
                this.$nextTick(() => this.scrollToTop())
        }
    },
    mounted() {
        this.getCategories().catch(() => {})
        window.addEventListener('resize', this.updateCategoryArrows)
        this.$nextTick(() => this.updateCategoryArrows())
        if(this.isMobile) {
            window.addEventListener('focus', this.handleMobileFocus)
        }
        eventBus.$on(`update_filter_${this.model}`, ()=>{
            this.reload()
        })
        eventBus.$on('notifications_categories_refresh', this.scheduleRefreshCategories)
        eventBus.$on('notifications_list_reload', this.scheduleSettingsReload)
        this.notySyncUnsubscribe = notySyncChannel.subscribe(this.onSyncMessage)
    },
    beforeDestroy() {
        this.stopHoverScroll()
        window.removeEventListener('resize', this.updateCategoryArrows)
        window.removeEventListener('focus', this.handleMobileFocus)
        if (this.refreshCategoriesTimer)
            clearTimeout(this.refreshCategoriesTimer)
        if (this.settingsReloadTimer)
            clearTimeout(this.settingsReloadTimer)
        if (this.notySyncUnsubscribe)
            this.notySyncUnsubscribe()
        eventBus.$off(`update_filter_${this.model}`)
        eventBus.$off('notifications_categories_refresh', this.scheduleRefreshCategories)
        eventBus.$off('notifications_list_reload', this.scheduleSettingsReload)
    }
}
</script>

<style lang="scss" scoped>
.badge-fade-slide-enter-active, .badge-fade-slide-leave-active {
    transition: all 0.3s ease
}
.badge-fade-slide-enter, .badge-fade-slide-leave-to {
    transform: translateX(-8px);
    opacity: 0
}
.header_noty__filters{
    position: sticky;
    z-index: 30;
    top: 0px;
    background: var(--eBg);
    padding-bottom: 10px;
    padding-top: 0.5rem;
    gap: 12px;
}
.grouping_switch{
    flex-shrink: 0;
    cursor: pointer;
    user-select: none;
}
.notify_tabs{
    margin-bottom: 0;
    flex: 1;
    min-width: 280px;
    &_extra{
        display: flex;
        align-items: center;
        height: 100%;
        padding-left: 8px;
    }
    .mentions_icon{
        font-size: 17px;
        line-height: 17px;
    }
    &::v-deep{
        .ant-tabs-bar.ant-tabs-top-bar{
            margin-bottom: 0px;
            .ant-tabs-extra-content{
                display: flex;
                align-items: center;
            }
            .ant-tabs-nav-container{
                padding-left: 0px;
                padding-right: 0px;
            }
        }
    }
}
.category_filter_head{
    display: flex;
    align-items: center;
    justify-content: space-between;
    font-weight: 500;
    margin-bottom: 8px;
    min-height: 24px;
}
.category_order_settings_btn{
    flex-shrink: 0;
}
.category_chips_wrapper{
    position: relative;
}
.category_chips{
    display: flex;
    align-items: center;
    flex-wrap: nowrap;
    gap: 5px;
    overflow-x: auto;
    padding-bottom: 4px;
    -ms-overflow-style: none;
    scrollbar-width: none;
    -webkit-overflow-scrolling: touch;
    min-height: 38px;
    &::-webkit-scrollbar{
        display: none;
    }
}
.category_chip{
    flex-shrink: 0;
    min-height: 32px;
    max-height: 32px;
}
.category_order_list{
    display: flex;
    flex-direction: column;
    gap: 8px;
}
.category_order_item{
    display: flex;
    align-items: center;
    gap: 8px;
    min-height: 36px;
}
.category_order_handle{
    flex-shrink: 0;
    cursor: move;
}
.category_order_chip{
    flex: 1;
    min-width: 0;
    min-height: 32px;
    max-height: 32px;
    padding: 0 12px;
    border-radius: 4px;
    background: var(--aColor, #eef3ff);
    color: var(--primary, #2f6fed);
    font-weight: 500;
}
.ghost{
    opacity: .45;
}
.scroll_arrow{
    position: absolute;
    z-index: 2;
    top: 50%;
    transform: translateY(-50%);
    &::v-deep .ant-btn{
        display: flex;
        align-items: center;
        justify-content: center;
    }
    &.left{
        left: 0;
    }
    &.right{
        right: 0;
    }
}
.slide-right-fade-enter-active,
.slide-right-fade-leave-active {
    transition: all .2s ease;
}
.slide-right-fade-enter,
.slide-right-fade-leave-to {
    opacity: 0;
    transform: translateX(10px);
}
.title {
    font-weight: 300;
    font-size: 24px;
}

.mob-text-lg {
    font-size: 1.4rem;
    line-height: 1.5;
}
</style>

<style lang="scss">
.category-order-modal-mobile{
    .ant-modal{
        width: 100vw !important;
        max-width: 100vw !important;
        margin: 0 !important;
        padding-bottom: 0 !important;
        top: 0 !important;
    }
    .ant-modal-content{
        width: 100vw;
        min-height: 100vh;
        border-radius: 0;
        display: flex;
        flex-direction: column;
    }
    .ant-modal-body{
        flex: 1;
        overflow-y: auto;
    }
}
</style>
