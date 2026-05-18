<template>
    <div class="task_delivery">
        <div 
            v-if="task.route_points && waypoints.length" 
            class="delivery_points mb-3 flex items-center">
            <a-button 
                :type="activeKey === 'default' ? 'primary' : 'default'"
                :ghost="activeKey === 'default'"
                :disabled="enabled"
                @click="selectPoint('all')">
                {{ $t('task.delivery.allPoints') }}
            </a-button>

            <draggable
                :list="pointsButton"
                :disabled="true"
                class="list-group"
                :class="enabled && 'enabled_drag'"
                ghost-class="ghost"
                @end="endDtrag()">
                <a-button 
                    v-for="point in pointsButton"
                    :key="point.id"
                    :type="activeKey === point.id ? 'primary' : 'default'"
                    :ghost="activeKey === point.id"
                    class="draggable_icon"
                    v-tippy="{ inertia : true}"
                    :content="point.name"
                    @click="selectPoint(point)">
                    {{ point.point }}
                </a-button>
            </draggable>
        </div>

        <a-tabs 
            v-if="task.logistic_tabs"
            v-model="activeTab"
            type="card">
            <a-tab-pane
                v-if="task.logistic_tabs.route && showTabMobile(task.logistic_tabs.route.mobile)"
                key="route">
                <span slot="tab">
                    {{ task.logistic_tabs.route.name }}
                </span>
                <div 
                    v-if="activePointData && activePointData.length" 
                    class="mb-4 points_list">
                    <div 
                        v-for="item in activePointData" 
                        :key="item.id"
                        class="item">
                        <div>
                            <div class="border-b pb-1">
                                <span class="font-semibold">{{ $t('task.delivery.address') }}:</span>
                                <span> {{ item.name }} </span> 
                            </div>
                            <div class="mt-2">
                                <div
                                    v-for="order in item.orders"
                                    :key="order.id"
                                    class="mb-2 py-2 px-3 border rounded-lg">
                                    <span class="font-semibold">{{ $t('task.delivery.order') }}:</span> {{ order.counter }}
                                    <div>
                                        <div>
                                            <span class="font-semibold">{{ $t('task.delivery.client') }}:</span> {{ order.contractor.name }}
                                        </div>
                                        <div v-if="order.contractor.phone">
                                            <span class="font-semibold">{{ $t('task.delivery.phone') }}:</span> <a :href="`tel:${order.contractor.phone}`">{{ order.contractor.phone }}</a>
                                        </div>
                                        <div v-if="order.contractor.email">
                                            <span class="font-semibold">{{ $t('task.delivery.email') }}:</span> {{ order.contractor.email }}
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                <a-spin :spinning="saveLoader">
                    <Map 
                        :key="activeKey && edited"
                        ref="map_component"
                        :deliveryPoints="deliveryPoints"
                        :task="task" 
                        :isMobile="isMobile"
                        :selectPoint="selectPoint"
                        :waypoints="waypoints" />
                </a-spin>
            </a-tab-pane>
            <a-tab-pane 
                v-if="task.logistic_tabs.list && showTabMobile(task.logistic_tabs.list.mobile)"
                key="list">
                <span slot="tab">
                    {{ task.logistic_tabs.list.name }}
                </span>
                <a-button 
                    v-if="isMobile && hideDeliveryMap" 
                    class="mb-2 flex items-center justify-center"
                    block
                    size="large"
                    @click="drawerMap = true">
                    <i class="fi fi-rr-map-marker mr-2"></i>
                    {{ $t('task.delivery.showOnMap') }}
                </a-button>
                <List
                    :task="task"
                    :deliveryPoints="deliveryPoints"
                    :waypoints="waypoints"
                    :showMap="showMap" />
            </a-tab-pane>
            <a-tab-pane 
                v-if="task.logistic_tabs.goods && showTabMobile(task.logistic_tabs.goods.mobile)"
                key="goods">
                <span 
                    slot="tab" 
                    class="flex items-center">
                    {{ task.logistic_tabs.goods.name }}
                    <a-badge 
                        class="ml-2" 
                        :number-style="{
                            backgroundColor: '#e6f7ff',
                            color: '#1890ff'
                        }"
                        :count="productList.length" />
                </span>
                <component 
                    :is="productTemplate"
                    :task="task"
                    :isOperator="isOperator"
                    :productList="productList"
                    :activeKey="activeKey" />
            </a-tab-pane>
        </a-tabs>

        <template v-if="isMobile">
            <a-drawer
                :visible="drawerMap"
                :destroyOnClose="true"
                :title="$t('task.delivery.routeOnMap')"
                placement="right"
                class="logist_map"
                :width="drawerWidth"
                :zIndex="5000"
                :afterVisibleChange="afterVisibleChange"
                @close="drawerMap = false">
                <Map 
                    :key="mapInit && activeKey"
                    ref="map_component"
                    style="height: 100%;"
                    :task="task" 
                    :selectPoint="selectPoint"
                    :waypoints="waypoints"
                    :pointsButton="pointsButton"
                    :activeKey="activeKey"
                    :showLabel="showLabel" />
            </a-drawer>
            <a-modal
                :title="$t('task.delivery.editRoute')"
                :visible="pointModal"
                :destroyOnClose="true"
                :closable="false"
                :zIndex="5000">
                <draggable
                    :list="pointsButton"
                    class="list-group modal_point_drag"
                    ghost-class="ghost"
                    @end="saveDrag()">
                    <a-button 
                        v-for="point in pointsButton"
                        :key="point.id"
                        block
                        type="dashed"
                        size="large"
                        class="draggable_icon flex items-center text-sm"
                        @click="selectPoint(point)">
                        <i class="fi fi-rr-arrows mr-2"></i>
                        <div class="truncate">
                            {{ point.point }} - {{ point.name }}
                        </div>
                    </a-button>
                </draggable>
                <template slot="footer">
                    <a-button 
                        type="primary"
                        block
                        size="large"
                        :loading="saveLoader"
                        @click="savePoints()">
                        {{ $t('task.delivery.save') }}
                    </a-button>
                </template>
            </a-modal>
        </template>
    </div>
