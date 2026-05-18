<template>
    <div class="list_card">
        <div class="mb-3 flex items-center gap-2">
            <a-input 
                v-model="search"
                :placeholder="$t('workplan.search')" 
                size="large" 
                class="tab_search"
                :class="useInject && 'bg_invert'"
                @change="changeSearch()">
                <template #suffix>
                    <transition name="fade-scale" mode="out-in">
                        <a-button 
                            v-if="search.length"
                            type="ui_ghost" 
                            size="small"
                            flaticon
                            shape="circle"
                            icon="fi-rr-cross-small"
                            @click="clearSearch()" />
                        <i v-else class="fi fi-rr-search mr-1" />
                    </transition>
                </template>
            </a-input>
            <div>
                <a-button v-if="isMobile" type="primary" style="min-width: auto;" shape="circle" size="large" flaticon icon="fi-rr-plus" @click="addTask()" />
                <a-button v-else type="primary" style="min-width: auto;" size="large" flaticon icon="fi-rr-plus" @click="addTask()">
                    {{ $t('workplan.add_task') }}
                </a-button>
            </div>
        </div>
        <transition name="banner-slide-down" appear>
            <component
                :is="taskWatchlistBannerComponent"
                v-if="canShowTaskWatchlist && taskWatchlistBannerComponent"
                class="mb-3"
                :overdue="taskWatchlistCount.overdue"
                :stalled="taskWatchlistCount.stalled"
                :startDate="taskWatchlistCount.start_date"
                :endDate="taskWatchlistCount.end_date"
                @action="openTaskWatchlist" />
        </transition>
        <component
            :is="taskWatchlistDrawerComponent"
            v-if="taskWatchlistCountLoaded && taskWatchlistDrawerComponent"
            v-model="taskWatchlistVisible"
            :storeKey="storeKey"
            :taskWatchlistCount="taskWatchlistCount"
            @reload-count="getTaskWatchlistCount" />
        <div class="mb-3 flex">
            <div :class="isMobile && 'mob_scroll'">
                <div :style="isMobile && 'padding-left:15px;padding-right:15px;'">
                    <Segmented 
                        v-model="role" 
                        deselectable
                        :bgInvert="useInject"
                        :options="roleList"
                        @change="reloadTaskData" />
                </div>
            </div>
        </div>
        <div v-if="focusList.results && focusList.results.length" class="task_block_item">
            <h2 class="task_block_title" style="color: #eb580e;">
                <i class="fi fi-rr-flag-alt mr-2" />
                {{ $t('workplan.focus_day') }}
            </h2>
            <Card 
                v-for="task in focusList.results" 
                :key="`focus_${task.id}`" 
                :storeKey="storeKey"
                :useInject="useInject"
                :hideReloadList="hideReloadList"
                listType="taskFocusList"
                :popupContainer="popupContainer"
                :task="task" />
            <a-button 
                v-if="focusList.results.length && focusList.next" 
                :loading="focusList.loading" 
                type="ui"
                ghost
                block
                @click="nextLoading('focus')">
                {{ $t('workplan.load_more') }}
            </a-button>
        </div>

        <div v-if="list.results && list.results.length" class="task_block_item">
            <h2 class="task_block_title">
                <a-badge status="processing" class="mr-1" />
                {{ $t('workplan.activity_today') }}
            </h2>
            <template v-if="list.page === 1 && list.loading">
                <CardLoading v-for="i in 3" :key="i" :useInject="useInject" />
            </template>
            <Card 
                v-for="task in list.results" 
                :key="task.id" 
                :storeKey="storeKey"
                :hideReloadList="hideReloadList"
                :useInject="useInject"
                listType="taskList"
                :popupContainer="popupContainer"
                :task="task" />
            <a-button 
                v-if="list.results.length && list.next" 
                :loading="list.loading" 
                type="ui"
                ghost
                block
                @click="nextLoading('activity')">
                {{ $t('workplan.load_more') }}
            </a-button>
        </div>

        <div class="task_block_item">
            <h2 class="task_block_title">
                <a-badge status="default" class="mr-1" />
                {{ $t('workplan.others') }}
            </h2>
            <a-empty v-if="otherList.empty" :description="$t('workplan.no_tasks')" />
            <template v-if="otherList.page === 1 && otherList.loading">
                <CardLoading v-for="i in 5" :key="`other_${i}`" :useInject="useInject" />
            </template>
            <Card 
                v-for="task in otherList.results" 
                :key="`other_${task.id}`" 
                :storeKey="storeKey"
                :hideReloadList="hideReloadList"
                :useInject="useInject"
                listType="taskOtherList"
                :popupContainer="popupContainer"
                :task="task" />
            <a-button 
                v-if="otherList.results.length && otherList.next" 
                :loading="otherList.loading" 
                type="ui"
                ghost
                block
                @click="nextLoading('other')">
                {{ $t('workplan.load_more') }}
            </a-button>
        </div>
    </div>
