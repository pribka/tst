<template>
    <div class="tabs_header" :class="!isMobile && 'desktop_tabs'" :style="isMobile ? 'gap: 20px;' : ''">
        <draggable
            v-if="!isMobile"
            v-model="desktopTabs"
            class="tabs_draggable"
            draggable=".drag_item"
            handle=".drag_handle"
            ghost-class="ghost"
            @start="onDragStart"
            @end="onDragEnd">
            <div
                v-for="tab in desktopTabs"
                :key="tab.key"
                class="tabs_item drag_item"
                :class="activeTab === tab.key && 'active'"
                @click="setActiveTab(tab.key)">
                <template v-if="tab.key === 'pulse'">
                    <span>{{ tab.labelKey ? $t(tab.labelKey) : tab.label }}</span>
                </template>
                <template v-else>
                    <span>{{ $t(tab.labelKey) }}</span>
                </template>
                <transition name="badge-fade-slide">
                    <a-badge
                        v-if="getTabCount(tab)"
                        class="ml-2"
                        :number-style="badgeNumberStyle"
                        :count="getTabCount(tab)" />
                </transition>
                <div
                    class="actions"
                    :style="dragging && 'opacity: 0;'">
                    <div class="actions__item drag_handle" @click.stop>
                        <i class="fi fi-rr-arrows-alt"></i>
                    </div>
                </div>
            </div>
        </draggable>

        <template v-else>
            <div
                v-for="tab in mobileTabs"
                :key="tab.key"
                class="tabs_item"
                :class="activeTab === tab.key && 'active'"
                @click="setActiveTab(tab.key)">
                <template v-if="tab.key === 'pulse'">
                    <span>{{ tab.labelKey ? $t(tab.labelKey) : tab.label }}</span>
                </template>
                <template v-else>
                    <span>{{ $t(tab.labelKey) }}</span>
                </template>
                <transition name="badge-fade-slide">
                    <a-badge
                        v-if="getTabCount(tab)"
                        class="ml-2"
                        :number-style="badgeNumberStyle"
                        :count="getTabCount(tab)" />
                </transition>
            </div>
        </template>
    </div>
</template>

<script>
import { getById, setData, updateById } from '@/utils/cacheDb'

const tabsDbName = 'workplan_tabs_positions'
const tabsDbPrefix = 'tabs'

