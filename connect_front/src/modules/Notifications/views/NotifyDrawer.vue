<template>
    <DrawerTemplate
        :placement="isMobile ? 'bottom' : 'right'"
        :zIndex="drawerZIndex"
        :width="drawerWidth"
        class="notify_drawer"
        bodyStyle="padding-top:0px;"
        destroyOnClose
        v-model="visible"
        @afterVisibleChange="afterVisibleChange"
        @close="visible = false">
        <template #title>
            <div class="drawer_title">
                {{ $t('noty.notificationList') }}
            </div>
        </template>
        <template #rightHeader>
            <TGLink />
            <div class="notify_settings_wrap">
                <a-button 
                    type="ui"
                    shape="circle"
                    ghost
                    class="settings_btn_animate"
                    v-tippy
                    :content="$t('noty.setting')"
                    flaticon
                    icon="fi-rr-settings"
                    @click="openSetting()" />
                <div
                    v-if="showNotificationTooltip"
                    class="notify_settings_tooltip"
                    @click="handleNotificationTooltipClick">
                    <button
                        type="button"
                        class="notify_settings_tooltip__close"
                        aria-label="Close"
                        @click.stop="closeNotificationTooltip">
                        <i class="fi fi-rr-cross-small"></i>
                    </button>
                    <div class="notify_settings_tooltip__text">
                        {{ $t('noty.browserPushTooltip') }}
                    </div>
                </div>
            </div>
        </template>
        <List />
        <template v-if="!isMobile">
            <transition name="slide-up-fade">
                <div 
                    v-if="backTopTopVisible"
                    class="back_top">
                    <a-button
                        shape="circle"
                        flaticon
                        size="large"
                        icon="fi-rr-angle-small-up"
                        @click="parentTopScroll()" />
                </div>
            </transition>
            <div class="drawer_dummy" />
        </template>
        <SettingDrawer ref="settingDrawer" />
        <template v-if="isMobile" #footer>
            <a-button type="ui" ghost block @click="visible = false">
                {{ $t('close') }}
            </a-button>
        </template>
    </DrawerTemplate>
</template>

<script>
import axios from '@/config/axios'
import { mapActions } from 'vuex'
import { getBrowserPushStatus } from '@/utils/webPush'

const NOTIFICATION_TOOLTIP_SYNC_KEY = 'notification_push_tooltip_sync'

