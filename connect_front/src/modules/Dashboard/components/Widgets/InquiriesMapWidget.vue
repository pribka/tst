<template>
    <WidgetWrapper :widget="widget" :class="isMobile && 'mobile_widget'">
        <div class="map_wrapper select-none">
            <a-spin :spinning="filterLoading">
                <MapFilter 
                    ref="mapFilter"
                    :mapData="mapData" 
                    :setFilters="setFilters"
                    :regionsCache="regionsCache"
                    :districts="districts"
                    :summaryData="summary"
                    :summaryLoader="summaryLoader"
                    :getData="getData"
                    :clearFilters="clearFilters"
                    :getMapCenter="getMapCenter" />
            </a-spin>
            <UseFullscreen v-slot="{ toggle, isFullscreen }">
                <div 
                    id="map" 
                    class="country_map" 
                    :class="[`zoom_level_${zoom}`, showFill, isFullscreen && 'fullscreen']"
                    style="height: 600px;">
                    <a-spin :spinning="loading">
                        <l-map 
                            ref="mapInstance" 
                            :zoom="zoom" 
                            :center="center" 
                            :options="options" 
                            style="height: 600px;"
                            :max-bounds="maxBounds"
                            :max-bounds-viscosity="0.5"
                            @zoomend="updateZoom"
                            @update:zoom="getMapCenter"
                            @update:center="getMapCenter">
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
                                    <template v-for="item in clusterPoints" >
                                        <l-marker 
                                            v-for="point in item.location_points"
                                            :key="item.id+point.lat+point.lon" 
                                            :lat-lng="[point.lat, point.lon]"
                                            :options="{ data: item }"
                                            @click="pointClickHandler(point, item)">   
                                            <l-icon
                                                :iconSize="[50, 50]"
                                                :class-name="`point_marker ${getMarkerColor(item)}`">
                                                <div class="point_marker__wrapper">
                                                    <span>{{ item.total_value }}</span>
                                                </div>
                                            </l-icon>
                                        </l-marker>
                                    </template>
                                </v-marker-cluster>
                            </template>
                            <template v-else>
                                <template v-if="markerPoints && markerPoints.length">
                                    <l-marker 
                                        v-for="(point, index) in markerPoints"
                                        :key="`${index}_point`" 
                                        :lat-lng="point.centroid"
                                        :options="{ data: point }"
                                        :icon="createClusterIcon(point.summary)"
                                        @click="getPointGeo(point)">  
                                    </l-marker>
                                </template>
                            </template>
                            <l-control position="topleft" >
                                <div class="flex flex-col">
                                    <a-button 
                                        flaticon 
                                        v-tippy="{ inertia : true, duration : '[600,300]'}"
                                        :content="$t('Switch map layer')"
                                        :class="!showTile && 'opacity-60'"
                                        icon="fi-rr-map"
                                        @click="toggleTile()" />
                                    <a-button 
                                        v-if="showTile"
                                        flaticon 
                                        v-tippy="{ inertia : true, duration : '[600,300]'}"
                                        :content="$t('Disable regions and districts')"
                                        :class="[hideRegion && 'opacity-60', 'mt-1']"
                                        icon="fi-rr-layers"
                                        @click="toggleRegion()" />
                                    <a-button 
                                        flaticon 
                                        v-tippy="{ inertia : true, duration : '[600,300]'}"
                                        :content="$t('Expand to Fullscreen')"
                                        class="mt-1"
                                        :icon="isFullscreen? 'fi-rr-compress-alt' : 'fi-rr-expand'"
                                        @click="toggle" />
                                </div>
                            </l-control>
                            <l-control 
                                v-if="!isMobile && isFullscreen" 
                                position="bottomleft">
                                {{ regionFilter && regionFilter.name }}
                                <template v-if="selectedDistrict">
                                    / {{ selectedDistrict.name }}
                                </template>
                            </l-control>
                        </l-map>
                    </a-spin>
                </div>
            </UseFullscreen>
        </div>
        <ViewDrawer />
    </WidgetWrapper>
</template>

