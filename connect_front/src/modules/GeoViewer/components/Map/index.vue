<template>
    <div class="h-full">
        <l-map
            ref="logist_map"
            :zoom="zoom"
            :center="center"
            :options="mapOptions"
            class="w-full h-full logist_map"
            @update:zoom="getMapCenter"
            @update:center="getMapCenter">
            <!-- <template v-if="logisticTaskRouting && logisticTaskRouting.length || logisticUserRouting && logisticUserRouting.length">
                <l-routing-machine
                    v-for="item in logisticTaskRouting"
                    :key="`${item.id}_routing_${reload}_${mapShowRouting}`"
                    :showMarkerPopup="showMarkerPopup"
                    :ref="`${item.id}_routing`"
                    :item="item"/>
                <l-routing-machine
                    v-for="item in logisticUserRouting"
                    :key="`${item.id}_routing_us_${reload}_${mapShowRouting}`"
                    :showMarkerPopup="showMarkerPopup"
                    :ref="`${item.id}_routing`"
                    :item="item"/>
            </template>
            <template v-else>
                <template v-if="activeTab === 'task'">
                    <l-marker
                        v-for="point in pointsData"
                        :key="point.id"
                        :lat-lng="[point.next_delivery_point.lat, point.next_delivery_point.lon]"
                        :ref="`marker_${point.id}`"
                        class="task_marker"
                        @mouseover="pointMouseover(point)"
                        @mouseleave="pointMouseleave(point)"
                        @click="getDeliveryPoints(point)">
                        <l-icon
                            class-name="marker_wrapper">
                            <div class="merker_icon">
                                <a-spin
                                    :spinning="taskPointLoader[point.id] ? true : false"
                                    size="small">
                                    <div
                                        class="marker_circle"
                                        :style="point.color && `background: ${point.color};`"></div>
                                </a-spin>
                                <div class="label">
                                    #{{ point.counter }}
                                </div>
                            </div>
                        </l-icon>
                        <l-popup>
                            <MapPopup :item="point" />
                        </l-popup>
                    </l-marker>
                </template>
            </template>
            <template v-if="mapClientsShow && mapClients.length">
                <l-marker
                    v-for="point in mapClients"
                    :key="point.id"
                    :lat-lng="[point.lat, point.lon]"
                    :ref="`client_${point.id}`"
                    class="client_marker">
                    <l-icon
                        class-name="client_marker_wrapper">
                        <div class="contractor_cluster">
                            <div class="circle_wrapper">
                                {{ point.contractors.length }}
                            </div>
                        </div>
                    </l-icon>
                    <l-popup :options="popupOptions" v-if="point.contractors.length">
                        <div class="client_popup_wrap">
                            <div
                                v-for="client in point.contractors"
                                class="client_item"
                                :key="`client_${client.id}`">
                                <ContractorCard
                                    :contractor=client
                                    :edit="false"
                                    :cart="true"
                                    :deliveryPointAddress=point.name
                                    :deliveryPointID=point.id />
                            </div>
                        </div>
                    </l-popup>
                </l-marker>
            </template>

            <template v-if="userLocation.length">
                <l-marker
                    v-for="driver in userLocation"
                    :key="driver.user.uuid"
                    :lat-lng="driver.location"
                    class="driver_marker">
                    <l-icon
                        class-name="driver_marker_wrapper">
                        <DriverMarker :driver="driver"/>
                    </l-icon>
                    <l-tooltip>
                        <div>{{ driver.user.first_name && driver.user.first_name }} {{ driver.user.last_name && driver.user.last_name }}</div>
                        <div v-if="driver.disconnected" class="mt-1">
                            Соединение потеряно: {{ $moment(driver.disconnectedDate).format('DD.MM.YYYY HH:mm:ss') }}
                        </div>
                        <template v-else>
                            <div v-if="driver.sdate" class="mt-1">
                                Последнее обновление: {{ $moment(driver.sdate).format('DD.MM.YYYY HH:mm:ss') }}
                            </div>
                        </template>
                    </l-tooltip>
                </l-marker>
            </template> -->

            <l-tile-layer
                :url="tileUrl"
                :attribution="attribution" />
            <l-control :position="'topleft'" :zIndex=900>
                <div class="flex flex-col">
                    <a-button
                        class="ant-btn-icon-only mb-1"
                        v-tippy="{ inertia : true}"
                        content="Развернуть карту"
                        :class="!mapFull && 'opacity-50'"
                        @click="mapToggleFull()">
                        <i class="fi fi-rr-expand"></i>
                    </a-button>
                    <a-button
                        class="ant-btn-icon-only mb-1"
                        v-tippy="{ inertia : true}"
                        content="Начальная позиция"
                        @click="mapReinitPosition()">
                        <i class="fi fi-rr-search-location"></i>
                    </a-button>
                </div>
            </l-control>
            <v-marker-cluster 
                style="width: 100px; background: #000;"
                :options="clusterOptions">
                <template 
                    v-for="task in mapLocatedTasks">
                    <l-marker 
                        v-for="point in task.task_points" 
                        :key="point.lat" 
                        :lat-lng="[point.lat, point.lon]"
                        :options="{task: task}"
                        class="client_marker">          
                        
                        <l-icon
                            class-name="marker_wrapper">
                            <div class="merker_icon">
                                <!-- <a-spin
                                    :spinning="taskPointLoader[point.id] ? true : false"
                                    size="small">
                                </a-spin> -->
                                <div
                                    class="marker_circle"
                                    :style="task.status.hex_color && `background: ${task.status.hex_color};`"></div>
                                <div class="label">
                                    #{{ task.counter }}
                                </div>
                            </div>
                        </l-icon>
                        <l-popup>
                            <MapPopup :item="task" />
                        </l-popup>

                    </l-marker>
                </template>

            </v-marker-cluster>
        </l-map>
        <!-- <selectWarehouseDrawer
            page_name="catalogs.list_warehouses_page"
            :markedWarehouseHandler="markedWarehouseHandler"
            :warehouseList="warehouseList"
            ref="selectWarehouseDrawer" /> -->
    </div>