export default {
    name: "NotifyDrawer",
    components: {
        List: () => import('./List.vue'),
        DrawerTemplate: () => import('@/components/DrawerTemplate.vue'),
        TGLink: () => import('./TGLink.vue'),
        SettingDrawer: () => import('./SettingDrawer.vue')
    },
    computed: {
        isMobile() {
            return this.$store.state.isMobile
        },
        windowWidth() {
            return this.$store.state.windowWidth
        },
        user() {
            return this.$store.state.user.user || {}
        },
        drawerZIndex() {
            return this.$store.state.notifications.drawerZIndex
        },
        drawerWidth() {
            if(this.windowWidth > 1200 && !this.isMobile)
                return 1200
            else {
                return '100%'
            }
        },
        visible: {
            get() {
                return this.$store.state.notifications.visible
            },
            set(val) {
                this.$store.commit('notifications/SET_DRAWER_VISIBLE', val)
            }
        },
        showNotificationTooltip() {
            return this.visible
                && this.browserPushStatus.supported
                && !this.browserPushStatus.enabled
                && this.user?.chat_ai_tooltip?.notification === false
        }
    },
    data() {
        return{
            scrollListener: null,
            scrollParent: null,
            backTopTopVisible: false,
            browserPushStatus: {
                supported: false,
                enabled: false
            },
            notificationTooltipUpdating: false
        }
    },
    methods: {
        ...mapActions({
            getCategories: 'notifications/getCategories'
        }),
        async refreshBrowserPushStatus() {
            try {
                this.browserPushStatus = await getBrowserPushStatus()
            } catch (error) {
                console.log(error, 'refreshBrowserPushStatus')
            }
        },
        syncNotificationTooltipState() {
            try {
                localStorage.setItem(NOTIFICATION_TOOLTIP_SYNC_KEY, JSON.stringify({
                    value: true,
                    ts: Date.now()
                }))
            } catch (error) {
                console.error('Failed to sync notification tooltip across tabs', error)
            }
        },
        handleTooltipStorageSync(event) {
            if (event.key !== NOTIFICATION_TOOLTIP_SYNC_KEY || !event.newValue) {
                return
            }

            try {
                const payload = JSON.parse(event.newValue)

                if (payload?.value !== true) {
                    return
                }

                const chatAiTooltip = {
                    ...(this.user?.chat_ai_tooltip || {}),
                    notification: true
                }

                this.$store.commit('user/SET_USER', {
                    chat_ai_tooltip: chatAiTooltip
                })
            } catch (error) {
                console.error('Failed to apply notification tooltip sync', error)
            }
        },
        async markNotificationTooltipAsSeen() {
            if (this.notificationTooltipUpdating || this.user?.chat_ai_tooltip?.notification === true) {
                return
            }

            this.notificationTooltipUpdating = true

            const chatAiTooltip = {
                ...(this.user?.chat_ai_tooltip || {}),
                notification: true
            }

            this.$store.commit('user/SET_USER', {
                chat_ai_tooltip: chatAiTooltip
            })
            this.syncNotificationTooltipState()

            try {
                await axios.patch('/users/chat_ai_tooltip/', {
                    notification: true
                })
            } catch (error) {
                console.error('Failed to update chat_ai_tooltip.notification', error)
            } finally {
                this.notificationTooltipUpdating = false
            }
        },
        async handleNotificationTooltipClick() {
            await this.openSetting()
        },
        async closeNotificationTooltip() {
            await this.markNotificationTooltipAsSeen()
        },
        async openSetting() {
            await this.markNotificationTooltipAsSeen()
            this.$nextTick(() => {
                if(this.$refs.settingDrawer)
                    this.$refs.settingDrawer.openDrawer()
            })
        },
        attachScrollListener() {
            const sp = this.getScrollParent(this.$el) || window
            this.scrollParent = sp
            if (!sp) return

            this.scrollListener = () => {
                this.handleScroll()
            }

            try {
                sp.addEventListener('scroll', this.scrollListener, { passive: true })
            } catch (e) {
                sp.addEventListener('scroll', this.scrollListener)
            }

            this.handleScroll()
        },
        detachScrollListener() {
            if (!this.scrollParent || !this.scrollListener) return

            try {
                this.scrollParent.removeEventListener('scroll', this.scrollListener, { passive: true })
            } catch (e) {
                this.scrollParent.removeEventListener('scroll', this.scrollListener)
            }

            this.scrollListener = null
        },
        handleScroll() {
            const sp = this.scrollParent || this.getScrollParent(this.$el) || window

            if (sp === window) {
                const rect = this.$el.getBoundingClientRect()
                const scrolled = window.pageYOffset || document.documentElement.scrollTop || 0
                const topOffset = scrolled + rect.top
                this.backTopTopVisible = scrolled - topOffset > 100
            } else {
                this.backTopTopVisible = (sp.scrollTop || 0) > 100
            }
        },
        getScrollParent(startElm = this.$el) {
            const el = startElm && (startElm.$el ? startElm.$el : startElm)
            if (!el) return window
            let wrap = null
            if (typeof el.closest === 'function') {
                wrap = el.closest('.drawer_wrap, .ant-drawer-wrapper, .ant-drawer') || document.querySelector('.drawer_wrap') || document.querySelector('.ant-drawer-wrapper')
            }
            if (wrap) {
                const inner = wrap.querySelector('.drawer_body') || wrap.querySelector('.ant-drawer-body .drawer_body') || wrap.querySelector('.ant-drawer-body')
                if (inner) return inner
            }
            let elm = el
            while (elm) {
                if (elm === window || elm === document) return window
                if (elm.nodeType === 1) {
                    const cls = (elm.className || '')
                    if (cls.indexOf('drawer_body') > -1 || cls.indexOf('ant-drawer-body') > -1) return elm
                    try {
                        const style = getComputedStyle(elm)
                        if (['scroll', 'auto'].indexOf(style.overflowY) > -1) return elm
                    } catch (e) {}
                    if (elm.tagName === 'BODY') return window
                }
                elm = elm.parentNode
            }
            return window
        },
        parentTopScroll() {
            const bodyRef = this.$refs.bodyRef
            const targetEl = bodyRef && bodyRef.$el ? bodyRef.$el : bodyRef || this.$el
            const candidate = this.scrollParent || this.getScrollParent(targetEl)
            let scrollEl = candidate
            if (candidate && candidate.nodeType === 1) {
                const inner = candidate.querySelector && (candidate.querySelector('.drawer_body') || candidate.querySelector('.ant-drawer-body .drawer_body'))
                if (inner) scrollEl = inner
            }
            if (!scrollEl) return
            if (scrollEl === window) {
                window.scrollTo({ top: 0, behavior: 'smooth' })
                return
            }
            if (typeof scrollEl.scrollTo === 'function') {
                scrollEl.scrollTo({ top: 0, behavior: 'smooth' })
                return
            }
            scrollEl.scrollTop = 0
        },
        afterVisibleChange(vis) {
            if(vis) {
                this.$nextTick(() => {
                    this.attachScrollListener()
                })
                this.getCategories().catch(() => {})
                this.refreshBrowserPushStatus()
                this.$store.commit('notifications/SET_DRAWER_Z_INDEX', 5000)
                this.$notification.destroy()
            } else {
                this.detachScrollListener()
                this.$store.commit('notifications/SET_ACTIVE_TAB', 'notifications')
                this.$store.commit('notifications/CLEAR_LIST')
            }
        }
    },
    mounted() {
        window.addEventListener('storage', this.handleTooltipStorageSync)
    },
    beforeDestroy() {
        window.removeEventListener('storage', this.handleTooltipStorageSync)
        this.detachScrollListener()
        this.$store.commit('notifications/SET_ACTIVE_TAB', 'notifications')
        this.$store.commit('notifications/CLEAR_LIST')
    }
}
</script>

