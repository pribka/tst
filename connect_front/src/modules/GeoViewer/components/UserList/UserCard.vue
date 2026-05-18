<template>
    <div class="user_card" v-on:dragover="onDrop">
        <div class="user_card_wrapper">
            <div class="flex items-center justify-between">
                <Profiler
                    :user="user"
                    initStatus
                    :avatarSize="22" />
                <Status 
                    v-if="user.work_status" 
                    :user="user" />
            </div>
            <div class="flex justify-end mt-1">
                <div class="user_actions">
                    <a-button 
                        v-if="visiblePoints"
                        type="link" 
                        size="small"
                        v-tippy="{ inertia : true}"
                        content="Свернуть"
                        class="ant-btn-icon-only text_current"
                        @click="closePoints()">
                        <i class="fi fi-rr-arrow-circle-up"></i>
                    </a-button>
                    <a-button
                        v-else
                        type="link" 
                        size="small"
                        v-tippy="{ inertia : true}"
                        content="Маршрут"
                        class="ant-btn-icon-only text_current"
                        @click="getDeliveryPoints()">
                        <i class="fi fi-rr-navigation"></i>
                    </a-button>
                </div>
            </div>
        </div>
        <Transition name="slide">
            <div 
                v-if="visiblePoints" 
                class="card_points w-full">
                <a-checkbox-group 
                    :value="selectPoint" 
                    class="w-full">
                    <draggable
                        v-model="routing"
                        class="list-group"
                        :class="!routing.length && 'empty'"
                        ghost-class="ghost"
                        group="card_points"
                        draggable=".point_item"
                        @start="dragging = true"
                        @end="dragging = false"
                        @change="change">
                        <template 
                            slot="header" 
                            role="group">
                            <div 
                                v-if="!routing.length" 
                                class="text-center gray">
                                {{ config.couriers && config.couriers.drag_text ? config.couriers.drag_text : 'Для создания задачи перетащите заказ' }}
                            </div>
                        </template>
                        <div
                            class="point_item"
                            v-for="(point, index) in routing"
                            :key="`${point.id}_${index}`">
                            <div class="flex items-center justify-between truncate">
                                <div class="truncate flex items-center">
                                    <div>
                                        <span 
                                            :style="`border-color: ${pointColor};`" 
                                            class="poin_icon mr-2">
                                            {{ index + 1 }}
                                        </span>
                                    </div>
                                    <span 
                                        v-if="point.is_start" 
                                        class="mr-2 point_icon"
                                        v-tippy="{ inertia : true}"
                                        content="Склад погрузки"
                                        :style="`color: ${pointColor};`">
                                        <i class="fi fi-rr-home-location-alt"></i>
                                    </span>
                                    <span class="truncate">
                                        {{ point.name }}
                                    </span>
                                </div>
                                <div class="pl-2 flex items-center">
                                    <a-badge 
                                        v-if="point.added" 
                                        status="error" />
                                    <a-checkbox
                                        :value="point.id"
                                        @change="changeCheckbox" />
                                </div>
                            </div>
                            <div class="point_info flex items-center gray">
                                <div 
                                    v-if="point.duration" 
                                    class="item_info">
                                    <i class="fi fi-rr-time-forward"></i> {{ point.duration }}
                                </div>
                                <!--<div class="item_info">
                                    <i class="fi fi-rr-map-marker"></i> 5 км
                                </div>
                                <template v-if="index === 0 && item.date_start_plan" >
                                    <div class="item_info">
                                        <i class="fi fi-rr-clock"></i> {{ $moment(item.date_start_plan).format('HH:mm') }}
                                    </div>
                                    <div v-if="item.date_start_fact" class="item_info">
                                        <i class="fi fi-rr-time-check"></i> {{ $moment(item.date_start_fact).format('HH:mm') }}
                                    </div>
                                </template>
                                <template v-if="index > 0">
                                    <div v-if="item.date_start_plan && point.duration" class="item_info">
                                        <i class="fi fi-rr-clock"></i> {{ deliveryTime(point) }}
                                    </div>
                                    <div v-if="item.date_start_fact" class="item_info">
                                        <i class="fi fi-rr-time-check"></i> {{ deliveryTime(point, 'fact') }}
                                    </div>
                                </template>-->
                            </div>
                        </div>
                    </draggable>
                </a-checkbox-group>
                <div 
                    v-if="user.edited || selectPoint.length" 
                    class="mt-3 flex items-center justify-end">
                    <a-button 
                        v-if="user.edited" 
                        block 
                        icon="plus"
                        type="primary"
                        @click="createTask()">
                        Добавить задачу
                    </a-button>
                    <template v-if="selectPoint.length">
                        <a-button 
                            class="ant-btn-icon-only mr-1 ml-1 px-2"
                            @click="uncheckAll()">
                            <i class="fi fi-rr-apps-delete"></i>
                        </a-button>
                        <a-popconfirm
                            title="Удалить выбранные заказы из задачи?"
                            ok-text="Удалить"
                            cancel-text="Нет"
                            @confirm="deleteConfirm">
                            <a-button 
                                class="ant-btn-icon-only px-2"
                                type="danger">
                                <i class="fi fi-rr-trash"></i>
                            </a-button>
                        </a-popconfirm>
                    </template>
                </div>
                <UserTaskList 
                    ref="UserTaskList"
                    :user="user" 
                    :openTask="openTask" />
            </div>
        </Transition>
    </div>