</template>

<script>
import { LMap, LTileLayer, LIcon, LControl, LPopup, LMarker, LTooltip } from 'vue2-leaflet'
import { latLng, Icon, icon } from 'leaflet'
import Vue2LeafletMarkercluster from 'vue2-leaflet-markercluster'
import "leaflet.markercluster/dist/MarkerCluster.css"

// import "leaflet.markercluster/dist/MarkerCluster.Default.css"

// import iconUrl from 'leaflet/dist/images/marker-icon.png'
// import shadowUrl from 'leaflet/dist/images/marker-shadow.png'

import MapPopup from './MapPopup.vue'
import eventBus from '@/utils/eventBus'
// import LRoutingMachine from './LRoutingMachine.vue'
// import DriverMarker from './DriverMarker.vue'
// import ContractorCard from '@apps/Dashboard/components/Sidebar/ContractorCard.vue'
// import selectWarehouseDrawer from '@apps/Orders/views/CreateOrder/widgets/selectWarehouseDrawer.vue'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import { mapState, mapActions } from 'vuex'
import { priceFormatter } from '@/utils'
let timer;
let timer2;

export default {
    props: {
        taskList: {
            type: Array,
            default: () => []
        },
        hoversPoint: {
            type: Object,
            default: () => null
        },
        activePoint: {
            type: Object,
            default: () => null
        },
        toggleOrderSidebar: {
            type: Function,
            default: () => {}
        },
        showOrderSidebar: {
            type: Boolean,
            default: true
        }
    },
    components: {
        LMap,
        LTileLayer,
        LControl,
        LPopup,
        MapPopup,
        // LTooltip,
        // LRoutingMachine,
        LMarker,
        LIcon,
        // DriverMarker,
        // ContractorCard,
        // selectWarehouseDrawer,
        'v-marker-cluster': Vue2LeafletMarkercluster,

    },
    computed: {
        ...mapState({
            // geoTasks: state => state.task.taskList['geo_tasks'],
            selectRouting: state => state.monitor.selectRouting,
            config: state => state.config.config,
            mapLocatedTasks: state => state.geoviewer.mapLocatedTasks,
            taskPointLoader: state => state.monitor.taskPointLoader,
            taskOpen: state => state.monitor.taskOpen,
            mapShowRouting: state => state.monitor.mapShowRouting,
            logisticUsers: state => state.monitor.logisticUsers,
            activeTab: state => state.monitor.activeTab,
            mapClientRequest: state => state.monitor.mapClientRequest,
            mapOWRequest: state => state.monitor.mapOWRequest,
            mapClients: state => state.monitor.mapClients,
            mapClientsShow: state => state.monitor.mapClientsShow,
            mapOWShow: state => state.monitor.mapOWShow,
            mapTasksShow: state => state.monitor.mapTasksShow,
            mConfig: state => state.monitor.config,
            mapFull: state => state.monitor.mapFull,
            userLocation: state => state.monitor.userLocation,
            mapOW: state => state.monitor.mapOW
        }),
        orderMap() {
            return this.mapOW?.orders?.length ? this.mapOW.orders : []
        },
        warehousesMap() {
            return this.mapOW?.warehouses?.length ? this.mapOW.warehouses : []
        },
        tileToken() {
            return this.config.map?.tileToken || null
        },
        url() {
            return this.config.map?.tileUrl || null // https://www.jawg.io/lab/access-tokens
        },
        tileUrl() {
            return `${this.url}${this.tileToken && `?access-token=${this.tileToken}`}`
        },
        // pointsData () {
        //     return this.logisticTask.filter(f => f.next_delivery_point && f.showInMap)
        // },
        points() {
            return this.pointsData.map(point => {
                return [point.next_delivery_point.lat, point.next_delivery_point.lon]
            })
        },
        // logisticTaskRouting() {
        //     return this.logisticTask.filter(f => f.routing?.length) || []
        // },
        // logisticUserRouting() {
        //     return this.logisticUsers.filter(f => f.routing?.length) || []
        // },
        // logisticTaskRoutingPoints() {
        //     if(this.logisticTaskRouting?.length) {
        //         let pointsArray = []

        //         this.logisticTaskRouting.forEach(task => {
        //             if(task.routing?.length) {
        //                 pointsArray = [
        //                     ...pointsArray,
        //                     ...task.routing.map(point => {
        //                         return [point.lat, point.lon]
        //                     })
        //                 ]
        //             }
        //         })
        //         return pointsArray
        //     } else {
        //         return []
        //     }
        // },
    },
    data() {
        return {
            center: this.mConfig?.map?.center || [40.6507984910922,-2.3281584814678657],
            attribution: '',
            zoom: this.mConfig?.map?.zoom || 3,
            reload: Date.now(),
            markerLoader: false,
            showMarkerPopup: true,
            currentCenter: null,
            mapOptions: {
                attributionControl: false,
                closePopupOnClick: false
            },
            popupOptions: {
                className: 'popup_contractor_card',
                autoClose: false,
                closeOnClick: false,
            },
            warehousePopupOptions: {
                className: 'popup_contractor_card',
                autoClose: true,
                closeOnClick: false,
            },
            warehouseList: [],
            warehouseLoader: false,
            markedOrder: null,
            loaderOW: false,

            clusterOptions: {
                iconCreateFunction: this.iconCreateFunction
            },
            initialLocation: latLng(-34.9205, -57.953646),
        }
    },
    async created() {
        if(typeof JSON.parse(localStorage.getItem('monitor_popup')) === 'boolean') {
            this.showMarkerPopup = JSON.parse(localStorage.getItem('monitor_popup'))
        }
        // if(this.mapClientsShow) {
        // this.getMapClientsCenter()
        // }
        // if(this.mapOWShow) {
        //     this.getMapOWCenter()
        // }

        
        await this.getMapLocatedTasks()
    },
    methods: {
        priceFormatter,
        async getMapLocatedTasks() {
            // if(this.mapClientsShow) {
            // try {
            //     await this.$store.dispatch('geoviewer/getMapLocatedTasks')
            // } catch(error) {
            //     console.error(error)
            // }
            
            clearTimeout(timer)
            if(this.mapClientRequest) {
                this.mapClientRequest.cancel()
                this.$store.commit('geoviewer/SET_MAP_CLIENT_REQUEST', null)
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
                            this.$store.commit('geoviewer/SET_MAP_BORDERS', {
                                lat__gte, lat__lte, lon__gte, lon__lte
                            })
                            await this.$store.dispatch('geoviewer/getMapLocatedTasks', {
                                lat__gte,
                                lat__lte,
                                lon__gte,
                                lon__lte,
                            })
                        } catch(e) {
                            console.log(e)
                        }
                    }
                })
            }, 500)
            // }
        },
        iconCreateFunction(cluster) {
            let childCount = cluster.getChildCount();
            let c = ' marker-cluster-';
            if (childCount < 10) {
                c += 'small';
            } else if (childCount < 100) {
                c += 'medium';
            } else {
                c += 'large';
            }
            
            let stats = {}
            this.getChildMarkers(cluster, stats)

            const iconSize = 50
            const iconRadius = iconSize/2
            const iconCenter = {
                x: iconRadius,
                y: iconRadius
            }
            const canvas = document.createElement('canvas')
            const ctx = canvas.getContext('2d')
            canvas.width = iconSize
            canvas.height = iconSize
            const baseStartAngle = -Math.PI/2
            const baseEndAngle = 1.5*Math.PI
            
            let color = "#fff"
            this.drawSector(ctx, iconCenter, iconRadius, baseStartAngle, baseEndAngle, color)

            let end = -Math.PI/2
            let start = baseStartAngle
            const outsideOffset = 4
            for (let statusCode in stats) {
                color = stats[statusCode].color
                const ratio = stats[statusCode].count/childCount
                end += 2*Math.PI * ratio
                this.drawSector(ctx, iconCenter, iconRadius-outsideOffset, start, end, color)
                start = end      
            }

            color = "#fff"
            this.drawSector(ctx, iconCenter, iconRadius/1.8, baseStartAngle, baseEndAngle, color)


            const template = document.createElement('template')
            const clusterWrapper = document.createElement('div')
            clusterWrapper.classList.add('cluster_wrapper')
            const label = document.createElement('span')
            label.textContent = childCount
            label.classList.add('cluster_label')

            clusterWrapper.appendChild(canvas)
            clusterWrapper.appendChild(label)
            template.appendChild(clusterWrapper)
            
            const clusterNode = template.firstChild

            return new L.DivIcon({ 
                html: clusterNode, 
                className: 'marker-cluster task-marker-cluster', 
                iconSize: new L.Point(iconSize, iconSize) 
            })
        },
        getChildMarkers(cluster, stats) {
            const childClusters = cluster._childClusters
            if (cluster._markers.length)
                this.getMarkerStats(cluster, stats)
            if (childClusters.length)
                for (let childCluster of childClusters)
                    this.getChildMarkers(childCluster, stats)
        },
        getMarkerStats(cluster, stats) {
            for (let marker of cluster._markers) {
                const statusCode = marker.options.task.status.code
                if (stats[statusCode]) {
                    stats[statusCode].count++
                    stats[statusCode].color = marker.options.task.status.hex_color

                } else {
                    stats[statusCode] = {
                        count: 1,
                        color: marker.options.task.status.hex_color
                    }
                }
            }

        },
        /**
         * Рисует сектор круга
         *
         * @param {CanvasRenderingContext2D} ctx - Контекст канваса
         * @param {Object} center - Центр круга
         * @param {number} center.x - кордината центра x 
         * @param {number} center.y - кордината центра y
         * @param {number} radius - Радиус
         * @param {number} start - Начальный угол
         * @param {number} end - Конечный угол
         * @param {string} color - Цвет сектора
         */
        drawSector(ctx, center, radius, start, end, color) {
            ctx.fillStyle = color
            ctx.beginPath()
            ctx.arc(center.x, center.y, radius, start, end)
            ctx.lineTo(center.x, center.y)
            ctx.fill()
            ctx.closePath()
        },        
        // draweSector(ctx, center, radius, ratio, color) {
        //     ctx.fillStyle = color
        //     ctx.beginPath()
        //     ctx.arc(center.x, center.y, radius, -Math.PI/2, 2*Math.PI * ratio)
        //     ctx.lineTo(center.x, center.y)
        //     ctx.fill()
        //     ctx.closePath()
        // },

        // getPopupContainer() {
        //     return this.$refs[`point_card_${this.item.id}`]
        // },
        // async checkOpenOrder(order){
        //     try {
        //         const { data } = await this.$http.get(`/crm/orders/${order.id}/action_info/`)
        //         if(data?.actions?.edit) {
        //             eventBus.$emit('orderEdit', order)
        //         } else {
        //             this.openOrder(order)
        //         }
        //     } catch(e) {
        //         console.log(e)
        //         this.openOrder(order)
        //     } finally {
        //         this.loading = false
        //     }
        // },
        // openOrder(order) {
        //     const query = Object.assign({}, this.$route.query)

        //     if(!query?.order || query.order !== order.id) {
        //         query.order = order.id
        //         this.$router.push({query})
        //     }
        // },
        // async getWarehouseList() {
        //     try {
        //         this.warehouseLoader = true
        //         const { data } = await this.$http.get("/catalogs/warehouses/")
        //         if(data.results) {
        //             this.warehouseList = data.results
        //         }
        //     } catch(e) {
        //         console.log(e)
        //     } finally {
        //         this.warehouseLoader = false
        //     }
        // },
        // async markedWarehouseHandler(warehouseID) {
        //     try {
        //         if(this.markedOrder) {
        //             const { data } = await this.$http.put(`/crm/orders/${this.markedOrder.id}/set_warehouse/`, {
        //                 warehouse: warehouseID
        //             })
                    
        //             if(data.status === 200) {
        //                 let pointIndex, orderIndex
        //                 const orderID = this.markedOrder.id
        //                 const warehouse = this.warehouseList.find(f => f.id === warehouseID)

        //                 pointIndex = this.mapOW.orders.findIndex(point => point.orders.findIndex(order => order.id === this.markedOrder.id) !== -1)

        //                 if(pointIndex !== -1) {
        //                     orderIndex = this.mapOW.orders[pointIndex].orders.findIndex(order => order.id === this.markedOrder.id)
        //                 }
                        
        //                 if(pointIndex !== -1  && orderIndex !== -1 && warehouse) {
        //                     this.$store.commit('monitor/SET_MAP_OW_ORDER_WAREHOUSE', {pointIndex, orderIndex, warehouse})
        //                     this.$store.commit('monitor/CHANGE_WAREHOUSE_IN_ORDER_DATA', {orderID, warehouse})
        //                     this.$message.info(`Заказ ${this.markedOrder.counter} успешно обновлен`)
        //                 }
                        
        //                 this.markedOrder = null
        //             } else {
        //                 this.$message.error(`${data.data}`)
        //             }
        //         }
        //     } catch(e) {
        //         console.log(e)
        //     }
        // },
        // async selestWarehouse(order) {
        //     this.markedOrder = order
        //     if(!this.warehouseList?.length) {
        //         await this.getWarehouseList()
        //     }
        //     this.$nextTick(() => {
        //         if(this.$refs['selectWarehouseDrawer']) {
        //             this.$refs['selectWarehouseDrawer'].toggleDrawer()
        //         }
        //     })
        // },
        // checkDriverAvatar(driver) {
        //     if(driver?.user?.avatar) {
        //         return `${window.location.origin}/media/avatars/${driver.user.avatar}`
        //     } else
        //         return null
        // },
        // getMapClientsCenter() {
        //     // if(this.mapClientsShow) {
        //     //     clearTimeout(timer)
        //     //     if(this.mapClientRequest) {
        //     //         this.mapClientRequest.cancel()
        //     //         this.$store.commit('monitor/SET_MAP_CLIENT_REQUEST', null)
        //     //     }

        //     timer = setTimeout(() => {
        //         this.$nextTick(async () => {
        //             if(this.$refs['logist_map']?.mapObject) {
        //                 try {
        //                     const map = this.$refs['logist_map'].mapObject
        //                     const lat__gte = map.getBounds().getSouth()
        //                     const lat__lte = map.getBounds().getNorth()
        //                     const lon__gte = map.getBounds().getWest()
        //                     const lon__lte = map.getBounds().getEast()
        //                     this.$store.commit('geoviewer/SET_MAP_BORDERS', {
        //                         lat__gte, lat__lte, lon__gte, lon__lte
        //                     })
        //                     await this.$store.dispatch('monitor/getMapClients', {
        //                         lat__gte,
        //                         lat__lte,
        //                         lon__gte,
        //                         lon__lte
        //                     })

        //                 } catch(e) {
        //                     console.log(e)
        //                 }
        //             }
        //         })
        //     }, 500)
        //     // }
        // },
        // getMapOWCenter() {
        //     this.$store.commit('monitor/SET_LOADER_OW_ON')
        //     if(this.mapOWShow) {
        //         clearTimeout(timer2)
        //         if(this.mapOWRequest) {
        //             this.mapOWRequest.cancel()
        //             this.$store.commit('monitor/SET_MAP_OW_REQUEST', null)
        //         }

        //         timer2 = setTimeout(() => {
        //             this.$nextTick(async () => {
        //                 if(this.$refs['logist_map']?.mapObject) {
        //                     try {
        //                         const map = this.$refs['logist_map'].mapObject
        //                         const lat__gte = map.getBounds().getSouth()
        //                         const lat__lte = map.getBounds().getNorth()
        //                         const lon__gte = map.getBounds().getWest()
        //                         const lon__lte = map.getBounds().getEast()

        //                         await this.$store.dispatch('monitor/getMapOrderAndWarehouse', {
        //                             lat__gte,
        //                             lat__lte,
        //                             lon__gte,
        //                             lon__lte
        //                         })
        //                     } catch(e) {
        //                         console.log(e)
        //                     } finally {
        //                         this.$store.commit('monitor/SET_LOADER_OW_OFF')
        //                     }
        //                 }
        //             })
        //         }, 500)
        //     }
        // },
        getMapCenter() {
            eventBus.$emit('MOVE_GEOTASK_MAP')
            // this.getMapClientsCenter()
            // this.getMapOWCenter()
            this.getMapLocatedTasks()
        },
        zoomUpdated() {
            this.getMapCenter()
        },
        // mapToggleShowPopup() {
        //     this.$nextTick(() => {
        //         this.showMarkerPopup = !this.showMarkerPopup
        //         localStorage.setItem('monitor_popup', this.showMarkerPopup)

        //         if(this.showMarkerPopup) {
        //             this.logisticTaskRouting.forEach(route => {
        //                 if(this.$refs[`${route.id}_routing`]?.[0]) {
        //                     this.$refs[`${route.id}_routing`][0].openAllPopup()
        //                 }
        //             })
        //         } else {
        //             this.logisticTaskRouting.forEach(route => {
        //                 if(this.$refs[`${route.id}_routing`]?.[0]) {
        //                     this.$refs[`${route.id}_routing`][0].hideAllPopup()
        //                 }
        //             })
        //         }
        //     })
        // },
        // mapToggleFull() {
        //     this.$store.commit('monitor/SET_MAP_FULL', !this.mapFull)
        // },
        // mapToggleClientsShow() {
        //     this.$store.commit('monitor/SET_MAP_CLIENTS_SHOW', !this.mapClientsShow)
        //     if(!this.mapClientsShow) {
        //         this.$store.commit('monitor/SET_MAP_CLIENT', [])
        //     } else {
        //         this.getMapClientsCenter()
        //     }
        // },
        // mapToggleOWShow() {
        //     this.$store.commit('monitor/SET_MAP_OW_SHOW', !this.mapOWShow)
        //     if(!this.mapOWShow) {
        //         this.$store.commit('monitor/SET_MAP_OW', null)
        //     } else {
        //         this.getMapOWCenter()
        //     }
        // },
        // mapToggleTesksShow() {
        //     this.$store.commit('monitor/SET_MAP_TASKS_SHOW', !this.mapTasksShow)
        //     this.$store.commit('monitor/SET_VISIBILITY_LOGISTIC_TASK', this.mapTasksShow)
        //     this.getMapOWCenter()
        // },
        // mapToggleShowRouting() {
        //     this.$store.commit('monitor/SET_MAP_SHOW_ROUTING', !this.mapShowRouting)
        // },
        // pointMouseover(point) {
        //     this.$nextTick(() => {
        //         this.$refs[`marker_${point.id}`][0].mapObject.openPopup()
        //     })
        // },
        // pointMouseleave(point) {
        //     this.$nextTick(() => {
        //         this.$refs[`marker_${point.id}`][0].mapObject.closePopup()
        //     })
        // },
        // async getDeliveryPoints(task) {
        //     try {
        //         this.$store.commit('monitor/SET_POPUP_MARKER_LOADER', {
        //             task,
        //             value: true
        //         })
        //         await this.$store.dispatch('monitor/getDeliveryPoints', {
        //             task,
        //             showPoint: true
        //         })
        //     } catch(e) {
        //         console.log(e)
        //     } finally {
        //         this.$store.commit('monitor/SET_POPUP_MARKER_LOADER', {
        //             task,
        //             value: false
        //         })
        //     }
        // },
        // mapReinitPosition() {
        //     this.$nextTick(() => {

        //         let markersPoints = []
        //         this.$refs['logist_map'].mapObject.eachLayer((layer) => {
        //             if(layer instanceof L.Marker) {
        //                 markersPoints.push(layer._latlng)
        //             }
        //         })

        //         if(markersPoints.length) {
        //             const bounds = L.latLngBounds(markersPoints)

        //             let width = 0,
        //                 maxZoom = 12

        //             if(this.taskOpen) {
        //                 width = 400
        //                 maxZoom = 11
        //             }

        //             const options = {
        //                 maxZoom,
        //                 paddingBottomRight: [width, 0]
        //             }
        //             if(this.logisticTaskRouting?.length) {
        //                 this.$refs['logist_map'].fitBounds(bounds, options)
        //             } else {
        //                 if(this.pointsData?.length) {
        //                     this.$refs['logist_map'].fitBounds(bounds, options)
        //                 }
        //             }
        //         }
        //     })
        // },
        // showPopup(point) {
        //     this.$refs['logist_map'].mapObject.setView({lat: +point.lat, lng: +point.lon})
        //     if(!this.mapOWShow) {
        //         this.mapToggleOWShow()
        //     }
        //     this.$nextTick(() => {
        //         if(this.$refs[`popup_${point.id}`][0]?.mapObject) {
        //             this.$refs[`popup_${point.id}`][0].mapObject.toggle()
        //         } else {
        //             this.$message.info('Данные не загружены')
        //         }
        //     })
        // },
        setCenter(point) {
            this.$refs['logist_map'].mapObject.setView(new L.LatLng(point.lat, point.lon));
        }
    },
    mounted() {
        eventBus.$on('SET_LEFT_PADDING', value => {
            const bounds = L.latLngBounds([this.points])
            this.$refs['logist_map'].fitBounds(bounds, {
                maxZoom: 17,
                paddingTopLeft: [value, 0]
            })
        })
        eventBus.$on('SET_START_POSITION', () => {
            this.mapReinitPosition()
        })
        eventBus.$on('mapReinitPosition', () => {
            this.mapReinitPosition()
        })
        eventBus.$on('routingReinit', () => {
            this.reload = Date.now()
        })
        eventBus.$on('show_popup', (point) => {
            this.showPopup(point)
        })
        eventBus.$on('update_ow_list', () => {
            this.getMapOWCenter()
        })
        eventBus.$on('setCenter', (point) => {
            this.setCenter(point)
        })
        

        
        
    },
    beforeUpdate() {
        // console.log(document)
        // let ctx = document.querySelector('.test-canvas').getContext('2d')
    
        // ctx.fillStyle = "rgb(200,0,0)";
        // ctx.fillRect (10, 10, 55, 50);

    },
    beforeDestroy() {
        eventBus.$off('SET_LEFT_PADDING')
        eventBus.$off('SET_START_POSITION')
        eventBus.$off('mapReinitPosition')
        eventBus.$off('routingReinit')
        eventBus.$off('show_popup')
        eventBus.$off('setCenter')
        eventBus.$off('update_ow_list')
    }
}
</script>

