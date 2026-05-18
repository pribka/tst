<template>
    <a-drawer
        :title="$t('sports.sectionCount3')"
        placement="right"
        :visible="visible"
        :width="drawerWidth"
        :after-visible-change="afterVisibleChange"
        @close="visible = false">
        <a-spin 
            :spinning="formLoading" 
            size="small">
            <a-form-model
                ref="formRef"
                :model="{
                    ...form,
                    sport_coach_type: listData
                }"
                class="objects_info_form">
                <a-table
                    :columns="columns"
                    class="table_wrap"
                    :pagination="false"
                    :scroll="{ x: 1150 }"
                    :row-key="record => record.sport_coach_type.id"
                    tableLayout="fixed"
                    :rowClassName="rowClassName"
                    :data-source="listData"
                    bordered>
                    <template slot="coaches_quantity" slot-scope="text, record, index">
                        <div v-if="record.footer" class="text-center">
                            {{ coaches_quantity }}
                        </div>
                        <template v-else>
                            <a-form-model-item 
                                v-if="checkEdit"
                                class="form_item"
                                :prop="'sport_coach_type.' + index + '.coaches_quantity'">
                                <a-input-number 
                                    v-model="listData[index].coaches_quantity" 
                                    :min="0" 
                                    size="large"
                                    :placeholder="$t('sports.pressNumber')"
                                    :disabled="!checkEdit"
                                    class="w-full"
                                    @keypress="handleKeyPress" />
                            </a-form-model-item>
                            <div v-else class="text-center">
                                {{ listData[index].coaches_quantity }}
                            </div>
                        </template>
                    </template>
                    <template slot="coaches_female" slot-scope="text, record, index">
                        <div v-if="record.footer" class="text-center">
                            {{ coaches_female }}
                        </div>
                        <template v-else>
                            <a-form-model-item 
                                v-if="checkEdit"
                                class="form_item"
                                :prop="'sport_coach_type.' + index + '.coaches_female'">
                                <a-input-number 
                                    v-model="listData[index].coaches_female" 
                                    :min="0" 
                                    size="large"
                                    :placeholder="$t('sports.pressNumber')"
                                    :disabled="!checkEdit"
                                    class="w-full"
                                    @keypress="handleKeyPress" />
                            </a-form-model-item>
                            <div v-else class="text-center">
                                {{ listData[index].coaches_female }}
                            </div>
                        </template>
                    </template>
                    <template slot="coaches_higher_education" slot-scope="text, record, index">
                        <div v-if="record.footer" class="text-center">
                            {{ coaches_higher_education }}
                        </div>
                        <template v-else>
                            <a-form-model-item 
                                v-if="checkEdit"
                                class="form_item"
                                :prop="'sport_coach_type.' + index + '.coaches_higher_education'">
                                <a-input-number 
                                    v-model="listData[index].coaches_higher_education" 
                                    :min="0" 
                                    size="large"
                                    :placeholder="$t('sports.pressNumber')"
                                    :disabled="!checkEdit"
                                    class="w-full"
                                    @keypress="handleKeyPress" />
                            </a-form-model-item>
                            <div v-else class="text-center">
                                {{ listData[index].coaches_higher_education }}
                            </div>
                        </template>
                    </template>
                    <template slot="coaches_middle_education" slot-scope="text, record, index">
                        <div v-if="record.footer" class="text-center">
                            {{ coaches_middle_education }}
                        </div>
                        <template v-else>
                            <a-form-model-item 
                                v-if="checkEdit"
                                class="form_item"
                                :prop="'sport_coach_type.' + index + '.coaches_middle_education'">
                                <a-input-number 
                                    v-model="listData[index].coaches_middle_education" 
                                    :min="0" 
                                    size="large"
                                    :placeholder="$t('sports.pressNumber')"
                                    :disabled="!checkEdit"
                                    class="w-full"
                                    @keypress="handleKeyPress" />
                            </a-form-model-item>
                            <div v-else class="text-center">
                                {{ listData[index].coaches_middle_education }}
                            </div>
                        </template>
                    </template>
                </a-table>
                <a-button 
                    v-if="checkEdit" 
                    type="primary" 
                    size="large"
                    :block="isMobile"
                    :loading="formLoading"
                    class="px-16 mt-5"
                    @click="formSubmit()">
                    {{ $t('sports.save') }}
                </a-button>
            </a-form-model>
        </a-spin>
    </a-drawer>
</template>

