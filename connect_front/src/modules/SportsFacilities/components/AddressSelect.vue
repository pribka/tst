<template>
    <div>
        <div 
            class="address_select ant-input ant-input-lg flex items-center justify-between truncate cursor-pointer"
            @click="visible = true">
            <div class="truncate">
                <!--<template v-if="value && value.name">
                    {{ value.name }}
                </template>-->
                <span style="color: rgba(0, 0, 0, 0.25);">
                    {{ $t('sports.address_select') }}
                </span>
            </div>
            <a-button 
                type="link"
                class="ml-2"
                icon="fi-rr-marker" 
                flaticon />
        </div>
        <a-drawer
            ref="selectAddressDrawer"
            title="Адреса"
            placement="right"
            wrapClassName="address_select_drawer"
            :width="drawerWidth"
            :visible="visible"
            destroyOnClose
            :afterVisibleChange="afterVisibleChange"
            @close="visible = false">
            <div class="drawer_body">
                <div class="aside">
                    <div class="form_wrapper">
                        <a-spin :spinning="loading">
                            <a-form-model
                                ref="formRef"
                                :model="form"
                                :rules="rules">
                                <a-form-model-item ref="name" :label="$t('sports.name')" prop="name">
                                    <a-input 
                                        v-model="form.name" 
                                        size="large" 
                                        :placeholder="$t('sports.name')" /> 
                                </a-form-model-item>
                                <a-form-model-item ref="address" :label="$t('sports.location')" prop="address">
                                    <a-input 
                                        v-model="form.address" 
                                        size="large" 
                                        :placeholder="$t('sports.location')" /> 
                                </a-form-model-item>
                                <div class="grid gap-4 lg:grid-cols-2">
                                    <a-form-model-item ref="lat" :label="$t('sports.lat')" prop="lat">
                                        <a-input 
                                            v-model="form.lat" 
                                            size="large" 
                                            :placeholder="$t('sports.lat')" /> 
                                    </a-form-model-item>
                                    <a-form-model-item ref="lon" :label="$t('sports.lng')" prop="lon">
                                        <a-input 
                                            v-model="form.lon" 
                                            size="large" 
                                            :placeholder="$t('sports.lng')" /> 
                                    </a-form-model-item>
                                </div>
                                <div class="grid gap-4 grid-cols-1 lg:grid-cols-2">
                                    <a-button type="primary" block size="large" @click="addressSave()">
                                        {{ $t('sports.save') }}
                                    </a-button>
                                    <a-button block size="large" @click="visible = false">
                                        {{ $t('sports.cancel') }}
                                    </a-button>
                                </div>
                            </a-form-model>
                        </a-spin>
                    </div>
                </div>
                <div class="map">
                    <l-map
                        ref="mapRef"
                        :zoom="zoom"
                        class="mapWrapper"
                        :center="center"
                        @dblclick="onMapClick">
                        <l-tile-layer
                            :url='url'
                            :attribution='attribution' />
                        <l-marker 
                            v-if="mapMarker"
                            :lat-lng="[mapMarker.lat, mapMarker.lon]" />
                        <l-control :zIndex=1100>
                            <div class="search_field">
                                <a-select
                                    show-search
                                    v-model="searchString"
                                    :placeholder="$t('sports.map_search')"
                                    :default-active-first-option="false"
                                    :show-arrow="false"
                                    size="large"
                                    :loading="searchLoading"
                                    :filter-option="false"
                                    :not-found-content="null"
                                    @search="handleSearch"
                                    @change="searchChange">
                                    <a-select-option v-for="item in searchResult" :key="item.place_id">
                                        {{ item.display_name }}
                                    </a-select-option>
                                </a-select>
                            </div>
                        </l-control>
                    </l-map>
                </div>
            </div>
        </a-drawer>
    </div>
</template>

<script>
import { mapState } from 'vuex'
import { LMap, LTileLayer, LMarker, LControl } from 'vue2-leaflet'
import { latLng } from "leaflet"
import 'leaflet/dist/leaflet.css'
import 'leaflet-geosearch/dist/geosearch.css'
import axios from 'axios'

