<template>
    <div>
        <div class="table_wrapper">
            <a-table 
                :columns="columns" 
                :pagination="false"
                :loading="loading"
                :scroll="scroll"
                :locale="{
                    emptyText: $t('wgr.no_data')
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
                        @click="openHandler(record.id)">
                        <div class="pr-2">
                            <a-avatar 
                                :size="26" 
                                icon="team" 
                                :src="workgroupLogoPath(record)" />
                        </div>
                        <span class="blue_color group_name">
                            {{ record.name }}
                        </span>
                    </div>
                </template>
                <template 
                    slot="dead_line" 
                    slot-scope="text">
                    <template v-if="text">
                        {{$moment(text).format('DD.MM.YYYY в HH:mm')}}
                    </template>
                    <template v-else>
                        <a-tag>
                            {{ $t('wgr.no_date') }}
                        </a-tag>
                    </template>
                </template>
                <template 
                    slot="date_start_plan" 
                    slot-scope="text">
                    <template v-if="text">
                        {{$moment(text).format('DD.MM.YYYY в HH:mm')}}
                    </template>
                    <template v-else>
                        <a-tag>
                            {{ $t('wgr.no_date') }}
                        </a-tag>
                    </template>
                </template>
                <template 
                    slot="public_or_private" 
                    slot-scope="text">
                    {{ text ? 'Закрытый' : 'Открытый' }}
                </template>
                <template 
                    slot="description" 
                    slot-scope="text">
                    <div class="group_desc">
                        {{ text }}
                    </div>
                </template>
                <template 
                    slot="founder" 
                    slot-scope="text, record">
                    <Members :item="record" />
                </template>
                <template 
                    slot="tasks"
                    slot-scope="text, record">
                    <Effects :item="record" />
                </template>
                <template 
                    slot="tasks_stat"
                    slot-scope="text, record">
                    <a-tag color="blue">
                        {{ record.tasks }}
                    </a-tag>
                    <a-tag color="#87d068">
                        {{ record.complete_tasks }}
                    </a-tag>
                </template>
                <template 
                    slot="finished"
                    slot-scope="text, record">
                    <a-tag 
                        v-if="record.finished" 
                        color="green">
                        Завершен
                    </a-tag>
                    <a-tag 
                        v-else 
                        color="blue">
                        Активный
                    </a-tag>
                </template>
            </a-table>
        </div>
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
import eventBus from "@/utils/eventBus"
import { mapGetters, mapState } from 'vuex'
export default {
    name: 'GroupTable',
    components: {
        Members: () => import('./Members.vue'),
        Effects: () => import('./Effects.vue')
    },
    props: {
        listProject: {
            type: Boolean,
            default: true
        },
        pageModel: {
            type: String,
            default: 'workgroups.WorkgroupModel'
        },
        page_name: {
            type: String,
            default: 'page_list_project_workgroups.WorkgroupModel'
        },
        tableColumnsList: {
            type: Array,
            default: () => []
        }
    },
    computed: {
        ...mapState({
            windowHeight: state => state.windowHeight,
            windowWidth: state => state.windowWidth,
            config: state => state.config.config
        }),
        ...mapGetters({
            getPageSize: 'workgroups/getTablePageSize'
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
        isMobile() {
            return this.$store.state.isMobile
        },
        tableSize() {
            return this.config?.theme?.tableSize ? this.config.theme.tableSize : 'small'
        },
        columns() {
            return this.tableColumnsList
        },
    },
    watch: {
        pageSize(newSize) {
            this.changePageSize(newSize)
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
    created() {
        eventBus.$on('update_workgroup_data', () => {
            this.getList()
        })
        const localPageSize = this.getPageSize(this.page_name)
        if(localPageSize)
            this.pageSize = localPageSize 

        this.getList()
    },
    methods: {
        handleTableChange(pagination, filters, sorter) {
            if(sorter.order) {
                this.sort = `${sorter.order === "ascend" ? '' : '-'}${sorter.field}`
            } else {
                this.sort = null
            }

            this.getList()
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
        changePageSize(size) {
            this.$store.commit('workgroups/SET_TABLE_PAGE_SIZE', {
                tableName: this.page_name,
                pageSize: size
            })
        },
        openHandler(id) {
            this.$router.replace({
                query: { viewGroup: id }
            })
        },
        async getList() {
            try {
                this.loading = true

                let params = {
                    is_project: this.listProject ? 1 : 0,
                    page: this.page,
                    page_size: this.pageSize,
                    page_name: this.page_name
                }

                if(this.sort) {
                    params.ordering = this.sort
                }

                const { data } = await this.$http.get('/work_groups/workgroups/', {
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
        reloadList() {
            
        },

        workgroupLogoPath(workgroup) {
            return workgroup?.workgroup_logo?.path || ''
        }
    },
    mounted() {
        eventBus.$on(`update_filter_${this.pageModel}`, () => {
            this.page = 1
            this.getList()
        })
        eventBus.$on('update_list_project', () => {
            this.getList()
        })
    },
    beforeDestroy() {
        eventBus.$off(`update_filter_${this.pageModel}`)
        eventBus.$off('update_list_project')
        eventBus.$off('update_workgroup_data')
    }
}
</script>

<style lang="scss" scoped>
.group_desc,
.group_name{
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
    text-overflow: ellipsis;
    transition: color 0.3s;
    word-break: break-word;
}
</style>