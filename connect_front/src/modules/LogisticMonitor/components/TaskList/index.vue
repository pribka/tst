<template>
    <div class="task_list h-full">
        <div class="pb-3 top_actions">
            <div class="flex items-center">
                <PageFilter 
                    class="w-full"
                    model="tasks.TaskModel"
                    :key="page_name"
                    size="large"
                    :excludeFields="['is_daily_filter', 'without_order_filter']"
                    :page_name="page_name" />
                <a-button 
                    v-if="config.task && config.task.create_button"
                    icon="plus" 
                    size="large" 
                    shape="circle"
                    class="ml-1"
                    v-tippy="{ inertia : true}"
                    content="Добавить рейс"
                    type="primary"
                    @click="addTask()" />
            </div>
            <div class="flex items-center mt-2 task_check check_button">
                <a-checkbox 
                    :checked="filters['is_daily_filter']"
                    @change="checkboxHandler($event, 'is_daily_filter')">
                    Сегодняшние
                </a-checkbox>
                <a-checkbox 
                    :checked="filters['without_order_filter']"
                    @change="checkboxHandler($event, 'without_order_filter')">
                    Без заказов
                </a-checkbox>
            </div>
        </div>
        <div class="list relative">
            <a-spin 
                :spinning="loading" 
                class="w-full">
                <div 
                    v-if="taskEmpty" 
                    class="pt-3">
                    <a-empty description="Нет данных" />
                </div>
                <PointCard 
                    v-for="item in logisticTask"
                    :key="item.id"
                    :ref="`log_card_${item.id}`"
                    :id="`log_card_${item.id}`"
                    :item="item"
                    :onDropInTimer="onDropInTimer"
                    :setRoutePoint="setRoutePoint"
                    :mapHoverPoint="mapHoverPoint"
                    :openTask="openTask"
                    :hoverPoint="hoverPoint" />
            </a-spin>
        </div>
        <div 
            v-if="listEdit" 
            class="list_edit_wrap">
            <div class="edit_dummy"></div>
            <div class="edit_button">
                <a-button 
                    type="primary" 
                    block
                    :loading="saveLoading"
                    size="large"
                    @click="saveRouting()">
                    Обновить маршруты
                </a-button>
            </div>
        </div>
    </div>
</template>

<script>
import PointCard from './PointCard.vue'
import { mapState } from 'vuex'
import PageFilter from '@/components/PageFilter'
import eventBus from '@/utils/eventBus'
let dropTimer;
let timerId;
export default {
    components: {
        PointCard,
        PageFilter
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
            logisticTask: state => state.monitor.logisticTask,
            listEdit: state => state.monitor.listEdit,
            taskOpen: state => state.monitor.taskOpen,
            taskListRequest: state => state.monitor.taskListRequest,
            loading: state => state.monitor.taskListLoader,
            config: state => state.monitor.config,
            filters: state => state.monitor.taskFilters,
            taskEmpty: state => state.monitor.taskEmpty
        })
    },
    data() {
        return {
            saveLoading: false,
            page_name: 'page_list_logistic_task.TaskModel',
        }
    },
    created() {
        this.getTask()
    },
    sockets: {
        task_update({data}) {
            if(data) {
                this.$store.commit('monitor/UPDATE_TASK_SOCKET', data)
            }
        }
    },
    methods: {
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
        addTask() {
            this.$store.commit('monitor/CLEAR_TASK_ALL_ROUTING')
            this.$store.commit('monitor/CLEAR_TASK_POINT_VISIBLE')
            this.$store.dispatch('task/sidebarOpen', {
                task_type: 'logistic'
            })
        },
        async saveRouting() {
            try {
                this.saveLoading = true
                const data = await this.$store.dispatch('monitor/updateRouting')

                if(data.status) {
                    this.$message.success('Маршрут обновлен')
                    eventBus.$emit('LOGISTIC_ORDER_RELOAD')

                    if(this.taskOpen)
                        eventBus.$emit('UPDATE_TASK_DRAWER')
                } else {
                    if(data?.error) {
                        let message = ''

                        for(const key in data.error) {
                            message = message + `${data.error[key].join(' ')} `
                        }

                        if(message) {
                            this.$message.error(message)
                        } else {
                            this.$message.error('Ошибка')
                        }
                    } else {
                        this.$message.error('Ошибка')
                    }
                }
            } catch(e) {
                console.log(e)
                this.$message.error('Ошибка')
            } finally {
                this.saveLoading = false
            }
        },
        async getTask(cOpen = null, topScroll = false) {
            try {
                await this.$store.dispatch('monitor/getLogisticTask')
                eventBus.$emit('SET_START_POSITION')

                if(this.sOrders?.logistic_task) {
                    this.$nextTick(() => {
                        this.setActive(this.sOrders.logistic_task)
                    })
                }

                if(cOpen) {
                    this.checkOpen(cOpen)
                }
                if(topScroll) {
                    this.scrollTop('tab_task')
                }
            } catch(e) {
                console.log(e)
            }
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
        eventBus.$on(`TASK_CREATED_logistic`, data => {
            this.$store.commit('monitor/CLEAR_TASK_POINT_VISIBLE')
            this.$store.commit('monitor/SET_TASK_EMPTY', false)
            this.checkTaskRequest()
            this.getTask(data)
        })
        eventBus.$on(`update_filter_tasks.TaskModel`, () => {
            this.$store.commit('monitor/FILTER_HANDLER')
            eventBus.$emit('TOGGLE_TASK_DRAWER_logistic')
            this.checkTaskRequest()
            this.getTask(null, true)
        })
        eventBus.$on(`filter_others_${this.page_name}`, data => {
            this.$store.commit('monitor/SET_TASK_FILTER', {
                is_daily_filter: data?.is_daily_filter || false
            })
        })
        eventBus.$on('OPEN_ORDER_TASK', data => {
            this.checkOpen(data)
        })
    },
    beforeDestroy() {
        eventBus.$off('OPEN_ORDER_TASK')
        eventBus.$off('update_filter_tasks.TaskModel')
        eventBus.$off('TASK_CREATED_logistic')
        eventBus.$off(`filter_start_${this.page_name}`)
        eventBus.$off(`filter_others_${this.page_name}`)
        this.checkTaskRequest()
    }
}
</script>

<style lang="scss" scoped>
.task_list{
    .top_actions{
        background: rgba(255, 255, 255, 0.95);
        margin-left: -15px;
        margin-right: -15px;
        padding-left: 15px;
        padding-right: 15px;
        padding-top: 15px;
        margin-top: -15px;
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