</template>

<script>
import { errorHandler } from '@/utils/index.js'
import eventBus from "@/utils/eventBus"
const listType = 'taskList'
const listFocusType = 'taskFocusList'
const listOtherType = 'taskOtherList'
let searchTimer;
let pinnedTimer;
let timerSyncTimer;
let watchlistRefreshTimer;
export default {
    props: {
        storeKey: {
            type: String,
            required: true
        },
        filterChange: {
            type: Function,
            default: () => {}
        },
        reloadTaskData: {
            type: Function,
            default: () => {}
        },
        popupContainer: {
            type: Function,
            default: () => document.body
        },
        useInject: {
            type: Boolean,
            default: false
        }
    },
    components: {
        Card: () => import('./Card.vue'),
        CardLoading: () => import('./CardLoading.vue'),
        Segmented: () => import('@apps/UIModules/Segmented')
    },
    computed: {
        list() {
            return this.$store.state.workplan[listType]?.[this.storeKey] || null
        },
        focusList() {
            return this.$store.state.workplan[listFocusType]?.[this.storeKey] || null
        },
        otherList() {
            return this.$store.state.workplan[listOtherType]?.[this.storeKey] || null
        },
        search: {
            get() {
                return this.$store.state.workplan.taskSearch?.[this.storeKey].search || ""
            },
            set(value) {
                this.$store.commit('workplan/UPDATE_SEARCH_VALUE', {
                    value: value, 
                    storeKey: this.storeKey
                })
            }
        },
        isMobile() { 
            return this.$store.state.isMobile
        },
        role: {
            get() {
                return this.$store.state.workplan.role?.[this.storeKey] || null
            },
            set(value) {
                this.$store.commit('workplan/CHANGE_FIELD', {
                    value,
                    field: 'role',
                    storeKey: this.storeKey
                })
            }
        },
        hasTaskWatchlistCounts() {
            return this.taskWatchlistCount.overdue > 0 || this.taskWatchlistCount.stalled > 0
        },
        canShowTaskWatchlist() {
            return this.showTaskWatchlist && this.taskWatchlistCountLoaded && this.hasTaskWatchlistCounts
        }
    },
    data() {
        return {
            showTaskWatchlist: false,
            taskWatchlistBannerComponent: null,
            taskWatchlistDrawerComponent: null,
            taskWatchlistVisible: false,
            taskWatchlistCountLoaded: false,
            taskWatchlistCount: {
                overdue: 0,
                stalled: 0,
                start_date: null,
                end_date: null,
                roles: {}
            },
            roleList: [
                {
                    key: 'is_executor',
                    title: this.$t('workplan.role_do')
                },
                {
                    key: 'is_owner',
                    title: this.$t('workplan.role_delegate')
                },
                {
                    key: 'is_visor',
                    title: this.$t('workplan.role_watch')
                },
                {
                    key: 'is_participant',
                    title: this.$t('workplan.role_member')
                }
            ]
        }
    },
    methods: {
        async fetchShowTaskWatchlist() {
            const { data } = await this.$http.get('/tasks/task/show_task_watchlist/')

            return !!data?.show_task_watchlist
        },
        async loadTaskWatchlistBanner() {
            try {
                const showTaskWatchlist = await this.fetchShowTaskWatchlist()

                this.showTaskWatchlist = false
                this.taskWatchlistCountLoaded = false

                if(!showTaskWatchlist)
                    return

                this.taskWatchlistBannerComponent = () => import('./TaskWatchlistBanner.vue')
                this.taskWatchlistDrawerComponent = () => import('./TaskWatchlistDrawer.vue')
                const countLoaded = await this.getTaskWatchlistCount()

                if(!countLoaded)
                    return

                this.taskWatchlistCountLoaded = true
                this.showTaskWatchlist = showTaskWatchlist
            } catch(error) {
                errorHandler({ error, show: false })
            }
        },
        async getTaskWatchlistCount() {
            try {
                const { data } = await this.$http.get('/tasks/task/task_watchlist_count/')

                this.taskWatchlistCount = {
                    overdue: Number(data?.overdue) || 0,
                    stalled: Number(data?.stalled) || 0,
                    start_date: data?.start_date || null,
                    end_date: data?.end_date || null,
                    roles: data?.roles || {}
                }

                return true
            } catch(error) {
                errorHandler({ error, show: false })
            }

            return false
        },
        addTask() {
            this.$store.commit('task/SET_PAGE_NAME', {
                pageName: 'page_list_task_task.TaskModel'
            })
            if(this.isMobile) {
                this.$store.dispatch('task/sidebarOpen', {
                    task_type: 'task'
                })
            } else {
                eventBus.$emit('add_task_modal', {
                    task_type: 'task'
                })
            }
        },
        clearSearch() {
            this.search = ""
            clearTimeout(searchTimer)
            this.reloadList()
        },
        changeSearch() {
            clearTimeout(searchTimer)
            searchTimer = setTimeout(() => {
                this.reloadList()
            }, 700)
        },
        roleChange(role) {
            this.role = role
            this.filterChange()
        },
        openTaskWatchlist() {
            if(!this.canShowTaskWatchlist || !this.taskWatchlistDrawerComponent)
                return

            this.taskWatchlistVisible = true
        },
        refreshTaskWatchlistBanner() {
            clearTimeout(watchlistRefreshTimer)
            watchlistRefreshTimer = setTimeout(async () => {
                try {
                    const [showTaskWatchlist, countLoaded] = await Promise.all([
                        this.fetchShowTaskWatchlist(),
                        this.getTaskWatchlistCount()
                    ])

                    this.showTaskWatchlist = showTaskWatchlist
                    this.taskWatchlistCountLoaded = countLoaded
                } catch(error) {
                    errorHandler({ error, show: false })
                }
            }, 800)
        },
        reloadList() {
            this.$store.commit('workplan/CLEAR_LIST', {
                storeKey: this.storeKey,
                list: listType
            })
            this.$store.commit('workplan/CLEAR_LIST', {
                storeKey: this.storeKey,
                list: listFocusType
            })
            this.$store.commit('workplan/CLEAR_LIST', {
                storeKey: this.storeKey,
                list: listOtherType
            })
            this.getList()
            this.getFocusList()
            this.getOtherList()
            this.$store.dispatch('workplan/getTabsCount', { storeKey: this.storeKey })
        },
        hideReloadList() {
            clearTimeout(pinnedTimer)
            pinnedTimer = setTimeout(() => {
                this.getList(true, false)
                this.getFocusList(true, false)
                this.getOtherList(true, false)
                this.$store.dispatch('workplan/getTabsCount', { storeKey: this.storeKey })
            }, 800)
        },
        nextLoading(group = 'activity') {
            let listGroup = listType
            if(group === 'focus') {
                listGroup = listFocusType
                this.$store.commit('workplan/CHANGE_LIST_FIELD', {
                    field: 'page', 
                    value: this.focusList.page + 1, 
                    storeKey: this.storeKey, 
                    list: listGroup
                })
            }
            if(group === 'other') {
                listGroup = listOtherType
                this.$store.commit('workplan/CHANGE_LIST_FIELD', {
                    field: 'page', 
                    value: this.otherList.page + 1, 
                    storeKey: this.storeKey, 
                    list: listGroup
                })
            }
            if(group === 'activity') {
                this.getList()
                this.$store.commit('workplan/CHANGE_LIST_FIELD', {
                    field: 'page', 
                    value: this.list.page + 1, 
                    storeKey: this.storeKey, 
                    list: listGroup
                })
            }
            if(group === 'focus')
                this.getFocusList()
            if(group === 'other')
                this.getOtherList()
        },
        async getList(reload = false, loading = true) {
            try {
                await this.$store.dispatch('workplan/getTaskList', { storeKey: this.storeKey, list: listType, group: 'activity', reload, loading })
            } catch(error) {
                errorHandler({error, show: false})
            }
        },
        async getFocusList(reload = false, loading = true) {
            try {
                await this.$store.dispatch('workplan/getTaskList', { storeKey: this.storeKey, list: listFocusType, group: 'pinned', reload, loading })
            } catch(error) {
                errorHandler({error, show: false})
            }
        },
        async getOtherList(reload = false, loading = true) {
            try {
                await this.$store.dispatch('workplan/getTaskList', { storeKey: this.storeKey, list: listOtherType, group: 'other', reload, loading })
            } catch(error) {
                errorHandler({error, show: false})
            }
        },
        handleGlobalTimerSync(payload = {}) {
            clearTimeout(timerSyncTimer)
            timerSyncTimer = setTimeout(() => {
                this.getList(true, false)
                this.getFocusList(true, false)
                this.getOtherList(true, false)
                if(payload?.action === 'stop_timer') {
                    this.$store.dispatch('workplan/getDayStatistics', { storeKey: this.storeKey })
                }
            }, 200)
        }
    },
    sockets: {
        task_update({data}) {
            if(data) {
                this.$store.dispatch('workplan/updateItem', {
                    item: data,
                    list: 'taskList'
                })
            }
        }
    },
    mounted() {
        this.$socket.client.emit("tasks") 
        this.loadTaskWatchlistBanner()

        if(!this.list.results?.length && !this.list.empty)
            this.getList()
        if(!this.focusList.results?.length && !this.focusList.empty)
            this.getFocusList()
        if(!this.otherList.results?.length && !this.otherList.empty)
            this.getOtherList()
        if(!this.list.results?.length && this.list.empty)
            this.reloadList()
        eventBus.$on('update_task_handler', () => {
            this.reloadList()
            this.refreshTaskWatchlistBanner()
        })
        eventBus.$on('global_timer_sync_required', this.handleGlobalTimerSync)
    },
    beforeDestroy() {
        eventBus.$off('update_task_handler')
        eventBus.$off('global_timer_sync_required', this.handleGlobalTimerSync)
        if(!this.useInject) return
        this.$store.commit('workplan/CLEAR_LIST', {
            storeKey: this.storeKey,
            list: listType
        })
        this.$store.commit('workplan/CLEAR_LIST', {
            storeKey: this.storeKey,
            list: listFocusType
        })
        this.$store.commit('workplan/CLEAR_LIST', {
            storeKey: this.storeKey,
            list: listOtherType
        })
    }
}
</script>