</template>

<script>
import draggable from 'vuedraggable'
import { mapState } from 'vuex'
import eventBus from '@/utils/eventBus'
export default {
    components: {
        Map: () => import('./Map.vue'),
        draggable,
        List: () => import('./List.vue')
    },
    props: {
        task: {
            type: Object,
            required: true
        },
        isMobile: {
            type: Boolean,
            default: false
        },
        isOperator: {
            type: Boolean,
            default: false
        },
        hideDeliveryMap: {
            type: Boolean,
            default: true
        }
    },
    computed: {
        ...mapState({
            taskDrawerOptions: state => state.task.taskDrawerOptions,
            windowWidth: state => state.windowWidth,
        }),
        drawerWidth() {
            if(this.windowWidth > 764)
                return 600
            else 
                return '100%'
        },
        miniSize() {
            return this.taskDrawerOptions?.showMap || false
        },
        productTemplate() {
            if(this.isMobile)
                return () => import('./ProductList.vue')
            else
                return () => import('./ProductTable.vue')
        },
        productList() {
            if(this.goodsList?.length) {
                return this.goodsList

                // if(this.activeKey !== 'default')
                //     return this.goodsList.filter(f => f.id === this.activeKey)
                // else
                //     return this.goodsList
            } else
                return []
        },
        activeKey() {
            return this.activePoint ? this.activePoint.id : 'default'
        },
        activePointData() {
            if(this.activePoint) {
                const filter = this.deliveryPoints.filter(f => f.id === this.activePoint.id)
                return filter
            } else
                return null
        },
        waypoints() {
            if(this.deliveryPoints) {
                const delivery_points = JSON.parse(JSON.stringify(this.deliveryPoints))
                const first = delivery_points.shift()

                let points = []

                if(this.activePoint) {
                    const findIndex = delivery_points.findIndex(f => f.id === this.activePoint.id)
                    points = [
                        first
                    ]

                    delivery_points.forEach((item, index) => {
                        if(index <= findIndex)
                            points.push(item)
                    })
                } else {
                    points = [
                        first,
                        ...delivery_points
                    ]
                }
                return points
            } else 
                return []
        }
    },
    data() {
        return {
            activePoint: null,
            enabled: false,
            activeTab: 'route',
            pointsButton: [],
            edited: false,
            saveLoader: false,
            listEdit: false,
            drawerMap: false,
            mapInit: false,
            pointModal: false,
            goodsList: [],
            deliveryPoints: []
        }
    },
    async created() {
        await this.getLogisticData()

        if(this.isMobile) {
            this.activeTab = 'list'
        } else {
            if(this.task.logistic_tabs?.route)
                this.activeTab = 'route'
            else
                this.activeTab = 'list'
        }

        this.initButtons()
    },
    methods: {
        showTabMobile(mobile) {
            if(this.isMobile)
                return mobile || false
            return true
        },
        enabledEditPoints() {
            if(this.isMobile) {
                this.listEdit = true
                this.pointModal = true
            } else
                this.enabled = !this.enabled
        },
        afterVisibleChange() {
            if(!this.mapInit)
                this.mapInit = true
        },
        saveDrag() {
            const points = JSON.parse(JSON.stringify(this.pointsButton))
            points.unshift(this.deliveryPoints[0])
            this.$store.commit('task/TASK_CHANGE_FIELD', {
                key: 'delivery_points',
                value: points,
                task: this.task
            })
        },
        endDtrag() {
            this.listEdit = true
            this.saveDrag()
            this.edited = !this.edited
        },
        async savePoints() {
            if(this.listEdit) {
                try {
                    this.saveLoader = true
                    const data = await this.$store.dispatch('task/savePoints', {
                        task: this.task,
                        points: this.pointsButton
                    })
                    this.listEdit = false
                    this.enabled = false
                    if(this.pointModal)
                        this.pointModal = false

                    if(data?.update_fields) {
                        this.initButtons()
                    }
                } catch(e) {
                    console.log(e)
                } finally {
                    this.saveLoader = false
                }
            } else {
                this.listEdit = false
                this.enabled = false
            }
        },
        initButtons() {
            if(this.deliveryPoints) {
                const delivery_points = JSON.parse(JSON.stringify(this.deliveryPoints))
                delivery_points.shift()

                this.pointsButton = delivery_points
            }
        },
        showMap(point) {
            this.activeTab = this.isMobile ? 'list' : 'route'
            this.selectPoint(point)
        },
        showLabel(i) {
            return i + 2
        },
        selectPoint(point) {
            if(point === 'all')
                this.activePoint = null
            else
                this.activePoint = point

            this.edited = !this.edited
            eventBus.$emit('TASK_LOGISTICK_CHANGE_POINT', point)
        },
        async getLogisticData() {
            try {
                this.deliveryPoints = await this.$store.dispatch('task/getDeliveryPoints', { taskId: this.task.id})
                this.goodsList = await this.$store.dispatch('task/getDeliveryGoods', { taskId: this.task.id})
                // const {data} = await this.$http(`tasks/${this.task.id}/goods/`)
                //  = data

                // const response = await this.$http(`tasks/${this.task.id}/delivery_points/`)
                //  = response.data
            } catch(error) {
                console.log(error)
            }
        }
    }
}
</script>

