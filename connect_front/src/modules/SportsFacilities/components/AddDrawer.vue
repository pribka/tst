<template>
    <DrawerTemplate
        ref="addInvestProjectDrawer"
        placement="right"
        :width="drawerWidth"
        v-model="visible"
        destroyOnClose
        @afterVisibleChange="afterVisibleChange"
        wrapClassName="sports_add_drawer"
        @close="visible = false">
        <template #title>
            <div class="drawer_title">
                {{ isEdit ? $t('sports.editTitle') : $t('sports.addTitle') }}
            </div>
        </template>
        <div ref="sportDrawerBody">
            <a-form-model
                v-if="editInit && visible"
                ref="formRef"
                :model="form"
                class="sport_form"
                :rules="rules">
                <div class="form_block">
                    <div class="form_block__header">
                        <h3>{{ $t('sports.formMainInfo') }}</h3>
                    </div>
                    <a-form-model-item ref="name" :label="$t('sports.object_name')" prop="name">
                        <a-input 
                            v-model="form.name" 
                            size="large" 
                            :placeholder="$t('sports.object_name')" /> 
                    </a-form-model-item>
                    <div class="grid gap-4 grid-cols-1 md:grid-cols-2">
                        <a-form-model-item ref="organization" :label="$t('sports.organization')" prop="organization">
                            <DSelect
                                v-model="form.organization"
                                size="large"
                                apiUrl="/contractor_permissions/organizations/"
                                class="w-full"
                                oneSelect
                                :listObject="false"
                                labelKey="name"
                                :params="{
                                    permission_type: 'create_sport_facility',
                                    display: 'descendants'
                                }"
                                :placeholder="$t('sports.selectFromList')"
                                :default-active-first-option="false"
                                :filter-option="false"
                                :not-found-content="null" />
                        </a-form-model-item>
                        <a-form-model-item ref="facility_type" :label="$t('sports.sportsFacilityType')" prop="facility_type">
                            <TreeSelect
                                v-model="form.facility_type"
                                apiUrl="/sports_facilities/types/"
                                titleKey="full_name"
                                :params="{
                                    parent: 'root'
                                }"
                                :treeDefaultExpandedKeys="facilityDefaultExpandedKeys"
                                @initLoading="sportsFacilityInitLoading" />
                        </a-form-model-item>
                    </div>
                </div>
                <div class="form_block">
                    <div class="form_block__header">
                        <h3>{{ $t('sports.cult_sports') }}</h3>
                    </div>
                    <a-form-model-item ref="sport_types" prop="sport_types">
                        <template v-if="isMobile">
                            <div 
                                v-for="(item, index) in form.sport_types" 
                                :key="item.id"
                                class="sport_type_card">
                                <a-form-model-item 
                                    :label="$t('sports.category')" 
                                    class="mb-1"
                                    :prop="'sport_types.' + index + '.sport_categories'">
                                    <TreeSelect
                                        v-model="form.sport_types[index].sport_categories"
                                        apiUrl="/sports_facilities/sport_categories/"
                                        :treeDefaultExpandedKeys="treeDefaultExpandedKeys"
                                        @change="changeSportCategory('sport_categories', index)"
                                        @initLoading="sportsCategoryInitLoading" />
                                </a-form-model-item>
                                <a-form-model-item 
                                    :label="$t('sports.sport_type')" 
                                    class="mb-1"
                                    :rules="
                                        form.sport_types[index].sport_categories ||
                                            form.sport_types[index].sport_categories2 ||
                                            form.sport_types[index].sport_categories3 ?
                                                {
                                                    required: true,
                                                    message: $t('field_required'),
                                                    trigger: 'blur'
                                                } : null"
                                    :prop="'sport_types.' + index + '.sport_types'">
                                    <DSelect
                                        v-model="form.sport_types[index].sport_types"
                                        size="large"
                                        apiUrl="/sports_facilities/sport_types/"
                                        class="w-full"
                                        oneSelect
                                        :getPContainer="getPContainer"
                                        usePopupContainer
                                        :params="{
                                            category: sportTypesParams(index)
                                        }"
                                        :listObject="false"
                                        valueKey="code"
                                        infinity
                                        :initList="isEdit ? true : false"
                                        :key="`${form.sport_types[index].sport_categories}${form.sport_types[index].sport_categories2}${form.sport_types[index].sport_categories3}`"
                                        :disabled="form.sport_types[index].sport_categories || form.sport_types[index].sport_categories2 || form.sport_types[index].sport_categories3 ? false : true"
                                        labelKey="name"
                                        placeholder="Выбрать"
                                        :default-active-first-option="false"
                                        :filter-option="false"
                                        :not-found-content="null" />
                                </a-form-model-item>
                                <a-form-model-item 
                                    :label="$t('sports.message_compliance')" 
                                    class="mb-2"
                                    :prop="'sport_types.' + index + '.repub_comp'">
                                    <a-checkbox v-model="form.sport_types[index].repub_comp" class="select-none">
                                        {{ $t('sports.Respond') }}
                                    </a-checkbox>
                                </a-form-model-item>
                                <a-button 
                                    v-if="form.sport_types && form.sport_types.length > 1"
                                    type="danger" 
                                    flaticon
                                    ghost
                                    block
                                    icon="fi-rr-trash"
                                    @click="deleteSportType(index)">
                                    Удалить
                                </a-button>
                            </div>
                        </template>
                        <a-table 
                            v-else
                            :columns="columns" 
                            :data-source="form.sport_types" 
                            :scroll="{ x: 1150 }"
                            class="c_table"
                            :locale="{
                                emptyText: $t('sports.noProjects')
                            }"
                            rowKey="id"
                            bordered
                            :pagination="false">
                            <div slot="sport_categories" slot-scope="text, record, index" class="w-full">
                                <TreeSelect
                                    v-model="form.sport_types[index].sport_categories"
                                    apiUrl="/sports_facilities/sport_categories/"
                                    :treeDefaultExpandedKeys="treeDefaultExpandedKeys"
                                    @change="changeSportCategory('sport_categories', index)"
                                    @initLoading="sportsCategoryInitLoading" />
                            </div>
                            <div slot="sport_types" slot-scope="text, record, index" class="w-full">
                                <a-form-model-item 
                                    :prop="'sport_types.' + index + '.sport_types'"
                                    class="mb-0"
                                    :rules="
                                        form.sport_types[index].sport_categories ||
                                            form.sport_types[index].sport_categories2 ||
                                            form.sport_types[index].sport_categories3 ?
                                                {
                                                    required: true,
                                                    message: $t('field_required'),
                                                    trigger: 'blur'
                                                } : null">
                                    <DSelect
                                        v-model="form.sport_types[index].sport_types"
                                        size="large"
                                        apiUrl="/sports_facilities/sport_types/"
                                        class="w-full"
                                        oneSelect
                                        :getPContainer="getPContainer"
                                        usePopupContainer
                                        :params="{
                                            category: sportTypesParams(index)
                                        }"
                                        :listObject="false"
                                        valueKey="code"
                                        infinity
                                        :initList="isEdit ? true : false"
                                        :key="`${form.sport_types[index].sport_categories}${form.sport_types[index].sport_categories2}${form.sport_types[index].sport_categories3}`"
                                        :disabled="form.sport_types[index].sport_categories || form.sport_types[index].sport_categories2 || form.sport_types[index].sport_categories3 ? false : true"
                                        labelKey="name"
                                        placeholder="Выбрать"
                                        :default-active-first-option="false"
                                        :filter-option="false"
                                        :not-found-content="null" />
                                </a-form-model-item>
                            </div>
                            <div slot="repub_comp" slot-scope="text, record, index" class="w-full">
                                <a-checkbox v-model="form.sport_types[index].repub_comp" class="select-none">
                                    {{ $t('sports.Respond') }}
                                </a-checkbox>
                            </div>
                            <div slot="id" slot-scope="text, record, index" class="w-full">
                                <a-button 
                                    v-if="form.sport_types && form.sport_types.length > 1"
                                    type="danger" 
                                    flaticon
                                    icon="fi-rr-trash"
                                    @click="deleteSportType(index)" />
                            </div>
                        </a-table>
                        <a-button 
                            type="primary" 
                            size="large" 
                            class="table_btn"
                            block
                            @click="addSportType()">
                            {{ $t('Add') }}
                        </a-button>
                    </a-form-model-item>
                </div>
                <div class="form_block">
                    <div class="form_block__header">
                        <h3>{{ $t('sports.formLocation') }}</h3>
                    </div>
                    <a-form-model-item ref="selectedLocation" :label="$t('sports.location')" prop="selectedLocation">
                        <a-input 
                            :value="locationName" 
                            size="large" 
                            disabled
                            :placeholder="$t('sports.location')" />
                        <a-checkbox v-model="form.is_countryside" class="mt-2">
                            {{ $t('sports.countryside') }}
                        </a-checkbox>
                    </a-form-model-item>
                    <div class="grid gap-4 grid-cols-1 md:grid-cols-2">
                        <a-form-model-item ref="locationRegion" :label="$t('sports.region')" prop="locationRegion">
                            <DSelect
                                v-model="form.locationRegion"
                                size="large"
                                apiUrl="/accounting_catalogs/locations/"
                                class="w-full"
                                :listObject="false"
                                :params="{
                                    parent: 'root'
                                }"
                                :placeholder="$t('sports.selectFromList')"
                                :default-active-first-option="false"
                                :filter-option="false"
                                :not-found-content="null"
                                @change="changeSelect('region')"
                                @changeGetObject="changeGetObject">
                                <template v-slot:option_item="{ data }">
                                    {{ data.code }} - {{ data.name }}
                                </template>
                            </DSelect>
                        </a-form-model-item>
                        <a-form-model-item ref="locationDistrict" :label="$t('sports.district')" prop="locationDistrict">
                            <DSelect
                                v-model="form.locationDistrict"
                                size="large"
                                apiUrl="/accounting_catalogs/locations/"
                                class="w-full"
                                :key="form.locationRegion"
                                :disabled="form.locationRegion ? false : true"
                                :initList="isEdit ? true : false"
                                :listObject="false"
                                :params="{
                                    parent: form.locationRegion
                                }"
                                :placeholder="$t('sports.selectFromList')"
                                :default-active-first-option="false"
                                :filter-option="false"
                                :not-found-content="null"
                                @change="changeSelect('district')"
                                @changeGetObject="changeGetObject">
                                <template v-slot:option_item="{ data }">
                                    {{ data.code }} - {{ data.name }}
                                </template>
                            </DSelect>
                        </a-form-model-item>
                        <a-form-model-item ref="location_akimat" :label="$t('sports.akimat')" prop="location_akimat">
                            <DSelect
                                v-model="form.location_akimat"
                                size="large"
                                apiUrl="/accounting_catalogs/locations/"
                                class="w-full"
                                :key="form.locationDistrict"
                                :disabled="form.locationDistrict ? false : true"
                                :initList="isEdit ? true : false"
                                :listObject="false"
                                :params="{
                                    parent: form.locationDistrict
                                }"
                                :placeholder="$t('sports.selectFromList')"
                                :default-active-first-option="false"
                                :filter-option="false"
                                :not-found-content="null"
                                @change="changeSelect('akimat')"
                                @changeGetObject="changeGetObject">
                                <template v-slot:option_item="{ data }">
                                    {{ data.code }} - {{ data.name }}
                                </template>
                            </DSelect>
                        </a-form-model-item>
                        <a-form-model-item ref="location_settlement" :label="$t('sports.settlement')" prop="location_settlement">
                            <DSelect
                                v-model="form.location_settlement"
                                size="large"
                                apiUrl="/accounting_catalogs/locations/"
                                class="w-full"
                                :key="form.location_akimat"
                                :disabled="form.location_akimat ? false : true"
                                :initList="isEdit ? true : false"
                                :listObject="false"
                                :params="{
                                    parent: form.location_akimat
                                }"
                                :placeholder="$t('sports.selectFromList')"
                                :default-active-first-option="false"
                                :filter-option="false"
                                :not-found-content="null"
                                @change="changeSelect('settlement')"
                                @changeGetObject="changeGetObject">
                                <template v-slot:option_item="{ data }">
                                    {{ data.code }} - {{ data.name }}
                                </template>
                            </DSelect>
                        </a-form-model-item>
                        <a-form-model-item ref="location" :label="$t('sports.village')" prop="location">
                            <DSelect
                                v-model="form.location"
                                size="large"
                                apiUrl="/accounting_catalogs/locations/"
                                class="w-full"
                                :key="form.location_settlement"
                                :disabled="form.location_settlement ? false : true"
                                :initList="isEdit ? true : false"
                                :listObject="false"
                                :params="{
                                    parent: form.location_settlement
                                }"
                                :placeholder="$t('sports.selectFromList')"
                                :default-active-first-option="false"
                                :filter-option="false"
                                :not-found-content="null"
                                @changeGetObject="changeGetObject">
                                <template v-slot:option_item="{ data }">
                                    {{ data.code }} - {{ data.name }}
                                </template>
                            </DSelect>
                        </a-form-model-item>
                        <a-form-model-item ref="location_point" :label="$t('sports.provide_address')" prop="location_point">
                            <AddressSelect v-model="form.location_point" ref="addressSelect"  />
                        </a-form-model-item>
                    </div>
                    <div v-if="form.location_point" class="address_item">
                        <span>
                            {{ form.location_point.address }}    
                        </span>
                        <div class="flex items-center pl-2">
                            <a-button 
                                icon="fi-rr-edit" 
                                flaticon
                                @click="editAddress()" />
                            <a-button 
                                type="danger"
                                class="ml-1"
                                icon="fi-rr-trash" 
                                flaticon
                                @click="form.location_point = null" />
                        </div>
                    </div>
                </div>
                <div class="form_block">
                    <div class="form_block__header">
                        <h3>{{ $t('sports.formObjectInfo') }}</h3>
                    </div>
                    <a-form-model-item ref="owner_name" :label="$t('sports.org_name')" prop="owner_name">
                        <a-input 
                            v-model="form.owner_name" 
                            size="large" 
                            :placeholder="$t('sports.org_name')" /> 
                    </a-form-model-item>
                    <div class="grid gap-4 grid-cols-1 md:grid-cols-2">
                        <a-form-model-item ref="owner_bin" :label="$t('sports.bin')" prop="owner_bin">
                            <a-input 
                                v-model="form.owner_bin" 
                                size="large" 
                                :placeholder="$t('sports.bin')" /> 
                        </a-form-model-item>
                        <a-form-model-item ref="ownership_form" :label="$t('sports.ownershipType')" prop="ownership_form">
                            <DSelect
                                v-model="form.ownership_form"
                                size="large"
                                apiUrl="/app_info/filtered_select_list/"
                                class="w-full"
                                valueKey="code"
                                listObject="filteredSelectList"
                                :params="{
                                    model: 'sports_facilities_info.SportFacilityOwnershipFormModel'
                                }"
                                :placeholder="$t('sports.selectFromList')"
                                :default-active-first-option="false"
                                :filter-option="false"
                                :not-found-content="null" />
                        </a-form-model-item>
                        <a-form-model-item ref="purpose3" :label="$t('sports.purpose')" prop="purpose3">
                            <DSelect
                                v-model="form.purpose3"
                                size="large"
                                apiUrl="/sports_facilities/purposes/"
                                class="w-full"
                                :listObject="false"
                                labelKey="name"
                                valueKey="code"
                                :params="{
                                    parent: 'root'
                                }"
                                :placeholder="$t('sports.selectFromList')"
                                :default-active-first-option="false"
                                :filter-option="false"
                                :not-found-content="null"
                                @change="changePurpose('purpose3')" />
                        </a-form-model-item>
                        <a-form-model-item ref="purpose2" :label="$t('sports.o_type')" prop="purpose2">
                            <DSelect
                                v-model="form.purpose2"
                                size="large"
                                apiUrl="/sports_facilities/purposes/"
                                class="w-full"
                                :listObject="false"
                                labelKey="name"
                                :key="form.purpose3"
                                :disabled="form.purpose3 && form.purpose3 !== 'physical_edu_sport' && form.purpose3 !== 'exercise_sport' ? false : true"
                                valueKey="code"
                                :params="{
                                    parent: form.purpose3
                                }"
                                :placeholder="$t('sports.selectFromList')"
                                :default-active-first-option="false"
                                :filter-option="false"
                                :not-found-content="null"
                                @change="changePurpose('purpose2')" />
                        </a-form-model-item>
                        <a-form-model-item ref="purpose" :label="$t('sports.sport_school_type')" prop="purpose">
                            <DSelect
                                v-model="form.purpose"
                                size="large"
                                apiUrl="/sports_facilities/purposes/"
                                class="w-full"
                                :listObject="false"
                                labelKey="name"
                                :key="form.purpose2"
                                :disabled="form.purpose2 ? false : true"
                                valueKey="code"
                                :params="{
                                    parent: form.purpose2
                                }"
                                :placeholder="$t('sports.selectFromList')"
                                :default-active-first-option="false"
                                :filter-option="false"
                                :not-found-content="null" />
                        </a-form-model-item>
                        <a-form-model-item ref="building_year" :label="$t('sports.constructionYear')" prop="building_year">
                            <a-input-number 
                                v-model="form.building_year" 
                                size="large" class="w-full" 
                                :placeholder="$t('sports.constructionYear')" 
                                :min="1" />
                        </a-form-model-item>
                    </div>
                </div>
                <div class="form_block">
                    <div class="form_block__header">
                        <h3>{{ $t('sports.formOtherInfo') }}</h3>
                    </div>
                    <div class="grid gap-4 grid-cols-1 md:grid-cols-2 xl:grid-cols-3">
                        <a-form-model-item ref="heating_type" :label="$t('sports.heating_type')" prop="heating_type">
                            <DSelect
                                v-model="form.heating_type"
                                size="large"
                                class="w-full"
                                valueKey="code"
                                :params="{
                                    model: 'sports_facilities_info.SportFacilityHeatingTypeModel'
                                }"
                                :placeholder="$t('sports.selectFromList')"
                                :default-active-first-option="false"
                                :filter-option="false"
                                :not-found-content="null" />
                        </a-form-model-item>
                        <a-form-model-item ref="staff_quantity" :label="$t('sports.staff_quantity')" prop="staff_quantity">
                            <a-input-number 
                                v-model="form.staff_quantity" 
                                size="large" 
                                class="w-full" 
                                :parser="decParser2"
                                :placeholder="$t('sports.staff_quantity')"
                                :min="1" />
                        </a-form-model-item>
                        <a-form-model-item ref="area" :label="$t('sports.area2')" prop="area">
                            <a-input-number 
                                v-model="form.area" 
                                size="large" 
                                class="w-full" 
                                :step="0.1"
                                :parser="decParser"
                                :min="1"
                                decimalSeparator="."
                                :placeholder="$t('sports.area2')" /> 
                        </a-form-model-item>
                        <a-form-model-item ref="bandwidth" :label="$t('sports.capacity2')" prop="bandwidth">
                            <a-input-number 
                                v-model="form.bandwidth" 
                                size="large" 
                                class="w-full" 
                                :parser="decParser2"
                                :placeholder="$t('sports.capacity2')"
                                :min="1" />
                        </a-form-model-item>
                        <a-form-model-item ref="storeys_number" :label="$t('sports.storeys')" prop="storeys_number">
                            <a-input-number 
                                v-model="form.storeys_number" 
                                size="large" class="w-full" 
                                :placeholder="$t('sports.storeys')" 
                                :max="100"
                                :min="1" />
                        </a-form-model-item>
                    </div>
                    <a-form-model-item ref="has_ramp" :label="$t('sports.hasLabel')" prop="has_ramp">
                        <div class="md:flex flex-wrap has_wrap">
                            <a-checkbox v-model="form.has_ramp" >
                                {{ $t('sports.has_ramp') }}
                            </a-checkbox>
                            <a-checkbox v-model="form.has_access_to_all_floors" >
                                {{ $t('sports.has_access_to_all_floors') }}
                            </a-checkbox>
                            <a-checkbox v-model="form.has_equipped_bathrooms" >
                                {{ $t('sports.has_equipped_bathrooms') }}
                            </a-checkbox>
                            <a-checkbox v-model="form.has_access_elevator" >
                                {{ $t('sports.has_access_elevator') }}
                            </a-checkbox>
                        </div>
                    </a-form-model-item>
                </div>
                <div class="grid gap-4 grid-cols-1 lg:grid-cols-2 mt-1">
                    <a-button type="primary" size="large" block :loading="loading" @click="formSubmit()">
                        {{ isEdit ? $t('sports.save') : $t('sports.create_object') }}
                    </a-button>
                    <a-button type="ui" size="large" block :disabled="loading" @click="visible = false">
                        {{ $t('sports.cancel') }}
                    </a-button>
                </div>
            </a-form-model>
        </div>
    </DrawerTemplate>
