<template>
    <div class="">
        <div class="flex flex-col h-[80vh]">
            <div class="list divide-y">
                <a-list
                    item-layout="horizontal"
                    v-for="(point, n) in taskPointsList"
                    :key="n">
                    <a-list-item @click="onClick(point)">
                        <a-list-item-meta>
                            <div slot="title" class="flex flex-row cursor-pointer" >
                                <div class="mr-5">{{ n+1 }}</div>
                                <div>{{ point.name }}</div>
                            </div>
                        </a-list-item-meta>
                    </a-list-item>
                </a-list>
                <div 
                    v-if="!taskPointsList.length"
                    class="flex items-center justify-center"
                    :class="isMobile && 'py-2'">
                    <a-empty :description="$t('task.no_data')" />
                </div>
            </div>
            <div class="map mt-5">
                <l-map
                    ref="map"
                    :zoom="zoom"
                    :center="center"
                    :options="mapOptions">
                    <l-tile-layer
                        :url='url'
                        :attribution='attribution'>
                    </l-tile-layer>
                    <l-marker
                        v-for="(point, n) in taskPointsList"
                        :key="n"
                        :lat-lng="[point.lat, point.lon]">
                        <l-tooltip>{{ point.name }}</l-tooltip>
                    </l-marker>
                </l-map>
            </div>
        </div>
    </div>
</template>
  
<script>
import { mapState } from 'vuex'
import { LMap, LTileLayer, LMarker, LTooltip } from 'vue2-leaflet'
import 'leaflet/dist/leaflet.css'

export default {
    name: 'TaskAddresses',
    props: {
        task: {
            type: Object,
            default: () => null
        },
        isMobile: {
            type: Boolean,
            default: false
        },
    },
    data() {
        return {
            zoom: 15,
            center: [51.15, 71.42],
            mapOptions: {
                attributionControl: false
            },
            attribution: '',
            fitBoundsOptions: {
                // maxZoom: 13
            }
        }
    },
    computed: {
        ...mapState({
            taskPointsList: state => state.task.taskPointsList,
            markersList: state => state.task.markersList,
            config: state => state.config.config
        }),
        url() {
            return `${this.config.map?.tileUrl || null}?access-token=${this.config.map?.tileToken || null}&lang=${this.config.map?.tileLang || null}`
        },
    },
    methods: {
        get_markers() {
            if (this.task?.task_points?.length !== 0) {
                const map = this.$refs.map.mapObject
                this.$nextTick(() => {
                    map.fitBounds(this.markersList, this.fitBoundsOptions)
                })
            }
        },
        onClick(point) {
            const map = this.$refs.map.mapObject
            this.$nextTick(() => {
                map.setView({lat: point.lat, lng: point.lon}, 17)
            })
        }
    },
    mounted() {
        if (this.task?.task_points?.length !== 0) {
            this.$store.commit('task/SET_TASK_POINT_LIST', this.task.task_points)
            this.$store.commit('task/SET_MARKERS_LIST', this.task.task_points)
            this.get_markers()
        }
    },
    components: {
        LMap,
        LTileLayer,
        LMarker,
        LTooltip,
    },
    destroyed() {
        this.$store.commit('task/SET_TASK_POINT_LIST', [])
        this.$store.commit('task/RESET_MARKERS_LIST')
    }
}
</script>

<style scoped>

.list {
  flex-basis: 33.33%;
  overflow: auto;
}

.map {
  flex-basis: 66.67%;
}
</style>