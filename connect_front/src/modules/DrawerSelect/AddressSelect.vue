<template>
    <div>
        <div 
            v-if="inputType === 'default'"
            class="address_select ant-btn ant-btn-primary ant-btn-lg ant-btn-block flex items-center justify-between truncate cursor-pointer"
            @click="visible = true">
            <div class="truncate">
                {{ displayPlaceholder }}
            </div>
            <i class="fi fi-rr-marker ml-2" />
        </div>
        <div v-if="inputType === 'ghost'" class="address_select_ghost truncate" :class="value && 'selected'" @click="visible = true">
            <div class="flex items-center select_placeholder truncate">
                <div class="mr-5">
                    <i class="fi fi-rr-marker" />
                </div>
                <span class="truncate">{{ value ? value.name : displayPlaceholder }}</span>
            </div>
            <i class="fi fi-rr-angle-small-down ml-2 select_arrow" />
        </div>
        <DrawerTemplate
            ref="selectAddressDrawer"
            placement="right"
            wrapClassName="address_select_drawer"
            :width="drawerWidth"
            v-model="visible"
            :zIndex="2000"
            destroyOnClose
            @afterVisibleChange="afterVisibleChange"
            @close="visible = false">
            <template #title>
                <div class="drawer_title">
                    Адреса
                </div>
            </template>
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
                                    <div v-on-click-outside="clickOutside2">
                                        <a-popover 
                                            :visible="searchVisible2"
                                            trigger="none"
                                            overlayClassName="search_popover"
                                            placement="bottomLeft"
                                            :getPopupContainer="trigger => trigger.parentElement">
                                            <a-input
                                                v-model="form.address"
                                                :placeholder="$t('sports.map_search')"
                                                size="large"
                                                class="w-full"
                                                @change="handleSearch2">
                                                <template slot="suffix">
                                                    <a-spin v-if="searchLoading2" size="small" />
                                                    <template v-else>
                                                        <a-button 
                                                            v-if="form.address"
                                                            flaticon
                                                            ghost
                                                            type="ui"
                                                            size="small"
                                                            shape="circle"
                                                            icon="fi-rr-cross-small"
                                                            @click="clearSelected()" />
                                                        <i v-else class="fi fi-rr-search" style="opacity: 0.6;" />
                                                    </template>
                                                </template>
                                            </a-input>
                                            <div class="mt-1" style="color:#000;line-height: 24px;">
                                                {{ $t('sports.map_select_point') }}
                                            </div>
                                            <template slot="content">
                                                <div class="search_content">
                                                    <div 
                                                        v-for="item in searchResult2" 
                                                        :key="item.place_id" 
                                                        class="search_item"
                                                        @click="selectAddress(item)">
                                                        {{ item.display_name }}
                                                    </div>
                                                </div>
                                            </template>
                                        </a-popover>
                                    </div>
                                </a-form-model-item>
                                <!--<div class="grid gap-4 lg:grid-cols-2">
                                    <a-form-model-item ref="lat" :label="$t('sports.lat')" prop="lat">
                                        <a-input 
                                            v-model="form.lat" 
                                            size="large" 
                                            disabled
                                            :placeholder="$t('sports.lat')" /> 
                                    </a-form-model-item>
                                    <a-form-model-item ref="lon" :label="$t('sports.lng')" prop="lon">
                                        <a-input 
                                            v-model="form.lon" 
                                            size="large" 
                                            disabled
                                            :placeholder="$t('sports.lng')" /> 
                                    </a-form-model-item>
                                </div>-->
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
                        <div v-if="addressList && addressList.length" class="mt-3">
                            <div v-for="(point, index) in addressList" :key="point.id" class="address_item">
                                <div style="color: #000;">
                                    <div v-if="point.name" class="mb-1">
                                        {{ point.name }}    
                                    </div>
                                    <span style="opacity: 0.6;">
                                        {{ point.address }}    
                                    </span>
                                    <div v-if="point.lat && point.lon" style="opacity: 0.6;">
                                        {{ point.lat }}, {{ point.lon }}
                                    </div>
                                </div>
                                <div class="flex items-center pl-2">
                                    <a-button 
                                        v-if="point.key !== form.key"
                                        icon="fi-rr-edit" 
                                        flaticon
                                        @click="addressEdit(point)" />
                                    <a-button 
                                        type="danger"
                                        class="ml-1"
                                        icon="fi-rr-trash" 
                                        flaticon
                                        @click="addressDelete(index)" />
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                <div class="map" ref="mapWrapper">
                    <l-map
                        v-if="leafletReady"
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
                                <div v-on-click-outside="clickOutside">
                                    <a-popover 
                                        :visible="searchVisible"
                                        trigger="none"
                                        overlayClassName="search_popover"
                                        placement="bottomLeft"
                                        :getPopupContainer="trigger => trigger.parentElement">
                                        <a-input
                                            v-model="searchString" 
                                            :placeholder="$t('sports.map_search')"
                                            size="large"
                                            class="w-full"
                                            @change="handleSearch">
                                            <template slot="suffix">
                                                <a-spin v-if="searchLoading" size="small" />
                                                <i v-else class="fi fi-rr-search" style="opacity: 0.6;" />
                                            </template>
                                        </a-input>
                                        <template slot="content">
                                            <div class="search_content">
                                                <div 
                                                    v-for="item in searchResult" 
                                                    :key="item.place_id" 
                                                    class="search_item"
                                                    @click="selectAddress(item)">
                                                    {{ item.display_name }}
                                                </div>
                                            </div>
                                        </template>
                                    </a-popover>
                                </div>
                            </div>
                        </l-control>
                    </l-map>
                </div>
            </div>
        </DrawerTemplate>
    </div>