</template>

<script>
import eventBus from '@/utils/eventBus'
import { mapState } from 'vuex'
export default {
    components: {
        DSelect: () => import('@apps/DrawerSelect/Select.vue'),
        AddressSelect: () => import('@apps/DrawerSelect/AddressSelect'),
        TreeSelect: () => import('@apps/DrawerSelect/TreeSelect.vue'),
        DrawerTemplate: () => import('@/components/DrawerTemplate.vue')
    },
    data() {
        return {
            isEdit: false,
            visible: false,
            loading: false,
            editInit: true,
            editData: null,
            facilityTree: [],
            treeDefaultExpandedKeys: [],
            facilityDefaultExpandedKeys: [],
            columns: [
                {
                    dataIndex: 'sport_categories',
                    title: this.$t('sports.category'),
                    key: 'sport_categories',
                    width: 300,
                    scopedSlots: { customRender: 'sport_categories' },
                },
                {
                    dataIndex: 'sport_types',
                    title: this.$t('sports.sport_type'),
                    key: 'sport_types',
                    width: 240,
                    scopedSlots: { customRender: 'sport_types' },
                },
                {
                    dataIndex: 'repub_comp',
                    title: this.$t('sports.message_compliance'),
                    key: 'repub_comp',
                    width: 200,
                    scopedSlots: { customRender: 'repub_comp' },
                },
                {
                    dataIndex: 'id',
                    title: '',
                    key: 'id',
                    width: 60,
                    scopedSlots: { customRender: 'id' },
                },
            ],
            form: {
                has_ramp: false,
                has_access_to_all_floors: false,
                has_access_elevator: false,
                has_equipped_bathrooms: false,
                name: "",
                selectedLocation: null,
                organization: null,
                facility_type: null,
                facility_type3: null,
                facility_type2: null,
                location: null,
                is_countryside: false,
                locationRegion: null,
                locationDistrict: null,
                location_akimat: null,
                location_settlement: null,
                location_point: null,
                owner_name: "",
                heating_type: null,
                staff_quantity: null,
                owner_bin: "",
                ownership_form: null,
                purpose: null,
                purpose3: null,
                purpose2: null,
                building_year: null,
                area: "",
                bandwidth: null,
                storeys_number: null,
                sport_types: [
                    {
                        sport_categories: null,
                        sport_categories2: null,
                        sport_categories3: null,
                        sport_types: null,
                        repub_comp: false,
                        id: Date.now()
                    }
                ]
            },
            rules: {
                name: [
                    { required: true, message: this.$t('sports.formError'), trigger: 'blur' }
                ],
                organization: [
                    { required: true, message: this.$t('sports.formError'), trigger: 'blur' }
                ],
                address: [
                    { required: true, message: this.$t('sports.formError'), trigger: 'blur' }
                ],
                building_year: [
                    { required: true, message: this.$t('sports.formError'), trigger: 'blur' }
                ],
                location_point: [
                    { required: true, message: this.$t('sports.formError'), trigger: 'blur' }
                ],
                selectedLocation: [
                    { required: true, message: this.$t('sports.formError'), trigger: 'blur' }
                ],
                facility_type: [
                    { required: true, message: this.$t('sports.formError'), trigger: 'blur' }
                ]
            }
        }
    },
    computed: {
        ...mapState({
            windowWidth: state => state.windowWidth
        }),
        isMobile() {
            return this.$store.state.isMobile
        },
        locationName() {
            if(this.form.selectedLocation) {
                return `${this.form.selectedLocation.code} - ${this.form.selectedLocation.full_name}`
            }
            return ""
        },
        drawerWidth() {
            if(this.windowWidth > 1300)
                return 1300
            else {
                return '100%'
            }
        }
    },
    methods: {
        sportsFacilityInitLoading(onLoadData) {
            if (this.isEdit) {
                function transformTreeToFlatArray(facilityType) {
                    const flatArray = []
                    const expandedKeys = []
                    let current = facilityType
                    let lastParentCode = null

                    while (current) {
                        const { code, name, parent } = current

                        if (parent)
                            lastParentCode = parent.code

                        const hasChildren = !!parent

                        const flatItem = {
                            id: code,
                            code: code,
                            value: code,
                            title: name,
                            isLeaf: !hasChildren,
                            pId: lastParentCode,
                            loaded: false
                        }

                        flatArray.push(flatItem)
                        onLoadData({
                            dataRef: flatItem
                        })

                        if (hasChildren)
                            expandedKeys.push(code)

                        if (!parent) {
                            this.facilityDefaultExpandedKeys.push(code)
                            break
                        }

                        current = parent
                    }

                    this.facilityDefaultExpandedKeys = this.facilityDefaultExpandedKeys.concat(expandedKeys)
                }

                const facilityType = this.editData.facility_type
                transformTreeToFlatArray.call(this, facilityType)
            }
        },
        sportsCategoryInitLoading(onLoadData) {
            if(this.isEdit) {
                function transformTreeToFlatArray(sportTypes) {
                    let flatArray = []
                    let expandedKeys = []

                    sportTypes.forEach(item => {
                        let current = item.sport_type.category
                        let lastParentCode = null

                        while (current) {
                            const { code, name, parent } = current

                            if (parent)
                                lastParentCode = parent.code

                            const hasChildren = !!parent

                            const flatItem = {
                                id: code,
                                code: code,
                                value: code,
                                title: name,
                                isLeaf: !hasChildren,
                                pId: lastParentCode,
                                loaded: false
                            }

                            flatArray.push(flatItem)
                            onLoadData({
                                dataRef: flatItem
                            })

                            if (hasChildren)
                                expandedKeys.push(code)

                            if (!parent) {
                                this.treeDefaultExpandedKeys.push(code)
                                break
                            }

                            current = parent
                        }
                    })

                    this.treeDefaultExpandedKeys = this.treeDefaultExpandedKeys.concat(expandedKeys)
                }
                const sportTypes = this.editData.sport_types
                transformTreeToFlatArray.call(this, sportTypes)
            }
        },
        decParser(input) {
            const sanitizedInput = input.replace(',', '.')
            const cleanedInput = sanitizedInput.replace(/[^\d.]/g, '')
            const parts = cleanedInput.split('.')
            if (parts.length > 2)
                return parts[0] + '.' + parts[1]
            if (parts[1]?.length > 1)
                parts[1] = parts[1].slice(0, 1)
            return parts.join('.')
        },
        decParser2(input) {
            return input.replace(/[^\d]/g, '')
        },
        getPContainer() {
            return this.$refs.sportDrawerBody
        },
        deleteSportType(index) {
            this.form.sport_types.splice(index, 1)
        },
        sportTypesParams(index) {
            if(this.form.sport_types[index].sport_categories3)
                return this.form.sport_types[index].sport_categories3
            if(this.form.sport_types[index].sport_categories2)
                return this.form.sport_types[index].sport_categories2
            if(this.form.sport_types[index].sport_categories)
                return this.form.sport_types[index].sport_categories
        },
        addSportType() {
            this.form.sport_types.push({
                sport_categories: null,
                sport_categories2: null,
                sport_categories3: null,
                sport_types: null,
                repub_comp: false,
                id: Date.now()
            })
        },
        editAddress() {
            this.$nextTick(() => {
                this.$refs.addressSelect.editAddress(this.form.location_point)
            })
        },
        changeGetObject(obj) {
            this.form.selectedLocation = obj
        },
        changeSelect(type) {
            switch (type) {
            case "region":
                this.form.locationDistrict = null
                this.form.location_akimat = null
                this.form.location_settlement = null
                this.form.location = null
                break;
            case "district":
                this.form.location_akimat = null
                this.form.location_settlement = null
                this.form.location = null
                break;
            case "akimat":
                this.form.location_settlement = null
                this.form.location = null
                break;
            case "settlement":
                this.form.location = null
                break;
            }
        },
        changePurpose(type) {
            switch (type) {
            case "purpose3":
                this.form.purpose2 = null
                this.form.purpose = null
                break;
            case "purpose2":
                this.form.purpose = null
                break;
            }
        },
        changeSportCategory(type, index) {
            this.form.sport_types[index].sport_types = null
        },
        afterVisibleChange(vis) {
            if(!vis) {
                this.editData = null
                this.isEdit = false
                this.treeDefaultExpandedKeys = []
                this.facilityDefaultExpandedKeys = []
                this.form = {
                    has_ramp: false,
                    has_access_to_all_floors: false,
                    has_access_elevator: false,
                    has_equipped_bathrooms: false,
                    name: "",
                    selectedLocation: null,
                    organization: null,
                    facility_type: null,
                    facility_type3: null,
                    facility_type2: null,
                    location: null,
                    heating_type: null,
                    staff_quantity: null,
                    is_countryside: false,
                    locationRegion: null,
                    locationDistrict: null,
                    location_akimat: null,
                    location_settlement: null,
                    location_point: null,
                    owner_name: "",
                    owner_bin: "",
                    ownership_form: null,
                    purpose: null,
                    purpose3: null,
                    purpose2: null,
                    building_year: null,
                    area: "",
                    bandwidth: null,
                    storeys_number: null,
                    sport_types: [
                        {
                            sport_categories: null,
                            sport_categories2: null,
                            sport_categories3: null,
                            sport_types: null,
                            repub_comp: false,
                            id: Date.now()
                        }
                    ]
                }
                this.editInit = true
            }
        },
        handleErrors(errors) {
            console.log(errors, 'errors')
            if (typeof errors === 'string') {
                // Если ошибка передается в виде строки
                this.$message.error(errors);
            } else if (errors.detail) {
                // Если есть ключ detail
                this.$message.error(errors.detail);
            } else if (typeof errors === 'object') {
                // Если это объект с несколькими ошибками
                Object.keys(errors).forEach(key => {
                    const errorMessages = errors[key];
                    if (Array.isArray(errorMessages)) {
                        // Если значение — массив ошибок
                        errorMessages.forEach(err => this.$message.error(err));
                    } else {
                        // Если значение — строка
                        this.$message.error(errorMessages);
                    }
                });
            } else {
                this.$message.error(this.$t('sports.unknown_error'));
            }
        },
        formSubmit() {
            this.$refs.formRef.validate(async valid => {
                if (valid) {
                    const queryData = {...this.form}
                    if(queryData.status)
                        delete queryData.status
                    if(queryData.author)
                        delete queryData.author
                    if(queryData.area)
                        queryData.area = String(queryData.area)
                    if(queryData.bandwidth)
                        queryData.bandwidth = String(queryData.bandwidth)
                    if(!queryData.location) {
                        if(queryData.locationRegion)
                            queryData.location = queryData.locationRegion
                        if(queryData.locationDistrict)
                            queryData.location = queryData.locationDistrict
                        if(queryData.location_akimat)
                            queryData.location = queryData.location_akimat
                        if(queryData.location_settlement)
                            queryData.location = queryData.location_settlement
                    }
                    if(!queryData.facility_type) {
                        if(queryData.facility_type3)
                            queryData.facility_type = queryData.facility_type3
                        if(queryData.facility_type2)
                            queryData.facility_type = queryData.facility_type2
                    }
                    if(!queryData.purpose) {
                        if(queryData.purpose3)
                            queryData.purpose = queryData.purpose3
                        if(queryData.purpose2)
                            queryData.purpose = queryData.purpose2
                    }
                    if(queryData.sport_types?.length) {
                        let edited = false
                        queryData.sport_types.forEach(item => {
                            if(item.sport_categories || item.sport_categories2 || item.sport_categories3 || item.sport_types) {
                                edited = true
                            }
                        })
                        queryData.sport_types = queryData.sport_types.map(item => {
                            const itemData = {
                                repub_comp: item.repub_comp
                            }
                            if(item.sport_categories)
                                itemData.sport_type = item.sport_categories
                            if(item.sport_categories2)
                                itemData.sport_type = item.sport_categories2
                            if(item.sport_categories3)
                                itemData.sport_type = item.sport_categories3
                            if(item.sport_types)
                                itemData.sport_type = item.sport_types
                            return itemData
                        })
                        if(!edited) {
                            queryData.sport_types = []
                        }
                    }
                    if(this.isEdit) {
                        try {
                            this.loading = true
                            const { data } = await this.$http.put(`/sports_facilities/${queryData.id}/`, queryData)
                            if(data) {
                                this.$message.success(this.$t('sports.object_pasport_updated'))
                                eventBus.$emit('update_sports_facilities_list')
                                this.$store.dispatch('facilities/getProject', { id: queryData.id, reload: true })
                                this.visible = false
                            }
                        } catch(error) {
                            this.handleErrors(error)
                        } finally {
                            this.loading = false
                        }
                    } else {
                        try {
                            this.loading = true
                            const { data } = await this.$http.post('/sports_facilities/', queryData)
                            if(data) {
                                this.$message.success(this.$t('sports.object_pasport_created'))
                                eventBus.$emit('update_sports_facilities_list')
                                this.visible = false
                            }
                        } catch(error) {
                            this.handleErrors(error)
                        } finally {
                            this.loading = false
                        }
                    }
                } else {
                    console.log('error submit!!');
                    this.$message.warning(this.$t('sports.field_empty'))
                    return false;
                }
            })
        },
        async getEditData(record) {
            try {
                const editData = {...record}
                this.editData = {...record}
                if(editData.organization)
                    editData.organization = editData.organization.id
                if(editData.heating_type)
                    editData.heating_type = editData.heating_type.code
                if(editData.ownership_form)
                    editData.ownership_form = editData.ownership_form.code

                if(editData.facility_type?.code) {
                    editData.facility_type = editData.facility_type.code
                }
                if(editData.purpose?.code) {
                    if(editData.purpose.parent) {
                        if(editData.purpose?.parent?.parent) {
                            editData.purpose3 = editData.purpose.parent.parent.code
                            editData.purpose2 = editData.purpose.parent.code
                            editData.purpose = editData.purpose.code
                        } else {
                            editData.purpose3 = editData.purpose.parent.code
                            editData.purpose2 = editData.purpose.code
                            editData.purpose = null
                        }
                    } else {
                        editData.purpose3 = editData.purpose.code
                        editData.purpose2 = null
                        editData.purpose = null
                    }
                }
                if(editData.sport_types?.length) {
                    editData.sport_types = editData.sport_types.map(item => {
                        const itemData = {
                            id: item.id,
                            repub_comp: item.repub_comp
                        }
                        const sportType = item.sport_type
                        if(sportType.category) {
                            itemData.sport_categories = sportType.category.code
                            itemData.sport_types = sportType.code
                        } else {
                            itemData.sport_categories = null
                            itemData.sport_categories2 = null
                            itemData.sport_categories3 = null
                            itemData.sport_types = sportType.code
                        }
                        return itemData
                    })
                } else {
                    editData.sport_types = [
                        {
                            sport_categories: null,
                            sport_categories2: null,
                            sport_categories3: null,
                            sport_types: null,
                            repub_comp: false,
                            id: Date.now()
                        }
                    ]
                }
                if(editData.location) {
                    editData.selectedLocation = editData.location
                    editData.location = editData.location.id
                }
                if(editData.author)
                    delete editData.author
                if(editData.status)
                    delete editData.status
                const { data } = await this.$http.get('/accounting_catalogs/locations/structure/', {
                    params: {
                        location: record.location.id
                    }
                })
                if(data) {
                    if(data.region) {
                        if(editData.location === data.region.id)
                            editData.location = null
                        editData.locationRegion = data.region.id
                    } else {
                        editData.locationRegion = null
                    }
                    if(data.district)  {
                        if(editData.location === data.district.id)
                            editData.location = null
                        editData.locationDistrict = data.district.id
                    } else {
                        editData.locationDistrict = null
                    }
                    if(data.akimat) {
                        if(editData.location === data.akimat.id)
                            editData.location = null
                        editData.location_akimat = data.akimat.id
                    } else {
                        editData.location_akimat = null
                    }
                    if(data.settlement) {
                        if(editData.location === data.settlement.id)
                            editData.location = null
                        editData.location_settlement = data.settlement.id
                    } else {
                        editData.location_settlement = null
                    }
                }
                this.form = editData
                //this.getCategories()
                this.visible = true
            } catch(e) {
                console.log(e)
            } finally {
                this.editInit = true
            }
        }
    },
    mounted(){
        eventBus.$on('add_sports_facilities', async () => {
            this.visible = true
            //this.getCategories()
        })
        eventBus.$on('edit_sports_facilities', data => {
            this.editInit = false
            this.isEdit = true
            this.getEditData(data)
        })
    },
    beforeDestroy() {
        eventBus.$off('add_sports_facilities')
        eventBus.$off('edit_sports_facilities')
    }
}
</script>