</template>

<script>
import draggable from "vuedraggable"
import { mapGetters, mapState } from 'vuex'
import Status from './Status.vue'
import UserTaskList from '../TaskList/UserTaskList.vue'
import eventBus from '@/utils/eventBus'
export default {
    components: {
        draggable,
        Status,
        UserTaskList
    },
    props: {
        user: {
            type: Object,
            required: true
        },
        openTask: {
            type: Function,
            default: () => {}
        },
        onDropInTimer: {
            type: Function,
            default: () => {}
        }
    },
    computed: {
        ...mapState({
            config: state => state.monitor.config
        }),
        ...mapGetters({
            getUserVisiblePoints: 'monitor/getUserVisiblePoints'
        }),
        visiblePoints() {
            return this.getUserVisiblePoints(this.user.id)
        },
        routing: {
            get() {
                return this.user.routing
            },
            set(routing) {
                this.$store.commit('monitor/CHANGE_USER_ROUTING', {
                    user: this.user,
                    routing
                })
            }
        }
    },
    data() {
        return {
            pointsLoader: false,
            selectPoint: [],
            dragging: false,
            pointColor: '#000000',
            deleteDisabled: false
        }
    },
    methods: {
        onDrop() {
            if(!this.visiblePoints && !this.pointsLoader) {
                this.onDropInTimer(this.user)
            }
        },
        clearUserAdded(data) {
            this.$store.commit('monitor/CLEAR_USER_ADDED', {
                user: this.user,
                data
            })
            this.$store.commit('monitor/DELETE_ORDER_MOVED_BY_ID', data)
            eventBus.$emit('LOGISTIC_ORDER_RELOAD')
            eventBus.$emit('monitor/CLEAR_ORDER_REMOVED')
        },
        createTask() {
            this.$store.dispatch('monitor/createUserTask', {
                user: this.user
            })
        },
        deleteConfirm() {
            this.$store.commit('monitor/ROUTER_USER_DELETED', {
                user: this.user,
                selectPoint: this.selectPoint
            })
            this.selectPoint = []
        },
        change() {
            
        },
        uncheckAll() {
            this.selectPoint = []
            this.deleteDisabled = false
        },
        changeCheckbox(e) {
            if(this.deleteDisabled)
                this.deleteDisabled = false

            const checked = e.target.checked,
                value = e.target.value

            if(checked) {
                this.selectPoint.push(value)
            }

            if(this.selectPoint?.length) {
                this.selectPoint.forEach(pointId => {
                    const index = this.routing.findIndex(f => f.id === value)
                    if(index !== -1) {
                        const route = this.routing[index]
                        if(route?.orders?.length) {
                            route.orders.forEach(order => {
                                const oid = order.id

                                const routeFilter = this.routing.filter(f => f.id !== value)

                                routeFilter.forEach(routeItem => {
                                    if(routeItem.id !== value && routeItem.orders?.length <= 1) {
                                        routeItem.orders.forEach(pOrder => {
                                            if(pOrder.id === oid) {
                                                if(checked) {
                                                    const find = this.selectPoint.find(f => f === routeItem.id)
                                                    if(!find) {
                                                        this.selectPoint.push(routeItem.id)
                                                    }
                                                } else {
                                                    const chcIndex = this.selectPoint.findIndex(f => f === routeItem.id)
                                                    if(chcIndex !== -1) {
                                                        this.selectPoint.splice(chcIndex, 1)
                                                    }
                                                }
                                            }
                                        })
                                    }
                                })
                            })
                        }
                    }
                })
            }

            if(!checked) {
                const chcIndex = this.selectPoint.findIndex(f => f === value)
                if(chcIndex !== -1) {
                    this.selectPoint.splice(chcIndex, 1)
                }
            }

            if(this.routing.length === this.selectPoint.length) {
                this.deleteDisabled = true
            }
        },
        closePoints() {
            this.$store.commit('monitor/CLEAR_TASK_POINT_VISIBLE')
            this.$store.commit('monitor/RETURN_DRAGGED_USER_ROUTING', { user: this.user })
            this.$store.commit('monitor/DELETE_ACTIVE_USER_ROUTING', { user: this.user })
            this.$store.commit('monitor/SET_USER_POINT_UNVISIBLE', { user: this.user })
        },
        async getDeliveryPoints() {
            try {
                this.pointsLoader = true
                this.$store.commit('monitor/SET_USER_POINT_LOADER', {
                    user: this.user,
                    value: true
                })
                await this.$store.dispatch('monitor/getUserPoint', { 
                    user: this.user,
                })
            } catch(e) {
                console.log(e)
            } finally {
                this.pointsLoader = false
                this.$store.commit('monitor/SET_USER_POINT_LOADER', {
                    user: this.user,
                    value: false
                })
            }
        }
    },
    mounted() {
        eventBus.$on(`TASK_CREATED_logistic_${this.user.id}`, data => {
            this.clearUserAdded(data)
        })
    },
    beforeDestroy() {
        // eventBus.$off('TASK_CREATED_logistic')
        eventBus.$off(`TASK_CREATED_logistic_${this.user.id}`)
    }
}
</script>