export default {
    components: {
        draggable: () => import('vuedraggable').then(m => m.default || m)
    },
    props: {
        storeKey: {
            type: String,
            required: true
        },
        useInject: {
            type: Boolean,
            default: false
        }
    },
    data() {
        return {
            dragging: false,
            desktopTabs: []
        }
    },
    computed: {
        isMobile() { 
            return this.$store.state.isMobile
        },
        userId() {
            return this.$store.state.user?.user?.id || null
        },
        tabsStorageId() {
            if(!this.userId) return null
            return `${tabsDbPrefix}:${this.userId}:${this.storeKey}`
        },
        tabsCount() {
            return this.$store.state.workplan.tabsCount?.[this.storeKey] || {}
        },
        badgeNumberStyle() {
            return {
                backgroundColor: '#e8ecfa',
                color: '#4777FF',
                boxShadow: 'initial',
                fontWeight: '400'
            }
        },
        hasHelpDeskTariff() {
            const sections = this.$store.state.user?.user?.tariff_section_codes || []
            return Array.isArray(sections) && sections.includes('help_desk')
        },
        canShowTicketsTab() {
            return this.hasHelpDeskTariff
        },
        mobileTabs() {
            return this.getDefaultTabs()
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
        }
    },
    created() {
        this.initDesktopTabs()
    },
    watch: {
        canShowTicketsTab() {
            this.rebuildDesktopTabs({ persist: false })
        },
        userId() {
            this.initDesktopTabs()
        },
        storeKey() {
            this.initDesktopTabs()
        }
    },
    methods: {
        setActiveTab(value) {
            if(!value || this.activeTab === value) return

            this.activeTab = value

            if(this.useInject) return
            if(!this.$route.query?.my_plan) return

            this.$router.replace({
                name: this.$route.name,
                params: this.$route.params,
                query: {
                    ...this.$route.query,
                    wtab: value
                }
            })
        },
        getDefaultTabs() {
            const tabs = [
                { key: 'tasks', labelKey: 'workplan.tab_tasks', countKey: 'tasks' },
                { key: 'events', labelKey: 'workplan.tab_events', countKey: 'events' },
                { key: 'meetings', labelKey: 'workplan.tab_meetings', countKey: 'meetings' },
                { key: 'pulse', labelKey: 'workplan.tab_pulse' }
            ]

            if(this.canShowTicketsTab) {
                tabs.splice(3, 0, {
                    key: 'tickets',
                    labelKey: 'workplan.tab_tickets',
                    countKey: 'helpdesk'
                })
            }

            return tabs
        },
        buildTabsByOrder(order = []) {
            const defaultTabs = this.getDefaultTabs()
            const map = defaultTabs.reduce((acc, item) => {
                acc[item.key] = item
                return acc
            }, {})

            const result = []
            const safeOrder = Array.isArray(order) ? order : []

            safeOrder.forEach(key => {
                if(map[key]) {
                    result.push(map[key])
                    delete map[key]
                }
            })

            Object.keys(map).forEach(key => {
                result.push(map[key])
            })

            return result
        },
        async initDesktopTabs() {
            const fallback = this.getDefaultTabs()

            if(this.isMobile) {
                this.desktopTabs = fallback
                return
            }

            if(!this.tabsStorageId) {
                this.desktopTabs = fallback
                return
            }

            try {
                const dbData = await getById({
                    id: this.tabsStorageId,
                    databaseName: tabsDbName
                })
                const savedOrder = Array.isArray(dbData?.value) ? dbData.value : []
                this.desktopTabs = this.buildTabsByOrder(savedOrder)
            } catch(e) {
                this.desktopTabs = fallback
            }
        },
        rebuildDesktopTabs({ persist = false } = {}) {
            const currentOrder = this.desktopTabs.map(item => item.key)
            this.desktopTabs = this.buildTabsByOrder(currentOrder)

            if(persist) {
                this.saveDesktopTabsOrder()
            }
        },
        getTabCount(tab) {
            if(!tab?.countKey) return null
            return this.tabsCount?.[tab.countKey] || null
        },
        onDragStart() {
            this.dragging = true
        },
        onDragEnd() {
            this.dragging = false
            this.saveDesktopTabsOrder()
        },
        async saveDesktopTabsOrder() {
            if(this.isMobile || !this.tabsStorageId) return

            const value = this.desktopTabs.map(item => item.key)

            try {
                const dbData = await getById({
                    id: this.tabsStorageId,
                    databaseName: tabsDbName
                })

                if(dbData) {
                    await updateById({
                        id: this.tabsStorageId,
                        value,
                        databaseName: tabsDbName
                    })
                } else {
                    await setData({
                        data: {
                            id: this.tabsStorageId,
                            value
                        },
                        databaseName: tabsDbName
                    })
                }
            } catch(e) {
                console.log(e)
            }
        }
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
.tabs_header{
    border-bottom: 1px solid var(--borderColor);
    display: flex;
    align-items: center;
    user-select: none;
    margin-bottom: 15px;
    overflow-x: auto;
    overflow-y: hidden;
    white-space: nowrap;
    -webkit-overflow-scrolling: touch;
    scrollbar-width: thin;
    &.desktop_tabs{
        overflow-y: visible;
    }
    .tabs_draggable{
        display: flex;
        align-items: center;
        gap: 30px;
        width: max-content;
    }
    .tabs_item{
        flex: 0 0 auto;
        cursor: pointer;
        display: flex;
        align-items: center;
        position: relative;
        transition: all 0.3s cubic-bezier(0.645, 0.045, 0.355, 1);
        padding: 8px 0;
        color: #888888;
        border-bottom: 2px solid transparent;
        font-size: 14px;
        line-height: 1.5;
        &:hover{
            color: var(--text);
            z-index: 6;
        }
        &.active{
            color: var(--text);
            border-color: #FF9A01;
            text-shadow: 0 0 .25px var(--text);
        }
        .actions{
            position: absolute;
            display: flex;
            align-items: center;
            top: 0px;
            right: 0px;
            z-index: 5;
            opacity: 0;
            transition: all 0.3s cubic-bezier(0.645, 0.045, 0.355, 1);
            &__item{
                font-size: 8px;
                cursor: grab;
                background: var(--text);
                height: 13px;
                width: 20px;
                color: #ffffff;
                display: flex;
                align-items: center;
                justify-content: center;
                border-radius: 18px;
                &:active{
                    cursor: grabbing;
                }
                i{
                    transition: all 0.3s cubic-bezier(0.645, 0.045, 0.355, 1);
                }
                &:hover{
                    i{
                        opacity: 0.7;
                    }
                }
            }
        }
        &:hover{
            .actions{
                opacity: 1;
            }
        }
    }
}
</style>
