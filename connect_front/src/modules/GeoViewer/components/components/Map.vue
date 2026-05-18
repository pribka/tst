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
            <!-- Форма поиска -->
            <l-control class="searsh-form">
                <a-form-item>
                    <a-auto-complete
                        class="auto-complete"
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
import { OpenStreetMapProvider } from 'leaflet-geosearch'
import { mapState } from 'vuex'

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
            address: '',
            searchVisible: false,
            shortAddress: '',
            autoCompleteResult: '',
            provider: new OpenStreetMapProvider({
                params: {
                    'accept-language': 'ru',
                    countrycodes: ['ru', 'kz'],
                    addressdetails: 0,
                    limit: 7,
                },
            }),
            options: {
                attributionControl: false
            },
            myCoordLoading: false,
            deliveryPoint: {
                lat: null,
                lon: null,
                address: '',
                name: '',
            }
        }
    },
    created() {
    },
    mounted () {
        eventBus.$on('reset_position', this.resetPosition)
    },
    beforeDestroy () {
        eventBus.$off('reset_position')
    },
    computed: {
        ...mapState({
            config: state => state.config.config,
        }),
        tileToken() {
            return this.config.map?.tileToken || null
        },
        url() {
            return `${this.config.map?.tileUrl || null}?access-token=${this.config.map?.tileToken || null}&lang=${this.config.map?.tileLang || null}`
        },
    },
    watch: {
    },
    methods: {
        setResult(result) {
            this.searchVisible = true
            this.searchAdress = {
                lat: result.raw.lat,
                lng: result.raw.lon
            }
            this.zoom = 15
            this.shortAddress = result.label.slice(0, 25)+'...'
            eventBus.$emit('show_position', this.searchAdress)
        },
        async handleAdressChange(value) {
            let autoCompleteResult = []

            try {
                const result = await this.provider.search({ query: value })
                if (result) {

                    result.forEach(element => {
                        autoCompleteResult.push(element.label)
                    })
                    this.autoCompleteResult = result
                }
            } catch (e) {
                console.error('Reverse Geocode Error->', e)
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
