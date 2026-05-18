<template>
    <div class="map_wrapper select-none">
        <a-modal
            :title="$t('sports.mapFilter')"
            :visible="visible"
            :footer="false"
            @cancel="visible = false">
            <a-spin :spinning="filterLoading">
                <MapFilter 
                    ref="mapFilter"
                    :mapData="mapData" 
                    :setFilters="setFilters"
                    :regionsCache="regionsCache"
                    :districts="districts"
                    :summaryLength="clusterPoints.length"
                    :summaryLoader="summaryLoader"
                    :getData="getData"
                    :clearFilters="clearFilters"
                    :getMapCenter="getMapCenter" />
            </a-spin>
        </a-modal>
        <UseFullscreen v-slot="{ toggle, isFullscreen, isSupported }">
            <div 
                id="map" 
                class="country_map" 
                :class="[`zoom_level_${zoom}`, showFill, isFullscreen && 'fullscreen']">
                <a-spin :spinning="loading">
                    <l-map 
                        ref="mapInstance" 
                        :zoom="zoom" 
                        :center="center" 
                        :options="options" 
                        style="height: 100%;"
                        :max-bounds="maxBounds"
                        :max-bounds-viscosity="0.5"
                        @zoomend="updateZoom"
                        @update:zoom="getMapCenter"
                        @update:center="getMapCenter">
                        <l-control 
                            v-if="!isMobile && isFullscreen" 
                            position="bottomleft">
                            {{ regionFilter && regionFilter.name }}
                            <template v-if="selectedDistrict">
                                / {{ selectedDistrict.name }}
                            </template>
                        </l-control>
                        <l-control position="topleft">
                            <div class="flex flex-col">
                                <a-button 
                                    v-if="isMobile && !isFullscreen"
                                    flaticon 
                                    icon="fi-rr-filter"
                                    class="mb-1"
                                    @click="visible = true" />
                                <a-button 
                                    flaticon 
                                    v-tippy="{ inertia : true, duration : '[600,300]'}"
                                    :content="$t('sports.mapLayout')"
                                    :class="!showTile && 'opacity-60'"
                                    icon="fi-rr-map"
                                    @click="toggleTile()" />
                                <a-button 
                                    v-if="showTile"
                                    flaticon 
                                    v-tippy="{ inertia : true, duration : '[600,300]'}"
                                    :content="$t('sports.disabledMapLayout')"
                                    :class="[hideRegion && 'opacity-60', 'mt-1']"
                                    icon="fi-rr-layers"
                                    @click="toggleRegion()" />
                                <a-button 
                                    v-if="isSupported"
                                    flaticon 
                                    v-tippy="{ inertia : true, duration : '[600,300]'}"
                                    :content="$t('sports.mapFullscreen')"
                                    class="mt-1"
                                    :icon="isFullscreen? 'fi-rr-compress-alt' : 'fi-rr-expand'"
                                    @click="toggle" />
                            </div>
                        </l-control>
                        <l-control 
                            v-if="!isMobile" 
                            position="topright">
                            <a-spin :spinning="filterLoading">
                                <MapFilter 
                                    ref="mapFilter"
                                    :mapData="mapData" 
                                    :setFilters="setFilters"
                                    :isFullscreen="isFullscreen"
                                    :regionsCache="regionsCache"
                                    :districts="districts"
                                    :summaryLength="summaryLength"
                                    :summaryLoader="summaryLoader"
                                    :getData="getData"
                                    :clearFilters="clearFilters"
                                    :getMapCenter="getMapCenter" />
                            </a-spin>
                        </l-control>
                        <l-tile-layer 
                            :url="tileUrl"
                            :attribution="tileAttribution" />
                        <template v-if="!regionFilter">
                            <l-geo-json
                                v-for="(region, index) in filteredRegion"
                                :key="region.id"
                                :geojson="region.geometry"
                                :optionsStyle="defaultStyle"
                                :ref="'geoJson' + index"
                                :options="{
                                    className: 'geo_poligon',
                                    onEachFeature: onEachFeatureFunction
                                }"
                                @click="clickToRegion(region)">
                            </l-geo-json>
                        </template>
                        <template v-else>
                            <template v-if="regionFilter">
                                <l-geo-json
                                    v-for="district in regionFilter.district"
                                    :key="district.id"
                                    :geojson="district.geometry"
                                    :options="{
                                        className: 'geo_poligon',
                                        onEachFeature: onEachFeatureFunction2
                                    }"
                                    :optionsStyle="defaultStyle"
                                    @click="clickToDistrict(district)" />
                            </template>
                        </template>
                        <template v-if="useCluster">
                            <v-marker-cluster 
                                v-if="clusterPoints && clusterPoints.length"
                                :options="clusterOptions"
                                style="width: 100px; background: #fff;">
                                <l-marker 
                                    v-for="point in clusterPoints"
                                    :key="point.id" 
                                    :lat-lng="[point.location_point.lat, point.location_point.lon]"
                                    :options="{ data: point }">   
                                    <l-icon
                                        :iconSize="[21, 25]"
                                        :class-name="`point_marker`">
                                        <svg xmlns="http://www.w3.org/2000/svg" width="21" height="25" viewBox="0 0 21 25" fill="none">
                                            <path d="M10.3969 0C7.64055 0.00303238 4.99799 1.09924 3.04889 3.04815C1.09978 4.99706 0.00330855 7.63951 0 10.3958C0 13.0729 2.07291 17.2625 6.16145 22.8479C6.64818 23.5147 7.28546 24.0571 8.02145 24.4311C8.75743 24.8051 9.57131 25 10.3969 25C11.2224 25 12.0363 24.8051 12.7723 24.4311C13.5083 24.0571 14.1455 23.5147 14.6323 22.8479C18.7208 17.2625 20.7937 13.0729 20.7937 10.3958C20.7904 7.63951 19.6939 4.99706 17.7448 3.04815C15.7957 1.09924 13.1532 0.00303238 10.3969 0ZM10.3969 14.5396C9.57277 14.5396 8.76719 14.2952 8.08199 13.8374C7.39678 13.3795 6.86273 12.7288 6.54737 11.9674C6.232 11.2061 6.14949 10.3683 6.31026 9.56003C6.47103 8.75177 6.86787 8.00934 7.45058 7.42663C8.0333 6.84391 8.77573 6.44707 9.58398 6.2863C10.3922 6.12553 11.23 6.20804 11.9914 6.52341C12.7527 6.83877 13.4035 7.37282 13.8613 8.05803C14.3191 8.74323 14.5635 9.54881 14.5635 10.3729C14.5635 11.478 14.1245 12.5378 13.3431 13.3192C12.5617 14.1006 11.5019 14.5396 10.3969 14.5396Z" fill="#1D65C0"/>
                                        </svg>
                                    </l-icon>
                                    <l-tooltip>
                                        <div style="max-width: 230px;min-width: 230px;color:#000;word-break: break-word;white-space: normal;">
                                            <div style="word-break: break-word;white-space: normal;" class="mb-1">{{ point.name }}</div>
                                            <div v-if="point.location_point" style="word-break: break-word;white-space: normal;opacity:0.6;">
                                                {{ $t('sports.mapAddress') }}: {{ point.location_point.address }}
                                            </div>
                                            <div v-if="!isMobile && point.image && point.image.path" class="card_img">
                                                <div class="card_img__wrap">
                                                    <img 
                                                        :data-src="point.image.path" 
                                                        :alt="point.image.name" 
                                                        class="lazyload" />
                                                </div>
                                            </div>
                                        </div>
                                    </l-tooltip>
                                    <l-popup>
                                        <div style="max-width: 300px;min-width: 300px;color:#000;word-break: break-word;white-space: normal;">
                                            <div style="word-break: break-word;white-space: normal;" class="mb-1">{{ point.name }}</div>
                                            <div v-if="point.location_point" style="word-break: break-word;white-space: normal;opacity:0.6;">
                                                {{ $t('sports.mapAddress') }}: {{ point.location_point.address }}
                                            </div>
                                            <div v-if="point.facility_type" style="word-break: break-word;white-space: normal;opacity:0.6;" class="mt-2">
                                                {{ point.facility_type.full_name }}
                                            </div>
                                            <div v-if="!isMobile && point.image && point.image.path" class="card_img">
                                                <div class="card_img__wrap">
                                                    <img 
                                                        :data-src="point.image.path" 
                                                        :alt="point.image.name" 
                                                        class="lazyload" />
                                                </div>
                                            </div>
                                            <a-button 
                                                type="primary" 
                                                size="large" 
                                                block
                                                class="mt-3"
                                                @click="openObject(point)">
                                                {{ $t('sports.mapOpen') }}
                                            </a-button>
                                            <a-button 
                                                type="primary" 
                                                size="large" 
                                                block 
                                                ghost
                                                class="mt-1"
                                                @click="pointClickHandler(point)">
                                                {{ $t('sports.mapZoomIn') }}
                                            </a-button>
                                        </div>
                                    </l-popup>
                                </l-marker>
                            </v-marker-cluster>
                        </template>
                        <template v-else>
                            <template v-if="markerPoints && markerPoints.length">
                                <l-marker 
                                    v-for="(point, index) in markerPoints"
                                    :key="`${index}_point`" 
                                    :lat-lng="point.centroid"
                                    :options="{ data: point }"
                                    @click="getPointGeo(point)">  
                                    <l-icon
                                        :iconSize="[21, 25]"
                                        :class-name="`point_marker_summary`">
                                        <div class="circle-container">
                                            <div class="circle-text">{{ point.count }}</div>
                                        </div>
                                    </l-icon>
                                </l-marker>
                            </template>
                        </template>
                    </l-map>
                </a-spin>
            </div>
        </UseFullscreen>
    </div>