<script>
import eventBus from '@/utils/eventBus'
import { mapState } from 'vuex'
import { handleKeyPress } from '../../utils.js'
export default {
    computed: {
        ...mapState({
            windowWidth: state => state.windowWidth,
            actions: state => state.facilities.projectActions
        }),
        isMobile() {
            return this.$store.state.isMobile
        },
        drawerWidth() {
            if(this.windowWidth > 1200)
                return 1200
            else {
                return '100%'
            }
        },
        checkEdit() {
            return this.actions?.sections_edit?.availability
        },
        coaches_quantity() {
            let allCount = 0
            this.listData.forEach(item => {
                const count = item.coaches_quantity || 0
                allCount = allCount + count
            })
            return allCount
        },
        coaches_female() {
            let allCount = 0
            this.listData.forEach(item => {
                const count = item.coaches_female || 0
                allCount = allCount + count
            })
            return allCount
        },
        coaches_higher_education() {
            let allCount = 0
            this.listData.forEach(item => {
                const count = item.coaches_higher_education || 0
                allCount = allCount + count
            })
            return allCount
        },
        coaches_middle_education() {
            let allCount = 0
            this.listData.forEach(item => {
                const count = item.coaches_middle_education || 0
                allCount = allCount + count
            })
            return allCount
        }
    },
    data() {
        return {
            visible: false,
            infoLoading: false,
            formLoading: false,
            form: {},
            listData: [],
            columns: [
                {
                    title: this.$t('sports.name'),
                    dataIndex: 'sport_coach_type.name',
                    className: 'vertical_bt',
                    width: 350,
                    key: 'sport_coach_type.name'
                },
                {
                    title: this.$t('sports.peopleCol3'),
                    dataIndex: 'coaches_quantity',
                    className: 'vertical_bt text_center',
                    width: 150,
                    key: 'coaches_quantity',
                    scopedSlots: { customRender: 'coaches_quantity' }
                },
                {
                    title: this.$t('sports.female'),
                    dataIndex: 'coaches_female',
                    className: 'vertical_bt text_center',
                    width: 150,
                    key: 'coaches_female',
                    scopedSlots: { customRender: 'coaches_female' }
                },
                {
                    title: this.$t('sports.coachesCol1'),
                    dataIndex: 'education',
                    className: 'text_center',
                    width: 450,
                    key: 'education',
                    children: [
                        {
                            title: this.$t('sports.higherEducation'),
                            dataIndex: 'coaches_higher_education',
                            width: 200,
                            className: 'text_center',
                            key: 'coaches_higher_education',
                            scopedSlots: { customRender: 'coaches_higher_education' }
                        },
                        {
                            title: this.$t('sports.middleEducation'),
                            dataIndex: 'coaches_middle_education',
                            width: 250,
                            className: 'text_center',
                            key: 'coaches_middle_education',
                            scopedSlots: { customRender: 'coaches_middle_education' }
                        },
                    ]
                }
            ]
        }
    },
    methods: {
        handleKeyPress,
        formSubmit() {
            this.$refs.formRef.validate(async valid => {
                if (valid) {
                    try {
                        this.formLoading = true
                        const queryData = {
                            id: this.form.id,
                            sport_coaches: []
                        }
                        this.listData.forEach(item => {
                            if(!item.footer) {
                                const itemData = {
                                    sport_coach_type: item.sport_coach_type.id,
                                    coaches_quantity: item.coaches_quantity || 0,
                                    coaches_female: item.coaches_female || 0,
                                    coaches_higher_education: item.coaches_higher_education || 0,
                                    coaches_middle_education: item.coaches_middle_education || 0
                                }
                                queryData.sport_coaches.push(itemData)
                            }
                        })
                        const { data } = await this.$http.post(`/sports_facilities/${this.$route.params.id}/section/coaches/update/`, queryData)
                        if(data) {
                            this.visible = false
                            this.$message.success(this.$t('sports.coachesEditSuccess'))
                            eventBus.$emit('sectionListUpdate')
                        }
                    } catch(e) {
                        console.log(e)
                        this.$message.error(this.$t('sports.error'))
                    } finally {
                        this.formLoading = false
                    }
                } else  
                    return false
            })
        },
        rowClassName(record, index) {
            if(record.footer)
                return 'footer_row'
            return ''
        },
        afterVisibleChange(vis) {
            if(!vis) {
                this.listData = []
                this.form = {}
            }
        },
        async getInfo() {
            try {
                this.infoLoading = true
                const { data } = await this.$http.get(`/sports_facilities/${this.$route.params.id}/section/coaches/`, {
                    params: {
                        id: this.form.id
                    }
                })
                if(data) {
                    this.listData = data.map(item => {
                        return {
                            ...item,
                            coaches_female: item.coaches_female || null,
                            coaches_higher_education: item.coaches_higher_education || null,
                            coaches_middle_education: item.coaches_middle_education || null,
                            coaches_quantity: item.coaches_quantity || null
                        }
                    })
                    if(this.listData.length) {
                        this.listData.push({
                            coaches_female: 0,
                            coaches_higher_education: 0,
                            coaches_middle_education: 0,
                            coaches_quantity: 0,
                            footer: true,
                            sport_coach_type: {
                                id: Date.now(),
                                name: this.$t('sports.totalCol')
                            }
                        })
                    }
                }
            } catch(e) {
                console.log(e)
            } finally {
                this.infoLoading = false
            }
        },
    },
    mounted() {
        eventBus.$on('openSectionTrainersCountDrawer', ({id}) => {
            this.form = {
                id
            }
            this.visible = true
            this.getInfo()
        })
    },
    beforeDestroy() {
        eventBus.$off('openSectionTrainersCountDrawer')
    }
}
</script>

<style lang="scss" scoped>
.table_wrap{
    &::v-deep{
        .ant-table-thead{
            background: #fff;
            .ant-table-column-title{
                color: #000000;
                font-weight: 400;
            }
            th{
                background: #fff;
                vertical-align: top;
                &.vertical_bt{
                    vertical-align: bottom;
                }
                &.text_center{
                    text-align: center;
                    .ant-table-column-title{
                        max-width: 270px;
                        display: block;
                    }
                }
            }
        }
        .ant-table-tbody{
            .ant-table-row{
                td{
                    color: #000;
                }
            }
        }
        tr.ant-table-expanded-row{
            background: #f0f2f6;
        }
        .footer_row{
            td{
                background: #f8f8f8;
            }
        }
    }
}
</style>