<template>
    <div>
        <a-table
            :columns="columns"
            :pagination="false"
            :loading="loading"
            ref="orgTable"
            class="org_table"
            :scroll="scroll"
            :expandedRowKeys="  expandedRowKeys"
            :locale="{
                emptyText: $t('team.no_data')
            }"
            :size="tableSize"
            :expandIconAsCell="false"
            :expandIconColumnIndex="-1"
            :row-key="(record, index) => `${record.id}-${index}`"
            :data-source="list">
            <!-- <template slot="expandedRowRender" slot-scope="text">
                <OrgInfo 
                    v-if="text.showChildren" 
                    :minusUserCount="minusUserCount" 
                    :updateTableRowsHeight="updateTableRowsHeight"
                    :org="text" />
            </template> -->
            <template
                slot="name"
                slot-scope="text, record, expanded, indent">
                <TableName 
                    :record="record" 
                    :expanded="expanded"
                    :toggleChildren="toggleChildren"
                    :indent="indent" />
            </template>
            <template
                slot="members_count"
                slot-scope="text">
                {{ text }}
            </template>
            <template
                slot="director"
                slot-scope="text">
                <Profiler
                    :user="text" 
                    :avatarSize="28"/>
            </template>
            <template
                slot="inn"
                slot-scope="text">
                {{ text }}
            </template>
            <template
                slot="email"
                slot-scope="text">
                {{ text }}
            </template>
            <template
                slot="phone"
                slot-scope="text">
                {{ text }}
            </template>
            <template
                slot="id"
                slot-scope="text, record, expanded">
                <Actions 
                    :id="record.id" 
                    :expanded="expanded"
                    :toggleChildren="toggleChildren"
                    :record="record" />
            </template>
        </a-table>
        <!-- <div class="flex justify-end pt-1">
            <a-pagination
                :current="page"
                size="small"
                :show-size-changer="pageSizeOptions.length > 1"
                :page-size.sync="pageSize"
                :defaultPageSize="Number(pageSize)"
                :pageSizeOptions="pageSizeOptions"
                :total="count"
                show-less-items
                @showSizeChange="sizeSwicth"
                @change="changePage">
                <template slot="buildOptionText" slot-scope="props">
                    {{ props.value }}
                </template>
            </a-pagination>
        </div> -->
    </div>
</template>

<script>
import { mapState } from 'vuex'
import eventBus from '@/utils/eventBus'
import Actions from './Actions'
import OrgInfo from './OrgInfo'
import TableName from './TableName.vue'
export default {
    components: {
        Actions,
        // OrgInfo,
        TableName
    },
    computed: {
        ...mapState({
            windowHeight: state => state.windowHeight,
            windowWidth: state => state.windowWidth,
            config: state => state.config.config
        }),
        tableScroll() {
            if(this.windowWidth > 1750)
                return false
            else
                return '100%'
        },
        scroll() {
            return {
                x: this.tableScroll,
                y: 'calc(100vh - 264px)'
            }
        },
        tableSize() {
            return this.config?.theme?.tableSize ? this.config.theme.tableSize : 'small'
        }
    },
    data() {
        return {
            loading: false,
            expandedRowKeys: [],
            list: [],
            page: 1,
            pageSize: 15,
            sort: '',
            count: 0,
            observer: null,
            tableOScroll: null,
            pageSizeOptions: ['15', '30', '50'],
            page_name: 'organization_list',
            columns: [
                {
                    dataIndex: 'name',
                    title: this.$t('team.name'),
                    // sorter: true,
                    key: 'name',
                    width: 420,
                    scopedSlots: { customRender: 'name' }
                },
                {
                    dataIndex: 'members_count',
                    title: this.$t('team.participants_count'),
                    key: 'members_count',
                    scopedSlots: { customRender: 'members_count' }
                },
                {
                    dataIndex: 'director',
                    title: this.$t('team.administrator'),
                    key: 'director',
                    scopedSlots: {customRender: 'director'}
                },
                {
                    dataIndex: 'id',
                    title: '',
                    key: 'id',
                    width: 70,
                    scopedSlots: { customRender: 'id' }
                }
            ]
        }
    },
    created() {
        this.getList()

        eventBus.$on('orgTableReload', () => {
            this.getList()
        })
        eventBus.$on('updateTableOrg', data => {
            this.updateItem(data)
        })
    },
    methods: {
        updateTableRowsHeight() {
            this.$refs['orgTable'].$children[0].$refs.vcTable.$children[0].handleWindowResize()
        },
        initTableObserver() {
            this.tableOScroll = this.$refs['orgTable'].$el.querySelector('.ant-table-scroll .ant-table-tbody')

            this.observer = new ResizeObserver(() => {
                this.$nextTick(() => {
                    this.updateTableRowsHeight()
                })
            })
            this.observer.observe(this.tableOScroll)
        },
        minusUserCount(record) {
            const index = this.list.findIndex(f => f.id === record.id)
            if(index !== -1) {
                const newCount = this.list[index].members_count - 1
                this.$set(this.list[index], 'members_count', newCount)
            }
        },
        sizeSwicth(current, pageSize) {
            this.page = 1
            this.pageSize = Number(pageSize)
            this.getList()
        },
        changePage(page) {
            this.page = page
            this.getList()
        },
        toggleChildren({ id, value, expanded }) {
            const index = this.list.findIndex(f => f.id === id)
            if(index !== -1) {
                this.$set(this.list[index], 'showChildren', value)
            }
            if(value) {
                this.expandedRowKeys.push(`${id}-${expanded}`)
            } else {
                const eIndex = this.expandedRowKeys.findIndex(f => f === `${id}-${expanded}`)
                if(eIndex !== -1) {
                    this.expandedRowKeys.splice(eIndex, 1)
                }
            }
        },
        updateItemByKey({ value, key, id }) {
            const index = this.list.findIndex(f => f.id === id)
            if(index !== -1) {
                this.$set(this.list[index], key, value)
            }
        },
        updateItem(data) {
            const index = this.list.findIndex(f => f.id === data.id)
            if(index !== -1) {
                this.$set(this.list, index, data)
            }
        },
        async getList() {
            try {
                this.loading = true

                let params = {
                    page: this.page,
                    page_size: this.pageSize,
                    page_name: this.page_name
                }

                const { data } = await this.$http.get('/users/my_organizations/', {
                    params
                })
                if(data?.results?.length) {
                    let testData = data.results.map(item => {
                        return {
                            ...item,
                            showChildren: false,
                            children: []
                        }
                    })
                    this.list = testData
                    this.count = data.count
                } else {
                    this.list = []
                    this.count = 0
                }
            } catch(e) {
                console.log(e)
            } finally {
                this.loading = false
            }
        },
    },
    mounted() {
        this.initTableObserver()
    },
    beforeCreate() {
        eventBus.$off('orgTableReload')
        eventBus.$off('updateTableOrg')
    }
}
</script>

<style lang="scss" scoped>
.org_table{
    &::v-deep{
        .ant-table-small > .ant-table-content > .ant-table-body{
            margin: 0px;
        }
    }
}
</style>