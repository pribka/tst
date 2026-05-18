<template>
    <div class="h-full page_full monitor_page flex flex-col relative">
        <div 
            v-if="loading" 
            class="flex justify-center pt-5">
            <a-spin />
        </div>
        <template v-else>
            <div 
                style="flex-grow: 1;" 
                class="overflow-hidden">
                <div class="h-full flex">
                    <div class="left_col flex">
                        <a-tabs 
                            v-model="activeTab" 
                            class="w-[340px] 2xl:w-[380px]">
                            <a-tab-pane
                                class="tab_task"
                                key="task">
                                <span 
                                    slot="tab" 
                                    class="flex items-center justify-center">
                                    <i :class="taskTab.icon" class="mr-2"></i>
                                    {{ taskTab.name }}
                                </span>
                                <div v-if="activeTab === 'task'" class="tabs_wrapper">
                                    <TaskList :openTask="openTask" :sOrders="sOrders" :scrollTop="scrollTop" />
                                </div>
                            </a-tab-pane>
                            <a-tab-pane
                                class="tab_users"
                                key="couriers">
                                <span 
                                    slot="tab" 
                                    class="flex items-center justify-center">
                                    <i :class="couriersTab.icon" class="mr-2"></i>
                                    {{ couriersTab.name }}
                                </span>
                                <div v-if="activeTab === 'couriers'" class="tabs_wrapper">
                                    <UserList :openTask="openTask" :scrollTop="scrollTop" />
                                </div>
                            </a-tab-pane>
                        </a-tabs>
                        <OrdersList 
                            v-if="showOrderSidebar" 
                            ref="OrdersList"
                            :changeActiveTab="changeActiveTab"
                            :showOrderSidebar="showOrderSidebar"
                            :toggleOrderSidebar="toggleOrderSidebar"
                            :openTask="openTask" />
                    </div>
                    <div 
                        class="right_col relative overflow-hidden w-full"
                        :class="mapFull && 'right_full'"
                        ref="logist_map_wrap">
                        <Map 
                            :key="edit"
                            ref="logist_map_component"
                            :pointHover="pointHover"
                            :showOrderSidebar="showOrderSidebar"
                            :toggleOrderSidebar="toggleOrderSidebar" />
                    </div>
                </div>
            </div>
            <indexEmded 
                :width="400"
                :showAsideHeader="false"
                :container="drawerContainer"
                :wrapStyle="{ position: 'absolute' }"
                :hideDeliveryMap="false"
                taskType="logistic" />
        </template>
    </div>
</template>

