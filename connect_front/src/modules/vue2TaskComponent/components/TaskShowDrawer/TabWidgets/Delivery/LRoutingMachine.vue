<template>
    <div style="display: none">
        <slot v-if="ready"></slot>
    </div>
</template>
  
<script>
import L from 'leaflet'
import { IRouter, IGeocoder, LineOptions } from 'leaflet-routing-machine'
import { findRealParent } from 'vue2-leaflet'
import { mapState } from 'vuex'
import 'leaflet-routing-machine/dist/leaflet-routing-machine.css'
const showLabel = (i) => {
    return i + 1
}

const props = {
    visible: {
        type: Boolean,
        default: true
    },
    waypoints: {
        type: Array,
        required: true
    },
    router: {
        type: IRouter
    },
    plan: {
        type: L.Routing.Plan
    },
    geocoder: {
        type: IGeocoder
    },
    fitSelectedRoutes: {
        type: [String, Boolean],
        default: 'smart'
    },
    lineOptions: {
        type: LineOptions
    },
    routeLine: {
        type: Function
    },
    autoRoute: {
        type: Boolean,
        default: true
    },
    routeWhileDragging: {
        type: Boolean,
        default: false
    },
    routeDragInterval: {
        type: Number,
        default: 500
    },
    waypointMode: {
        type: String,
        default: 'connect'
    },
    useZoomParameter: {
        type: Boolean,
        default: false
    },
    showAlternatives: {
        type: Boolean,
        default: false
    },
    altLineOptions: {
        type: LineOptions
    },
    selectPoint: {
        type: Function,
        default: () => {}
    },
    pointDesc: {
        type: Function,
        default: () => {}
    }
}
export default {
    props,
    name: 'LRoutingMachineMonitor',
    computed: {
        ...mapState({
            config: state => state.config.config
        }),
        seriveUrl() {
            return this.config?.map?.serviceUrl ? this.config.map.serviceUrl : null
        }
    },
    data() {
        return {
            parentContainer: null,
            ready: false,
            layer: null
        }
    },
    methods: {
        add () {
            if (this.parentContainer._isMounted) {
                const {
                    waypoints,
                    fitSelectedRoutes,
                    autoRoute,
                    routeWhileDragging,
                    routeDragInterval,
                    waypointMode,
                    useZoomParameter,
                    showAlternatives
                } = this

                const options = {
                    language: 'ru',
                    waypoints,
                    fitSelectedRoutes,
                    autoRoute,
                    routeWhileDragging,
                    routeDragInterval,
                    waypointMode,
                    collapsible: true,
                    show: false,
                    useZoomParameter,
                    collapseBtn: function(itinerary) {
                        var collapseBtn = L.DomUtil.create('span', itinerary.options.collapseBtnClass);
                        L.DomEvent.on(collapseBtn, 'click', itinerary._toggle, itinerary);
                        itinerary._container.insertBefore(collapseBtn, itinerary._container.firstChild);
                    },
                    createMarker:  (i, waypoint, n) => {
                        switch (i) {
                        case 0:
                            return L.marker(waypoint.latLng, {
                                draggable: false,
                                bounceOnAdd: false,
                                icon: L.divIcon({
                                    className: 'map-marker',
                                    iconSize:null,
                                    html:`
                                    <div class="map_marker start">
                                        ${showLabel(i)}
                                    </div>
                                `
                                })
                            }).bindTooltip(`${this.$t('task.map_start_point')}: ${waypoints[i].name}`)
                        case n - 1:
                            return L.marker(waypoint.latLng, {
                                draggable: false,
                                bounceOnAdd: false,
                                icon: L.divIcon({
                                    className: 'map-marker',
                                    iconSize:null,
                                    html:`
                                        <div class="map_marker end"> 
                                            ${showLabel(i)}
                                        </div>
                                    `
                                })
                            })
                                .bindTooltip(`<div class="mb-1">${this.$t('task.map_end_point')}:</div>${this.pointDesc(waypoints[i])}`)
                                .on('click', (e) => {
                                    this.selectPoint(waypoints[i])
                                })
                        default:
                            return L.marker(waypoint.latLng, {
                                draggable: false,
                                bounceOnAdd: false,
                                icon: L.divIcon({
                                    className: 'map-marker',
                                    iconSize:null,
                                    html:`
                                            <div class="map_marker 1">  
                                                ${showLabel(i)}
                                            </div>
                                        `
                                })
                            })
                                .bindTooltip(`<div class="mb-1">${this.$t('task.map_intermediate_point')}:</div>${this.pointDesc(waypoints[i])}`)
                                .on('click', (e) => {
                                    this.selectPoint(waypoints[i])
                                })
                        }
                    }
                }

                if(this.seriveUrl)
                    options.serviceUrl = this.seriveUrl

                const { mapObject } = this.parentContainer
                const routingLayer = L.Routing.control(options)
                routingLayer.addTo(mapObject)
                this.layer = routingLayer
            }
        },
        init() {
            this.parentContainer = findRealParent(this.$parent)
            this.add()
            this.ready = true
        }
    },
    mounted() {
        this.init()
        console.log()
    },
    beforeDestroy() {
        return this.layer ? this.layer.remove() : null
    }
}
</script>