</template>

<script>
import { LMap, LTileLayer, LGeoJson, LMarker, LControl, LIcon, LTooltip, LPopup } from 'vue2-leaflet'
import 'leaflet/dist/leaflet.css'
import L, { latLng } from 'leaflet'
import Vue2LeafletMarkercluster from 'vue2-leaflet-markercluster'
import "leaflet.markercluster/dist/MarkerCluster.css"
import MapFilter from './MapFilter.vue'
import axios from 'axios'
import { addDataLazy, maxBounds, expandBounds, iconCreateFunction, isPointInPolygon } from './utils.js'
import eventBus from '@/utils/eventBus'
import { UseFullscreen } from '@vueuse/components'
let timer;
export default {
    components: {
        LMap,
        LTileLayer,
        LGeoJson,
        LTooltip,
        LMarker,
        MapFilter,
        LPopup,
        LControl,
        LIcon,
        UseFullscreen,
        'v-marker-cluster': Vue2LeafletMarkercluster
    },
    props: {
        page_name: {
            type: String,
            required: true
        },
        model: {
            type: String,
            required: true
        },
        statusFilter: {
            type: String,
            default: ''
        }
    },
    computed: {
        selectedDistrict() {
            return this.regionFilter?.district?.find(d => d.id === this.filters.district) || null
        },
        useCluster() {
            return this.zoom >= 10 || this.filters.district ? true : false
        },
        showFill() {
            return this.zoom <= 8 ? '' : 'hide_fill'
        },
        onEachFeatureFunction() {
            return (feature, layer) => {
                if(this.zoom <= 9) {
                    layer.bindTooltip(
                        `<div>${feature.name}</div>`,
                        { permanent: false, sticky: true }
                    )
                }
            }
        },
        onEachFeatureFunction2() {
            return (feature, layer) => {
                if(feature?.name && this.zoom <= 9) {
                    layer.bindTooltip(
                        `<div>${feature.name}</div>`,
                        { permanent: false, sticky: true }
                    )
                }
            }
        },
        mapInstance() {
            return this.$refs.mapInstance.mapObject
        },
        isMobile() {
            return this.$store.state.isMobile;
        },
        kzMap() {
            return this.zoom < 9 ? true : false
        },
        tileUrl() {
            if(!this.showTile && this.kzMap)
                return ''
            return 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png'
        },
        filteredRegion() {
            return this.regionFilter 
                ? [this.regions.find(f => f.id === this.regionFilter.id)] 
                : this.regions
        },
        defaultStyle() {
            if (!this.showTile) {
                return {
                    color: this.zoom <= 8 ? '#92a6b8' : '#1890ff',
                    weight: 1,
                    fillColor: '#f0f2f6',
                    fillOpacity: this.zoom <= 8 ? 1 : 0
                }
            }
    
            if (this.hideRegion)
                return { weight: 0, fillOpacity: 0 };
    
            return {
                color: '#1e65bf',
                weight: 1,
                fillColor: '#1e65bf',
                fillOpacity: this.zoom <= 8 ? 0.1 : 0
            }
        }
    },
    data() {
        return {
            axiosCancel: null,
            tileAttribution: '',
            regions: [],
            visible: false,
            summaryLoader: false,
            clusterOptions: {
                iconCreateFunction: iconCreateFunction
            },
            loading: false,
            zoom: 5,
            summaryLength: 0,
            districts: [],
            mapData: [],
            filters: {},
            filterLoading: false,
            clusterPoints: [],
            markerPoints: [],
            center: [48.0196, 66.9237],
            regionFilter: null,
            showTile: false,
            hideRegion: false,
            regionsCache: [],
            options: {
                minZoom: 4,
                attributionControl: false
            },
            maxBounds: maxBounds,
            hoverStyle: {
                color: '#1e65bf',
                weight: 1,
                fillColor: '#1e65bf',
                fillOpacity: 0.2,
            }
        }
    },
    created() {
        const initTile = localStorage.getItem('MapShowTile')
        if(initTile)
            this.showTile = JSON.parse(initTile)
        const initRegion = localStorage.getItem('MapRegion')
        if(initRegion)
            this.hideRegion = JSON.parse(initRegion)

        this.getData(true)
        this.getMapCenter()
    },
    methods: {
        getPointGeo(point) {
            const geoJson = this.regionFilter?.district?.length ? this.regionFilter.district : this.filteredRegion
            const foundRegion = geoJson.find((region) => {
                const coordinates = region.geometry.coordinates
                const type = region.geometry.type
                if (type === "Polygon") {
                    return isPointInPolygon(point.centroid, coordinates[0])
                } else if (type === "MultiPolygon") {
                    return coordinates.some((polygon) => isPointInPolygon(point.centroid, polygon[0]))
                }
                return false
            })
            if (foundRegion) {
                if(this.regionFilter?.district?.length)
                    this.clickToDistrict(foundRegion)
                else
                    this.clickToRegion(foundRegion)
            }
        },
        openObject(point) {
            const routeData = this.$router.resolve({
                name: 'full_sports_facilities_gallery',
                params: { id: point.id }
            })
            window.open(routeData.href, '_blank')
        },
        pointClickHandler(point) {
            this.$nextTick(() => {
                this.$refs.mapInstance.mapObject.flyTo(latLng(point.location_point.lat, point.location_point.lon), 17, {
                    duration: 1.5,
                    easeLinearity: 1.5
                })
                this.$refs.mapInstance.mapObject.invalidateSize()
            })
        },
        getMapCenter() {
            this.$nextTick(() => {
                this.center = this.$refs['mapInstance'].mapObject.getCenter()
            })
            if(this.axiosCancel) {
                this.axiosCancel.cancel()
                this.axiosCancel = null
            }
            clearTimeout(timer)
            timer = setTimeout(async () => {
                await this.$nextTick()

                const map = this.$refs['mapInstance']?.mapObject
                if (!map) return

                try {
                    this.summaryLoader = true
                    const axiosSource = axios.CancelToken.source()
                    this.axiosCancel = axiosSource
                    const map = this.$refs['mapInstance'].mapObject
                    const lat__gte = map.getBounds().getSouth()
                    const lat__lte = map.getBounds().getNorth()
                    const lon__gte = map.getBounds().getWest()
                    const lon__lte = map.getBounds().getEast()
                    const params = {
                        page_size: 'all',
                        lat__gte,
                        lat__lte,
                        lon__gte,
                        lon__lte,
                        zoom: this.zoom,
                        page_name: this.page_name,
                        ...(this.statusFilter && { filters: JSON.stringify({ status: this.statusFilter }) }),
                        ...(this.filters.region && { region: this.filters.region }),
                        ...(this.filters.district && { district: this.filters.district })
                    }
                    const { data } = await this.$http.post('sports_facilities/locations/count/', params)
                    if(this.useCluster)
                        this.clusterPoints = data.points?.length ? data.points : []
                    else
                        this.markerPoints = data.centroids?.length ? data.centroids : []
                    this.summaryLength = data?.count || 0
                } catch(e) {
                    console.log(e)
                } finally {
                    this.summaryLoader = false
                }
            }, 500)
        },
        setFilters(filters) {
            this.visible = false
            this.filters = filters
            if(filters.region) {
                const find = this.regionsCache.find(f => f.id === filters.region)
                if(find)
                    this.zoomToRegion(find)
            } else {
                if(this.regionFilter) 
                    this.clearFilters()
            }
        },
        clearFilters() {
            this.visible = false
            this.regionFilter = null
            this.setDefaultPosition()
        },
        async getData(init = false) {
            try {
                this.loading = true
                this.filterLoading = true
                const params = this.filters?.region ? { parent: this.filters.region } : {}
                const { data } = await this.$http.get('/catalogs/location_admin_area/', { params })
        
                if (!data) return
        
                if (init) this.regionsCache = data
                this.mapData = data

                if (params.parent) {
                    const selectedRegion = this.regionsCache.find(region => region.id === params.region)
                    this.districts = data.results
                    if (selectedRegion) this.zoomToRegion(selectedRegion)
                } else {
                    if (this.districts.length) this.districts = []
                    if (this.regionFilter) this.regionFilter = null
                    this.setDefaultPosition()
            
                    addDataLazy(
                        this.regions,
                        data,
                        item => ({
                            ...item,
                            geometry: { ...item.geometry, ...item }
                        })
                    )
                }
            } catch (error) {
                console.error(error)
            } finally {
                this.loading = false
                this.filterLoading = false
            }
        },
        toggleTile() {
            this.showTile = !this.showTile
            localStorage.setItem('MapShowTile', JSON.stringify(this.showTile))
        },
        toggleRegion() {
            this.hideRegion = !this.hideRegion
            localStorage.setItem('MapRegion', JSON.stringify(this.hideRegion))
        },
        setDefaultPosition() {
            this.zoom = 5
            this.center = [48.0196, 66.9237]
            this.maxBounds = maxBounds
        },
        updateZoom(event) {
            this.zoom = event.target.getZoom()
            //if(this.zoom >= 7)
            //this.getMapDestricts()
            if(this.zoom <= 5 && this.regionFilter) {
                this.regionFilter = null
                this.maxBounds = maxBounds
                if(this.filters?.region)
                    this.filters.region = null
                if(this.filters?.district)
                    this.filters.district = null
                this.$refs.mapFilter.setRegion(null)
                this.$refs.mapFilter.setDistrict(null)
            }
        },
        generateRegionDist(region) {
            this.$nextTick(async () => {
                try {
                    this.loading = true
                    const bounds = L.geoJSON(region.geometry).getBounds()
                    this.$refs['mapInstance'].fitBounds(bounds)
                    this.maxBounds = expandBounds(bounds, 2.0)
                    const { data } = await this.$http.get('/catalogs/location_admin_area/', { 
                        params: {
                            parent: region.id
                        }
                    })
                    if(data) {
                        this.regionFilter = {
                            ...region,
                            district: []
                        }
                        addDataLazy(
                            this.regionFilter.district,
                            data,
                            item => ({
                                ...item,
                                geometry: {
                                    ...item.geometry,
                                    ...item
                                }
                            }),
                            4
                        )
                        setTimeout(() => {
                            const find = this.regionFilter.district.find(f => f.id === this.filters.district)
                            if(find && this.filters.district)
                                this.zoomToDistrict(find)
                        }, 500)
                    }
                } catch(e) {
                    console.log(e)
                } finally {
                    this.loading = false
                }
            })
        },
        zoomToRegion(region) {
            this.generateRegionDist(region)
        },
        async clickToRegion(region) {
            this.$set(this.filters, 'region', region.id)
            this.$nextTick(() => {
                this.$refs.mapFilter.setRegion(region.id)
            })
            this.generateRegionDist(region)
        },
        clickToDistrict(district) {
            this.$set(this.filters, 'district', district.id)
            this.$nextTick(() => {
                this.$refs.mapFilter.setDistrict(district.id)
            })
            if (district.geometry) {
                this.$nextTick(() => {
                    const bounds = L.geoJSON(district.geometry).getBounds()
                    this.$refs['mapInstance'].fitBounds(bounds)
                })
            }
        },
        zoomToDistrict(district) {
            if (district.geometry) {
                this.$nextTick(() => {
                    const bounds = L.geoJSON(district.geometry).getBounds()
                    this.$refs['mapInstance'].fitBounds(bounds)
                })
            }
        }
    },
    mounted() {
        eventBus.$on(`update_filter_${this.model}_${this.page_name}`, () => {
            this.getMapCenter()
        })
        eventBus.$on('update_sports_facilities_list', () => {
            this.getMapCenter()
        })
        eventBus.$on(`update_map_${this.model}_${this.page_name}`, () => {
            this.getMapCenter()
        })
    },
    beforeDestroy() {
        eventBus.$off(`update_filter_${this.model}_${this.page_name}`)
        eventBus.$off(`update_map_${this.model}_${this.page_name}`)
        eventBus.$off('update_sports_facilities_list')
    }
}
</script>

