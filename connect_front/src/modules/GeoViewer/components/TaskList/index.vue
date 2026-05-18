<template>
    <div class="task_list overflow-y-scroll h-full">
        <div class="pb-3 top_actions">
            <div>
                <PageFilter 
                    class="w-full"
                    model="tasks.TaskModel"
                    :key="page_name"
                    size="large"
                    :excludeFields="['is_daily_filter', 'without_order_filter']"
                    :page_name="page_name" />
                <DropdownSort 
                    model="tasks.TaskModel"
                    :page_name="page_name" />
            </div>
        </div>
        <div class="list relative">
            <!-- <a-spin 
                :spinning="loading" 
                class="w-full"> -->
            <div 
                v-if="showEmpty" 
                class="pt-3">
                <a-empty description="Нет данных" />
            </div>
            <TaskCard 
                v-for="item in locatedTasks"
                :key="item.id"
                :ref="`log_card_${item.id}`"
                :id="`log_card_${item.id}`"
                :item="item"
                :onDropInTimer="onDropInTimer"
                :setRoutePoint="setRoutePoint"
                :mapHoverPoint="mapHoverPoint"
                :openTask="openTask"
                :hoverPoint="hoverPoint" />
            <infinite-loading 
                v-if="hasMapBorders"
                ref="infiniteLoading"
                @infinite="getTaskList"
                :identifier="infiniteId"
                :distance="10">
                <div 
                    slot="spinner"
                    class="flex items-center justify-center inf_spinner">
                    <a-spin />
                </div>
                <div slot="no-more"></div>
                <div slot="no-results"></div>
            </infinite-loading>
            <!-- </a-spin> -->
        </div>
    </div>
</template>

<script>
import TaskCard from './TaskCard.vue'
import { mapState } from 'vuex'
import PageFilter from '@/components/PageFilter'
import DropdownSort from './DropdownSort.vue'
import eventBus from '@/utils/eventBus'
import InfiniteLoading from 'vue-infinite-loading'

