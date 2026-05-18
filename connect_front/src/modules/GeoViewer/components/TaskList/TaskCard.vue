<template>
    <div 
        class="point_card"
        v-on:dragover="onDrop"
        :ref="`point_card_${item.id}`">
        <div 
            class="card_wrapper" 
            :class="visiblePoints && 'visible_points'">
            <div class="cursor-pointer flex items-center justify-between" >
                <a-tag 
                    :color="item.status.color === 'default' ? '' : item.status.color">
                    {{ item.status.name }}
                </a-tag>
                <div class="card_actions">
                    <div class="votes">
                        <span>
                            <i 
                                class="fi fi-rr-social-network transition-colors"
                                :class="{ 'blue_color': previous_vote === 'like'}"></i>
                            <span class="ml-1 text-sm">{{ item.vote.likes_count }}</span>
                        </span>
                        <span class="ml-3">
                            <i 
                                class="fi fi-rr-hand transition-colors"
                                :class="{ 'text_red': previous_vote === 'dislike'}"></i>
                            <span class="ml-1 text-sm">{{ item.vote.dislikes_count }}</span>
                        </span>
                    </div>
                </div>
            </div>
            <template v-if="item?.project">
                <div class="mt-2 flex items-center justify-between">
                    <span 
                        class="truncate text-sm font-light">
                        {{ item.project.name }}
                    </span>
                </div>
            </template>
            <div 
                class="flex items-center justify-between"
                :class="item?.project ? 'mt-1' : 'mt-3'">
                <span 
                    @click="openTask(item)"
                    class="blue_color truncate text-sm">
                    #{{ item.counter }} {{ item.name }}
                </span>
            </div>
            <div class="mt-3 flex items-center justify-between">
                <DeadLine 
                    :taskStatus="item.status" 
                    :date="item.dead_line" />
            </div>
            <div :class="item.date_start_plan && item.dead_line ? 'mt-1' : 'mt-3'">
                <div
                    v-for="point in item.task_points"
                    :key="point.id"
                    class="address_item">
                    <i class="mr-1 fi fi-rr-marker"></i>
                    <span 
                        @click="shopPointOnMap(point)" 
                        class="cursor-pointer text-sm">
                        {{ point.name }}
                    </span>
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
                                </div>
                            </div>
                        </div>
                    </draggable>
                </a-checkbox-group>
            </div>
        </Transition>
    </div>
</template>

<script>
import draggable from "vuedraggable"
import eventBus from '@/utils/eventBus'
import DeadLine from '@apps/vue2TaskComponent/components/DeadLine'

import { mapGetters, mapState } from 'vuex'
export default {
    components: {
        draggable,
        DeadLine
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
        previous_vote() {
            return this.item.vote.previous_vote
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
        // /** @param {string} choice принимает значения 'like' и 'dislike' */
        // async vote(choice) {
        //     const task = this.item
        //     const payload = {}
        //     if (choice === 'like')
        //         payload.vote = true
        //     else if (choice === 'dislike')
        //         payload.vote = false

        //     await this.$http.post(`vote/${task.id}/`, payload)
        //         .then(() => {
        //             const voteChanging = choice === this.previous_vote ? -1 : 1
        //             if (choice === 'like')
        //                 this.item.vote.likes_count += voteChanging
        //             else if (choice === 'dislike')
        //                 this.item.vote.dislikes_count += voteChanging
    
        //             if (choice === this.previous_vote)
        //                 this.item.vote.previous_vote = null
        //             else
        //                 this.item.vote.previous_vote = choice
        //         })
        //         .catch(error => console.error(error))
        // },
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
        shopPointOnMap(point) {
            eventBus.$emit(`setCenter`, point)
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

.address_item {
    transition: color 0.05s;
}
.address_item:hover {
    color: var(--blue);
}
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
        padding: 8px 12px;
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