<template>
    <div>
        <a-table
            :columns="columns"
            :pagination="false"
            :loading="loading"
            class="org_ref_table"
            :locale="{
                emptyText: this.$t('team.no_related_organizations')
            }"
            :size="tableSize"
            :row-key="record => record.id"
            :data-source="list">
            <template
                slot="contractor"
                slot-scope="text, record">
                <TableName :record="record" :org="org" />
            </template>
            <template
                slot="relation_type"
                slot-scope="text, record">
                <RelationType :record="record" :org="org" />
            </template>
            <template
                slot="id">
            </template>
        </a-table>
        <div class="flex justify-end pt-1">
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
        </div>
    </div>
</template>

<script>
import { mapState } from 'vuex'
import eventBus from '@/utils/eventBus'
import TableName from './TableName.vue'
import RelationType from './RelationType.vue'
export default {
    props: {
        org: {
            type: [Object],
            required: true
        }
    },
    components: {
        TableName,
        RelationType
    },
    computed: {
        ...mapState({
            windowHeight: state => state.windowHeight,
            windowWidth: state => state.windowWidth,
            config: state => state.config.config,
            isMobile: state => state.isMobile,
            user: state => state.user.user
        }),
        tableSize() {
            return this.config?.theme?.tableSize ? this.config.theme.tableSize : 'small'
        }
    },
    created() {
        this.getList()
    },
    data() {
        return {
            page: 1,
            pageSize: 15,
            pageSizeOptions: ['15', '30', '50'],
            sort: '',
            count: 0,
            columns: [
                {
                    dataIndex: 'contractor',
                    title: this.$t('team.name'),
                    key: 'contractor',
                    scopedSlots: { customRender: 'contractor' }
                },
                {
                    dataIndex: 'relation_type',
                    title: this.$t('team.connection_type'),
                    key: 'relation_type',
                    scopedSlots: { customRender: 'relation_type' }
                }
            ],
            list: [],
            loading: false
        }
    },
    methods: {
        isAuthor(id) {
            return this.org?.director?.id === id
        },
        async getList() {
            try {
                this.loading = true

                let params = {
                    page: this.page,
                    page_size: this.pageSize
                }

                const { data } = await this.$http.get(`/users/my_organizations/${this.org.id}/relations/`, {
                    params
                })
                if(data?.results?.length) {
                    this.list = data.results
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
        sizeSwicth(current, pageSize) {
            this.page = 1
            this.pageSize = Number(pageSize)
            this.getList()
        },
        changePage(page) {
            this.page = page
            this.getList()
        }
    }
}
</script>

<style lang="scss" scoped>
.org_ref_table{
    &::v-deep{
        .ant-table-thead{
            background: #f4f7f7;
        }
    }
}
</style>