<style lang="scss">
.user_card{
    .slide-enter-active {
    -moz-transition-duration: 0.1s;
    -webkit-transition-duration: 0.1s;
    -o-transition-duration: 0.1s;
    transition-duration: 0.1s;
    -moz-transition-timing-function: ease-in;
    -webkit-transition-timing-function: ease-in;
    -o-transition-timing-function: ease-in;
    transition-timing-function: ease-in;
    }

    .slide-leave-active {
    -moz-transition-duration: 0.1s;
    -webkit-transition-duration: 0.1s;
    -o-transition-duration: 0.1s;
    transition-duration: 0.1s;
    -moz-transition-timing-function: cubic-bezier(0, 1, 0.5, 1);
    -webkit-transition-timing-function: cubic-bezier(0, 1, 0.5, 1);
    -o-transition-timing-function: cubic-bezier(0, 1, 0.5, 1);
    transition-timing-function: cubic-bezier(0, 1, 0.5, 1);
    }

    .slide-enter-to, .slide-leave {
    max-height: 100px;
    overflow: hidden;
    }

    .slide-enter, .slide-leave-to {
    overflow: hidden;
    max-height: 0;
    }
}
</style>

<style lang="scss" scoped>
.user_card{
    border: 1px solid var(--border2);
    border-radius: var(--borderRadius);
    &:not(:last-child){
        margin-bottom: 10px;
    }
    .user_card_wrapper{
        padding: 6px 12px;
    }
    .card_points{
        background-color: #eff2f5;
        padding: 12px;
        border-radius: 0px 0px var(--borderRadius) var(--borderRadius);
    }
    .list-group{
        &.empty{
            min-height: 50px;
        }
    }
    .point_item{
        padding: 6px 12px;
        background: #fff;
        box-shadow: 0 1px 0 rgb(9 30 66 / 15%);
        cursor: move;
        position: relative;
        border-radius: var(--borderRadius);
        &:not(:last-child){
            margin-bottom: 7px;
        }
        .point_icon{
            font-size: 16px;
        }
        .point_info{
            border-top: 1px solid var(--border2);
            margin-top: 5px;
            padding-top: 5px;
            font-size: 12px;
            .item_info{
                i{
                    font-size: 11px;
                    margin-right: 2px;
                }
                &:not(:last-child){
                    margin-right: 15px;
                }
            }
        }
        .poin_icon{
            width: 17px;
            height: 17px;
            border-radius: 50%;
            border: 2px solid black;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 10px;
            background: #ffffff;
        }
    }
}
</style>