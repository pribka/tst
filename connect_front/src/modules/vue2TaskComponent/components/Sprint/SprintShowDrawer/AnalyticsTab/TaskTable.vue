<template>
    <div class="pb-14">
        <a-table 
            :columns="columns" 
            :loading="loading"
            :rowKey="key => key.id"
            :pagination="false"
            class="time_table"
            :scroll="{ x: 1136 }"
            :data-source="list">
            <template slot="name" slot-scope="text, record">
                <div class="task_link blue_color" @click="openTask(record)">
                    {{ text }}
                </div>
            </template>
            <template slot="time_tracking" slot-scope="text, record">
                <div v-for="(time, index) in record.time_tracking" :key="index" class="time_block flex items-center">
                    <Profiler
                        :avatarSize="22"
                        hideSupportTag
                        nameWrapperClass="truncate"
                        wrapperClass="truncate"
                        nameClass="truncate"
                        :user="time.author" />
                </div>
            </template>
            <template slot="role" slot-scope="text, record">
                <div 
                    v-for="(time, index) in record.time_tracking" 
                    :key="`${index}_role`" 
                    :title="time.role"
                    class="time_block flex items-center">
                    <span>{{ time.role }}</span>
                </div>
            </template>
            <template slot="time" slot-scope="text, record">
                <div v-for="(time, index) in record.time_tracking" :key="`${index}_time`" class="time_block flex items-center justify-center">
                    {{ time.hours_sum }}
                </div>
            </template>
            <template slot="status" slot-scope="text, record">
                <TaskStatus :status="record.status" />
            </template>
            <template slot="excluded" slot-scope="text, record">
                <a-tag v-if="record.excluded" color="purple" class="m-0">
                    {{ $t('task.returned') }}
                </a-tag>
                <span v-else></span>
            </template>
        </a-table>
        <div class="mt-2 flex justify-end">
            <a-pagination 
                v-model="page" 
                size="small"
                :total="count" 
                :pageSize="page_size"
                show-less-items
                @change="changePage" />
        </div>
    </div>
</template>

<script>
import TaskStatus from '../../../TaskStatus.vue'
export default {
    props: {
        model: {
            type: String,
            required: true
        },
        sprint: {
            type: Object,
            required: true
        },
        page_name: {
            type: String,
            required: true
        }
    },
    components: {
        TaskStatus
    },
    computed: {
        columns() {
            const cols = [
                {
                    title: '#',
                    width: 100,
                    dataIndex: 'counter',
                    key: 'counter',
                    scopedSlots: { customRender: 'counter' }
                },
                {
                    title: this.$t('task.name'),
                    dataIndex: 'name',
                    width: 250,
                    key: 'name',
                    scopedSlots: { customRender: 'name' }
                },
                {
                    title: this.$t('task.employee'),
                    width: 270,
                    dataIndex: 'time_tracking',
                    key: 'time_tracking',
                    scopedSlots: { customRender: 'time_tracking' }
                },
                {
                    title: this.$t('task.role'),
                    width: 180,
                    dataIndex: 'role',
                    key: 'role',
                    scopedSlots: { customRender: 'role' }
                },
                {
                    title: this.$t('task.time_spent_short'),
                    dataIndex: 'time',
                    key: 'time',
                    width: 165,
                    scopedSlots: { customRender: 'time' }
                },
                {
                    title: this.$t('task.task_status'),
                    dataIndex: 'status',
                    key: 'status',
                    scopedSlots: { customRender: 'status' }
                }
            ]
            if(this.sprint.status === 'completed')
                cols.push({
                    title: this.$t('task.returned'),
                    dataIndex: 'excluded',
                    key: 'excluded',
                    scopedSlots: { customRender: 'excluded' }
                })
            return cols
        }
    },
    data() {
        return {
            page_size: 5,
            page: 1,
            list: [],
            count: 0,
            loading: false,
            selectedUser: null
        }
    },
    created() {
        this.getTask()
    },
    methods: {
        clearTaskFilter() {
            this.selectedUser = null
            this.reloadTableData()
        },
        taskSetFilter(item) {
            const author = item.customData.author
            this.selectedUser = author
            this.page = 1
            this.getTask(author)
        },
        reloadTableData() {
            this.page = 1
            this.getTask()
        },
        changePage() {
            this.getTask()
        },
        openTask(record) {
            let query = Object.assign({}, this.$route.query)
            query.task = record.id
            if(!this.$route.query.task) 
                this.$router.push({query})
        },
        async getTask(user = null) {
            try {
                this.loading = true
                const params = {
                    page: this.page,
                    page_size: this.page_size,
                    page_name: this.page_name
                }
                if (this.selectedUser) {
                    params.user = this.selectedUser
                }
                const { data } = await this.$http.get(`/tasks/sprint/${this.sprint.id}/report/tasks/`, { params })
                this.list = data.results
                this.count = data.count
            } catch(e) {
                console.log(e)
            } finally {
                this.loading = false
            }
        }
    }
}
</script>

<style lang="scss" scoped>
.time_table{
    &::v-deep{
        tr{
            td{
                &.ant-table-row-cell-break-word{
                    padding-top: 0px;
                    padding-bottom: 0px;
                    
                }
            }
        }
    }
}
.time_block{
    min-height: 45px;
    max-height: 45px;
    line-height: 15px;
    padding: 10px 0;
    &:not(:last-child){
        border-bottom: 1px solid #e8e8e8;
    }
    span{
        display: -webkit-box;
        -webkit-line-clamp: 3;
        -webkit-box-orient: vertical;
        overflow: hidden;
        text-overflow: ellipsis;
        word-break: break-word;
    }
}
.task_link{
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
    text-overflow: ellipsis;
    transition: color 0.3s;
    word-break: break-word;
    cursor: pointer;
}
</style>