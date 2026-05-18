<template>
    <div 
        class="point_card"
        v-on:dragover="onDrop"
        :ref="`point_card_${item.id}`">
        <div 
            class="card_wrapper" 
            :class="visiblePoints && 'visible_points'">
            <div 
                class="blue_color cursor-pointer flex justify-between truncate" 
                @click="openTask(item)">
                <span class="truncate">
                    #{{item.counter}} {{ item.name }}
                </span>
                <a-tag 
                    :color="item.status.color === 'default' ? '' : item.status.color" 
                    class="ml-2 mr-0">
                    {{ item.status.name }}
                </a-tag>
            </div>
            <div class="flex items-center justify-between">
                <div class="flex items-center">
                    <div 
                        class="users_info flex items-center mr-3" 
                        :ref="`kanban_card_${item.id}`">
                        <div 
                            class="flex items-center" 
                            @click="filter({operator: item.operator.id})">
                            <Profiler
                                :user="item.operator"
                                :showUserName="false"
                                :avatarSize="18"
                                initStatus
                                :getPopupContainer="getPopupContainer" />
                            <div v-if="!item.has_order" class="ml-2 text-xs gray">
                                пустой рейс
                            </div>
                        </div>
                    </div>
                    <!--<div class="point_card_info gray flex items-center">
                        <i class="fi fi-rr-map-marker"></i> 38.5 км
                    </div>
                    <div class="point_card_info gray flex items-center">
                        <i class="fi fi-rr-time-forward"></i>
                        2.2 ч
                    </div>
                    <div class="point_card_info gray flex items-center">
                        <i class="fi fi-rr-checkbox"></i>
                        44/21
                    </div>-->
                </div>
                <div class="flex items-center">
                    <a-button 
                        type="link" 
                        size="small"
                        v-tippy="{ inertia : true}"
                        content="Показать описание точки"
                        class="ant-btn-icon-only text_current"
                        :class="!showPopup && 'opacity-50'"
                        @click="toggleMapPopup()">
                        <i class="fi fi-rr-comment-alt-middle"></i>
                    </a-button>
                    <a-button 
                        type="link" 
                        size="small"
                        v-tippy="{ inertia : true}"
                        content="Показать на карте"
                        class="ant-btn-icon-only text_current"
                        :class="!showInMap && 'opacity-50'"
                        @click="toggleMapShow()">
                        <i class="fi fi-rr-map"></i>
                    </a-button>
                    <a-button 
                        type="link" 
                        size="small"
                        v-tippy="{ inertia : true}"
                        content="Показать маршрут"
                        class="ant-btn-icon-only text_current"
                        :class="!routingLine && 'opacity-50'"
                        @click="toggleRoutingLines()">
                        <i class="fi fi-rr-road"></i>
                    </a-button>
                    <a-button 
                        type="link" 
                        size="small"
                        v-tippy="{ inertia : true}"
                        content="Открыть задачу"
                        class="ant-btn-icon-only text_current"
                        @click="openTask(item)">
                        <i class="fi fi-rr-eye"></i>
                    </a-button>
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
                        :loading="pointsLoader"
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
                class="card_poinst">
                <a-checkbox-group 
                    :value="selectPoint" 
                    class="w-full">
                    <draggable
                        v-model="routing"
                        class="list-group"
                        ghost-class="ghost"
                        :class="!routing.length && 'empty'"
                        group="card_points"
                        draggable=".point_item"
                        :forceFallback="true"
                        @start="dragging = true"
                        @end="dragging = false"
                        :options="{disabled : item.status.is_complete ? true : false}"
                        @change="change">
                        <template 
                            slot="header" 
                            role="group">
                            <div 
                                v-if="!routing.length" 
                                class="text-center gray">
                                {{ config.task && config.task.drag_text ? config.task.drag_text : 'Перетащите заказы для формирования маршрута' }}
                            </div>
                        </template>
                        <div
                            class="point_item"
                            :class="item.status.is_complete && 'disabled_move'"
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
                                        v-if="!item.status.is_complete"
                                        :value="point.id"
                                        @change="changeCheckbox" />
                                </div>
                            </div>
                            <div class="point_info flex items-center gray justify-between">
                                <div class="flex items-center">
                                    <div 
                                        v-for="ord in point.orders" 
                                        :key="ord.id"
                                        class="cursor-pointer point_order_counter"
                                        @click="openOrder(ord.id)">
                                        #{{ ord.counter }}
                                    </div>
                                    <!--<div 
                                        v-if="point.duration" 
                                        class="item_info">
                                        <i class="fi fi-rr-time-forward"></i> {{ point.duration }}
                                    </div>
                                    <div class="item_info">
                                        <i class="fi fi-rr-map-marker"></i> 5 км
                                    </div>-->
                                    <!--<template v-if="index === 0 && item.date_start_plan" >
                                        <div class="item_info">
                                            <i class="fi fi-rr-clock"></i> {{ $moment(item.date_start_plan).format('HH:mm') }}
                                        </div>
                                        <div v-if="item.date_start_fact" class="item_info">
                                            <i class="fi fi-rr-time-check"></i> {{ $moment(item.date_start_fact).format('HH:mm') }}
                                        </div>
                                    </template>-->
                                    <!--<template v-if="index > 0">
                                        <div v-if="item.date_start_plan && point.duration" class="item_info">
                                            <i class="fi fi-rr-clock"></i> {{ deliveryTime(point) }}
                                        </div>
                                        <div v-if="item.date_start_fact" class="item_info">
                                            <i class="fi fi-rr-time-check"></i> {{ deliveryTime(point, 'fact') }}
                                        </div>
                                    </template>-->
                                </div>
                                <!--<div 
                                    v-if="point.orders.length" 
                                    class="cursor-pointer">
                                    <template v-if="point.orders.length > 1">
                                        <a-dropdown :trigger="['click']">
                                            <a 
                                                class="ant-dropdown-link gray" 
                                                @click="e => e.preventDefault()">
                                                подробнее
                                            </a>
                                            <a-menu slot="overlay">
                                                <a-menu-item disabled>
                                                    Выберите заказ
                                                </a-menu-item>
                                                <a-menu-divider />
                                                <a-menu-item 
                                                    v-for="ord in point.orders" 
                                                    :key="ord.id"
                                                    @click="openOrder(ord.id)">
                                                    {{ ord.counter }}
                                                </a-menu-item>
                                            </a-menu>
                                        </a-dropdown>
                                    </template>
                                    <div 
                                        v-else 
                                        class="ant-dropdown-link gray" 
                                        @click="openOrder(point.orders[0].id)">
                                        подробнее
                                    </div>
                                </div>-->
                            </div>
                        </div>
                    </draggable>
                </a-checkbox-group>
                <div v-if="selectPoint.length || inlineEdited && item.edited" class="mt-3 flex items-center justify-end">
                    <a-button 
                        v-if="inlineEdited && item.edited"
                        block
                        :loading="saveLoading"
                        type="primary"
                        @click="updateTask()">
                        Обновить маршрут
                    </a-button>
                    <template v-if="selectPoint.length">
                        <a-button 
                            class="ant-btn-icon-only mr-1 px-2 ml-1"
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
            </div>
        </Transition>
    </div>