<style lang="scss">
.task_delivery{
    .leaflet-control-attribution{
        display: none;
    }
    .delivery_points{
        .ant-btn{
            &:not(:last-child) {
                margin-right: 5px;
            }
        }
    }
}
.logist_map{
    .leaflet-control-attribution{
        display: none;
    }
    .ant-drawer-content,
    .ant-drawer-wrapper-body{
        overflow: hidden;
    }
    .ant-drawer-body{
        padding: 0px;
        height: calc(100% - 40px);
        .vue2leaflet-map{
            height: 100%;
        }
    }
}
</style>

<style lang="scss" scoped>
.ghost {
  opacity: 0.5;
  background: #88b0e2;
}
@mixin iconAnimate {
    cursor: all-scroll;
    &:nth-child(2n) {
        animation-name: keyframes1;
        animation-iteration-count: infinite;
        transform-origin: 50% 10%;
        -webkit-transition: all .2s ease-in-out;
    }
    &:nth-child(2n-1) {
        animation-name: keyframes2;
        animation-iteration-count: infinite;
        animation-direction: alternate;
        transform-origin: 30% 5%;
    }
    animation-delay: -0.65; 
    animation-duration: .20s
}
.modal_point_drag{
    .draggable_icon{
        &:not(:last-child){
            margin-bottom: 10px;
        }
    }
}
.enabled_drag{
    .draggable_icon{
        @include iconAnimate;
    }
}
.points_list{
    .item{
        &:not(:last-child){
            margin-bottom: 5px;
            padding-bottom: 5px;
            border-bottom: 1px solid var(--borderColor);
        }
    }
}

@keyframes keyframes1 {
    0% {
    transform: rotate(-1deg);
    animation-timing-function: ease-in;
    }

    50% {
    transform: rotate(1.5deg);
    animation-timing-function: ease-out;
    }
}

@keyframes keyframes2 {
    0% {
    transform: rotate(1deg);
    animation-timing-function: ease-in;
    }

    50% {
    transform: rotate(-1.5deg);
    animation-timing-function: ease-out;
    }
}
</style>