<style lang="scss" scoped>
.map_wrapper{
    width: 100%;
    overflow: auto;
    height: 100%;
    min-height: 700px;
    .card_img{
        overflow: hidden;
        position: relative;
        height: 70px;
        width: 150px;
        border-radius: 4px;
        margin-top: 10px;
        &__wrap{
            height: 100%;
            left: 0;
            margin: 0;
            overflow: hidden;
            position: absolute;
            top: 0;
            width: 100%;
            display: flex;
            align-items: flex-start;
            justify-content: flex-start;
            img{
                object-fit: contain;
                vertical-align: middle;
                -o-object-fit: contain;
                max-height: 100%;
                border-style: none;
                border-radius: 4px;
                opacity: 0;
                transition: all 0.3s cubic-bezier(0.645, 0.045, 0.355, 1);
                &.lazyloaded{
                    opacity: 1;
                }
            }
        }
    }
}
.country_map{
    width: 100%;
    position: relative;
    z-index: 10;
    &::v-deep{
        .leaflet-control-container{
            .leaflet-right{
                .leaflet-control{
                    margin: 0px;
                    background: rgba(247, 249, 252, 0.7);
                    padding-left: 15px;
                    padding-bottom: 10px;
                    padding-top: 10px;
                    padding-right: 15px;
                }
            }
            .leaflet-bottom{
                &.leaflet-left{
                    .leaflet-control{
                        margin: 0px;
                        background: rgba(247, 249, 252, 0.7);
                        padding-left: 15px;
                        padding-bottom: 10px;
                        padding-top: 10px;
                        padding-right: 15px;
                    }
                }
            }
        }
        .vue2leaflet-map{
            min-height: 700px;
        }
        .leaflet-popup{
            .leaflet-popup-content-wrapper{
                border-radius: 6px;
                box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
            }
        }
        .leaflet-tooltip{
            &::before{
                display: none;
            }
        }
        .circle-container {
            position: relative;
            width: 35px;
            height: 35px;
            background: #fff;
            border-radius: 50%;
            display: flex;
            color: #000;
            align-items: center;
            justify-content: center;
            border: 3px solid #FF9231;
            font-size: 10px;
            overflow: hidden;
        }
        .ant-spin-container,
        .ant-spin-nested-loading{
            height: 100%;
        }
        .leaflet-container{
            background: #f7f9fc!important;
        }
        &:not(.hide_fill) {
            .geo_poligon{
                outline: none;
                &:hover{
                    fill: #1e65bf;
                    fill-opacity: 0.2;
                    stroke: #1e65bf;
                }
            }
        }
        .region_marker{
            width: initial!important;
            height: initial!important;
            text-align: center;
            font-size: 16px!important;
            margin-left: -50px!important;
            margin-top: -20px!important;
            transition: all 0.3s cubic-bezier(0.645, 0.045, 0.355, 1);
            pointer-events: none;
            .region_name{
                color: #000;
                min-width: 100px;
            }
            .region_stat{
                color: var(--blue);
            }
        }
    }
    &.zoom_level_4{
        &::v-deep{
            .region_marker{
                font-size: 10px!important;
            }
        }
    }
    &.fullscreen{
        height: 100%;
        &::v-deep{
            .ant-spin-nested-loading,
            .ant-spin-container,
            .vue2leaflet-map{
                min-height: 100%;
                height: 100%;
            }
        }
    }
}
</style>