<script>
import { LMap, LTileLayer, LGeoJson, LMarker, LControl, LIcon } from 'vue2-leaflet'
import 'leaflet/dist/leaflet.css'
import L, { latLng } from 'leaflet'
import Vue2LeafletMarkercluster from 'vue2-leaflet-markercluster'
import "leaflet.markercluster/dist/MarkerCluster.css"
import axios from 'axios'
import { addDataLazy, maxBounds, expandBounds, generateIcon, getMarkerColor, iconCreateFunction, createClusterIcon, isPointInPolygon } from './components/Inquiries/utils.js'
import { UseFullscreen } from '@vueuse/components'
let timer;
export default {
    props: {
        widget: {
            type: Object,
            required: true
        }
    },
    components: {
        WidgetWrapper: () => import('../WidgetWrapper.vue'),
        LMap,
        LTileLayer,
        LGeoJson,
        LMarker,
        MapFilter: () => import('./components/Inquiries/MapFilter'),
        LControl,
        LIcon,
        ViewDrawer: () => import('./components/Inquiries/ViewDrawer'),
        UseFullscreen,
        'v-marker-cluster': Vue2LeafletMarkercluster
    },
    computed: {
        useCluster() {
            return this.zoom >= 10 || this.filters.district ? true : false
        },
        selectedDistrict() {
            return this.regionFilter?.district?.find(d => d.id === this.filters.district) || null
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
            summary: null,
            summaryLoader: false,
            clusterOptions: {
                iconCreateFunction: iconCreateFunction
            },
            loading: false,
            zoom: 5,
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
        generateIcon,
        getMarkerColor,
        createClusterIcon,
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
        pointClickHandler(point, item) {
            if(this.zoom <= 8) {
                this.$nextTick(() => {
                    this.$refs.mapInstance.mapObject.flyTo(latLng(point.lat, point.lon), 16, {
                        duration: 1.5,
                        easeLinearity: 1.5
                    })
                    this.$refs.mapInstance.mapObject.invalidateSize()
                })
            }
            this.$nextTick(() => {
                this.$refs.mapFilter.getInfo(item)
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
            timer = setTimeout(async() => {
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
                        ...(this.filters.region && { region: this.filters.region }),
                        ...(this.filters.district && { district: this.filters.district }),
                        ...(this.filters.issue_date_gte && {
                            issue_date_gte: this.$moment(this.filters.issue_date_gte).format('YYYY-MM-DD'),
                        }),
                        ...(this.filters.issue_date_lte && {
                            issue_date_lte: this.$moment(this.filters.issue_date_lte).format('YYYY-MM-DD'),
                        }),
                        ...(this.filters.categories?.length && {
                            categories: this.filters.categories.join(','),
                        }),
                        ...(this.filters.total_value?.length && {
                            total_value: this.filters.total_value.join(','),
                        }),
                    }
                    const { data } = await this.$http.post('risk_assessment/locations/summary/', params)
                    if(this.useCluster)
                        this.clusterPoints = data.points?.length ? data.points : []
                    else
                        this.markerPoints = data.centroids?.length ? data.centroids : []
                    if(data)
                        this.summary = data.summary
                } catch(e) {
                    console.log(e)
                } finally {
                    this.summaryLoader = false
                }
            }, 500)
        },
        setFilters(filters) {
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
    }
}
</script>

<style lang="scss" scoped>
.map_wrapper{
    display: grid;
    gap: 20px;
    grid-template-columns: 400px 1fr;
    width: 100%;
    overflow: auto;
    height: 100%;
}
.country_map{
    width: 100%;
    position: relative;
    z-index: 10;
    &::v-deep{
        .leaflet-control-container{
            .leaflet-bottom{
                &.leaflet-left{
                    .leaflet-control{
                        margin: 0px;
                        background: rgba(255, 255, 255, 0.7);
                        padding-left: 15px;
                        padding-bottom: 10px;
                        padding-top: 10px;
                        padding-right: 15px;
                    }
                }
            }
        }
        .point_marker{
            display: flex;
            align-items: center;
            justify-content: center;
            &::after{
                content: "";
                position: absolute;
                top: 0;
                left: 0;
                width: 50px;
                height: 50px;
                border-radius: 50%;
                opacity: 0.4
            }
            &__wrapper{
                display: flex;
                align-items: center;
                justify-content: center;
                color: #000;
                border-radius: 50%;
                width: 40px;
                height: 40px;
                position: relative;
                
                span{
                    position: relative;
                    z-index: 10;
                }
            }
            &.orange {
                &::after{
                    background: #ff8812;
                }
                .point_marker__wrapper{
                    background: #ff8812;
                }
            }
            &.red {
                &::after{
                    background: #ff4e46;
                }
                .point_marker__wrapper{
                    background: #ff4e46;
                }
            }
            &.white {
                &::after{
                    background: #A9B3BF;
                }
                .point_marker__wrapper{
                    background: #A9B3BF;
                }
            }
            &.yellow {
                &::after{
                    background: #fee933;
                }
                .point_marker__wrapper{
                    background: #fee933;
                }
            }
        }
        .cluster_wrapper {
            position: relative;
            width: 40px;
            height: 40px;
            background: #fff;
            border-radius: 50%;
            .cluster_label {
                position: absolute;
                top: 50%;
                left: 50%;
                transform: translate(-50%, -50%);
            }
        }
        .circle-container {
            position: relative;
            width: 40px;
            height: 40px;
            background: #fff;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .circular-chart {
            transform: rotate(-90deg);
            width: 100%;
            height: 100%;
        }
        .circle {
            fill: none;
            stroke-width: 4;
        }
        .circle.orange {
            stroke: #ff8812;
        }
        .circle.red {
            stroke: #ff4e46;
        }
        .circle.white {
            stroke: #A9B3BF;
        }
        .circle.yellow {
            stroke: #fee933;
        }
        .circle-text {
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            font-size: 12px;
        }
        .ant-spin-container,
        .ant-spin-nested-loading{
            height: 100%;
        }
        .leaflet-container{
            background: #fff!important;
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
    &.fullscreen{
        height: 100%!important;
        &::v-deep{
            .ant-spin-nested-loading,
            .ant-spin-container,
            .vue2leaflet-map{
                min-height: 100%;
                height: 100%;
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
}
</style>