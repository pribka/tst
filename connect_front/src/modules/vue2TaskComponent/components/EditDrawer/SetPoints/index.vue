<template>
    <div class="points_wrap" :style="isMobile ? 'overflow-y: auto;' : 'display: flex;'">
        <div class="map" :class="isMobile && 'map_mobile'" :style="isMobile ? 'height: 300px;' : 'flex: 0 0 50%;'">
            <l-map
                ref="mapRef"
                :zoom="mapConfig.zoom"
                :center="mapConfig.center"
                :options="mapConfig.mapOptions"
                @dblclick="onMapClick">
                <l-tile-layer
                    :url='url'
                    :attribution='attribution'>
                </l-tile-layer>
                <l-marker v-if="markedPoint.lat && markedPoint.lng"
                          :lat-lng="markedPoint" />
                <l-marker
                    v-for="(point, n) in taskPointsList"
                    :key="n"
                    :lat-lng="[point.lat, point.lon]">
                    <l-tooltip>{{ point.name }}</l-tooltip>
                </l-marker>
                <l-marker v-if="searchMarker.lat && searchMarker.lon"
                          :visible="searchMarkerVisible"
                          :lat-lng="[searchMarker.lat, searchMarker.lon]">
                    <l-tooltip :options="{ permanent: true }">
                        {{ searchMarker.toolTipText }}
                    </l-tooltip>            
                </l-marker>
                <l-control :zIndex=1100>
                    <div class="search_field">
                        <a-auto-complete
                            :value="searchString"
                            class="auto-complete"
                            :placeholder="$t('task.map_search_placeholder')"
                            :getPopupContainer="trigger => trigger.parentElement"
                            @search="handleAdressChange">
                            <template slot="dataSource">
                                <a-select-option
                                    v-for="(result, index) in autoCompleteResult"
                                    :key=String(index)
                                    @click="setResult(result)">
                                    {{ result.label }}
                                </a-select-option>
                            </template>
                            <a-input-search
                                allowClear
                                :loading="searchLoading"
                                @input="onInput"/>
                        </a-auto-complete>
                    </div>
                </l-control>
            </l-map>
        </div>
        <div class="points_list_wrap" :style="!isMobile && 'flex: 0 0 50%; height: 100%;'">
            <div>
                <div v-if="taskTitle" class="font-semibold text-base mb-5">
                    {{ $t('task.task') }}: {{ taskTitle }}
                </div>
                <a-form-model
                    ref="newPointForm"
                    :model="pointFormData"
                    :rules="mapConfig.form_rules">
                    <a-row>
                        <a-col :span="24">
                            <a-form-model-item prop="name">
                                <a-spin :spinning="inputLoading">
                                    <a-input v-model="pointFormData.name" :placeholder="$t('task.small_name')" />
                                </a-spin>
                            </a-form-model-item>
                        </a-col>
                    </a-row>
                    <a-row type="flex" justify="space-between" :gutter="16">
                        <a-col :span="12">
                            <a-form-model-item prop="lat">
                                <a-spin :spinning="inputLoading">
                                    <a-input v-model="pointFormData.lat"
                                             size="large"
                                             :placeholder="$t('task.latitude')"
                                             disabled="disabled" />
                                </a-spin>
                            </a-form-model-item>
                        </a-col>
                        <a-col :span="12">
                            <a-form-model-item prop="lon">
                                <a-spin :spinning="inputLoading">
                                    <a-input v-model="pointFormData.lon"
                                             size="large"
                                             :placeholder="$t('task.longitude')"
                                             disabled="disabled" />
                                </a-spin>
                            </a-form-model-item>
                        </a-col>
                    </a-row>
                    <a-row>
                        <a-col :span="24">
                            <a-form-model-item prop="address">
                                <a-spin :spinning="inputLoading">
                                    <a-input v-model="pointFormData.address" size="large" type="textarea" :placeholder="$t('task.address')" />
                                </a-spin>
                            </a-form-model-item>
                        </a-col>
                    </a-row>
                    <a-form-model-item v-if="!isMobile">
                        <a-button type="primary" :disabled="inputLoading" @click="setPoint()">
                            {{ $t('task.add_address') }}
                        </a-button>
                        <a-button class="ml-2" type="dashed" @click="resetForm()">
                            {{ $t('task.clear') }}
                        </a-button>
                    </a-form-model-item>
                    <template v-else>
                        <a-button type="primary" :disabled="inputLoading" block class="mb-2" @click="setPoint()">
                            {{ $t('task.add_address') }}
                        </a-button>
                        <a-button class="mb-6" block type="dashed" @click="resetForm()">
                            {{ $t('task.clear') }}
                        </a-button>
                    </template>
                </a-form-model>
            </div>
            <div v-if="taskPointsList.length !== 0">
                <div v-if="mapConfig.listTitle" class="font-semibold text-base mb-5">
                    {{ mapConfig.listTitle }}
                </div>
                <a-list
                    class="loadmore-list"
                    item-layout="horizontal"
                    v-for="(point, n) in taskPointsList"
                    :key="n">
                    <a-list-item>
                        <a-button :class="isMobile && 'ant-btn-icon-only'" slot="actions" @click="showConfirm(point)">
                            <template v-if="isMobile">
                                <i class="fi fi-rr-trash"></i>
                            </template>
                            <template v-else>
                                {{ $t('task.remove') }}
                            </template>
                        </a-button>
                        <a-list-item-meta :description="point.lat+', '+point.lon">
                            <div slot="title" class="list-item">
                                <h3>{{ point.name }}</h3>
                                <p>{{ point.address }}</p>
                            </div>
                        </a-list-item-meta>
                    </a-list-item>
                </a-list>
            </div>
        </div>
    </div>
