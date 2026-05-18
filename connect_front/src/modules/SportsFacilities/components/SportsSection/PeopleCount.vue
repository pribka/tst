<template>
    <a-drawer
        :title="$t('sports.sectionCount2')"
        placement="right"
        :visible="visible"
        :width="drawerWidth"
        :after-visible-change="afterVisibleChange"
        @close="visible = false">
        <a-spin 
            :spinning="infoLoading" 
            size="small">
            <a-form-model
                ref="formRef"
                :model="{
                    ...form,
                    sport_groups: listData
                }"
                class="objects_info_form">
                <a-table
                    :columns="columns"
                    class="table_wrap"
                    :pagination="false"
                    :scroll="{ x: 1650 }"
                    :row-key="record => record.sport_group_type.id"
                    tableLayout="fixed"
                    :rowClassName="rowClassName"
                    :data-source="listData"
                    bordered>
                    <template slot="members_variable_quantity" slot-scope="text, record, index">
                        <div v-if="record.footer" class="text-center">
                            {{ members_variable_quantity }}
                        </div>
                        <template v-else>
                            <a-form-model-item 
                                v-if="checkEdit"
                                class="form_item"
                                :prop="'sport_groups.' + index + '.members_variable_quantity'">
                                <a-input-number 
                                    v-model="listData[index].members_variable_quantity" 
                                    :min="0" 
                                    size="large"
                                    :placeholder="$t('sports.pressNumber')"
                                    :disabled="!checkEdit"
                                    class="w-full"
                                    @keypress="handleKeyPress" />
                            </a-form-model-item>
                            <div v-else class="text-center">
                                {{ listData[index].members_variable_quantity }}
                            </div>
                        </template>
                    </template>
                    <template slot="members_constant_quantity" slot-scope="text, record, index">
                        <div v-if="record.footer" class="text-center">
                            {{ members_constant_quantity }}
                        </div>
                        <template v-else>
                            <a-form-model-item 
                                v-if="checkEdit"
                                class="form_item"
                                :prop="'sport_groups.' + index + '.members_constant_quantity'">
                                <a-input-number 
                                    v-model="listData[index].members_constant_quantity" 
                                    :min="0" 
                                    size="large"
                                    :placeholder="$t('sports.pressNumber')"
                                    :disabled="!checkEdit"
                                    class="w-full"
                                    @keypress="handleKeyPress" />
                            </a-form-model-item>
                            <div v-else class="text-center">
                                {{ listData[index].members_constant_quantity }}
                            </div>
                        </template>
                    </template>
                    <template slot="members_constant_female" slot-scope="text, record, index">
                        <div v-if="record.footer" class="text-center">
                            {{ members_constant_female }}
                        </div>
                        <template v-else>
                            <a-form-model-item 
                                v-if="checkEdit"
                                class="form_item"
                                :prop="'sport_groups.' + index + '.members_constant_female'">
                                <a-input-number 
                                    v-model="listData[index].members_constant_female" 
                                    :min="0" 
                                    size="large"
                                    :placeholder="$t('sports.pressNumber')"
                                    :disabled="!checkEdit"
                                    class="w-full"
                                    @keypress="handleKeyPress" />
                            </a-form-model-item>
                            <div v-else class="text-center">
                                {{ listData[index].members_constant_female }}
                            </div>
                        </template>
                    </template>
                    <template slot="members_constant_before_17" slot-scope="text, record, index">
                        <div v-if="record.footer" class="text-center">
                            {{ members_constant_before_17 }}
                        </div>
                        <template v-else>
                            <a-form-model-item 
                                v-if="checkEdit"
                                class="form_item"
                                :prop="'sport_groups.' + index + '.members_constant_before_17'">
                                <a-input-number 
                                    v-model="listData[index].members_constant_before_17" 
                                    :min="0" 
                                    size="large"
                                    :placeholder="$t('sports.pressNumber')"
                                    :disabled="!checkEdit"
                                    class="w-full"
                                    @keypress="handleKeyPress" />
                            </a-form-model-item>
                            <div v-else class="text-center">
                                {{ listData[index].members_constant_before_17 }}
                            </div>
                        </template>
                    </template>
                    <template slot="members_constant_before_18_19" slot-scope="text, record, index">
                        <div v-if="record.footer" class="text-center">
                            {{ members_constant_before_18_19 }}
                        </div>
                        <template v-else>
                            <a-form-model-item 
                                v-if="checkEdit"
                                class="form_item"
                                :prop="'sport_groups.' + index + '.members_constant_before_18_19'">
                                <a-input-number 
                                    v-model="listData[index].members_constant_before_18_19" 
                                    :min="0" 
                                    size="large"
                                    :placeholder="$t('sports.pressNumber')"
                                    :disabled="!checkEdit"
                                    class="w-full"
                                    @keypress="handleKeyPress" />
                            </a-form-model-item>
                            <div v-else class="text-center">
                                {{ listData[index].members_constant_before_18_19 }}
                            </div>
                        </template>
                    </template>
                    <template slot="members_first_category" slot-scope="text, record, index">
                        <div v-if="record.footer" class="text-center">
                            {{ members_first_category }}
                        </div>
                        <template v-else>
                            <a-form-model-item 
                                v-if="checkEdit"
                                class="form_item"
                                :prop="'sport_groups.' + index + '.members_first_category'">
                                <a-input-number 
                                    v-model="listData[index].members_first_category" 
                                    :min="0" 
                                    size="large"
                                    :placeholder="$t('sports.pressNumber')"
                                    :disabled="!checkEdit"
                                    class="w-full"
                                    @keypress="handleKeyPress" />
                            </a-form-model-item>
                            <div v-else class="text-center">
                                {{ listData[index].members_first_category }}
                            </div>
                        </template>
                    </template>
                    <template slot="members_kms" slot-scope="text, record, index">
                        <div v-if="record.footer" class="text-center">
                            {{ members_kms }}
                        </div>
                        <template v-else>
                            <a-form-model-item 
                                v-if="checkEdit"
                                class="form_item"
                                :prop="'sport_groups.' + index + '.members_kms'">
                                <a-input-number 
                                    v-model="listData[index].members_kms" 
                                    :min="0" 
                                    size="large"
                                    :placeholder="$t('sports.pressNumber')"
                                    :disabled="!checkEdit"
                                    class="w-full"
                                    @keypress="handleKeyPress" />
                            </a-form-model-item>
                            <div v-else class="text-center">
                                {{ listData[index].members_kms }}
                            </div>
                        </template>
                    </template>
                    <template slot="members_ms" slot-scope="text, record, index">
                        <div v-if="record.footer" class="text-center">
                            {{ members_ms }}
                        </div>
                        <template v-else>
                            <a-form-model-item 
                                v-if="checkEdit"
                                class="form_item"
                                :prop="'sport_groups.' + index + '.members_ms'">
                                <a-input-number 
                                    v-model="listData[index].members_ms" 
                                    :min="0" 
                                    size="large"
                                    :placeholder="$t('sports.pressNumber')"
                                    :disabled="!checkEdit"
                                    class="w-full"
                                    @keypress="handleKeyPress" />
                            </a-form-model-item>
                            <div v-else class="text-center">
                                {{ listData[index].members_ms }}
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
            if(this.windowWidth > 1700)
                return 1700
            else {
                return '100%'
            }
        },
        checkEdit() {
            return this.actions?.sections_edit?.availability
        },
        members_variable_quantity() {
            let allCount = 0
            this.listData.forEach(item => {
                const count = item.members_variable_quantity || 0
                allCount = allCount + count
            })
            return allCount
        },
        members_constant_quantity() {
            let allCount = 0
            this.listData.forEach(item => {
                const count = item.members_constant_quantity || 0
                allCount = allCount + count
            })
            return allCount
        },
        members_constant_female() {
            let allCount = 0
            this.listData.forEach(item => {
                const count = item.members_constant_female || 0
                allCount = allCount + count
            })
            return allCount
        },
        members_constant_before_17() {
            let allCount = 0
            this.listData.forEach(item => {
                const count = item.members_constant_before_17 || 0
                allCount = allCount + count
            })
            return allCount
        },
        members_constant_before_18_19() {
            let allCount = 0
            this.listData.forEach(item => {
                const count = item.members_constant_before_18_19 || 0
                allCount = allCount + count
            })
            return allCount
        },
        members_first_category() {
            let allCount = 0
            this.listData.forEach(item => {
                const count = item.members_first_category || 0
                allCount = allCount + count
            })
            return allCount
        },
        members_kms() {
            let allCount = 0
            this.listData.forEach(item => {
                const count = item.members_kms || 0
                allCount = allCount + count
            })
            return allCount
        },
        members_ms() {
            let allCount = 0
            this.listData.forEach(item => {
                const count = item.members_ms || 0
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
                    dataIndex: 'sport_group_type.name',
                    className: 'vertical_bt text-left',
                    width: 300,
                    key: 'sport_group_type.name'
                },
                {
                    title: this.$t('sports.peopleCol1'),
                    dataIndex: 'variable_quantity',
                    key: 'variable_quantity',
                    className: 'text_center',
                    width: 200,
                    children: [
                        {
                            title: '',
                            dataIndex: 'members_variable_quantity',
                            key: 'members_variable_quantity',
                            scopedSlots: { customRender: 'members_variable_quantity' },
                            width: 200,
                        }
                    ]
                },
                {
                    title: this.$t('sports.peopleCol2'),
                    dataIndex: 'constant_quantity',
                    key: 'constant_quantity',
                    className: 'text_center',
                    width: 370,
                    children: [
                        {
                            title: this.$t('sports.peopleCol3'),
                            dataIndex: 'members_constant_quantity',
                            className: 'text_center',
                            scopedSlots: { customRender: 'members_constant_quantity' },
                            key: 'members_constant_quantity'
                        },
                        {
                            title: this.$t('sports.peopleCol4'),
                            dataIndex: 'members_constant_female',
                            className: 'text_center',
                            key: 'members_constant_female',
                            scopedSlots: { customRender: 'members_constant_female' }
                        },
                        {
                            title: this.$t('sports.peopleCol5'),
                            dataIndex: 'members_constant_before_17',
                            className: 'text_center',
                            key: 'members_constant_before_17',
                            scopedSlots: { customRender: 'members_constant_before_17' }
                        },
                        {
                            title: this.$t('sports.peopleCol6'),
                            dataIndex: 'members_constant_before_18_19',
                            className: 'text_center',
                            key: 'members_constant_before_18_19',
                            scopedSlots: { customRender: 'members_constant_before_18_19' }
                        }
                    ]
                },
                {
                    title: this.$t('sports.peopleCol7'),
                    dataIndex: 'first_category',
                    key: 'first_category',
                    className: 'text_center',
                    width: 250,
                    children: [
                        {
                            title: '',
                            dataIndex: 'members_first_category',
                            key: 'members_first_category',
                            scopedSlots: { customRender: 'members_first_category' },
                            width: 250
                        }
                    ]
                },
                {
                    title: this.$t('sports.peopleCol8'),
                    dataIndex: 'kms',
                    className: 'text_center',
                    key: 'kms',
                    width: 250,
                    children: [
                        {
                            title: '',
                            dataIndex: 'members_kms',
                            key: 'members_kms',
                            scopedSlots: { customRender: 'members_kms' },
                            width: 250
                        }
                    ]
                },
                {
                    title: this.$t('sports.peopleCol9'),
                    dataIndex: 'ms',
                    key: 'ms',
                    className: 'text_center',
                    width: 200,
                    children: [
                        {
                            title: '',
                            dataIndex: 'members_ms',
                            key: 'members_ms',
                            scopedSlots: { customRender: 'members_ms' },
                            width: 200
                        }
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
                            sport_groups: []
                        }
                        this.listData.forEach(item => {
                            if(!item.footer) {
                                const itemData = {
                                    sport_group_type: item.sport_group_type.id,
                                    members_variable_quantity: item.members_variable_quantity || 0,
                                    members_constant_quantity: item.members_constant_quantity || 0,
                                    members_constant_female: item.members_constant_female || 0,
                                    members_constant_before_17: item.members_constant_before_17 || 0,
                                    members_constant_before_18_19: item.members_constant_before_18_19 || 0,
                                    members_first_category: item.members_first_category || 0,
                                    members_kms: item.members_kms || 0,
                                    members_ms: item.members_ms || 0
                                }
                                queryData.sport_groups.push(itemData)
                            }
                        })
                        const { data } = await this.$http.post(`/sports_facilities/${this.$route.params.id}/section/groups/update/`, queryData)
                        if(data) {
                            this.visible = false
                            this.$message.success(this.$t('sports.peopleEditSuccess'))
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
        async getInfo() {
            try {
                this.infoLoading = true
                const { data } = await this.$http.get(`/sports_facilities/${this.$route.params.id}/section/groups/`, {
                    params: {
                        id: this.form.id
                    }
                })
                if(data) {
                    this.listData = data.map(item => {
                        return {
                            ...item,
                            members_variable_quantity: item.members_variable_quantity || null,
                            members_constant_quantity: item.members_constant_quantity || null,
                            members_constant_female: item.members_constant_female || null,
                            members_constant_before_17: item.members_constant_before_17 || null,
                            members_constant_before_18_19: item.members_constant_before_18_19 || null,
                            members_first_category: item.members_first_category || null,
                            members_kms: item.members_kms || null,
                            members_ms: item.members_ms || null
                        }
                    })
                    if(this.listData.length) {
                        this.listData.push({
                            members_variable_quantity: 0,
                            members_constant_quantity: 0,
                            members_constant_female: 0,
                            members_constant_before_17: 0,
                            members_constant_before_18_19: 0,
                            members_first_category: 0,
                            members_kms: 0,
                            members_ms: 0,
                            footer: true,
                            sport_group_type: {
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
        afterVisibleChange(vis) {
            if(!vis) {
                this.form = {}
                this.listData = []
            }
        }
    },
    mounted() {
        eventBus.$on('openSectionPeopleCountDrawer', ({id}) => {
            this.form = {
                id
            }
            this.visible = true
            this.getInfo()
        })
    },
    beforeDestroy() {
        eventBus.$off('openSectionPeopleCountDrawer')
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
.form_item{
    margin-bottom: 0px;
}
</style>