let searchTimer;
export default {
    components: {
        LMap,
        LTileLayer,
        LMarker,
        LControl
    },
    props: {
        value: {
            type: Object,
            default: null
        },
    },
    computed: {
        ...mapState({
            config: state => state.config.config,
            windowWidth: state => state.windowWidth
        }),
        url() {
            return `${this.config.map?.tileUrl || null}?access-token=${this.config.map?.tileToken || null}&lang=${this.config.map?.tileLang || null}`
        },
        drawerWidth() {
            if(this.windowWidth > 1200)
                return this.windowWidth - 100
            else {
                return '100%'
            }
        }
    },
    data() {
        return {
            searchString: '',
            searchLoading: false,
            searchResult: [],
            loading: false,
            mapMarker: null,
            visible: false,
            zoom: 5,
            attribution: '',
            center: [50.38232184619959,69.70316200029406],
            rules: {
                name: [
                    { required: true, message: this.$t('sports.formError'), trigger: 'blur' }
                ],
                lat: [
                    { required: true, message: this.$t('sports.formError'), trigger: 'blur' }
                ],
                lon: [
                    { required: true, message: this.$t('sports.formError'), trigger: 'blur' }
                ],
                address: [
                    { required: true, message: this.$t('sports.formError'), trigger: 'blur' }
                ],
            },
            form: {
                lat: "",
                lon: "",
                name: "",
                address: ""
            }
        }
    },
    methods: {
        editAddress(address) {
            this.form = address
            this.mapMarker = {
                lat: address.lat,
                lon: address.lon
            }
            this.center = latLng(address.lat, address.lon)
            this.zoom = 17
            this.visible = true
        },
        searchChange(place_id) {
            const find = this.searchResult.find(f => f.place_id === place_id)
            if(find) {
                this.mapMarker = {
                    lat: find.lat,
                    lon: find.lon
                }
                //this.center = latLng(find.lat, find.lon)
                //this.zoom = 16
                this.$nextTick(() => {
                    this.$refs.mapRef.mapObject.flyTo(latLng(find.lat, find.lon), 17, {
                        duration: 1.5,
                        easeLinearity: 1.5
                    })
                    this.$refs.mapRef.mapObject.invalidateSize()
                })
                this.getPointData(find.lat, find.lon)
            }
        },
        handleSearch(q) {
            clearTimeout(searchTimer)
            searchTimer = setTimeout(async () => {
                try {
                    this.searchLoading = true
                    const { data } = await axios.get('https://nominatim.openstreetmap.org/search', {
                        params: {
                            format: "json",
                            countrycodes: "kz",
                            "accept-language": "ru",
                            addressdetails: 0,
                            limit: 10,
                            q
                        }
                    })
                    if(data) {
                        this.searchResult = data
                    }
                } catch(e) {
                    console.log(e)
                } finally {
                    this.searchLoading = false
                }
            }, 500)
        },
        addressSave() {
            this.$refs.formRef.validate(valid => {
                if (valid) {
                    this.$emit('input', this.form)
                    this.visible = false
                } else {
                    console.log('error submit!!')
                    return false;
                }
            })
        },
        afterVisibleChange(vis) {
            if(!vis) {
                this.mapMarker = null
                this.zoom = 5
                this.searchString = ''
                this.searchResult = []
                this.center = [50.38232184619959,69.70316200029406]
                this.form = {
                    lat: "",
                    lon: "",
                    name: "",
                    address: ""
                }
            } else {
                if(this.value) {
                    this.form = this.value
                    if(this.value.lat && this.value.lon) {
                        //this.center = latLng(this.value.lat, this.value.lon)
                        //this.zoom = 16
                        this.$nextTick(() => {
                            this.$refs.mapRef.mapObject.flyTo(latLng(this.value.lat, this.value.lon), 17, {
                                duration: 1.5,
                                easeLinearity: 1.5
                            })
                            this.$refs.mapRef.mapObject.invalidateSize()
                        })
                        this.mapMarker = this.value
                    }
                }
            }
        },
        onMapClick(e) {
            this.mapMarker = {
                lat: e.latlng.lat,
                lon: e.latlng.lng
            }
            this.getPointData(e.latlng.lat, e.latlng.lng)
        },
        async getPointData(lat, lon) {
            try {
                this.loading = true
                const { data } = await axios.get('https://nominatim.openstreetmap.org/reverse', {
                    params: {
                        format: "jsonv2",
                        lat,
                        lon,
                        "accept-language": "ru"
                    }
                })
                if(data) {
                    this.form = {
                        lat,
                        lon,
                        name: data.address.road || data.display_name,
                        address: data.display_name
                    }
                }
            } catch(e) {
                console.log(e)
            } finally {
                this.loading = false
            }
        }
    }
}
</script>

<style lang="scss" scoped>
.mapWrapper{
    border-radius: 8px;
    height: 400px;
    @media (min-width: 1024px) {
        height: 100%;
    }
}
.address_select_drawer{
    &::v-deep{
        .ant-drawer-wrapper-body,
        .ant-drawer-content{
            overflow: hidden;
        }
        .ant-drawer-body{
            padding: 0px;
            height: calc(100% - 40px);
        }
    }
    .drawer_body{
        padding: 15px;
        display: grid;
        gap: 20px;
        overflow-y: auto;
        height: 100%;
        @media (min-width: 1024px) {
            overflow-y: hidden;
            gap: 30px;
            padding: 20px;
            grid-template-columns: 440px 1fr;
        }
    }
    .form_wrapper{
        background: #FAFAFA;
        border-radius: 8px;
        padding: 15px;
        @media (min-width: 1024px) {
            padding: 20px;
        }
    }
    .search_field{
        &::v-deep{
            .ant-select{
                min-width: 300px;
                max-width: 300px;
                @media (min-width: 1105px) {
                    min-width: 500px;
                    max-width: 500px;
                }
            }
        }
    }
}
</style>