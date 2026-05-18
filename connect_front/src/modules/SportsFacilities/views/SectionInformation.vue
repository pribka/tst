<template>
    <div ref="tableWrapper">
        <a-button 
            v-if="isMobile && actions && actions.sections_add && actions.sections_add.availability"
            type="primary" 
            size="large" 
            class="mb-3"
            block
            @click="showSectionAdd()">
            {{ $t('sports.addOnly') }}
        </a-button>
        <a-spin 
            v-if="isMobile"
            :spinning="loading" 
            size="small">
            <SectionCard 
                v-for="item in listData" 
                :key="item.id" 
                :deleteHandler="deleteHandler"
                :addHandler="addHandler"
                :item="item" />
        </a-spin>
        <a-table 
            v-else
            :columns="columns" 
            :data-source="listData" 
            :loading="loading"
            class="table_wrap"
            bordered
            :pagination="false"
            tableLayout="fixed"
            :row-key="record => record.id"
            :scroll="{ x: 1200 }">
            <template slot="category" slot-scope="text, record">
                {{ record.sport_type.category && record.sport_type.category.name ? record.sport_type.category.name : '-' }}
            </template>
            <template slot="sport_type" slot-scope="text, record">
                {{ record.sport_type.name }}
            </template>
            <template slot="sections_quantity" slot-scope="text, record">
                <div v-if="record.sections_quantity" class="flex items-center justify-between">
                    <span>{{ record.sections_quantity }}</span>
                    <a-button 
                        type="link" 
                        class="more_btn lowercase"
                        size="small"
                        @click="addHandler(record, 'openSectionInformationDrawer')">
                        {{ $t('sports.more') }}
                    </a-button>
                </div>
                <a-button 
                    v-else 
                    type="link" 
                    size="small" 
                    class="more_btn"
                    block
                    @click="addHandler(record, 'openSectionInformationDrawer')">
                    {{ $t('sports.addOnly') }}
                </a-button>
            </template>
            <template slot="members_quantity" slot-scope="text, record">
                <div v-if="record.members_quantity" class="flex items-center justify-between">
                    <span>{{ record.members_quantity }}</span>
                    <a-button 
                        type="link" 
                        class="more_btn lowercase"
                        size="small"
                        @click="addHandler(record, 'openSectionPeopleCountDrawer')">
                        {{ $t('sports.more') }}
                    </a-button>
                </div>
                <a-button 
                    v-else 
                    type="link" 
                    size="small" 
                    class="more_btn"
                    block
                    @click="addHandler(record, 'openSectionPeopleCountDrawer')">
                    {{ $t('sports.addOnly') }}
                </a-button>
            </template>
            <template slot="coaches_quantity" slot-scope="text, record">
                <div v-if="record.coaches_quantity" class="flex items-center justify-between">
                    <span>{{ record.coaches_quantity }}</span>
                    <a-button 
                        type="link" 
                        class="more_btn lowercase"
                        size="small"
                        @click="addHandler(record, 'openSectionTrainersCountDrawer')">
                        {{ $t('sports.more') }}
                    </a-button>
                </div>
                <a-button 
                    v-else 
                    type="link" 
                    size="small" 
                    class="more_btn"
                    block
                    @click="addHandler(record, 'openSectionTrainersCountDrawer')">
                    {{ $t('sports.addOnly') }}
                </a-button>
            </template>
            <template slot="id" slot-scope="text, record">
                <a-button 
                    v-if="actions && actions.sections_delete && actions.sections_delete.availability"
                    type="ui" 
                    flaticon
                    ghost
                    shape="circle"
                    icon="fi-rr-trash"
                    @click="deleteHandler(record)" />
            </template>
        </a-table>
        <a-button 
            v-if="!isMobile && actions && actions.sections_add && actions.sections_add.availability"
            type="primary" 
            size="large" 
            class="add_btn"
            block
            @click="showSectionAdd()">
            {{ $t('sports.addOnly') }}
        </a-button>
        <EditDrawer />
        <PeopleCount />
        <TrainersCount />
        <AddSection 
            v-if="actions && actions.sections_add && actions.sections_add.availability" 
            :getSections="getSections" />
    </div>
</template>

<script>
import { mapState } from 'vuex'
import eventBus from '@/utils/eventBus'
export default {
    components: {
        EditDrawer: () => import('../components/SportsSection/EditDrawer.vue'),
        PeopleCount: () => import('../components/SportsSection/PeopleCount.vue'),
        TrainersCount: () => import('../components/SportsSection/TrainersCount.vue'),
        AddSection: () => import('../components/SportsSection/AddSection.vue'),
        SectionCard: () => import('../components/SectionCard.vue')
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
                {
                    title: this.$t('sports.category'),
                    dataIndex: 'category',
                    scopedSlots: { customRender: 'category' }
                },
                {
                    title: this.$t('sports.sport_type'),
                    dataIndex: 'sport_type',
                    scopedSlots: { customRender: 'sport_type' }
                },
                {
                    title: this.$t('sports.sectionCount'),
                    className: 'text_center',
                    dataIndex: 'sections_quantity',
                    scopedSlots: { customRender: 'sections_quantity' }
                },
                {
                    title: this.$t('sports.sectionCount2'),
                    className: 'text_center',
                    dataIndex: 'members_quantity',
                    scopedSlots: { customRender: 'members_quantity' }
                },
                {
                    title: this.$t('sports.sectionCount3'),
                    className: 'text_center',
                    dataIndex: 'coaches_quantity',
                    scopedSlots: { customRender: 'coaches_quantity' }
                },
                {
                    title: "",
                    className: 'text_center',
                    dataIndex: 'id',
                    width: 60,
                    scopedSlots: { customRender: 'id' }
                }
            ],
            listData: []
        }
    },
    created() {
        this.getSections()
    },
    methods: {
        deleteHandler(record) {
            this.$confirm({
                title: this.$t('sports.sectionDelete'),
                content: '',
                okText: this.$t('sports.delete'),
                okType: 'danger',
                zIndex: 2000,
                closable: true,
                maskClosable: true,
                cancelText: this.$t('sports.close'),
                onOk: () => {
                    return new Promise((resolve, reject) => {
                        this.$http.post(`/sports_facilities/${this.$route.params.id}/section/delete/`, {
                            id: record.id
                        })
                            .then(() => {
                                this.$message.success(this.$t('sports.sectionDeleteSuccess'))
                                this.getSections()
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
        showSectionAdd() {
            eventBus.$emit('addSection')
        },
        async getSections() {
            try {
                this.loading = true
                const { data } = await this.$http.get(`/sports_facilities/${this.$route.params.id}/get_sections/`)
                this.listData = data
            } catch(e) {
                console.log(e)
            } finally {
                this.loading = false
            }
        },
        addHandler(record, type) {
            eventBus.$emit(type, {
                id: record.id
            })
        }
    },
    mounted() {
        eventBus.$on('sectionListUpdate', () => {
            this.getSections()
        })
    },
    beforeDestroy() {
        eventBus.$off('sectionListUpdate')
    }
}
</script>

<style lang="scss" scoped>
.more_btn{
    padding-left: 0;
    padding-right: 0;
    &::v-deep{
        span{
            text-decoration: underline;
        }
    }
}
.add_btn{
    border-top-left-radius: 0;
    border-top-right-radius: 0;
}
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
    }
}
</style>