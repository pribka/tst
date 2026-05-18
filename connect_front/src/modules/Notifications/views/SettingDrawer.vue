<template>
    <DrawerTemplate
        :width="drawerWidth"
        class="notify_drawer"
        bodyStyle="padding-top:0px;"
        destroyOnClose
        v-model="visible"
        @afterVisibleChange="afterVisibleChange"
        @close="visible = false">
        <template #title>
            <div class="drawer_title flex items-center">
                {{ $t('noty.setting') }}
            </div>
        </template>

        <div ref="bodyRef">
            <ListView labelDark class="list_view">
                <ListViewItem>
                    <div
                        class="flex items-center justify-between event_item cursor-pointer select-none"
                        @click="toggleProfileSetting('hide_read_notifications')">
                        <div class="mr-2">{{ $t('noty.hideReadNotifications') }}</div>
                        <a-switch
                            :checked="hideReadNotifications"
                            :loading="profileSettingsLoading.hide_read_notifications"
                            size="small" />
                    </div>
                    <div
                        class="flex items-center justify-between event_item cursor-pointer select-none"
                        @click="toggleProfileSetting('send_to_tg_always')">
                        <div class="mr-2">{{ $t('noty.sendToTgAlways') }}</div>
                        <a-switch
                            :checked="sendToTgAlways"
                            :loading="profileSettingsLoading.send_to_tg_always"
                            size="small" />
                    </div>
                    <div
                        class="flex items-center justify-between event_item cursor-pointer select-none"
                        @click="toggleSoundSetting">
                        <div class="mr-2">{{ $t('noty.soundNotifications') }}</div>
                        <a-switch :checked="soundEnabled" size="small" />
                    </div>
                    <div
                        v-if="showPushSetting"
                        class="flex items-start justify-between event_item cursor-pointer select-none"
                        @click="toggleBrowserPushSetting">
                        <div class="mr-3">
                            <div>{{ $t('noty.browserPushNotifications') }}</div>
                            <div v-if="pushHint" class="push_hint">
                                {{ pushHint }}
                            </div>
                            <div v-if="showPwaInstallHint" class="push_hint push_install_hint">
                                <div>{{ $t('noty.browserPushPwaHint') }}</div>
                                <a-button
                                    v-if="deferredPrompt"
                                    type="primary"
                                    size="small"
                                    class="push_install_btn"
                                    @click.stop="installPwaApp">
                                    {{ $t('install') }}
                                </a-button>
                            </div>
                        </div>
                        <a-switch
                            :checked="browserPushEnabled"
                            :loading="browserPushLoading"
                            :disabled="browserPushDisabled"
                            size="small" />
                    </div>
                </ListViewItem>
                <template v-if="!loading">
                    <ListViewItem v-for="item in list" :key="item.code">
                        <div
                            class="group_header flex items-center justify-between cursor-pointer select-none"
                            @click="toggleCategorySetting(item.code, item.enabled)">
                            <div class="item_label mb-0">
                                {{ item.name }}
                            </div>
                            <a-switch
                                :checked="item.enabled"
                                :loading="!!categorySettingsLoading[item.code]"
                                size="small" />
                        </div>
                        <div 
                            v-for="event in item.events" 
                            :key="event.code"
                            class="flex items-center justify-between event_item cursor-pointer select-none"
                            @click="toggleSetting(event.code, event.enabled, item.code)">
                            <div class="mr-2">{{ event.name }}</div>
                            <a-switch
                                :checked="event.enabled"
                                :disabled="!item.enabled"
                                size="small" />
                        </div>
                    </ListViewItem>
                </template>
            </ListView>
            <ListView v-if="loading" labelDark class="list_view card_loading mt-2">
                <ListViewItem>
                    <a-skeleton class="skeleton_title" active :paragraph="{ rows: 0 }" />
                    <div v-for="(item, index) in sceletonItems" :key="index" class="flex items-center justify-between event_item event_sceleton cursor-pointer select-none">
                        <a-skeleton active :paragraph="{ rows: 0 }" :title="{width: '100%'}" :style="`width: ${item.width}%`" />
                        <a-skeleton active :paragraph="{ rows: 0 }" :title="{width: '100%'}" style="width: 30px" />
                    </div>
                </ListViewItem>
            </ListView>

            <div class="drawer_dummy" />

            <div v-if="isMobile" class="float_picker">
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
            </div>
            <transition v-if="!isMobile" name="slide-up-fade">
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
        </div>

        <template #footer>
            <a-button 
                type="ui_ghost" 
                block 
                @click="visible = false">
                {{ $t('close') }}
            </a-button>
        </template>
    </DrawerTemplate>
</template>