</template>

<script>
import draggable from "vuedraggable"
import eventBus from '@/utils/eventBus'
import { mapGetters, mapState } from 'vuex'
export default {
    components: {
        draggable
    },
    props: {
        item: {
            type: Object,
            required: true
        },
        openTask: {
            type: Function,
            default: () => {}
        },
        hoverPoint: {
            type: Function,
            default: () => {}
        },
        showMapPoint: {
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
        inlineEdited: {
            type: Boolean,
            default: false
        },
        onDropInTimer: {
            type: Function,
            default: () => {}
        }
    },
    computed: {
        ...mapState({
            listEdit: state => state.monitor.listEdit,
            config: state => state.monitor.config
        }),
        ...mapGetters({
            getTaskVisiblePoints: 'monitor/getTaskVisiblePoints'
        }),
        visiblePoints() {
            return this.getTaskVisiblePoints(this.item.id)
        },
        routing: {
            get() {
                return this.item.routing
            },
            set(routing) {
                this.$store.commit('monitor/CHANGE_TASK_ROUTING', {
                    task: this.item,
                    routing
                })
            }
        },
        routingLine() {
            return this.item.routingLine
        },
        showInMap() {
            return this.item.showInMap
        },
        showPopup() {
            return this.item.showPopup
        },
        pointColor() {
            return this.item.color || '#000000'
        }
    },
    data() {
        return {
            pointsLoader: false,
            deliveryPointsList: [],
            dragging: false,
            selectPoint: [],
            deleteDisabled: false,
            saveLoading: false
        }
    },
    watch: {
        visiblePoints(val) {
            if(!val) {
                this.selectPoint = []
                this.dragging = false
            }
        }
    },
    methods: {
        onDrop() {
            if(!this.visiblePoints && !this.pointsLoader) {
                this.onDropInTimer(this.item)
            }
        },
        openOrder(id) {
            let query = Object.assign({}, this.$route.query)

            if(!query?.order || query.order !== id) {
                query.order = id
                this.$router.push({query})
            }
        },
        async updateTask() {
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
        setEdit() {
            if(!this.listEdit)
                this.$store.commit('monitor/SET_LIST_EDIT', true)

            this.$store.commit('monitor/CHECK_ALL_EDITING')
        },
        toggleRoutingLines() {
            this.$store.commit('monitor/CHANGE_ROUTING_LINE', {
                task: this.item,
                value: !this.routingLine
            })
        },
        toggleMapShow() {
            this.$store.commit('monitor/CHANGE_TASK_IN_MAP', {
                task: this.item,
                value: !this.showInMap
            })
            if(this.showInMap) {
                this.$store.commit('monitor/SET_MAP_TASKS_SHOW', this.showInMap)
            }
        },
        toggleMapPopup() {
            this.$store.commit('monitor/CHANGE_TASK_POPUP', {
                task: this.item,
                value: !this.showPopup
            })
            eventBus.$emit(`toggle_map_popup_${this.item.id}`, this.showPopup)
        },
        deleteConfirm() {
            this.$store.commit('monitor/ROUTER_DELETED', {
                task: this.item,
                selectPoint: this.selectPoint
            })
            this.selectPoint = []
            this.setEdit()
        },
        change(e) {
            this.setEdit()
            if(e.moved) {
                this.$store.commit('monitor/ROUTER_MOVED', {
                    task: this.item,
                    router: e.moved.element
                })
            }
            if(e.added) {
                this.$store.commit('monitor/ROUTER_ADDED', {
                    task: this.item,
                    router: e.added.element
                })
            }
            if(e.removed) {
                this.$store.commit('monitor/ROUTER_REMOVED', {
                    task: this.item,
                    router: e.removed.element
                })
            }
        },
        deliveryTime(point, type = 'plan') {
            if(this.item.date_start_plan) {
                let time = type === 'plan' ? this.$moment(this.item.date_start_plan) : this.$moment(this.item.date_start_fact)
                const index = this.deliveryPointsList.findIndex(f => f.id === point.id)

                if(index !== -1) {
                    for (let i = 0; i <= index; i++) {
                        if(i > 0) {
                            if(this.deliveryPointsList[i].delivery_date)
                                time = this.$moment(this.deliveryPointsList[i].delivery_date).add(this.deliveryPointsList[i].duration, 'minutes')
                            else
                                time = time.add(this.deliveryPointsList[i].duration, 'minutes')
                        }
                    }

                    return this.$moment(time).format('HH:mm')
                } else
                    return null
            } else
                return null
        },
        getPopupContainer() {
            return this.$refs[`point_card_${this.item.id}`]
        },
        closePoints() {
            this.$store.commit('monitor/RETURN_DRAGGED_ROUTING', { task: this.item })
            this.$store.commit('monitor/DELETE_ACTIVE_ROUTING', { task: this.item })
            this.$store.commit('monitor/SET_TASK_POINT_UNVISIBLE', { task: this.item })
            this.$store.commit('monitor/CHECK_UPDATE_IN_CLOSE')
        },
        async getDeliveryPoints() {
            try {
                this.pointsLoader = true
                this.$store.commit('monitor/SET_POPUP_MARKER_LOADER', {
                    task: this.item,
                    value: true
                })
                await this.$store.dispatch('monitor/getDeliveryPoints', { 
                    task: this.item, 
                    showPoint: true 
                })
            } catch(e) {
                console.log(e)
            } finally {
                this.pointsLoader = false
                this.$store.commit('monitor/SET_POPUP_MARKER_LOADER', {
                    task: this.item,
                    value: false
                })
            }
        }
    },
    mounted() {
        eventBus.$on(`show_log_${this.item.id}`, data => {
            this.getDeliveryPoints()
        })
    },
    beforeDestroy() {
        eventBus.$off(`show_log_${this.item.id}`)
    }
}
</script>

<style lang="scss">
.point_card{
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
.point_card{
    border: 1px solid var(--border2);
    border-radius: var(--borderRadius);
    &:not(:last-child){
        margin-bottom: 10px;
    }
    .list-group{
        &.empty{
            min-height: 50px;
        }
    }
    .point_card_info{
        font-size: 12px;
        i{
            margin-right: 5px;
        }
        &:not(:last-child){
            margin-right: 10px;
        }
    }
    .card_wrapper{
        padding: 6px 12px;
        background: #ffffff;
        &:not(.visible_points) {
            border-radius: var(--borderRadius);
        }
        &.visible_points{
            border-radius: var(--borderRadius) var(--borderRadius) 0px 0px;
        }
    }
    .card_poinst{
        background-color: #eff2f5;
        padding: 12px;
        border-radius: 0px 0px var(--borderRadius) var(--borderRadius);
    }
    .point_item{
        padding: 6px 12px;
        background: #fff;
        box-shadow: 0 1px 0 rgb(9 30 66 / 15%);
        position: relative;
        border-radius: var(--borderRadius);
        &:not(.disabled_move) {
            cursor: move;
        }
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
            .point_order_counter{
                transition: all 0.3s cubic-bezier(0.645, 0.045, 0.355, 1);
                &:hover{
                    color: var(--blue);
                }
            }
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