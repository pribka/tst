<template>
    <div class="page_block">
        <div class="md:flex items-center justify-between mb-4">
            <div class="p_title">
                {{ $t('sports.objectsInfo') }}
            </div>
            <a-button 
                v-if="actions && actions.buildings_add && actions.buildings_add.availability"
                type="primary"
                flaticon
                :block="isMobile"
                icon="fi-rr-plus"
                class="mt-2 md:mt-0"
                @click="addHandler()">
                {{ $t('sports.addObject') }}
            </a-button>
        </div>
        <a-spin 
            v-if="isMobile" 
            :spinning="loading" 
            size="small">
            <ObjectCard 
                v-for="item in listData" 
                :key="item.id" 
                :editHandler="editHandler"
                :deleteHandler="deleteHandler"
                :item="item" />
        </a-spin>
        <a-table 
            v-else
            :columns="columns" 
            :loading="loading"
            :data-source="listData"
            class="table_wrap"
            bordered
            size="small"
            :pagination="false"
            tableLayout="fixed"
            :row-key="record => record.id"
            :scroll="{ x: 900 }"
            :expand-icon="customExpandIcon">
            <div slot="name" slot-scope="text" class="table_name_row" :title="text">
                {{ text }}
            </div>
            <div slot="building_type" slot-scope="text, record" class="table_name_row">
                {{ record.purpose_type && record.purpose_type.building_type ? record.purpose_type.building_type.name : '-' }}
            </div>
            <template slot="actions" slot-scope="text, record">
                <div class="flex items-center">
                    <a-button 
                        v-if="actions && actions.buildings_edit && actions.buildings_edit.availability"
                        type="ui" 
                        flaticon
                        ghost
                        class="mr-1"
                        shape="circle"
                        icon="fi-rr-edit"
                        @click="editHandler(record)" />
                    <a-button 
                        v-if="actions && actions.buildings_delete && actions.buildings_delete.availability"
                        type="ui" 
                        flaticon
                        ghost
                        shape="circle"
                        icon="fi-rr-trash"
                        @click="deleteHandler(record)" />
                </div>
            </template>
            <div 
                slot="expandedRowRender" 
                slot-scope="record"
                style="margin: 0">
                <div class="expand_list">
                    <div v-for="item in getListData(record)" :key="item.id" class="expand_list__item">
                        <div class="flex items-center justify-between item_row">
                            <div class="item_name">{{ item.name }}</div>
                            <div class="item_value">{{ item.value }}</div>
                        </div>
                    </div>
                </div>
            </div>
        </a-table>
        <ObjectInformationDrawer />
    </div>
</template>

