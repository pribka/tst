<template>
    <div class='mdpc-map'>
        <l-map
            ref='l-map'
            @dblclick="onMapClick"
            @update:center="centerUpdate"
            :zoom.sync='zoom'
            :options='options'
            :center='getCenterPoint()'>
            <l-tile-layer
                :url='url'
                :attribution='attribution'>
            </l-tile-layer>
            <l-marker
                v-for="(point, n) in contractorDeliveryPointsList"
                :key="n"
                :lat-lng="[point.lat, point.lon]">
                <l-tooltip>{{ point.name }}</l-tooltip>
            </l-marker>
            <l-marker v-if="position.lat && position.lng"
                      visible
                      draggable
                      :lat-lng.sync="position" />
            <l-marker v-if="searchAdress.lat && searchAdress.lng"
                      :visible="searchVisible"
                      :lat-lng.sync="searchAdress">
                <l-tooltip :options="{ permanent: true }">
                    {{ shortAddress }}
                </l-tooltip>            
            </l-marker>
            <l-control position="topleft">
                <a-popover placement="right">
                    <template slot="content">
                        <p>Моё местоположение</p>
                    </template>
                    <a-button
                        icon="environment"
                        :loading="myCoordLoading"
                        @click="clickHandler"/>
                </a-popover>
            </l-control>
            <l-control class="searsh-form">
                <a-form-item>
                    <a-auto-complete
                        class="auto-complete"
                        :getPopupContainer="trigger => trigger.parentElement"
                        @change="handleAdressChange">
                        <template slot="dataSource">
                            <a-select-option
                                v-for="(result, i) in autoCompleteResult"
                                :key=String(i)
                                @click="setResult(result)">
                                {{ result.label }}
                            </a-select-option>
                        </template>
                        <a-input-search placeholder="Поиск на карте"
                                        allowClear
                                        :loading="searchLoading"
                                        @search="onSearchAdress">
                        </a-input-search>
                    </a-auto-complete>
                </a-form-item>
            </l-control>
        </l-map>
    </div>
</template>

<script>
import eventBus from '@/utils/eventBus.js'
import { mapState } from 'vuex'

let timer

export default {
    name: 'MapConponent',
    components: {
        LMap: () => import('vue2-leaflet').then(m => m.LMap),
        LTileLayer: () => import('vue2-leaflet').then(m => m.LTileLayer),
        LMarker: () => import('vue2-leaflet').then(m => m.LMarker),
        LTooltip: () => import('vue2-leaflet').then(m => m.LTooltip),
        LControl: () => import('vue2-leaflet').then(m => m.LControl)
    },
    props: {
        defaultLocation: {
            type: Object,
            default: () => ({
                lat: 55.755969527097,
                lon: 37.617635382487
            })
        },
        centerPointlat: null,
        centerPointlon: null,
        contractorDeliveryPointsList: {
            type: Array,
            default: () => []
        }
    },
    data () {
        return {
            attribution: '',
            zoom: 12,
            center: [],
            position: {},
            searchAdress: {},
            searchLoading: false,
            address: '',
            searchVisible: false,
            shortAddress: '',
            autoCompleteResult: [],
            provider: null,
            providerPromise: null,
            options: {
                attributionControl: false
            },
            myCoordLoading: false,
            deliveryPoint: {
                lat: null,
                lon: null,
                address: '',
                name: ''
            }
        }
    },
    mounted () {
        eventBus.$on('reset_position', this.resetPosition)
    },
    beforeDestroy () {
        eventBus.$off('reset_position')
    },
    computed: {
        ...mapState({
            config: state => state.config.config
        }),
        tileToken() {
            return this.config.map?.tileToken || null
        },
        url() {
            return `${this.config.map?.tileUrl || null}?access-token=${this.config.map?.tileToken || null}&lang=${this.config.map?.tileLang || null}`
        }
    },
    methods: {
        async ensureProvider() {
            if (this.provider) return
            if (!this.providerPromise) {
                this.providerPromise = import('leaflet-geosearch').then(mod => {
                    const OpenStreetMapProvider = mod.OpenStreetMapProvider || mod.default?.OpenStreetMapProvider
                    this.provider = new OpenStreetMapProvider({
                        params: {
                            'accept-language': 'ru',
                            countrycodes: ['ru', 'kz'],
                            addressdetails: 0,
                            limit: 7
                        }
                    })
                })
            }
            await this.providerPromise
        },
        setResult(result) {
            this.searchVisible = true
            this.$refs['l-map'].mapObject.setView({lat: result.y, lng: result.x}, 17)
            if(result.bounds)
                this.$refs['l-map'].mapObject.fitBounds(result.bounds)
            this.searchAdress = {
                lat: result.raw.lat,
                lng: result.raw.lon
            }
            this.shortAddress = result.label.slice(0, 25)+'...'
        },
        async handleAdressChange(value) {
            if(value === '') {
                this.autoCompleteResult = []
                this.searchVisible = false
            }
            clearTimeout(timer)
            if(value.trim().length >= 3) {
                timer = setTimeout(async () => {
                    this.searchLoading = true
                    try {
                        await this.ensureProvider()
                        this.provider.search({ query: value })
                            .then(result => {
                                this.autoCompleteResult = result
                            })
                    } catch(e) {
                        console.log(e)
                    } finally {
                        this.searchLoading = false
                    }
                }, 700)
            }
        },
        onSearchAdress(value) {
        },
        centerUpdate(center) {
            eventBus.$emit('center_has_changed', center)
        },
        getCenterPoint() {
            return [this.centerPointlat || this.defaultLocation.lat,
                this.centerPointlon || this.defaultLocation.lon]
        },
        clickHandler() {
            this.myCoordLoading = true
            navigator.geolocation.getCurrentPosition(this.onPosition, this.errorPosition, {
                enableHighAccuracy: true
            })
            this.myCoordLoading = false
        },
        onPosition({ coords }) {
            let my_posipion = {
                lat: coords.latitude,
                lng: coords.longitude
            }
            eventBus.$emit('show_position', my_posipion)
        },
        errorPosition({ message }) {
            console.log('Error:', message)
        },
        async onMapClick (value) {
            this.position = value.latlng
            this.searchVisible = false
            let address = 'Не удалось определить адрес'
            let name = ''
            this.$emit('inputLoading', true)
            try {
                const { lat, lng } = this.position
                const result = await fetch(
                  `https://nominatim.openstreetmap.org/reverse?format=jsonv2&lat=${lat}&lon=${lng}&accept-language=ru`
                )
                if (result.status === 200) {
                    const body = await result.json()
                    address = body.display_name
                    name = `${address.split(', ', 2)[1]}, ${address.split(', ', 2)[0]}`
                }
            } catch (e) {
                console.error('Reverse Geocode Error->', e)
            } finally {
                this.$emit('inputLoading', false)
            }
            this.deliveryPoint.lat = this.position.lat
            this.deliveryPoint.lon = this.position.lng
            this.deliveryPoint.address = address
            this.deliveryPoint.name = name
            this.$emit('markedPoint', this.deliveryPoint)
        },
        resetPosition () {
            this.position = {}
        }
    }
}
</script>

<style scoped lang="scss">
.auto-complete {
    width: 100%;
}
.searsh-form {
    width: 35vw;
}
</style>