<style lang="scss" scoped>


.client_item{
    &:not(:last-child){
        margin-bottom: 10px;
        padding-bottom: 10px;
        border-bottom: 1px solid var(--border2);
    }
    &.client_info{
        &:not(:last-child){
            margin-bottom: 6px;
        }
    }
}
.client_popup_wrap{
    max-height: 200px;
    overflow-y: auto;
}
.client_marker_wrapper{
    .contractor_cluster{
        width: 30px;
        height: 30px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        color: #fff;
        font-size: 14px;
        font-weight: 600;
        box-shadow: 0 2px 8px rgb(0 0 0 / 15%);
        border: 2px solid #ec4949;
        .circle_wrapper{
            background: #ec4949;
            width: 23px;
            height: 23px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
        }
    }
}
.order_marker_wrapper{
    .contractor_cluster{
        align-items: center;
        background-color: #7b1fa2;
        border-radius: 50%;
        display: flex;
        font-size: 14px;
        gap: 15px;
        height: 30px;
        justify-content: center;
        padding: 4px;
        position: relative;
        width: 30px;
        color: #fff;
        &::after{
            border-left: 9px solid transparent;
            border-right: 9px solid transparent;
            border-top: 9px solid #7b1fa2;
            content: "";
            height: 0;
            left: 50%;
            position: absolute;
            top: 90%;
            transform: translate(-50%);
            width: 0;
            z-index: 1;
        }
    }
}
.warehouses_marker_wrapper{
    .contractor_cluster{
        align-items: center;
        background-color: #0288d1;
        border-radius: 50%;
        display: flex;
        font-size: 14px;
        gap: 15px;
        height: 30px;
        justify-content: center;
        padding: 4px;
        position: relative;
        width: 30px;
        color: #fff;
        &::after{
            border-left: 9px solid transparent;
            border-right: 9px solid transparent;
            border-top: 9px solid #0288d1;
            content: "";
            height: 0;
            left: 50%;
            position: absolute;
            top: 90%;
            transform: translate(-50%);
            width: 0;
            z-index: 1;
        }
    }
}
.marker_wrapper{
    .merker_icon{
        background: rgba(255, 255, 255, 0.9);
        display: flex;
        align-items: center;
        padding: 4px;
        border-radius: 30px;
        box-shadow: 0 2px 8px rgb(0 0 0 / 15%);
        .marker_circle{
            width: 23px;
            height: 23px;
            border-radius: 50%;
            background: rgb(29, 101, 192);
        }
        .label{
            font-size: 16px;
            padding-left: 6px;
            padding-right: 6px;
        }
        .ow_marker_circle{
            width: 23px;
            min-width: 23px;
            height: 23px;
            border-radius: 50%;
            background: #7b1fa2;
            display: flex;
            align-items: center;
            justify-content: center;
            color: rgb(255 255 255);
            font-weight: 700;
        }
        .ow_label{
            font-size: 10px;
            padding-left: 6px;
            padding-right: 6px;
        }
        .goods_content {
            width: 65px;
        }
    }
}
</style>