<style lang="scss" scoped>
.has_wrap{
    &::v-deep{
        .ant-checkbox-wrapper{
            display: block;
            margin-left: 0px;
            &:not(:last-child){
                @media (min-width: 768px) {
                    margin-right: 15px;
                }
            }
        }
    }
}
.form_block{
        padding: 15px 15px 5px 15px;
        border: 1px solid var(--border2);
        border-radius: var(--borderRadius);
        margin-bottom: 20px;
        @media (min-width: 768px) {
            padding: 30px 30px 10px 30px;
        }
        &__header{
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 20px;
            h3{
                font-size: 20px;
                color: #000000;
                font-weight: 400;
                margin: 0px;
            }
        }
    }
.sports_add_drawer{
    &::v-deep{
        .ant-drawer-body{
            padding: 20px 10px;
            @media (min-width: 768px) {
                padding: 24px;
            }
        }
    }
}
.address_item{
    margin-bottom: 15px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    border: 1px solid #e1e7ec;
    padding: 15px;
    border-radius: 8px;
}
.table_btn{
    @media (min-width: 768px) {
        border-radius: 0 0 8px 8px;
    }
}
.c_table{
    &::v-deep{
        .ant-table-thead{
            tr{
                th{
                    background: #fff;
                    font-weight: 400;
                    vertical-align: bottom;
                }
            }
        }
    }
}
.sport_type_card{
    border: 1px solid #EBEBEB;
    border-radius: 8px;
    padding: 15px 10px;
    &:not(:last-child){
        margin-bottom: 10px;
    }
}
.sport_form{
    &::v-deep{
        .ant-col ant-form-item-label{
            @media (max-width: 767px) {
                line-height: 18px;
            }
        }
    }
}
</style>