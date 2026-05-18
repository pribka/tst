<template>
    <component
        :is="wrapperWidget"
        v-model="visible"
        @afterVisibleChange="afterVisibleChange"
        @close="visible = false">
        <template v-if="showHeader" #title>
            <div class="flex items-center gap-5">
                <div class="title">{{ $t('workplan.drawer_title') }}</div>
                <component 
                    v-if="!isMobile" 
                    :is="rangeInputComp" 
                    :storeKey="storeKey" 
                    :reloadAllData="reloadAllData" />
            </div>
        </template>
        <template #body>
            <div ref="bodyRef" class="body_work">
                <div v-if="useInject && isMobile" class="mb-2">
                    <component
                        :is="rangeInputComp" 
                        :storeKey="storeKey" 
                        :reloadAllData="reloadAllData" />
                </div>
                <DayStat v-if="!isMobile" :storeKey="storeKey" />
                <a-row 
                    :gutter="isMobile ? 0 : 30" 
                    :style="isMobile && 'min-height: 900px;'"
                    :type="isMobile ? null : 'flex'">
                    <a-col 
                        :sm="24" 
                        :lg="isMobile ? 24 : 16"
                        :xl="isMobile ? 24 : 17"
                        :xxl="isMobile ? 24 : 17"
                        class="body_col">
                        <Segmented 
                            v-if="isMobile"
                            block
                            :bgInvert="useInject"
                            class="mb-2"
                            v-model="viewType" 
                            :options="listType" />
                        <FilterBlock 
                            v-if="isMobile"
                            :storeKey="storeKey"
                            :useInject="useInject"
                            :clearFilter="clearFilter"
                            :userChange="userChange"
                            :popupContainer="popupContainer"
                            :filterChange="filterChange" />
                        <template v-if="showList">
                            <AIIntent v-if="isMobile" :storeKey="storeKey" :reloadOnKeyData="reloadOnKeyData" />

                            <TabsHeader :storeKey="storeKey" :useInject="useInject" />

                            <div v-show="activeTab === 'tasks'">
                                <TaskList ref="taskList" :storeKey="storeKey" :popupContainer="popupContainer" :filterChange="filterChange" :reloadTaskData="reloadTaskData" :useInject="useInject" />
                            </div>
                            <div v-show="activeTab === 'events'">
                                <EventList ref="eventList" :storeKey="storeKey" :useInject="useInject" />
                            </div>
                            <div v-show="activeTab === 'meetings'">
                                <MeetingList ref="meetingList" :storeKey="storeKey" :useInject="useInject" />
                            </div>
                            <div v-if="canShowTicketsTab" v-show="activeTab === 'tickets'">
                                <TicketsList
                                    ref="ticketsList"
                                    :storeKey="storeKey"
                                    :useInject="useInject"
                                    :isActiveTab="activeTab === 'tickets'" />
                            </div>
                            <div v-show="activeTab === 'pulse'">
                                <DayPulse
                                    :storeKey="storeKey"
                                    :useInject="useInject" />
                            </div>
                        </template>
                        <template v-if="showResults">
                            <AIIntent :storeKey="storeKey" :reloadOnKeyData="reloadOnKeyData" />
                            <component :is="dayResultsComponent" :storeKey="storeKey" :useInject="useInject" />
                        </template>
                        <div class="drawer_dummy" />
                    </a-col>
                    <a-col 
                        v-if="!isMobile"
                        :sm="24" 
                        :lg="8"
                        :xl="7"
                        :xxl="7">
                        <StatisticsForDay :storeKey="storeKey" />
                        <FilterBlock 
                            v-if="!isMobile"
                            vertical
                            :useInject="useInject"
                            :clearFilter="clearFilter"
                            :storeKey="storeKey"
                            :userChange="userChange"
                            :popupContainer="popupContainer"
                            :filterChange="filterChange" />
                        <AIIntent :storeKey="storeKey" :reloadOnKeyData="reloadOnKeyData" />
                    </a-col>
                </a-row>
                <div v-if="!useInject && isMobile" class="float_picker">
                    <component
                        :is="rangeInputComp" 
                        :storeKey="storeKey" 
                        :reloadAllData="reloadAllData" />
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
                <transition v-if="!useInject && !isMobile" name="slide-up-fade">
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
        </template>
    </component>
