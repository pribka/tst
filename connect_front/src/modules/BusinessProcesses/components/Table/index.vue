<template>
    <div class="h-full">
        <a-table 
            :columns="columns" 
            :data-source="data"
            :loading="tableLoading"
            :pagination="false"
            :scroll="{x: 1200, y: 'calc(100vh - 315px)'}"
            :size="size"
            :locale="{
                emptyText: 'Нет данных'
            }"
            :row-key="record => record.id">
            <template slot="owner" slot-scope="text">
                <Profiler
                    :avatarSize="22"
                    nameClass="text-sm"
                    :user="text" />
            </template>
            <template 
                slot="finished_date" 
                slot-scope="text">
                <template v-if="text">
                    {{$moment(text).format('DD.MM.YYYY HH:mm')}}
                </template>
            </template>
            <template 
                slot="created_at" 
                slot-scope="text">
                {{$moment(text).format('DD.MM.YYYY HH:mm')}}
            </template>
            <template 
                slot="amount_of_money" 
                slot-scope="text">
                {{ tableAmount(text) }}
            </template>
            <template 
                slot="dead_line" 
                slot-scope="text">
                <DeadLine :date="text" />
            </template>
            <template 
                slot="name" 
                slot-scope="text, record">
                <span 
                    class="table_link" 
                    @click="open(record.id)">
                    {{ text }}
                </span>
            </template>
            <template 
                slot="status" 
                slot-scope="text, record">
                <Status :record="record" />
            </template>
            <template 
                slot="actions" 
                slot-scope="text, record">
                <Actions 
                    :record="record"
                    :updateModel="updateModel"
                    :actionLoader="actionLoader"
                    :deleteHandler="deleteHandler" />
            </template>
            <template 
                slot="itinerary" 
                slot-scope="text">
                {{ text.name }}
            </template>
        </a-table>
        <div 
            v-if="pagination" 
            class="pager pt-2 flex justify-end">
            <a-pagination
                size="small"
                :value="page"
                :total="count"
                :defaultPageSize="page_size"
                :show-size-changer="pageSizeOptions.length > 1"
                :page-size.sync="page_size"
                :pageSizeOptions="pageSizeOptions"
                @showSizeChange="changeSize"
                @change="changePage"
                show-less-items>
                <template slot="buildOptionText" slot-scope="props">
                    {{ props.value }}
                </template>
            </a-pagination>
        </div>
    </div>
</template>