<script>
import { errorHandler } from '@/utils/index.js'
import { getNotificationSoundEnabled, setNotificationSoundEnabled } from '@/modules/Notifications/soundSettings'
import eventBus from '@/utils/eventBus'
import { getBrowserPushStatus, registerBrowserPush, unregisterBrowserPush } from '@/utils/webPush'
let timer;
export default {
    components: {
        DrawerTemplate: () => import('@/components/DrawerTemplate.vue'),
    },
    computed: {
        isMobile() {
            return this.$store.state.isMobile
        },
        windowWidth() {
            return this.$store.state.windowWidth
        },
        user() {
            return this.$store.state.user.user
        },
        hideReadNotifications() {
            return !!this.user?.hide_read_notifications
        },
        sendToTgAlways() {
            return !!this.user?.send_to_tg_always
        },
        deferredPrompt() {
            return this.$store.state.deferredPrompt
        },
        showPushSetting() {
            return this.browserPushStatus.supported || this.browserPushStatus.isIos
        },
        browserPushEnabled() {
            return !!this.browserPushStatus.hasSubscription && !!this.browserPushStatus.backendSubscribed
        },
        browserPushDisabled() {
            return this.browserPushLoading || this.browserPushStatus.needsPwaInstall
        },
        pushHint() {
            if (this.browserPushStatus.needsPwaInstall) {
                return this.$t('noty.browserPushIosHint')
            }
            
            return ''
        },
        showPwaInstallHint() {
            return !this.browserPushStatus.isIos
                && !this.browserPushStatus.isStandalonePwa
        },
        drawerWidth() {
            if(this.windowWidth > 600 && !this.isMobile)
                return 600
            else {
                return '100%'
            }
        },
    },
    data() {
        return {
            scrollListener: null,
            scrollParent: null,
            backTopTopVisible: false,
            visible: false,
            list: [],
            updatedItems: [],
            soundEnabled: true,
            browserPushLoading: false,
            browserPushStatus: {
                supported: false,
                permission: 'default',
                isIos: false,
                isStandalonePwa: false,
                canPrompt: false,
                hasSubscription: false,
                enabled: false,
                backendChecked: false,
                backendSubscribed: false,
                backendStatus: null,
                auth: null,
                needsPwaInstall: false
            },
            categorySettingsLoading: {},
            profileSettingsLoading: {
                hide_read_notifications: false,
                send_to_tg_always: false
            },
            loading: false,
            sceletonItems: []
        }
    },
    methods: {
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
        async toggleSoundSetting() {
            const enabled = !this.soundEnabled
            this.soundEnabled = enabled

            try {
                const saved = await setNotificationSoundEnabled({
                    userId: this.user?.id,
                    enabled
                })
                if(!saved) throw new Error('failed to save sound setting')
            } catch(error) {
                this.soundEnabled = !enabled
                errorHandler({ error, show: false })
            }
        },
        async changeProfileSetting(key, value) {
            const previousValue = !!this.user?.[key]

            try {
                this.$set(this.profileSettingsLoading, key, true)
                this.$store.commit('user/SET_USER', {
                    [key]: value
                })

                await this.$http.patch('/users/update_profile/', {
                    [key]: value
                })
                if (key === 'hide_read_notifications')
                    eventBus.$emit('notifications_list_reload')
            } catch(error) {
                this.$store.commit('user/SET_USER', {
                    [key]: previousValue
                })
                errorHandler({ error })
            } finally {
                this.$set(this.profileSettingsLoading, key, false)
            }
        },
        toggleProfileSetting(key) {
            if (this.profileSettingsLoading[key]) return
            this.changeProfileSetting(key, !this.user?.[key])
        },
        async loadSoundSetting() {
            this.soundEnabled = await getNotificationSoundEnabled(this.user?.id)
        },
        async refreshBrowserPushStatus() {
            try {
                this.browserPushStatus = await getBrowserPushStatus()
            } catch (error) {
                console.log(error, 'refreshBrowserPushStatus')
            }
        },
        async toggleBrowserPushSetting() {
            if (this.browserPushDisabled) return

            try {
                this.browserPushLoading = true

                if (this.browserPushEnabled) {
                    await unregisterBrowserPush({ unsubscribe: true })
                } else {
                    await registerBrowserPush({ requestPermission: true })
                }

                await this.refreshBrowserPushStatus()
            } catch (error) {
                errorHandler({ error, show: false })
                await this.refreshBrowserPushStatus()
            } finally {
                this.browserPushLoading = false
            }
        },
        async installPwaApp() {
            if (!this.deferredPrompt) return

            try {
                await this.deferredPrompt.prompt()
                await this.deferredPrompt.userChoice
            } catch (error) {
                console.log(error, 'installPwaApp')
            } finally {
                this.$store.commit('SET_PWA_POPUP', null)
                await this.refreshBrowserPushStatus()
            }
        },
        async toggleCategorySetting(code, enabled) {
            const index = this.list.findIndex(item => item.code === code)
            if (index < 0 || this.categorySettingsLoading[code]) return

            const previousValue = !!this.list[index].enabled
            const is_enabled = !enabled

            this.$set(this.categorySettingsLoading, code, true)
            this.$set(this.list[index], 'enabled', is_enabled)

            try {
                await this.$http.put('/notifications/settings/update_category/', {
                    category: code,
                    is_enabled
                })
                eventBus.$emit('notifications_categories_refresh')
            } catch (error) {
                this.$set(this.list[index], 'enabled', previousValue)
                errorHandler({ error })
            } finally {
                this.$set(this.categorySettingsLoading, code, false)
            }
        },
        toggleSetting(code, enabled, parentCode){
            clearTimeout(timer)

            const index = this.list.findIndex(f => f.code === parentCode)
            if(this.list[index]) {
                if (!this.list[index].enabled) return

                const cIndex = this.list[index].events.findIndex(f => f.code === code)
                if(this.list[index].events[cIndex]) {
                    const is_enabled = !enabled
                    this.$set(this.list[index].events[cIndex], 'enabled', is_enabled)
                    this.updatedItems.push({
                        event_type_code: code,
                        is_enabled
                    })
                }
            }

            timer = setTimeout(() => {
                this.updatedEvents()
            }, 800)
        },
        async updatedEvents() {
            if(!this.updatedItems.length) return

            const payload = [...this.updatedItems]
            this.updatedItems = []

            try {
                await Promise.all(
                    payload.map(item =>
                        this.$http.put('/notifications/settings/update_event/', item)
                    )
                )
                eventBus.$emit('notifications_categories_refresh')
            } catch(error) {
                errorHandler({ error })
            }
        },
        openDrawer() {
            this.visible = true
        },
        generateSkeletons() {
            if(!this.list.length && !this.loading) {
                this.sceletonItems = Array.from({ length: 30 }).map(() => {
                    return {
                        width: Math.floor(Math.random() * 41) + 40
                    }
                })
            }
        },
        afterVisibleChange(vis) {
            if(vis) {
                this.getSettings()
                this.loadSoundSetting()
                this.refreshBrowserPushStatus()
                this.$nextTick(() => {
                    this.attachScrollListener()
                })
            } else {
                this.detachScrollListener()
                this.backTopTopVisible = false
                this.updatedItems = []
            }
        },
        async getSettings() {
            if(!this.list.length && !this.loading) {
                try {
                    this.loading = true
                    const { data } = await this.$http.get('/notifications/settings/')
                    if(data?.length)
                        this.list = data
                } catch(error) {
                    errorHandler({error, show: false})
                } finally {
                    this.loading = false
                }
            }
        }
    },
    mounted() {
        this.generateSkeletons()
    },
    beforeDestroy() {
        this.detachScrollListener()
    }
}
</script>