<style lang="scss">
.task-marker-cluster {
    .cluster_wrapper {
        position: relative;
        .cluster_label {
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
        }
    }

    // margin: -50%;
}

.popup_contractor_card {
    .leaflet-popup-content{
        margin: 0px;
    }
    .client_popup_wrap{
        max-height: 250px;
        overflow-y: auto;
    }
    .title{
        font-size: 15px;
    }
    .contact{
        font-size: 12px;
    }
    .cart{
        font-size: 25px;
    }
    .info_tag{
        font-size: 12px;
    }
    .contractor_card{
        margin-bottom: 0;
    }
    .ant-card-bordered{
        border: 0px;
    }
    .ant-card{
        border: 0px;
    }
}
.logist_map{
    .leaflet-popup{
        &:hover{
            z-index: 99999!important;
        }
    }
    .leaflet-popup-content-wrapper{
        border-radius: var(--borderRadius);
    }
    .leaflet-top{
        &.leaflet-right{
            bottom: 0;
            top: initial;
            left: 0;
            right: initial;
            .leaflet-bar{
                margin-right: 0px!important;
                margin-top: 0px!important;
                margin-left: 10px;
                margin-bottom: 10px;
            }
        }
    }
}
.marker_wrapper{
    width: initial!important;
}
.order_popup_wrap{
    padding: 5px;
    .list {
        max-height: 40vh;
        overflow-y: auto;
    }
    h5{
        font-size: 16px;
        font-weight: bold;
        margin-bottom: 5px;
    }
    .o_item{
        &:not(:last-child){
            padding-bottom: 8px;
            margin-bottom: 8px;
            border-bottom: 1px solid var(--border2);
        }
        &__value{
            &:not(:last-child){
                margin-bottom: 5px;
            }
        }
        &__green{
            color: green;
        }
        &__red{
            color: red;
        }
    }
}
.warehouses_popup_wrap{
    padding: 5px;
    h5{
        font-size: 16px;
        font-weight: bold;
        margin-bottom: 10px;
    }
    .w_item{
        &:not(:last-child){
            padding-bottom: 8px;
            margin-bottom: 8px;
            border-bottom: 1px solid var(--border2);
        }
        &__value{
            &:not(:last-child){
                margin-bottom: 5px;
            }
        }
    }
}
</style>