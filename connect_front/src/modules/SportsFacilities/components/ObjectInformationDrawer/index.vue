<template>
    <a-drawer
        :title="$t('sports.objectsInfo')"
        placement="right"
        :visible="visible"
        :width="drawerWidth"
        :after-visible-change="afterVisibleChange"
        @close="visible = false">
        <a-spin :spinning="formLoading" size="small">
            <a-form-model
                ref="formRef"
                :model="form"
                class="objects_info_form"
                :rules="rules">
                <div class="grid gap-4 grid-cols-1 md:grid-cols-2">
                    <a-form-model-item ref="purpose" :label="$t('sports.purposeObject')" prop="purpose">
                        <DSelect
                            v-model="form.purpose"
                            size="large"
                            class="w-full"
                            oneSelect
                            valueKey="code"
                            :params="{
                                model: 'sports_facilities_info.SportBuildingPurposeModel'
                            }"
                            :placeholder="$t('sports.selectFromList')"
                            :default-active-first-option="false"
                            @change="purposeChange" />
                    </a-form-model-item>
                    <a-form-model-item ref="building_type" :label="$t('sports.roomType')" prop="building_type">
                        <DSelect
                            v-model="form.building_type"
                            size="large"
                            :key="form.purpose"
                            :disabled="form.purpose ? false : true"
                            class="w-full"
                            oneSelect
                            valueKey="code"
                            :params="{
                                model: 'sports_facilities_info.SportBuildingTypeModel',
                                purpose: form.purpose
                            }"
                            :placeholder="$t('sports.selectFromList')"
                            :default-active-first-option="false"
                            @change="buildingTypeChange" />
                    </a-form-model-item>
                </div>
                <a-form-model-item ref="name" :label="$t('sports.nameObject')" prop="name">
                    <a-input 
                        v-model="form.name" 
                        size="large" 
                        :placeholder="$t('sports.nameObject')" /> 
                </a-form-model-item>
                <div class="form_label">
                    {{ $t('sports.objectCharacteristics') }}  
                </div>
                <a-spin :spinning="pvhLoading" size="small">
                    <pvh 
                        :pvhWidgets="pvhWidgets" 
                        :setSelectsList="setSelectsList"
                        :form="form" />
                    <a-alert 
                        v-if="!(form.purpose && form.building_type) && !pvhLoading" 
                        :message="$t('sports.objectInfoAlert')" 
                        class="mb-4"
                        banner
                        type="info" />
                </a-spin>
                <div class="grid gap-4 grid-cols-1 md:grid-cols-2">
                    <a-button 
                        type="primary" 
                        size="large" 
                        :disabled="formCheck"
                        :loading="loading"
                        block
                        @click="formSubmit()">
                        {{ edit ? $t('sports.saveChanges') : $t('sports.addObject') }}
                    </a-button>
                    <a-button 
                        type="ui" 
                        size="large" 
                        block
                        @click="visible = false">
                        {{ $t('sports.cancel') }}
                    </a-button>
                </div>
            </a-form-model>
        </a-spin>
    </a-drawer>
</template>