<style lang="scss" scoped>
.float_picker{
    position: sticky;
    bottom: 20px;
    height: 0px;
    z-index: 105;
    display: flex;
    align-items: center;
    justify-content: flex-end;
    .back_top{
        position: relative;
        display: block;
        bottom: 20px;
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
    bottom: 20px;
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
.drawer_dummy{
    min-height: 40px;
}
.skeleton_title{
    &::v-deep{
        .ant-skeleton-paragraph{
            display: none;
        }
        .ant-skeleton-title{
            margin-top: 0px;
            margin-bottom: 20px;
        }
    }
}
.list_view{
    &::v-deep{
        .item_label{
            font-weight: 600;
            font-size: 18px;
            margin-bottom: 20px;
            position: sticky;
            top: 0;
            z-index: 10;
            background: #fff;
            margin-bottom: 0px!important;
            padding-bottom: 5px;
        }
        .list_view__item{
            &:not(:last-child){
                border-bottom: 1px solid var(--borderColor);
                padding-bottom: 15px;
            }
        }
    }
}
.event_item{
    &:not(:last-child){
        margin-bottom: 10px;
    }
}
.group_header{
    margin-bottom: 16px;
}
.push_hint{
    color: #8c8c8c;
    font-size: 12px;
    line-height: 1.4;
    margin-top: 4px;
}
.push_install_hint{
    display: flex;
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
}
.push_install_btn{
    min-width: 96px;
}
.event_sceleton{
    &::v-deep{
        .ant-skeleton-paragraph{
            display: none;
        }
        .ant-skeleton-title{
            margin-top: 0px;
            margin-bottom: 0px;
        }
    }
    &.event_item{
        &:not(:last-child){
            margin-bottom: 15px;
        }
    }
}
</style>
