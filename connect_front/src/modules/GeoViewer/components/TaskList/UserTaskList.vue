<template>
    <div class="task_list">
        <a-spin 
            :spinning="loading" 
            size="small"
            class="w-full">
            <div 
                v-if="taskFiltered.length" 
                class="task_list_wrapper pt-2 mt-2">
                <div class="label mb-2">
                    Активные маршруты
                </div>
                <div class="list relative">
                    <PointCard 
                        v-for="item in taskFiltered" 
                        :key="item.id"
                        :item="item"
                        :setRoutePoint="setRoutePoint"
                        :mapHoverPoint="mapHoverPoint"
                        :openTask="openTask"
                        inlineEdited
                        :hoverPoint="hoverPoint" />
                </div>
            </div>
        </a-spin>
    </div>
</template>

<script>
import PointCard from './PointCard.vue'
import { mapState } from 'vuex'
// import PageFilter from '@/components/PageFilter'
import eventBus from '@/utils/eventBus'
export default {
    components: {
        PointCard
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
        user: {
            type: Object,
            required: true
        }
    },
    computed: {
        ...mapState({
            logisticTask: state => state.monitor.logisticTask,
            listEdit: state => state.monitor.listEdit,
            taskOpen: state => state.monitor.taskOpen,
        }),
        taskFiltered() {
            if(this.logisticTask?.length) {
                return this.logisticTask.filter(f => f.userFilter === this.user.id) || []
            } else
                return []
        }
    },
    data() {
        return {
            loading: false,
            saveLoading: false,
            page_name: 'page_list_logistic_task.TaskModel_user',
        }
    },
    created() {
        if(!this.taskFiltered?.length)
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
        addTask() {
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
        async getTask() {
            try {
                this.loading = true
                await this.$store.dispatch('monitor/getLogisticUserTask', {
                    user: this.user
                })
                eventBus.$emit('SET_START_POSITION')
            } catch(e) {
                console.log(e)
            } finally {
                this.loading = false
            }
        }
    }
}
</script>

<style lang="scss" scoped>
.task_list_wrapper{
    border-top: 1px solid var(--border2);
}
</style>