</template>

<script>
import { clearTabQuery } from '@/utils/routerUtils.js'
import { getById } from '@/utils/cacheDb'
import { mapState } from 'vuex'

let filterTimer;
const tabsDbName = 'workplan_tabs_positions'
const tabsDbPrefix = 'tabs'

export default {
    props: {
        storeKey: {
            type: String,
            required: true
        },
        showHeader: {
            type: Boolean,
            default: true
        },
        useInject: {
            type: Boolean,
            default: false
        }
    },
    components: {
        DayPulse: () => import('./widgets/DayPulse/index.vue'),
        TaskList: () => import('./widgets/TaskList/index.vue'),
        TicketsList: () => import('./widgets/TicketsList/index.vue'),
        EventList: () => import('./widgets/EventList/index.vue'),
        MeetingList: () => import('./widgets/MeetingList/index.vue'),
        Segmented: () => import('@apps/UIModules/Segmented'),
        AIIntent: () => import('./AIIntent/index.vue'),
        FilterBlock: () => import('./FilterBlock.vue'),
        DayStat: () => import('./widgets/DayStat.vue'),
        StatisticsForDay: () => import('./widgets/StatisticsForDay.vue'),
        TabsHeader: () => import('./TabsHeader.vue')
    },
    computed: {
        ...mapState({ 
            windowWidth: state => state.windowWidth,
            isMobile: state => state.isMobile
        }),
        userId() {
            return this.$store.state.user?.user?.id || null
        },
        tabsStorageId() {
            if(!this.userId) return null
            return `${tabsDbPrefix}:${this.userId}:${this.storeKey}`
        },
        wrapperWidget() {
            if(this.useInject)
                return () => import('./InjectWrapper.vue')
            return () => import('./DrawerWrapper.vue')
        },
        mainDate() {
            return this.$store.state.workplan.mainDate?.[this.storeKey].join('') || ''
        },
        activeTab: {
            get() {
                return this.$store.state.workplan.activeTab?.[this.storeKey] || 'tasks'
            },
            set(value) {
                this.$store.commit('workplan/CHANGE_ACTIVE_TAB', {
                    value,
                    storeKey: this.storeKey
                })
            }
        },
        hasHelpDeskTariff() {
            const sections = this.$store.state.user?.user?.tariff_section_codes || []
            return Array.isArray(sections) && sections.includes('help_desk')
        },
        canShowTicketsTab() {
            return this.hasHelpDeskTariff
        },
        rangeInputComp() {
            if(this.isMobile)
                return () => import("./MobileRangeInput.vue")
            return () => import("./RangeInput.vue")
        },
        showList() {
            if(this.isMobile)
                return this.viewType === 'list'
            return true
        },
        showResults() {
            if(this.isMobile)
                return this.viewType === 'results'
            return false
        },
        dayResultsComponent() {
            if(this.isMobile && this.viewType === 'results')
                return () => import('./widgets/DayResults.vue')
            return () => import('./widgets/DayResults.vue')
        },
        project: {
            get() {
                return this.$store.state.workplan.project?.[this.storeKey] || null
            },
            set(value) {
                this.$store.commit('workplan/CHANGE_FIELD', {
                    value,
                    field: 'project',
                    storeKey: this.storeKey
                })
            }
        },
        workgroup: {
            get() {
                return this.$store.state.workplan.workgroup?.[this.storeKey] || null
            },
            set(value) {
                this.$store.commit('workplan/CHANGE_FIELD', {
                    value,
                    field: 'workgroup',
                    storeKey: this.storeKey
                })
            }
        },
        user: {
            get() {
                return this.$store.state.workplan.user?.[this.storeKey] || null
            },
            set(value) {
                this.$store.commit('workplan/CHANGE_FIELD', {
                    value,
                    field: 'user',
                    storeKey: this.storeKey
                })
            }
        },
        viewType: {
            get() {
                return this.$store.state.workplan.viewType?.[this.storeKey] || 'list'
            },
            set(value) {
                this.$store.commit('workplan/CHANGE_FIELD', {
                    value,
                    field: 'viewType',
                    storeKey: this.storeKey
                })
            }
        }
    },
    data() {
        return {
            scrollListener: null,
            scrollParent: null,
            visible: false,
            defaultUserSelectId: 'workplan',
            backTopTopVisible: false,
            ensureActiveTabRequestId: 0,
            listType: [
                {
                    key: 'list',
                    title: this.$t('workplan.list')
                },
                {
                    key: 'results',
                    title: this.$t('workplan.day_results')
                }
            ]
        }
    },
    methods: {
        popupContainer() {
            return this.$refs.bodyRef
        },
        clearFilter() {
            this.user = []
            this.project = null
            this.workgroup = null
            clearTimeout(filterTimer)
            this.reloadAllData()
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
        userChange() {
            this.$store.commit('workplan/CHANGE_FIELD', {
                value: null,
                field: 'role',
                storeKey: this.storeKey
            })
            this.filterChange()
        },
        filterChange() {
            clearTimeout(filterTimer)
            filterTimer = setTimeout(() => {
                this.reloadAllData()
            }, 600)
        },
        reloadOnKeyData(update) {
            this.$nextTick(() => {
                if(update.task && this.$refs.taskList)
                    this.$refs.taskList.reloadList()
                if(update.event && this.$refs.eventList)
                    this.$refs.eventList.reloadList()
                if(update.meeting && this.$refs.meetingList)
                    this.$refs.meetingList.reloadList()
                if(update.ticket && this.canShowTicketsTab && this.$refs.ticketsList)
                    this.$refs.ticketsList.reloadList()

                if(update.task || update.event || update.meeting || update.ticket)
                    this.$store.dispatch('workplan/getDayStatistics', { storeKey: this.storeKey })
                this.$store.dispatch('workplan/getWorkHoursSummaryReportSetting', { storeKey: this.storeKey })
            })
        },
        reloadAllData() {
            this.$nextTick(() => {
                if(this.$refs.taskList)
                    this.$refs.taskList.reloadList()
                if(this.$refs.eventList)
                    this.$refs.eventList.reloadList()
                if(this.$refs.meetingList)
                    this.$refs.meetingList.reloadList()
                if(this.canShowTicketsTab && this.$refs.ticketsList)
                    this.$refs.ticketsList.reloadList()
                this.$store.dispatch('workplan/getTabsCount', { storeKey: this.storeKey })
                this.$store.dispatch('workplan/getDayStatistics', { storeKey: this.storeKey })
                this.$store.dispatch('workplan/getWorkHoursSummaryReportSetting', { storeKey: this.storeKey })
                this.$store.dispatch('workplan/getAIIntents', { storeKey: this.storeKey })
                this.parentTopScroll()
            })
        },
        reloadTaskData() {
            clearTimeout(filterTimer)
            filterTimer = setTimeout(() => {
                this.$nextTick(() => {
                    if(this.$refs.taskList)
                        this.$refs.taskList.reloadList()
                    this.$store.dispatch('workplan/getTabsCount', { storeKey: this.storeKey })
                    this.$store.dispatch('workplan/getDayStatistics', { storeKey: this.storeKey })
                    this.$store.dispatch('workplan/getWorkHoursSummaryReportSetting', { storeKey: this.storeKey })
                    this.$store.dispatch('workplan/getAIIntents', { storeKey: this.storeKey })
                    this.parentTopScroll()
                })
            }, 400)
        },
        afterVisibleChange(vis) {
            if(vis) {
                this.reloadAllData()
                this.ensureActiveTab({ force: true })
                this.$nextTick(() => {
                    this.attachScrollListener()
                })
            } else {
                this.detachScrollListener()
                this.closeDrawer()
            }
        },
        closeDrawer() {
            this.scrollParent = null
            const next = clearTabQuery({
                ...this.$route.query,
                my_plan: undefined,
                wtab: undefined
            })
            this.$router.replace({
                name: this.$route.name,
                params: this.$route.params,
                query: next
            })
        },
        getDefaultTabOrder() {
            const order = ['tasks', 'events', 'meetings', 'pulse']

            if(this.canShowTicketsTab)
                order.splice(3, 0, 'tickets')

            return order
        },
        buildTabOrder(order = []) {
            const defaultOrder = this.getDefaultTabOrder()
            const allowedMap = defaultOrder.reduce((acc, key) => {
                acc[key] = true
                return acc
            }, {})
            const result = []
            const safeOrder = Array.isArray(order) ? order : []

            safeOrder.forEach(key => {
                if(allowedMap[key] && !result.includes(key)) {
                    result.push(key)
                }
            })

            defaultOrder.forEach(key => {
                if(!result.includes(key)) {
                    result.push(key)
                }
            })

            return result
        },
        async getSavedTabOrder() {
            const fallbackOrder = this.getDefaultTabOrder()

            if(!this.tabsStorageId)
                return fallbackOrder

            try {
                const dbData = await getById({
                    id: this.tabsStorageId,
                    databaseName: tabsDbName
                })
                return this.buildTabOrder(dbData?.value)
            } catch(e) {
                return fallbackOrder
            }
        },
        async ensureActiveTab({ force = false } = {}) {
            const requestId = ++this.ensureActiveTabRequestId

            if(!this.userId) {
                return
            }

            const order = await this.getSavedTabOrder()
            if(requestId !== this.ensureActiveTabRequestId) return

            const firstAvailableTab = order[0] || 'tasks'
            const routeTab = this.useInject ? null : this.$route.query?.wtab
            const tabFromRoute = routeTab && order.includes(routeTab) ? routeTab : null
            const targetTab = tabFromRoute || firstAvailableTab
            const currentRawActiveTab = this.$store.state.workplan.activeTab?.[this.storeKey]
            const isCurrentValid = currentRawActiveTab && order.includes(currentRawActiveTab)

            if((force || !isCurrentValid || Boolean(tabFromRoute)) && currentRawActiveTab !== targetTab) {
                this.activeTab = targetTab
            }
        }
    },
    watch: {
        '$route.query'(val) {
            if(this.useInject) return
            if(val.my_plan) {
                this.visible = true
                this.ensureActiveTab({ force: true })
            }
        },
        '$route.query.wtab'() {
            if(this.useInject) return
            if(this.$route.query?.my_plan)
                this.ensureActiveTab({ force: true })
        },
        canShowTicketsTab(val) {
            if(!val && this.activeTab === 'tickets') {
                this.ensureActiveTab({ force: true })
                return
            }
            this.ensureActiveTab()
        },
        userId() {
            this.ensureActiveTab({ force: true })
        },
        storeKey() {
            this.ensureActiveTab({ force: true })
        }
    },
    mounted() {
        this.ensureActiveTab({ force: true })
        if(this.useInject) {
            this.$nextTick(() => {
                this.$store.dispatch('workplan/getTabsCount', { storeKey: this.storeKey })
                this.$store.dispatch('workplan/getDayStatistics', { storeKey: this.storeKey })
                this.$store.dispatch('workplan/getWorkHoursSummaryReportSetting', { storeKey: this.storeKey })
                this.$store.dispatch('workplan/getAIIntents', { storeKey: this.storeKey })
                this.attachScrollListener()
            })
            return
        }
        if(this.$route.query?.my_plan)
            this.visible = true
    },
    beforeDestroy() {
        this.detachScrollListener()
    }
}
</script>

<style lang="scss" scoped>
.body_work{
    &::v-deep{
        .tab_search{
            .ant-input{
                &.ant-input-lg{
                    height: 38px;
                    border-color: #fff;
                    box-shadow: initial!important;
                    font-size: 14px;
                    &::placeholder{
                        font-size: 14px;
                        color: #888888;
                    }
                }
            }
        }
    }
}
.drawer_dummy{
    min-height: 50px;
}
.float_picker{
    position: sticky;
    bottom: 20px;
    height: 0px;
    z-index: 105;
    display: flex;
    align-items: center;
    justify-content: space-between;
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
.body_col{
    &::v-deep{
        .list_card{
            &:not(:last-child){
                margin-bottom: 30px;
            }
            .list_card__label{
                font-size: 18px;
                font-weight: 600;
                color: #000;
                margin-bottom: 10px;
                @media (min-width: 768px) {
                    margin-bottom: 15px;
                }
            }
        }
    }
}
</style>