<script>
import Status from './Status'
import Actions from './Actions'
import DeadLine from '../DeadLine.vue'
import { numberWithSpaces } from '../../utils'
import eventBus from '../../utils/eventBus'
import globalEventBus from '@/utils/eventBus'
export default {
    components: {
        Status,
        Actions,
        DeadLine
    },
    props: {
        id: {
            type: [String, Number],
            required: true
        },
        size: {
            type: String,
            default: 'large'
        },
        pagination: {
            type: Boolean,
            default: true
        },
        pageSizeOptions: {
            type: Array,
            default: () => ['15', '30', '50']
        },
        updateModel: {
            type: String,
            default: 'main'
        },
        page_name: {
            type: [String, Number],
            default: ''
        }
    },
    data() {
        return {
            tableLoading: false,
            data: [],
            actionLoader: {},
            page_size: 15,
            count: 0,
            page: 1,
            columns: [
                {
                    title: 'Наименование',
                    dataIndex: 'name',
                    key: 'name',
                    scopedSlots: { customRender: 'name' },
                    width: 200,
                    fixed: 'left'
                },
                {
                    title: 'Дата создания',
                    dataIndex: 'created_at',
                    key: 'created_at',
                    scopedSlots: { customRender: 'created_at' }
                },
                {
                    title: 'Автор',
                    dataIndex: 'owner',
                    key: 'owner',
                    scopedSlots: { customRender: 'owner' }
                },
                {
                    title: 'Сумма заявки (тг)',
                    dataIndex: 'amount_of_money',
                    key: 'amount_of_money',
                    scopedSlots: { customRender: 'amount_of_money' }
                },
                {
                    title: 'Крайний срок',
                    dataIndex: 'dead_line',
                    key: 'dead_line',
                    scopedSlots: { customRender: 'dead_line' }
                },
                {
                    title: 'Тип заявки',
                    dataIndex: 'itinerary',
                    key: 'itinerary',
                    scopedSlots: { customRender: 'itinerary' }
                },
                {
                    title: 'Дата закрытия',
                    dataIndex: 'finished_date',
                    key: 'finished_date',
                    scopedSlots: { customRender: 'finished_date' }
                },
                {
                    title: 'Статус',
                    dataIndex: 'status',
                    key: 'status',
                    width: 100,
                    fixed: 'right',
                    scopedSlots: { customRender: 'status' }
                },
                {
                    title: '',
                    dataIndex: 'actions',
                    key: 'actions',
                    width: 50,
                    fixed: 'right',
                    scopedSlots: { customRender: 'actions' }
                }
            ]
        }
    },
    created() {
        this.getData()
    },
    methods: {
        tableAmount(sum) {
            return numberWithSpaces(sum)
        },
        open(id) {
            let query = Object.assign({}, this.$route.query)
            if(query.bprocess && query.bprocess !== id || !query.bprocess) {
                query.bprocess = id
                this.$router.push({query})
            }
        },
        changeSize(current, pageSize) {
            this.page = 1
            this.page_size = Number(pageSize)
            this.getData()
        },
        changePage(page) {
            this.page = page
            this.getData()
        },
        deleteInList(item) {
            const index = this.data.findIndex(f => f.id === item.id)
            if(index !== -1)
                this.data.splice(index, 1)
        },
        deleteHandler(item) {
            this.$confirm({
                title: 'Предупреждение',
                content: 'Вы действительно хотите удалить заявку?',
                zIndex: 1200,
                cancelText: 'Закрыть',
                okText: 'Удалить',
                okType: 'danger',
                onOk: () => {
                    return new Promise((resolve, reject) => {
                        this.$set(this.actionLoader, item.id, true)
                        this.$http.post('/table_actions/update_is_active/', [{ id: item.id, is_active: false }])
                            .then(() => {
                                this.$message.success('Заявка удалена')
                                this.deleteInList(item)
                                resolve()
                            })
                            .catch((e) => {
                                console.log(e)
                                reject()
                            })
                            .finally(() => {
                                this.$delete(this.actionLoader, item.id)
                            })
                    })
                },
                onCancel() {}
            })
        },
        async getData() {
            try {
                this.tableLoading = true
                const { data } = await this.$http.get('/processes/financial_application/list/', {
                    params: {
                        template_id: this.id,
                        page: this.page,
                        page_size: this.page_size,
                        page_name: this.page_name
                    }
                })
                this.data = data.results
                this.count = data.count
            } catch(e) {
                console.log(e)
            } finally {
                this.tableLoading = false
            }
        },
        updateListItem(item) {
            const index = this.data.findIndex(f => f.id === item.id)
            if(index !== -1)
                this.$set(this.data, index, item)
        }
    },
    mounted() {
        eventBus.$on(`UNSHIFT_PROCESS_LIST_${this.updateModel}`, data => {
            this.data.unshift(data)
            this.count += 1
        })
        eventBus.$on('DELETE_PROCESS', process => {
            this.deleteInList(process)
        })
        eventBus.$on('UPDATE_PROCESS_LIST', process => {
            this.updateListItem(process)
        })
        globalEventBus.$on(`update_filter_processes.FinancialApplicationModel`, () => {
            this.page = 1
            this.getData()
        })
    },
    beforeDestroy() {
        eventBus.$off(`UNSHIFT_PROCESS_LIST_${this.updateModel}`)
        eventBus.$off('DELETE_PROCESS')
        eventBus.$off('UPDATE_PROCESS_LIST')
        globalEventBus.$off('update_filter_processes.FinancialApplicationModel')
    }
}
</script>

<style lang="scss">
.table_link{
    cursor: pointer;
    color: var(--blue);
}
</style>