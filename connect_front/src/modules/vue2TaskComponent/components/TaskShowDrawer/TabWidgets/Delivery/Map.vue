<template>
    <l-map
        ref="task_map"
        :zoom="zoom"
        :style="`height: ${mapHeight}; width: 100%;`">
        <l-tile-layer 
            :url="url" 
            :attribution="attribution" />
        <l-routing-machine
            v-if="waypoints.length && waypoints[0]"
            :selectPoint="selectPoint"
            :pointDesc="pointDesc"
            ref="map_machine"
            :waypoints="waypoints"/>
        <l-control 
            v-if="isMobile" 
            :position="'topleft'">
            <div class="flex flex-col">
                <a-button 
                    :type="activeKey === 'default' ? 'primary' : 'default'"
                    class="mb-1"
                    @click="selectPoint('all')">
                    <i class="fi fi-rr-home-location-alt"></i>
                </a-button>
                <a-button 
                    v-for="(point, index) in pointsButton"
                    :key="point.id"
                    class="mb-1"
                    :type="activeKey === point.id ? 'primary' : 'default'"
                    @click="selectPoint(point)">
                    {{ showLabel(index) }}
                </a-button>
            </div>
        </l-control>
    </l-map>
</template>

<script>
import { LMap, LTileLayer, LControl } from 'vue2-leaflet'
import LRoutingMachine from './LRoutingMachine.vue'
import 'leaflet/dist/leaflet.css'
export default {
    components: {
        LMap,
        LTileLayer,
        LControl,
        LRoutingMachine,
    },
    props: {
        task: {
            type: Object,
            required: true
        },
        deliveryPoints: {
            type: Array,
            required: true
        },
        waypoints: {
            type: Array,
            default: () => []
        },
        selectPoint: {
            type: Function,
            default: () => {}
        },
        pointsButton: {
            type: Array,
            default: () => []
        },
        activeKey: {
            type: String,
            default: 'default'
        },
        showLabel: {
            type: Function,
            default: () => {}
        },
        isMobile: {
            type: Boolean,
            default: false
        }
    },
    computed: {
        mapHeight() {
            return this.isMobile ? '100%' : '600px'
        }
    },
    data() {
        return {
            tileToken: 'TxHF6NGutBdDCrc8gzQylV8ilVu8dy6BPIkYzmFfITFRxwih9lC2vNramKoaJ02s',
            url: `https://tile.jawg.io/jawg-sunny/{z}/{x}/{y}{r}.png?access-token=TxHF6NGutBdDCrc8gzQylV8ilVu8dy6BPIkYzmFfITFRxwih9lC2vNramKoaJ02s`, // https://www.jawg.io/lab/access-tokens
            attribution: '',
            zoom: 16
        }
    },
    created() {
        // this.selectPoint('all')
    },
    methods: {
        pointDesc(point) {
            const filter = this.deliveryPoints.filter(f => f.id === point.id)

            if(filter?.length) {
                let template = ``
                filter.forEach(item => {
                    let contractorNameTemplate = ``
                    item.orders.forEach(order => {
                        contractorNameTemplate += `
                            <p>${order.contractor.name}</p>`
                        // return contractorNameTemplate
                    })
                    template = template + `
                        <div class="map_clients">
                            <div class="item">
                                <span class="font-semibold">${this.$t('task.client')}:</span> ${contractorNameTemplate}
                            </div>
                            <div class="item">
                                <span class="font-semibold">${this.$t('task.address')}:</span> ${item.name}
                            </div>
                            ${point?.duration && `
                                <div class="item">
                                    <span class="font-semibold">${this.$t('task.delivery_time')}:</span> ${point.duration} мин
                                </div>    
                            `}
                            ${item?.orders?.[0]?.contractor?.phone && `
                                <div class="item">
                                    <span class="font-semibold">${this.$t('task.phone')}:</span> ${item.orders[0].contractor.phone}
                                </div>    
                            `}
                            ${item?.orders?.[0]?.contractor?.email && `
                                <div class="item">
                                    <span class="font-semibold">E-mail:</span> ${item.orders[0].contractor.email}
                                </div>    
                            `}
                        </div>
                    `
                })
                return template;
            } else
                return ''
        }
    }
}
</script>

<style lang="scss">
.map_clients{
    &:not(:last-child){
        margin-bottom: 5px;
        padding-bottom: 5px;
        border-bottom: 1px solid var(--borderColor);
    }
}
</style>