<style lang="scss" scoped>
.task_block_item{
    &:not(:last-child){
        margin-bottom: 15px;
    }
}
.fade-scale-enter-active,
.fade-scale-leave-active {
    transition: opacity .15s ease, transform .15s ease
}
.fade-scale-enter,
.fade-scale-leave-to {
    opacity: 0;
    transform: scale(.55)
}
.banner-slide-down-enter-active,
.banner-slide-down-leave-active {
    transition: opacity .3s ease, transform .3s ease;
}
.banner-slide-down-enter,
.banner-slide-down-leave-to {
    opacity: 0;
    transform: translateY(-18px);
}
.task_block_title{
    font-weight: 600;
    font-size: 18px;
    margin-bottom: 10px;
    display: flex;
    align-items: center;
}
.mob_scroll{
    display: -webkit-box;
    margin-bottom: 0;
    overflow-x: scroll;
    width: 100%;
    margin-left: -15px;
    margin-right: -15px;
    -ms-overflow-style: none;
    scrollbar-width: none;
    -webkit-overflow-scrolling: touch;
    &::v-deep{
        .segmented{
            flex-wrap: initial;
        }
    }
}
.tab_search{
    &.bg_invert{
        &::v-deep{
            .ant-input{
                background: #f7f9fc;
            }
        }
    }
}
</style>