<style lang="scss">
.leaflet-routing-container-hide .leaflet-routing-collapse-btn{
    background-image: url('data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAACAAAAAgCAYAAABzenr0AAAABHNCSVQICAgIfAhkiAAAAAlwSFlzAAAA7AAAAOwBeShxvQAAABl0RVh0U29mdHdhcmUAd3d3Lmlua3NjYXBlLm9yZ5vuPBoAAAKZSURBVFiFvdZfqI1ZGAbwnz85/tWhRNSJ5pJGEYkRLiijIblyhTSXw7hz4YZC4+JopFxIioQSYeZippAyF9PkhoiLM2WGaUgNOeYP5pztYq3dWXud7+z9ne07nlrtvu991vs8+1vrXe+iNT7DOTzBm/h7FstKzP0gjMFR1JqMI5E3Ivi2hXh9dI+E+GL0Z0LP8RP+yt73YWHVBk5kIqcwPsYm42IWP161gQdJ8heYEA2sx1h0ChuyzrlftYGnSfLb8d2a+Lw4PvcknKdVG7ibJH+NqRiNTzEKs/B/wrlTtYGrGtf4R8yIsS7cyuKXqzawIxOo7/Y/DK6OGr6q2sDsKFjmHOiL/MpxuaSBSyMhDksVf+509GPJSBkgNJ1mBs4MMW8a1mEzVhk4xIaNWcIRXCT+HDMz/hxc0FiiNfTiG0xsx8TnBi9FPzZkvEVNzKaH2tR2TBzKEh3M4lOEEi2zaa+2Y2CMgQb0ndAPUuzLRP4R2vlOXCkwsbKM6HRh3c5HAx1CP+go4D5Mkr8TKijFwczAsWbCM4Wbzr+R/BIrmvDHajy0rsf3C4U23iEsUbqPbhYlmobDwuer4RX2a71pxmUGvo/v1wpNqlNo5+8Szq2iRD8khBvRUFn8mcztFcoxxZcal+BsUZKNeJSQfsYmoQ23wrVM4BG2CUu3D/9l8T1DJRot3Hp+Sci/4mvhMw6FXZlAqzG/xJ+yXCi5+qRn2Kt4T3RpXONm40EZ8RQLcDoR6BWqpCvjnSlpYPtwDdTxSRSuV8mbaGxujM/F2xbiPYrPkWFhBg4It+WaUILrYqy7hYEvPlQ8xWRhc/6O3+LzJOGKXiR+skrxFOOwNQ6Yh78z8XvabMXtYksi/srAPvmo2I3HWN2M9B6A4E5bsqvdNAAAAABJRU5ErkJggg==');
    background-position: center;
    background-repeat: no-repeat;
    background-size: contain;
    left: 0px;
    top: 0px;
    opacity: 0.6;
    cursor: pointer;
}
.map_marker{
    width: 25px;
    height: 25px;
    background: #fff;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    border: 5px solid #1c65c0;
    padding: 5px;
    font-size: 12px;
    font-weight: 600;
    img{
        max-width: 100%!important;
        width: 100%!important;
    }
    &.end{
        border-color: #54d91c;
    }
    &.start{
        border-color: #a02de5;
    }
}
</style>