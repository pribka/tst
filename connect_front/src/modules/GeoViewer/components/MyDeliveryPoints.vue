<template> 
    <!-- comment -->
    <a-drawer
        title="Точки доставки"
        :width="windowWidth > 1500 ? 1500 : windowWidth"
        class="my_points_drawer"
        :zIndex="1100"
        placement="right"
        :visible="visible"
        :after-visible-change="afterVisibleChange"
        :destroyOnClose = "true"
        @close="onClose">
        <div class="points_wrap" :style="isMobile ? 'overflow-y: auto;' : 'display: flex;'">
            <div class="mdpc-map" :class="isMobile && 'map_mobile'" :style="isMobile ? 'height: 300px;' : 'flex: 0 0 50%; height: 100%;'">
                <MapConponent
                    :contractorDeliveryPointsList='contractorDeliveryPointsList'
                    :centerPointlat='centerPointlat'
                    :centerPointlon='centerPointlon'
                    :key='mapComponentKey'
                    class="h-full"
                    @markedPoint="onMarker"
                    @inputLoading="inputLoadingChange" />
            </div>
            <div class="points_list_wrap" :style="!isMobile && 'flex: 0 0 50%; height: 100%;'">
                <div>
                    <a-descriptions title="Новая точка доставки" />
                    <a-form-model
                        ref="newDeliveryPointForm"
                        :model="formData"
                        :rules="rules">
                        <a-row>
                            <a-col :span="24">
                                <a-form-model-item prop="name">
                                    <a-input v-model="formData.name" placeholder="Краткое имя" />
                                </a-form-model-item>
                            </a-col>
                        </a-row>
                        <a-row type="flex" justify="space-between" :gutter="16">
                            <a-col :span="12">
                                <a-form-model-item prop="lat">
                                    <a-spin :spinning="inputLoading">
                                        <a-input v-model="formData.lat"
                                                 size="large"
                                                 placeholder="Широта"
                                                 disabled="disabled" />
                                    </a-spin>
                                </a-form-model-item>
                            </a-col>
                            <a-col :span="12">
                                <a-form-model-item prop="lon">
                                    <a-spin :spinning="inputLoading">
                                        <a-input v-model="formData.lon"
                                                 size="large"
                                                 placeholder="Долгота"
                                                 disabled="disabled" />
                                    </a-spin>
                                </a-form-model-item>
                            </a-col>
                        </a-row>
                        <a-row>
                            <a-col :span="24">
                                <a-form-model-item prop="address">
                                    <a-spin :spinning="inputLoading">
                                        <a-input v-model="formData.address" size="large" type="textarea" placeholder="Адрес" />
                                    </a-spin>
                                </a-form-model-item>
                            </a-col>
                        </a-row>
                        <a-form-model-item v-if="!isMobile">
                            <a-button type="primary" @click="createDeliveryPoint()">
                                Создать точку доставки
                            </a-button>
                            <a-button class="ml-2" type="dashed" @click="resetForm()">
                                Очистить
                            </a-button>
                        </a-form-model-item>
                        <template v-else>
                            <a-button type="primary" block class="mb-2" @click="createDeliveryPoint()">
                                Создать точку доставки
                            </a-button>
                            <a-button class="mb-6" block type="dashed" @click="resetForm()">
                                Очистить
                            </a-button>
                        </template>
                    </a-form-model>
                </div>
                <div id="v-model-select" class="mb-4 flex items-center">
                    <label for="contractorSelect" class="mr-2">Клиент:</label>
                    <a-select 
                        v-model="selectedContractor"
                        id ="contractorSelect"
                        class="w-full"
                        style="max-width: 240px;"
                        :loading="selectLoading"
                        @change="selectContractor">
                        <a-select-option disabled value="">Выберите клиента</a-select-option>
                        <a-select-option value="allContractors">Все клиенты</a-select-option>
                        <a-select-option 
                            v-for="contractor in contractorsList"
                            :key="contractor.id"
                            :value="contractor.id">
                            {{ contractor.string_view }}
                        </a-select-option>
                    </a-select>
                </div>
                <div>
                    <a-descriptions title="Точки доставки" />
                    <PointsList
                        :contractorDeliveryPointsList="contractorDeliveryPointsList"
                        :selectedContractor="selectedContractor" 
                        :loading="loading" />
                </div>
            </div>
        </div>
    </a-drawer>
</template>

<script>
import eventBus from '@/utils/eventBus.js'
import { Modal } from 'ant-design-vue'
import 'leaflet/dist/leaflet.css'
import 'leaflet-geosearch/dist/geosearch.css'
import { Icon } from 'leaflet'
delete Icon.Default.prototype._getIconUrl