<script>
import eventBus from '@/utils/eventBus'
import { mapState } from 'vuex'
export default {
    components: {
        ObjectInformationDrawer: () => import('../components/ObjectInformationDrawer/index.vue'),
        ObjectCard: () => import('../components/ObjectCard.vue')
    },
    computed: {
        ...mapState({
            actions: state => state.facilities.projectActions
        }),
        isMobile() {
            return this.$store.state.isMobile
        }
    },
    data() {
        return {
            loading: false,
            columns: [
                { title: this.$t('sports.objectName'), dataIndex: 'name', key: 'name', scopedSlots: { customRender: 'name' }, width: 250 },
                { title: this.$t('sports.purpose'), dataIndex: 'purpose_type.purpose.name', key: 'purpose_type.purpose.name', width: 250 },
                { title: this.$t('sports.roomType'), dataIndex: 'purpose_type.building_type', key: 'purpose_type.building_type', scopedSlots: { customRender: 'building_type' } },
                { title: "", dataIndex: 'id', key: 'id', scopedSlots: { customRender: 'actions' }, width: 100 }
            ],
            listData: []
        }
    },
    created() {
        this.getList()
    },
    methods: {
        deleteHandler(record) {
            this.$confirm({
                title: this.$t('sports.objectDelete'),
                content: '',
                okText: this.$t('sports.delete'),
                okType: 'danger',
                zIndex: 2000,
                closable: true,
                maskClosable: true,
                cancelText: this.$t('sports.close'),
                onOk: () => {
                    return new Promise((resolve, reject) => {
                        this.$http.post(`/sports_facilities/${this.$route.params.id}/building/delete/`, {
                            id: record.id
                        })
                            .then(() => {
                                this.$message.success(this.$t('sports.objectDeleteSuccess'))
                                this.getList()
                                resolve()
                            })
                            .catch(e => {
                                console.log(e)
                                this.$message.error({ content: e[0] ? e[0] : this.$t('sports.deletedError'), key: loadingKey })
                                reject(e)
                            })
                    })
                }
            })
        },
        getListData(record) {
            const values = []
            for(const key in record) {
                if(key.includes("x_")) {
                    values.push({
                        ...record[key],
                        name: record[key].name || "-",
                        value: this.widgetValueData(record[key])
                    })
                }
            }
            return values
        },
        widgetValueData(record) {
            if(record.widgetType === 'Checkbox')
                return record.value ? this.$t('sports.yes') : this.$t('sports.no')
            if(!record.value)
                return '-'
            if(record.widgetType === 'ForeignKey') {
                if(Array.isArray(record.value)) {
                    if(!record.value?.length)
                        return '-'
                    return record.value.map(item => item.name).join(', ')
                } else {
                    return record.value.name
                }
            }
            return record.value
        },
        async getList() {
            try {
                this.loading = true
                const { data } = await this.$http.get(`/sports_facilities/${this.$route.params.id}/get_buildings/`)
                if(data) {
                    this.listData = data
                }
            } catch(e) {
                console.log(e)
            } finally {
                this.loading = false
            }
        },
        addHandler() {
            eventBus.$emit('openObjectInformationDrawer')
        },
        editHandler(record) {
            eventBus.$emit('editObjectInformationDrawer', record)
        },
        customExpandIcon({ expanded, onExpand, record }) {
            return expanded ? (
                <a-button 
                    type="primary" 
                    size="small" 
                    shape="circle"
                    icon="fi-rr-angle-small-up" 
                    flaticon
                    onClick={e => onExpand(record, e)} />
            ) : (
                <a-button 
                    type="primary" 
                    size="small" 
                    shape="circle"
                    icon="fi-rr-angle-small-down" 
                    flaticon
                    onClick={e => onExpand(record, e)} />
            )
        }
    },
    mounted() {
        eventBus.$on('updateObjectInformation', () => {
            this.getList()
        })
    },
    beforeDestroy() {
        eventBus.$off('updateObjectInformation')
    }
}
</script>

<style lang="scss" scoped>
.table_name_row{
    display: -webkit-box;
    -webkit-line-clamp: 3;
    -webkit-box-orient: vertical;
    overflow: hidden;
    text-overflow: ellipsis;
    word-break: break-word;
}
.expand_list{
    max-width: 100%;
    @media (min-width: 992px) {
        max-width: 80%;
    }
    @media (min-width: 1400px) {
        max-width: 70%;
    }
    @media (min-width: 1600px) {
        max-width: 50%;
    }
    &__item{
        display: flex;
        color: #000000;
        line-height: 18px;
        width: 100%;
        .item_name{
            min-width: 300px;
            max-width: 300px;
            opacity: 0.6;
            @media (min-width: 1200px) {
                min-width: 400px;
                max-width: 400px;
            }
        }
        .item_value{
            padding-left: 20px;
            text-align: right;
        }
        .item_row{
            padding: 10px 0;
            width: 100%;
        }
        &:not(:last-child){
            .item_row{
                border-bottom: 1px solid #c0c2c4;
            }
        }
    }
}
.p_title{
    font-size: 16px;
    font-weight: 400;
    line-height: 16px;
    color: #262626;
}
.table_wrap{
    &::v-deep{
        .ant-table-thead{
            background: #f8f8f8;
            .ant-table-column-title{
                color: #000000;
                opacity: 0.6;
                font-weight: 400;
            }
            th{
                background: #f8f8f8;
                &:not(:last-child){
                    border-right: 0px;
                }
            }
        }
        .ant-table-tbody{
            .ant-table-row{
                td{
                    color: #000;
                    &:not(:last-child){
                        border-right: 0px;
                    }
                }
            }
        }
        .ant-table-expanded-row{
            td{
                &:not(:last-child){
                    border-right: 0px;
                }
            }
        }
        tr.ant-table-expanded-row{
            background: #f0f2f6;
        }
    }
}
</style>