</template>
  
<script>
import { LMap, LTileLayer, LMarker, LTooltip, LControl } from 'vue2-leaflet'
import { OpenStreetMapProvider } from 'leaflet-geosearch'
import { mapState } from 'vuex'
import 'leaflet/dist/leaflet.css'
import 'leaflet-geosearch/dist/geosearch.css'

let timer

export default {
    name: 'SetPoints',
    props: {
        mapConfig: {
            type: Object,
            default: () => {}
        },
        ownerSelect: {
            type: Boolean,
            default: false
        },
        taskTitle: {
            type: String,
            default: ''
        }
    },
    components: {
        LMap,
        LTileLayer,
        LMarker,
        LTooltip,
        LControl,
    },
    data() {
        return {
            provider: new OpenStreetMapProvider({
                params: {
                    'accept-language': 'ru',
                    countrycodes: ['ru', 'kz'],
                    addressdetails: 0,
                    limit: 7,
                },
            }),
            attribution: '',
            autoCompleteResult: [],
            searchMarkerVisible: false,
            searchLoading: false,
            searchString: '',
            inputLoading: false,
            point: {
                lat: null,
                lon: null,
                address: '',
                name: '',
            },
        };
    },
    computed: {
        ...mapState({
            config: state => state.config.config,
            taskPointsList: state => state.task.taskPointsList,
            pointFormData: state => state.task.pointFormData,
            markedPoint: state => state.task.markedPoint,
            searchMarker: state => state.task.searchMarker,
        }),
        url() {
            return `${this.config.map?.tileUrl || null}?access-token=${this.config.map?.tileToken || null}&lang=${this.config.map?.tileLang || null}`
        },
        isMobile() {
            return this.$store.state.isMobile
        },
    },
    methods: {
        clearAll() {
            this.autoCompleteResult = []
            this.searchString = ''
            this.$store.commit('task/RESET_POINT_FORM_DATA')
            this.$store.commit('task/SET_MARKED_POINT', {})
        },
        hideSearchResult() {
            this.searchMarkerVisible = false
            this.$store.commit('task/SET_SEARCH_MARKER', {
                lat: null,
                lon: null,
                toolTipText: ''
            })
        },
        onInput(val) {
            if(this.searchString === '') {
                this.hideSearchResult()
            }
        },
        showConfirm(point) {
            this.$confirm({
                title: this.$t('task.point_delete'),
                content: h => <div ><p><b>{point.name}</b></p><p>{point.address}</p><p>({point.lat}, {point.lon})</p></div>,
                okText: this.$t('task.yes'),
                okType: 'danger',
                cancelText: this.$t('task.no'),
                zIndex: 1100,
                onOk: () => {
                    this.$store.commit('task/DELETE_FROM_TASK_POINT_LIST', point)
                    this.$message.info(this.$t('task.address_deleted'))
                    this.$store.commit('task/SET_MARKED_POINT', {})
                },
                onCancel() {},
            })
        },
        setPoint() {
            this.$refs.newPointForm.validate(async valid => {
                if (valid) {
                    this.$store.commit('task/ADD_TO_TASK_POINT_LIST', this.pointFormData)
                    this.$store.commit('task/SET_MARKED_POINT', {})
                } else {
                    this.$message.error(this.$t('task.form_field_required'))
                }
            })
        },
        resetForm () {
            this.$refs.newPointForm.resetFields()
            this.$store.commit('task/SET_MARKED_POINT', {})
        },
        async onMapClick (value) {

            this.$nextTick(() => {
                this.$store.commit('task/SET_MARKED_POINT', value.latlng)
            })
            
            this.inputLoading = true
            try {
                const { lat, lng } = value.latlng
                const result = await fetch(
                  `https://nominatim.openstreetmap.org/reverse?format=jsonv2&lat=${lat}&lon=${lng}&accept-language=ru`
                )
                if (result.status === 200) {
                    this.hideSearchResult()
                    const body = await result.json()
                    this.pointFormData.lat = +value.latlng.lat.toFixed(12)
                    this.pointFormData.lon = +value.latlng.lng.toFixed(12)
                    this.pointFormData.address = body.display_name
                    this.pointFormData.name = `${body.display_name.split(', ', 2)[1]}, ${body.display_name.split(', ', 2)[0]}`
                }
            } catch (e) {
                console.error('Reverse Geocode Error->', e)
            } finally {
                this.inputLoading = false
            }
        },
        async handleAdressChange(value) {
            this.searchString = value
            if(value === '') {
                this.autoCompleteResult = []
                this.searchMarkerVisible = false
            }
            clearTimeout(timer)
            if(value.trim().length >= 3) {
                timer = setTimeout(() => {
                    this.searchLoading = true
                    try {
                        this.provider.search({ query: value })
                            .then((result)=> {
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
        setResult(result) {
            this.searchMarkerVisible = true
            this.searchString = result.label
            this.$refs.mapRef.mapObject.setView({lat: result.y, lng: result.x}, 17)
            if(result.bounds)
                this.$refs.mapRef.mapObject.fitBounds(result.bounds)
            this.$store.commit('task/SET_SEARCH_MARKER', {
                lat: result.y,
                lon: result.x,
                toolTipText: result.label.slice(0, 25)+'...'
            })
        },
    }
}
</script>

<style lang="scss">

.set_task_points{
    .map {
        height: 100%;
    }
    .ant-drawer-content,
    .ant-drawer-wrapper-body{
        overflow-y: hidden;
    }
    .ant-drawer-body{
        padding: 0px;
        height: calc(100% - 80px);
    }
    .leaflet-top {
        width: 100%;
    }
    .search_field {
        width: 70vh;
        margin-left: auto;
    }
    .d_footer{
        align-items: center;
        height: 40px;
        border-top: 1px solid #e8e8e8;
        padding-left: 30px;
        padding-right: 30px;
            .close_btn{
                margin-right: 5px;
            }
    }
}
</style>

<style lang="scss">
.points_wrap{
    &.map_mobile{
        .points_wrap{
            height: 100%;
            width: 100%;
        }
    }
}
</style>

<style scoped lang="scss">
.set_task_points{
    .points_wrap{
        flex-direction: row;
        justify-content: space-between;
        align-items: stretch;
        height: 100%;
        .points_list_wrap{
            padding: 20px 15px;
            overflow-y: auto;
        }
    }
}
.auto-complete {
    width: 100%;
}
.list-item {
    h3 {
        font-weight: bold;
    }
}
</style>