<script>
import eventBus from '@/utils/eventBus'
import { mapState } from 'vuex'
export default {
    components: {
        Map: () => import('./components/Map/index.vue'),
        TaskList: () => import('./components/TaskList/index.vue'),
        indexEmded: () => import('@apps/vue2TaskComponent/components/TaskShowDrawer/indexEmded.vue'),
        OrdersList: () => import('./components/OrdersList/index.vue'),
        UserList: () => import('./components/UserList/index.vue')
    },
    computed: {
        ...mapState({
            logisticTask: state => state.monitor.logisticTask,
            taskListRequest: state => state.monitor.taskListRequest,
            userListRequest: state => state.monitor.userListRequest,
            orderListRequest: state => state.monitor.orderListRequest,
            config: state => state.monitor.config,
            mapFull: state => state.monitor.mapFull
        }),
        taskTab() {
            return this.config?.tabs?.task || {
                name: 'Задачи',
                icon: 'fi fi-rr-truck-side'
            }
        },
        couriersTab() {
            return this.config?.tabs?.couriers || {
                name: 'Курьеры',
                icon: 'fi fi-rr-users-alt'
            }
        },
        showOrderSidebar: {
            get() {
                return this.$store.state.monitor.showOrderSidebar
            },
            set(val) {
                this.$store.commit('monitor/SET_ORDER_SIDEBAR', val)
                localStorage.setItem('monitor_sidebar', val)

                this.$nextTick(() => {
                    if(val) {
                        this.$refs['OrdersList'].listInit()
                    }
                })
            }
        },
        activeTab: {
            get() {
                return this.$store.state.monitor.activeTab
            },
            set(val) {
                if(this.activeTab !== val) {
                    let query = Object.assign({}, this.$route.query)
                    query.active_tab = val
                    this.$router.push({query})
                }

                if(val === 'couriers') {
                    if(this.taskListRequest) {
                        this.taskListRequest.cancel()
                        this.$store.commit('monitor/SET_TASK_LIST_REQUEST', null)
                    }
                }
                if(val === 'task') {
                    if(this.userListRequest) {
                        this.userListRequest.cancel()
                        this.$store.commit('monitor/SET_USER_LIST_REQUEST', null)
                    }
                }

                this.$store.commit('monitor/CLEAR_STATE_TYPE', val)
                this.$store.commit('monitor/SET_ACTIVE_TAB', val)
                this.$store.commit('monitor/ORDER_RETURN_DEFAULT')
                eventBus.$emit('TOGGLE_TASK_DRAWER_logistic')
                eventBus.$emit('mapReinitPosition')
            }
        }
    },
    data() {
        return {
            hoversPoint: null,
            drawerContainer: () => document.body,
            rountignPoints: [],
            edit: false,
            loading: false,
            sOrders: null
        }
    },
    watch: {
        task(val) {
            if(val?.delivery_points?.length) {
                this.rountignPoints = JSON.parse(JSON.stringify(val.delivery_points))
                this.mapChangePositionPosition()
            } else
                this.rountignPoints = []
        }
    },
    beforeCreate() {
        if(this.$route.query?.active_tab)
            this.$store.commit('monitor/SET_ACTIVE_TAB', this.$route.query.active_tab)
    },
    created() {
        this.getConfig()
        this.$socket.client.emit("tasks") 
    },
    methods: {
        scrollTop(tabName) {
            this.$nextTick(() => {
                const scrollWrap = document.querySelector(`.${tabName}`)
                if(scrollWrap) {
                    scrollWrap.scroll({top:0})
                }
            })
        },
        changeActiveTab(sOrders) {
            this.sOrders = sOrders
            this.$store.commit('monitor/SET_ACTIVE_TAB', 'task')
        },
        async getConfig() {
            try {
                this.loading = true
                await this.$store.dispatch('monitor/getConfig')
            } catch(e) {
                console.log(e)
            } finally {
                this.loading = false
            }
        },
        checkOrderRequest() {
            if(this.orderListRequest) {
                this.orderListRequest.cancel()
                this.$store.commit('monitor/SET_ORDER_LIST_REQUEST', null)
            }
        },
        toggleOrderSidebar() {
            this.showOrderSidebar = !this.showOrderSidebar
            if(!this.showOrderSidebar)
                this.checkOrderRequest()
        },
        addTask() {
            this.$store.dispatch('task/sidebarOpen', {
                task_type: 'logistic'
            })
        },
        pointHover(point) {
            this.hoversPoint = point
        },
        openTask(task) {
            this.$nextTick(() => {
                this.drawerContainer = () => this.$refs['logist_map_wrap']
                this.$store.commit('monitor/SET_TASK_OPEN', true)
                eventBus.$emit('OPEN_TASK', task.id)
                eventBus.$emit('mapReinitPosition')
            })
        }
    },
    mounted() {
        eventBus.$on('CLOSE_TASK_DRAWER_logistic', () => {
            this.$store.commit('monitor/SET_TASK_OPEN', false)
            eventBus.$emit('mapReinitPosition')
        })

        let resizeId;
        window.addEventListener('resize', () => {
            clearTimeout(resizeId)
            resizeId = setTimeout(() => {
                eventBus.$emit('mapReinitPosition')
            }, 150)
        })
    },
    beforeDestroy() {
        eventBus.$off('CLOSE_TASK_DRAWER')
        this.$store.commit('monitor/CLEAR_ALL_STATE')
        this.checkOrderRequest()
    }
}
</script>

<style lang="scss">
.monitor_page{
    .left_col{
        .filter_pop_wrapper{
            min-width: 100%;
        }
        .ant-tabs-tabpane{
            overflow-y: auto;
            overflow-x: hidden;
        }
        .ant-tabs-content{
            height: calc(100% - 44px);
        }
        .ant-tabs{
            height: 100%;
        }
        .ant-tabs-bar{
            margin-bottom: 0px;
        }
        .ant-tabs-nav{
            width: 100%;
        }
        .ant-tabs-tab{
            margin: 0;
            width: 50%;
            text-align: center;
        }
        .tabs_wrapper{
            padding: 15px;
        }
    }
}
</style>

<style lang="scss" scoped>
.monitor_page{
    .monitor_content{
        height: calc(100% - 56px);
    }
}
.right_col{
    background: rgba(0, 0, 0, 0.07);
    &.right_full{
        position: absolute;
        z-index: 100;
        left: 0;
        top: 0;
        height: 100%;
    }
}
</style>

<style lang="scss">
.mapSpin{
    & > div{
        .ant-spin{
            max-height: 100%;
        }
    }
}
.check_button{
    .ant-checkbox-wrapper{
        .ant-checkbox{
            display: none;
            & + span{
                padding: 2px 8px;
                border: 1px solid var(--borderColor);
                border-radius: 30px;
                display: inline-block;
                background: #e3e6ea;
                cursor: pointer;
                -moz-user-select: none;
                -khtml-user-select: none;
                user-select: none;
                transition: all 0.3s cubic-bezier(0.645, 0.045, 0.355, 1);
                &:hover{
                    background: var(--primaryHover);
                }
            }
            &.ant-checkbox-checked{
                & + span{
                    background: var(--primaryHover);
                    color: var(--blue);
                }
            }
        }
    }
}
</style>