<style lang="scss" scoped>
.drawer_dummy{
    min-height: 30px;
}
.notify_settings_wrap{
    position: relative;
}
.notify_settings_tooltip{
    position: absolute;
    top: calc(100% + 10px);
    right: -6px;
    z-index: 20;
    width: 240px;
    padding: 14px 34px 14px 14px;
    border: 1px solid #d9e1ff;
    border-radius: 16px;
    background: #ffffff;
    box-shadow: 0 12px 30px rgba(66, 85, 141, 0.16);
    cursor: pointer;

    &::before {
        content: '';
        position: absolute;
        top: -7px;
        right: 18px;
        width: 14px;
        height: 14px;
        background: #ffffff;
        border-top: 1px solid #d9e1ff;
        border-left: 1px solid #d9e1ff;
        transform: rotate(45deg);
    }

    &__text{
        position: relative;
        z-index: 1;
        color: #2f3a58;
        font-size: 13px;
        line-height: 18px;
        font-weight: 500;
    }

    &__close{
        position: absolute;
        top: 8px;
        right: 8px;
        z-index: 1;
        display: flex;
        align-items: center;
        justify-content: center;
        width: 20px;
        height: 20px;
        padding: 0;
        border: 0;
        background: transparent;
        color: #8f97b3;
        cursor: pointer;
    }
}
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
.back_top{
    position: sticky;
    bottom: 40px;
    height: 0px;
    z-index: 100;
    display: flex;
    justify-content: flex-end;
    &::v-deep{
        .ant-btn{
            --alpha: 1;
            backdrop-filter: blur(calc(7px * (2 - var(--alpha))));
            background: rgba(255, 255, 255, 0.8);
            box-shadow: 0 0 0 1px #e6e6e8;
            border: initial!important;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 22px;
        }
    }
}
</style>