</template>

<script>
import { mapState } from 'vuex'
import { latLng } from "leaflet"
import 'leaflet-geosearch/dist/geosearch.css'
import axios from 'axios'
import { vOnClickOutside } from '@vueuse/components'
let searchTimer;
let searchTimer2;
import { v1 as uuidv1 } from 'uuid'
export default {
    components: {
        LMap: () => import('vue2-leaflet').then(m => m.LMap),
        LTileLayer: () => import('vue2-leaflet').then(m => m.LTileLayer),
        LMarker: () => import('vue2-leaflet').then(m => m.LMarker),
        LControl: () => import('vue2-leaflet').then(m => m.LControl),
        DrawerTemplate: () => import('@/components/DrawerTemplate.vue')
    },
    directives: {
        onClickOutside: vOnClickOutside
    },
    props: {
        inputType: {
            type: String,
            default: 'default'
        },
        value: {
            type: Object,
            default: null
        },
        placeholder: {
            type: String,
            default: 'sports.specify_address'
        },
        addressList: {
            type: Array,
            default: () => []
        },
        addressDelete: {
            type: Function,
            default: () => {}
        }
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
        },
        displayPlaceholder() {
            if (!this.placeholder) {
                return ''
            }

            return this.$te(this.placeholder) ? this.$t(this.placeholder) : this.placeholder
        }
    },
    data() {
        const checkAddress = (rule, value, callback) => {
            if (!value)
                return callback(new Error(this.$t('sports.formError')))

            const lat = String(this.form.lat || '').trim()
            const lon = String(this.form.lon || '').trim()

            if (!lat.length || !lon.length)
                return callback(new Error(this.$t('sports.map_select_warning')))

            callback()
        }
        return {
            leafletReady: false,
            isEdit: false,
            searchString: '',
            searchLoading: false,
            searchLoading2: false,
            searchResult: [],
            searchResult2: [],
            loading: false,
            mapMarker: null,
            visible: false,
            searchVisible: false,
            searchVisible2: false,
            zoom: 5,
            attribution: '',
            center: [50.38232184619959,69.70316200029406],
            rules: {
                name: [
                    { required: true, message: this.$t('sports.formError'), trigger: 'blur' }
                ],
                address: [
                    { validator: checkAddress, trigger: 'blur' }
                ],
            },
            form: {
                lat: "",
                lon: "",
                name: "",
                address: "",
                key: null
            }
        }
    },
    methods: {
        addressEdit(point) {
            this.isEdit = true
            this.form = {...point}
        },
        clearSelected() {
            this.form.lat = ""
            this.form.lon = ""
            this.form.name = ""
            this.form.address = ""
            this.searchClear()
        },
        clickOutside() {
            if(this.searchVisible)
                this.searchClear()
        },
        clickOutside2() {
            if(this.searchVisible2)
                this.searchClear()
        },
        searchClear() {
            this.searchVisible = false
            this.searchResult = []
            this.searchString = ''
            this.searchVisible2 = false
            this.searchResult2 = []
        },
        getPopupContainer() {
            return this.$refs.mapWrapper
        },
        editAddress(address) {
            this.isEdit = true
            this.form = {...address}
            this.mapMarker = {
                lat: address.lat,
                lon: address.lon
            }
            this.center = latLng(address.lat, address.lon)
            this.zoom = 17
            this.visible = true
        },
        selectAddress(item) {
            this.mapMarker = {
                lat: item.lat,
                lon: item.lon
            }
            this.$nextTick(() => {
                this.$refs.mapRef.mapObject.flyTo(latLng(item.lat, item.lon), 17, {
                    duration: 1.5,
                    easeLinearity: 1.5
                })
                this.$refs.mapRef.mapObject.invalidateSize()
            })
            this.getPointData(item.lat, item.lon)
        },
        handleSearch(e) {
            const q = e.target.value
            clearTimeout(searchTimer)
            if(q.length) {
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
                        this.searchResult = data
                        if(data?.length) {
                            this.searchVisible = true
                        } else {
                            if(this.searchVisible)
                                this.searchVisible = false
                        }
                    } catch(e) {
                        console.log(e)
                    } finally {
                        this.searchLoading = false
                    }
                }, 500)
            } else {
                this.searchVisible = false
                this.searchResult = []
            }
        },
        handleSearch2(e) {
            const q = e.target.value
            clearTimeout(searchTimer2)
            if(q.length) {
                searchTimer2 = setTimeout(async () => {
                    try {
                        this.searchLoading2 = true
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
                        this.searchResult2 = data
                        if(data?.length) {
                            this.searchVisible2 = true
                        } else {
                            if(this.searchVisible2)
                                this.searchVisible2 = false
                        }
                    } catch(e) {
                        console.log(e)
                    } finally {
                        this.searchLoading2 = false
                    }
                }, 500)
            } else {
                this.searchVisible2 = false
                this.searchResult2 = []
            }
        },
        addressSave() {
            this.$refs.formRef.validate(valid => {
                if (valid) {
                    const lat = String(this.form.lat || '').trim()
                    const lon = String(this.form.lon || '').trim()

                    if (lat.length && lon.length) {
                        this.$emit('input', this.form)
                        this.$emit('change', this.form)
                        this.visible = false
                    } else {
                        this.$message.warning(this.$t('sports.map_select_warning'))
                    }
                } else {
                    return false
                }
            })
        },
        async afterVisibleChange(vis) {
            if(!vis) {
                this.isEdit = false
                this.mapMarker = null
                this.zoom = 5
                this.searchString = ''
                this.searchResult = []
                this.searchResult2 = []
                this.searchVisible2 = false
                this.searchVisible1 = false
                this.center = [50.38232184619959,69.70316200029406]
                this.form = {
                    lat: "",
                    lon: "",
                    name: "",
                    address: "",
                    key: null
                }
            } else {
                if (!this.leafletReady) {
                    await import('leaflet/dist/leaflet.css')
                    const L = (await import('leaflet')).default || (await import('leaflet'))
                    const iconRetina = require('leaflet/dist/images/marker-icon-2x.png')
                    const icon = require('leaflet/dist/images/marker-icon.png')
                    const shadow = require('leaflet/dist/images/marker-shadow.png')
                    delete L.Icon.Default.prototype._getIconUrl
                    L.Icon.Default.mergeOptions({
                        iconRetinaUrl: iconRetina,
                        iconUrl: icon,
                        shadowUrl: shadow
                    })
                    this.leafletReady = true
                    this.$nextTick(() => {
                        if (this.$refs.mapRef && this.$refs.mapRef.mapObject)
                            this.$refs.mapRef.mapObject.invalidateSize()
                    })
                }
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
                    if(this.isEdit) {
                        this.form = {
                            lat,
                            lon,
                            name: data.address.road || data.display_name,
                            address: data.display_name,
                            key: this.form.key,
                            id: this.form.id
                        }
                    } else {
                        this.form = {
                            key: uuidv1(),
                            id: uuidv1(),
                            lat,
                            lon,
                            name: data.address.road || data.display_name,
                            address: data.display_name,
                        }
                    }
                    this.searchClear()
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
.address_select_ghost{
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: space-between;
    user-select: none;
    .select_arrow{
        margin-right: 7px;
        color: #2D2D2D;
        font-size: 15px;
    }
    .select_placeholder{
        span{
            color: #888888;
        }
    }
    &.selected{
        .select_placeholder{
            span{
                color: var(--text);
            }
        }
    }
}
.address_item{
    margin-bottom: 15px;
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    border: 1px solid #e1e7ec;
    padding: 15px;
    border-radius: 8px;
}
.search_content{
    max-height: 400px;
    overflow-y: auto;
}
.search_item{
    padding: 5px 0;
    max-width: 500px;
    cursor: pointer;
    transition: all 0.3s cubic-bezier(0.645, 0.045, 0.355, 1);
    &:not(:last-child){
        border-bottom: 1px solid var(--border2);
    }
    &:hover{
        color: var(--blue);
    }
}
.address_select{
    color: #fff;
}
.mapWrapper{
    border-radius: 8px;
    height: 400px;
    @media (min-width: 1024px) {
        height: 100%;
    }
}
.drawer_body{
    display: grid;
    gap: 20px;
    overflow-y: auto;
    height: 100%;
    @media (min-width: 1024px) {
        overflow-y: hidden;
        gap: 30px;
        grid-template-columns: 440px 1fr;
    }
    .aside{
        max-height: 100%;
        overflow-y: auto;
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
        .ant-input{
            min-width: 300px;
            max-width: 300px;
            @media (min-width: 1105px) {
                min-width: 500px;
                max-width: 500px;
            }
        }
    }
}
.address_select_drawer{
    &::v-deep{
        .ant-drawer-wrapper-body,
        .ant-drawer-content{
            overflow: hidden;
        }
    }
    
}
</style>
