<template>
    <div>
        <a-table
            :columns="columns"
            :pagination="false"
            :loading="loading"
            :scroll="scroll"
            :locale="{
                emptyText: $t('meeting.noData')
            }"
            :size="tableSize"
            :row-key="record => record.id"
            :data-source="list"
            @change="handleTableChange">
            <template
                slot="name"
                slot-scope="text, record">
                <div
                    class="flex items-center cursor-pointer"
                    @click="open(record)">
                    <span class="blue_color meeting_name">
                        {{ record.name }}
                    </span>
                </div>
            </template>
            <template
                slot="date_begin"
                slot-scope="text">
                <template v-if="text">
                    {{ $t('meeting.formated_start_date', { 
                        date: $moment(text).format('DD.MM.YYYY'), 
                        time: $moment(text).format('HH:mm') 
                    })}}
                </template>
                <template v-else>
                    <a-tag>
                        {{ $t('meeting.no_data') }}
                    </a-tag>
                </template>
            </template>
            <template
                slot="duration"
                slot-scope="text">
                <div
                    v-if="text"
                    class="flex items-center">
                    <i class="fi fi-rr-clock-three mr-1 text-xs"></i>
                    {{ dFormat(text) }}
                </div>
            </template>
            <template
                slot="status"
                slot-scope="text">
                <Status :status="text" />
            </template>
            <template
                slot="author"
                slot-scope="text, record">
                <Members :item="record" />
            </template>
            <template
                slot="id"
                slot-scope="text, record">
                <CardActions
                    :item="record"
                    :page_name="page_name" />
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
import { mapState, mapGetters } from 'vuex'
import eventBusGlobal from '@/utils/eventBus'
import eventBus from '../utils/eventBus'
import Status from './Status.vue'
import Members from './Members.vue'
import CardActions from './CardActions.vue'
import { durationFormat } from '../utils/index.js'
export default {
    name: 'MeetingTypeTable',
    components: {
        Status,
        Members,
        CardActions
    },
    props: {
        pageModel: {
            type: String,
            default: 'meetings.PlannedMeetingModel'
        },
        page_name: {
            type: String,
            default: 'page_list_meetings.PlannedMeetingModel'
        }
    },
    computed: {
        ...mapState({
            windowHeight: state => state.windowHeight,
            windowWidth: state => state.windowWidth,
            config: state => state.config.config
        }),
        ...mapGetters({
            getPageSize: 'meeting/getTablePageSize'
        }),
        tableScroll() {
            if(this.windowWidth > 1750)
                return false
            else
                return 1200
        },
        scroll() {
            return {
                x: this.tableScroll,
                y: 'calc(100vh - 264px)'
            }
        },
        tableSize() {
            return this.config?.theme?.tableSize ? this.config.theme.tableSize : 'small'
        },
        columns() {
            return [
                {
                    dataIndex: 'name',
                    title: this.$t('meeting.name'),
                    sorter: true,
                    key: 'name',
                    width: 360,
                    scopedSlots: { customRender: 'name' }
                },
                {
                    dataIndex: 'date_begin',
                    title: this.$t('meeting.startDate'),
                    sorter: true,
                    key: 'date_begin',
                    scopedSlots: { customRender: 'date_begin' }
                },
                {
                    dataIndex: 'duration',
                    title: this.$t('meeting.duration'),
                    sorter: true,
                    key: 'duration',
                    scopedSlots: { customRender: 'duration' }
                },
                {
                    dataIndex: 'author',
                    title: this.$t('meeting.author2'),
                    key: 'author',
                    width: 120,
                    scopedSlots: { customRender: 'author' }
                },
                {
                    dataIndex: 'status',
                    title: this.$t('meeting.status'),
                    key: 'status',
                    scopedSlots: { customRender: 'status' }
                },
                {
                    dataIndex: 'id',
                    title: '',
                    key: 'id',
                    scopedSlots: { customRender: 'id' }
                }
            ]
        }
    },
    data() {
        return {
            loading: false,
            list: [],
            page: 1,
            pageSize: 15,
            sort: '',
            count: 0,
            pageSizeOptions: ['15', '30', '50']
        }
    },
    watch: {
        pageSize(newSize) {
            this.changePageSize(newSize)
        }
    },
    created() {
        const localPageSize = this.getPageSize(this.page_name)
        if(localPageSize)
            this.pageSize = localPageSize 

        this.getList()
    },
    methods: {
        dFormat(duration) {
            return durationFormat(duration)
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
        handleTableChange(pagination, filters, sorter) {
            if(sorter.order)
                this.sort = `${sorter.order === "ascend" ? '' : '-'}${sorter.field}`
            else
                this.sort = null
            this.getList()
        },
        async getList() {
            try {
                this.loading = true

                let params = {
                    page: this.page,
                    page_size: this.pageSize,
                    page_name: this.page_name,
                    model: this.pageModel
                }

                if(this.sort) {
                    params.ordering = this.sort
                }

                const { data } = await this.$http.get('/meetings/', {
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
        open(record) {
            let query = Object.assign({}, this.$route.query)
            if(!query?.meeting) {
                query.meeting = record.id
                this.$router.push({query})
            }
        },
        endConference(id) {
            const index = this.list.findIndex(f => f.id === id)
            if(index !== -1)
                this.list[index].status = 'ended'
        },
        restartConference(id) {
            const index = this.list.findIndex(f => f.id === id)
            if(index !== -1)
                this.list[index].status = 'new'
        },
        changePageSize(size) {
            this.$store.commit('meeting/SET_TABLE_PAGE_SIZE', {
                tableName: this.page_name,
                pageSize: size
            })
        },
    },
    mounted() {
        eventBusGlobal.$on(`update_filter_${this.pageModel}`, () => {
            this.page = 1
            this.getList()
        })
        // eventBus.$on(`reload_list_${this.page_name}`, (page_default = false) => {
        //     if(page_default)
        //         this.page = 1

        //     this.getList()
        // })
        eventBus.$on('END_CONFERENCE', id => {
            this.endConference(id)
        })
        eventBus.$on('RESTART_CONFERENCE', id => {
            this.restartConference(id)
        })
    },
    beforeDestroy() {
        eventBusGlobal.$off(`update_filter_${this.pageModel}`)
        // eventBus.$off(`reload_list_${this.page_name}`)
        eventBus.$off('END_CONFERENCE')
        eventBus.$off('RESTART_CONFERENCE')
    }
}
</script>

<style lang="scss" scoped>
.meeting_name{
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
    text-overflow: ellipsis;
    transition: color 0.3s;
    word-break: break-word;
}
</style>