let dropTimer;
let timerId;
export default {
    components: {
        TaskCard,
        PageFilter,
        DropdownSort,
        InfiniteLoading
    },
    props: {
        openTask: {
            type: Function,
            default: () => {}
        },
        hoverPoint: {
            type: Function,
            default: () => {}
        },
        mapHoverPoint: {
            type: Object,
            default: () => null
        },
        setRoutePoint: {
            type: Function,
            default: () => {}
        },
        sOrders: {
            type: Object,
            default: () => null
        },
        scrollTop: {
            type: Function,
            default: () => {}
        }
    },
    computed: {
        ...mapState({
            locatedTasksNext: state => state.geoviewer.locatedTasksNext,
            locatedTasksPage: state => state.geoviewer.locatedTasksPage,
            locatedTasks: state => state.geoviewer.locatedTasks,
            mapBorders: state => state.geoviewer.mapBorders,

            logisticTask: state => state.geoviewer.logisticTask,
            listEdit: state => state.geoviewer.listEdit,
            taskOpen: state => state.geoviewer.taskOpen,
            taskListRequest: state => state.geoviewer.taskListRequest,
            loading: state => state.geoviewer.taskListLoader,
            config: state => state.geoviewer.config,
            filters: state => state.geoviewer.taskFilters,
            taskEmpty: state => state.geoviewer.taskEmpty,
        }),
        hasMapBorders() {
            const bordersKeys = Object.keys(this.mapBorders)
            return bordersKeys.length
        },
        currentNext() {
            return Boolean(this.locatedTasksNext)
        },
        nextPage() {
            const defaultPage = 1
            const currentPage = this.locatedTasksPage
            return currentPage ? (currentPage + 1) : defaultPage
        },
        showEmpty() {
            return !this.currentNext && !this.locatedTasks
        }
    },
    data() {
        return {
            saveLoading: false,
            page_name: 'page_list_located_task.TaskModel',

            locatedTasksLoading: false,
            infiniteId: new Date(),

        }
    },
    sockets: {
        task_update({data}) {
            if(data) {
                this.$store.commit('geoviewer/UPDATE_TASK_SOCKET', data)
            }
        }
    },
    methods: {
        async getTaskList($state) {
            
            ;("page", this.currentNext, this.page)
            if (!this.locatedTasksLoading && this.currentNext)
                try {
                    this.setLoadingState(true)

                    let params = {
                        ...this.mapBorders,
                        page_size: 5,
                        page: this.nextPage,
                    }
                    await this.$store.dispatch('geoviewer/getLocatedTask', { params })
                    
                    if(this.currentNext) {
                        $state.loaded()
                    } else {
                        this.checkAndSetShowEmpty()
                        $state.complete()
                    }

                } catch(e) {
                    console.log(e, 'getTaskList')
                } finally {
                    this.setLoadingState(false)
                }
            else {
                this.checkAndSetShowEmpty()
                $state.complete()
            }
        },
        getMapClientsCenter() {
            if(this.mapClientsShow) {
                clearTimeout(timer)
                if(this.mapClientRequest) {
                    this.mapClientRequest.cancel()
                    this.$store.commit('monitor/SET_MAP_CLIENT_REQUEST', null)
                }

                timer = setTimeout(() => {
                    this.$nextTick(async () => {
                        if(this.$refs['logist_map']?.mapObject) {
                            try {
                                const map = this.$refs['logist_map'].mapObject
                                const lat__gte = map.getBounds().getSouth()
                                const lat__lte = map.getBounds().getNorth()
                                const lon__gte = map.getBounds().getWest()
                                const lon__lte = map.getBounds().getEast()

                                await this.$store.dispatch('monitor/getMapClients', {
                                    lat__gte,
                                    lat__lte,
                                    lon__gte,
                                    lon__lte
                                })
                            } catch(e) {
                                console.log(e)
                            }
                        }
                    })
                }, 500)
            }
        },

        checkAndSetShowEmpty() {
            // if(this.currentTaskList && !this.currentTaskList.length) 
            //     this.showEmpty = true
            // else 
            //     this.showEmpty = false
        },
        reload() {
            this.$store.state.geoviewer.locatedTasks = []
            this.$store.state.geoviewer.locatedTasksNext = true
            this.$store.state.geoviewer.locatedTasksPage = 0
            this.$nextTick(()=>{
                if(this.$refs.infiniteLoading){
                    this.$refs.infiniteLoading.stateChanger.reset(); 
                }
            })

        },
        
        setLoadingState(isLoading) {
            this.locatedTasksLoading = isLoading
        },


        onDropInTimer(data) {
            if(timerId && timerId === data.id) {
                // this.$refs[`log_card_${data.id}`][0].getDeliveryPoints()
            } else {
                timerId = data.id
                clearTimeout(dropTimer)
                dropTimer = setTimeout(() => {
                    this.$refs[`log_card_${data.id}`][0].getDeliveryPoints()
                }, 700)
            }
        },
        checkboxHandler(e, key) {
            const value = e.target.checked

            this.$store.commit('monitor/SET_TASK_FILTER_BY_KEY', {
                value,
                key
            })

            eventBus.$emit(`send_include_fields_${this.page_name}`, {
                fields: {
                    is_daily_filter: {
                        active: this.filters.is_daily_filter ? true : false,
                        values: {
                            value: this.filters.is_daily_filter
                        }
                    },
                    without_order_filter: {
                        active: this.filters.without_order_filter ? true : false,
                        values: {
                            value: this.filters.without_order_filter
                        }
                    }
                },
                others: {
                    ...this.filters
                }
            })
        },
        checkTaskRequest() {
            if(this.taskListRequest) {
                this.taskListRequest.cancel()
                this.$store.commit('monitor/SET_TASK_LIST_REQUEST', null)
            }
        },
        setActive(data) {
            this.$store.commit('monitor/CLEAR_TASK_ALL_ROUTING')
            this.$store.commit('monitor/CLEAR_TASK_POINT_VISIBLE')
            this.$nextTick(() => {
                eventBus.$emit(`show_log_${data.id}`)
                const item = document.getElementById(`log_card_${data.id}`)
                if(item) {
                    item.scrollIntoView({block: "center", behavior: "smooth"})
                }
            })
            eventBus.$emit('routingReinit')
        },
        checkOpen(data) {
            if(this.logisticTask.length) {
                const find = this.logisticTask.find(f => f.id === data.id)
                if(find) {
                    eventBus.$emit('TOGGLE_TASK_DRAWER_logistic')
                    this.setActive(data)
                } else {
                    this.openTask(data)
                }
            }
        }
    },
    mounted() {
        eventBus.$on(`update_filter_tasks.TaskModel`, () => {
            this.reload()
        })
        eventBus.$on('MOVE_GEOTASK_MAP', () => {
            this.reload()
        })

        // eventBus.$on(`TASK_CREATED_logistic`, data => {
        //     this.$store.commit('monitor/CLEAR_TASK_POINT_VISIBLE')
        //     this.$store.commit('monitor/SET_TASK_EMPTY', false)
        //     this.checkTaskRequest()
        // })
        // eventBus.$on(`update_filter_tasks.TaskModel`, () => {
        //     this.$store.commit('monitor/FILTER_HANDLER')
        //     eventBus.$emit('TOGGLE_TASK_DRAWER_logistic')
        //     this.checkTaskRequest()
        // })
        // eventBus.$on(`filter_others_${this.page_name}`, data => {
        //     this.$store.commit('monitor/SET_TASK_FILTER', {
        //         is_daily_filter: data?.is_daily_filter || false
        //     })
        // })
        // eventBus.$on('OPEN_ORDER_TASK', data => {
        //     this.checkOpen(data)
        // })
    },
    beforeDestroy() {
        // eventBus.$off('OPEN_ORDER_TASK')
        eventBus.$off('update_filter_tasks.TaskModel')
        eventBus.$off('MOVE_GEOTASK_MAP')
        // eventBus.$off('TASK_CREATED_logistic')
        // eventBus.$off(`filter_start_${this.page_name}`)
        // eventBus.$off(`filter_others_${this.page_name}`)
        this.checkTaskRequest()
    }
}
</script>

<style lang="scss" scoped>
.task_list{
    .top_actions{
        background: rgba(255, 255, 255, 0.95);
        position: sticky;
        top: 0;
        z-index: 5;
    }
}
.list_edit_wrap{
    .edit_dummy{
        height: 45px;
    }
    .edit_button{
        position: absolute;
        bottom: 0;
        left: 0;
        width: 100%;
        padding-left: 15px;
        padding-right: 15px;
        padding-bottom: 10px;
        z-index: 5;
    }
}
</style>