Icon.Default.mergeOptions({
    iconRetinaUrl: require('leaflet/dist/images/marker-icon-2x.png'),
    iconUrl: require('leaflet/dist/images/marker-icon.png'),
    shadowUrl: require('leaflet/dist/images/marker-shadow.png')
})

export default {
    name: 'MyDeliveryPointsComponent',
    components: {
        MapConponent: () => import('./components/Map.vue'),
        PointsList: () => import('./components/PointsList.vue')
    },
    computed: {
        windowWidth() {
            return this.$store.state.windowWidth
        },
        isMobile() {
            return this.$store.state.isMobile
        }
    },
    data() {
        return{
            visible: false,
            contractorDeliveryPointsList: [],
            allContractorsDeliveryPointsList: [],
            contractorsList: [],
            loading: false,
            selectLoading: false,
            inputLoading: false,
            selectedContractor: '',
            mapComponentKey: true,
            centerPoint: {},
            centerPointlat: null,
            centerPointlon: null,
            currentContactor: '',
            requestSource: '',
            rules: {
                name: {
                    type: 'string',
                    required: true,
                    whitespace: true,
                    message: 'Обязательно для заполнения',
                },
                lat: [
                    {
                        type: 'number',
                        message: 'Необходимо ввести число',
                        trigger: 'blur'
                    },
                    {
                        required: true,
                        message: 'Обязательно для заполнения',
                        trigger: 'blur'
                    }],
                lon: [
                    {
                        type: 'number',
                        message: 'Необходимо ввести число',
                        trigger: 'blur'
                    },
                    {
                        required: true,
                        message: 'Обязательно для заполнения',
                        trigger: 'blur'
                    }],
                address: {
                    type: 'string',
                    required: true,
                    whitespace: true,
                    message: 'Обязательно для заполнения',
                }
            },
            formData: {
                name: '',
                lat: null,
                lon: null,
                address: ''
            }
        }
    },
    mounted () {
        eventBus.$on('open_delivery_points_drawer', (contractor='', source='') => {
            this.visible = true
            this.requestSource = source
            this.selectedContractor = contractor
            this.getContractorsDeliveryPointsList (contractor)
        })
        eventBus.$on('delet_delivery_points', this.deletDeliveryPoint)
        eventBus.$on('show_position', (coords = {}) => {
            this.getCenter(coords)
        })
        eventBus.$on('center_has_changed', (coords = {}) => {
            this.getCenter(coords)
        })
    },
    beforeDestroy () {
        eventBus.$off('open_delivery_points_drawer')
        eventBus.$off('delet_delivery_points')
        eventBus.$off('show_position')
        eventBus.$off('center_has_changed')
        
    },
    methods: {
        afterVisibleChange() {
            this.getContractorsList()
            this.getAllContractorDeliveryPoints()
        },
        async getContractorsList () {
            try {
                this.selectLoading = true
                await this.$http.get('/app_info/filtered_select_list/', {
                    params: {
                        model: 'catalogs.ContractorModel',
                        ordering: '-created_at',
                        filters: {
                            "is_carrier": false
                        }
                    }
                })
                    .then((data) => {
                        if (data?.data?.filteredSelectList) {
                            this.contractorsList = data.data.filteredSelectList
                        }
                    })
            } catch(e) {
                console.log(e)
            } finally {
                this.selectLoading = false
            }
        },
        async getAllContractorDeliveryPoints () {
            try {
                this.loading = true
                await this.$http.get('/catalogs/my_delivery_points/')
                    .then((data) => {
                        if (data?.data) {
                            this.allContractorsDeliveryPointsList = data.data
                        }
                    })
                    .then((res) => {
                        this.getContractorsDeliveryPointsList(this.selectedContractor)
                        if (!this.formData.address) {
                            this.getCenter()
                        }
                    })
            } catch(e) {
                console.log(e)
            } finally {
                this.loading = false
            }
        },
        async getContractorsDeliveryPointsList (contractor) {
            if (contractor === '' || contractor === 'allContractors') {
                this.contractorDeliveryPointsList = this.allContractorsDeliveryPointsList.filter(point => true)
                this.getCenter()
            } else {
                try {
                    this.Loading = true
                    await this.$http.get('/catalogs/my_delivery_points/', {
                        params: {
                            contractor: contractor
                        }
                    })
                        .then((data) => {
                            if (data?.data) {
                                this.contractorDeliveryPointsList = data?.data
                            }
                            if (!this.formData.address) {
                                this.getCenter()
                            }
                        })
                } catch(e) {
                    console.log(e)
                } finally {
                    this.Loading = false
                }
            }
        },
        getCenter (coords=null) {
            if (!coords) {
                if (this.contractorDeliveryPointsList?.[0]?.lat)
                    this.centerPointlat = this.contractorDeliveryPointsList[0].lat
                
                if (this.contractorDeliveryPointsList?.[0]?.lon) 
                    this.centerPointlon = this.contractorDeliveryPointsList[0].lon
            } else {
                this.centerPointlat = coords.lat
                this.centerPointlon = coords.lng
            }
            
        },
        async selectContractor () {
            await this.getContractorsDeliveryPointsList(this.selectedContractor)
            if (!this.formData.address) {
                this.getCenter()
            }
        },
        async deletDeliveryPoint (point) {
            let pointIndex = this.contractorDeliveryPointsList.indexOf(point)
            try {
                await this.$http.delete(`/catalogs/my_delivery_points/${point.id}/`)
                    .then((response) => {
                        if (response?.status === 204) {
                            this.getAllContractorDeliveryPoints ()
                            this.contractorDeliveryPointsList.splice(pointIndex, 1)
                            if(pointIndex === 0) {
                                if(this.contractorDeliveryPointsList.length) {
                                    this.$store.commit('dashboard/ADD_LAST_DELIVERY_POINT', {
                                        contractorId: this.selectedContractor,
                                        point: this.contractorDeliveryPointsList[0]
                                    })
                                } else {
                                    this.$store.commit('dashboard/ADD_LAST_DELIVERY_POINT', {
                                        contractorId: this.selectedContractor,
                                        point: {
                                            id: '',
                                            name: ''
                                        }
                                    })
                                }
                            }
                            if(this.requestSource === 'orderForm') {
                                eventBus.$emit('add_new_point', this.selectedContractor)
                            }
                            eventBus.$emit('update_address_list')
                            this.getCenter()
                        }
                    })
            } catch(e) {
                console.log(e)
            }
        },
        onClose () {
            this.centerPoint = {}
            this.visible = false
            this.resetForm()
        },
        onMarker (point) {
            this.formData.lat = Number(point.lat)
            this.formData.lon = Number(point.lon)
            this.formData.address = point.address
            this.formData.name = point.name
        },
        inputLoadingChange (value) {
            this.inputLoading = value
        },
        resetForm () {
            this.$refs.newDeliveryPointForm.resetFields()
            eventBus.$emit('reset_position')
        },
        async createDeliveryPoint () {
            if (this.selectedContractor === '' || this.selectedContractor === 'allContractors') {
                Modal.warning({
                    title: 'Не указан клиент',
                    content: 'Выберите в списке клиента, для которого создается точка доставки',
                })
            } else {
                this.$refs.newDeliveryPointForm.validate(async valid => {
                    if (valid) {
                        const data = {
                            lat: Number.parseFloat(this.formData.lat).toFixed(12),
                            lon: Number.parseFloat(this.formData.lon).toFixed(12),
                            address: this.formData.address,
                            name: this.formData.name,
                            contractor: this.selectedContractor
                        }
                        try {
                            await this.$http.post('/catalogs/my_delivery_points/', data)
                                .then((response) => {
                                    if (response?.status === 200 || response?.status === 201) {
                                        this.getAllContractorDeliveryPoints ()
                                        this.contractorDeliveryPointsList.unshift(response.data)
                                        this.resetForm()
                                        this.$store.commit('dashboard/ADD_LAST_DELIVERY_POINT', {
                                            contractorId: this.selectedContractor,
                                            point: response.data
                                        })
                                        eventBus.$emit('update_address_list')
                                        if(this.requestSource === 'orderForm') {
                                            eventBus.$emit('add_new_point', this.selectedContractor)
                                        }
                                    }
                                })
                        } catch(e) {
                            console.log(e)
                        }
                    } else {
                        console.log('Не удалось отправить данные!')
                        return false
                    }
                })
            }
        }
    }
}
</script>

<style lang="scss">

.my_points_drawer{
    .ant-drawer-content,
    .ant-drawer-wrapper-body{
        overflow: hidden;
    }
    .ant-drawer-body{
        padding: 0px;
        height: calc(100% - 40px);
    }
}
</style>

<style lang="scss">
.mdpc-map{
    &.map_mobile{
        .mdpc-map{
            height: 100%;
            width: 100%;
        }
    }
}
</style>

<style scoped lang="scss">
.my_points_drawer{
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
</style>