<script>
import eventBus from '@/utils/eventBus'
import { mapState } from 'vuex'
import DSelect from '@apps/DrawerSelect/Select.vue'
import pvh from './pvh/index.vue'
export default {
    components: {
        DSelect,
        pvh
    },
    computed: {
        ...mapState({
            windowWidth: state => state.windowWidth
        }),
        isMobile() {
            return this.$store.state.isMobile
        },
        drawerWidth() {
            if(this.windowWidth > 944)
                return 944
            else {
                return '100%'
            }
        },
        formCheck() {
            return !(this.form.purpose && this.form.building_type && this.form.name)
        }
    },
    data() {
        return {
            visible: false,
            loading: false,
            pvhWidgets: [],
            pvhLoading: false,
            formLoading: false,
            edit: false,
            selectLists: {},
            form: {
                purpose: null,
                building_type: null,
                name: ''
            },
            rules: {
                name: [
                    { required: true, message: this.$t('sports.formError'), trigger: 'blur' }
                ],
                purpose: [
                    { required: true, message: this.$t('sports.formError'), trigger: 'blur' }
                ],
                building_type: [
                    { required: true, message: this.$t('sports.formError'), trigger: 'blur' }
                ]
            }
        }
    },
    methods: {
        setSelectsList(key, list) {
            this.$set(this.selectLists, key, list)
        },
        buildingTypeChange() {
            this.pvhWidgets = []
            this.selectLists = {}
            this.defaultForm()
            this.getFormInfo()
        },
        async getFormInfo(initForm = true) {
            try {
                this.pvhLoading = true
                const queryData = {
                    model:"sports_facilities_info.TPSportFacilityBuildingModel",
                    condition:{
                        "purpose.code": this.form.purpose
                    }
                }
                if(this.form.building_type)
                    queryData.condition["building_type.code"] = this.form.building_type
                const { data } = await this.$http.post('/pvh/properties/', queryData)
                if(data) {
                    this.pvhWidgets = data
                    if(initForm) {
                        data.forEach(item => {
                            if(item.widget.type === 'Checkbox')
                                this.$set(this.form, `x_${item.property.code}`, item.widget.defaultValue || false)
                            else
                                this.$set(this.form, `x_${item.property.code}`, item.widget.defaultValue || null)
                        })
                    }
                }
            } catch(e) {
                console.log(e)
            } finally {
                this.pvhLoading = false
            }
        },
        purposeChange() {
            this.form.building_type = null
            this.pvhWidgets = []
            this.selectLists = {}
            this.defaultForm()
        },
        defaultForm() {
            this.form = {
                purpose: this.form.purpose,
                building_type: this.form.building_type,
                name: this.form.name
            }
        },
        formSubmit() {
            this.$refs.formRef.validate(async valid => {
                if (valid) {
                    try {
                        this.loading = true
                        const queryData = {...this.form}
                        if(Object.keys(this.selectLists)?.length) {
                            for(const key in this.selectLists) {
                                queryData[key] = this.selectLists[key]
                            }
                        }
                        if(queryData.purpose_type)
                            delete queryData.purpose_type
                        if(this.edit) {
                            const { data } = await this.$http.put(`/sports_facilities/${this.$route.params.id}/building/update/`, queryData)
                            if(data) {
                                this.visible = false
                                this.$message.success(this.$t('sports.objectInfoUpdated'))
                                eventBus.$emit('updateObjectInformation')
                            }
                        } else {
                            const { data } = await this.$http.post(`/sports_facilities/${this.$route.params.id}/building/create/`, queryData)
                            if(data) {
                                this.visible = false
                                this.$message.success(this.$t('sports.objectInfoCreated'))
                                eventBus.$emit('updateObjectInformation')
                            }
                        }
                    } catch(e) {
                        console.log(e)
                        this.$message.error(this.$t('sports.error'))
                    } finally {
                        this.loading = false
                    }
                } else {
                    this.$message.warning(this.$t('sports.field_empty'))
                    return false;
                }
            })
        },
        afterVisibleChange(vis) {
            if(!vis) {
                this.edit = false
                this.pvhWidgets = []
                this.selectLists = {}
                this.form = {
                    purpose: null,
                    building_type: null,
                    name: '',
                }
            }
        },
        async getObject(record) {
            try {
                this.formLoading = true
                const { data } = await this.$http.get(`/sports_facilities/${this.$route.params.id}/building/detail/`, {
                    params: {
                        id: record.id
                    }
                })
                if(data) {
                    const editData = data
                    if(editData.purpose_type?.purpose?.code)
                        editData.purpose = editData.purpose_type.purpose.code
                    if(editData.purpose_type?.building_type?.code)
                        editData.building_type = editData.purpose_type.building_type.code
                    for(const key in editData) {
                        if(key.includes('x_')) {
                            if(editData[key].widgetType === 'ForeignKey') {
                                this.$set(this.selectLists, key, editData[key].value)
                                if(Array.isArray(editData[key].value)) {
                                    if(editData[key].value.length)
                                        editData[key] = editData[key].value.map(item => item.id)
                                    else
                                        editData[key] = []
                                } else {
                                    if(editData[key].value) {
                                        editData[key] = editData[key].value.id
                                    } else
                                        editData[key] = null
                                }
                            } else
                                editData[key] = editData[key].value
                        }
                    }
                    this.form = editData
                    await this.getFormInfo(false)
                }
            } catch(e) {
                console.log(e)
            } finally {
                this.formLoading = false
            }
        }
    },
    mounted() {
        eventBus.$on('openObjectInformationDrawer', () => {
            this.visible = true
        })
        eventBus.$on('editObjectInformationDrawer', record => {
            this.edit = true
            this.visible = true
            this.getObject(record)
        })
    },
    beforeDestroy() {
        eventBus.$off('openObjectInformationDrawer')
        eventBus.$off('editObjectInformationDrawer')
    }
}
</script>

<style lang="scss" scoped>
.form_label{
    margin-bottom: 20px;
    font-size: 16px;
    line-height: 20px;
    color: #000;
}
</style>