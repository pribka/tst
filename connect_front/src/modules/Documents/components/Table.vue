<template>
    <div>
        <a-table
            :columns="columns"
            :pagination="false"
            :loading="loading"
            ref="docTable"
            :scroll="scroll"
            :locale="{
                emptyText: 'Нет данных'
            }"
            :size="tableSize"
            :row-key="(record, index) => `${record.id}-${index}`"
            :data-source="list">
            <template
                slot="name"
                slot-scope="text, record">
                <div class="cursor-pointer blue_color doc_name" @click="openDocument(record.id)">
                    {{ text }}
                </div>
            </template>
            <template
                slot="contractor"
                slot-scope="text, record">
                <div v-if="record.contractor" class="flex items-center truncate">
                    <div :key="record.contractor.logo" class="pr-2">
                        <a-avatar 
                            :size="30"
                            :src="record.contractor.logo"
                            icon="fi-rr-users-alt" 
                            flaticon />
                    </div>
                    <span class="truncate">{{ record.contractor.name }}</span>
                </div>
                <template v-else>
                    -
                </template>
            </template>
            <template
                slot="customer"
                slot-scope="text, record">
                <template v-if="record.customer">
                    {{ record.customer.name }}
                </template>
                <template v-else>
                    -
                </template>
            </template>
            <template
                slot="template"
                slot-scope="text, record">
                <template v-if="record.template">
                    {{ record.template.name }}
                </template>
                <template v-else>
                    -
                </template>
            </template>
            <template
                slot="template_type"
                slot-scope="text, record">
                <template v-if="record.template">
                    {{ record.template.doc_type.name }}
                </template>
                <template v-else>
                    -
                </template>
            </template>
            <template
                slot="approval_status"
                slot-scope="text, record">
                <a-tag v-if="record.approval_status && record.approval_status.name" :color="record.approval_status.color || ''">
                    {{ record.approval_status.name }}
                </a-tag>
                <template v-else>
                    -
                </template>
            </template>
            <template
                slot="delivery_status"
                slot-scope="text, record">
                <a-tag v-if="record.delivery_status && record.delivery_status.name" :color="record.delivery_status.color || ''">
                    {{ record.delivery_status.name }}
                </a-tag>
                <template v-else>
                    -
                </template>
            </template>
            <template
                slot="created_at"
                slot-scope="text">
                {{ $moment(text).format('DD.MM.YYYY') }}
            </template>
            <template
                slot="author"
                slot-scope="text">
                <Profiler :user="text" />
            </template>
            <template
                slot="id"
                slot-scope="text, record">
                <div class="flex justify-end items-center">
                    <a-tag v-if="record.locked">
                        <i class="fi fi-rr-lock"></i>
                    </a-tag>
                    <Actions 
                        :id="record.id" 
                        :record="record" />
                </div>
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
export default {
    components: {
        Actions: () => import('./Actions')
    },
    props: {
        page_name: {
            type: String,
            default: ''
        },
        model: {
            type: String,
            default: ''
        }
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
                return 1600
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
            list: [],
            page: 1,
            pageSize: 15,
            sort: '',
            count: 0,
            pageSizeOptions: ['15', '30', '50'],
            columns: [
                {
                    dataIndex: 'name',
                    title: 'Название',
                    key: 'name',
                    width: 200,
                    scopedSlots: {
                        customRender: "name"
                    }
                },
                {
                    dataIndex: 'contractor',
                    title: 'Организация',
                    key: 'contractor',
                    width: 150,
                    scopedSlots: {
                        customRender: "contractor"
                    }
                },
                {
                    dataIndex: 'customer',
                    title: 'Контрагент',
                    key: 'customer',
                    width: 150,
                    scopedSlots: {
                        customRender: "customer"
                    }
                },
                {
                    dataIndex: 'template',
                    title: 'Шаблон',
                    key: 'template',
                    width: 150,
                    scopedSlots: {
                        customRender: "template"
                    }
                },
                {
                    dataIndex: 'template_type',
                    title: 'Тип документа',
                    key: 'template_type',
                    width: 150,
                    scopedSlots: {
                        customRender: "template_type"
                    }
                },
                {
                    dataIndex: 'author',
                    title: 'Автор',
                    key: 'author',
                    width: 180,
                    scopedSlots: {
                        customRender: "author"
                    }
                },
                {
                    dataIndex: 'created_at',
                    title: 'Дата создания',
                    key: 'created_at',
                    width: 100,
                    scopedSlots: {
                        customRender: "created_at"
                    }
                },
                {
                    dataIndex: 'approval_status',
                    title: 'Статус',
                    key: 'approval_status',
                    width: 80,
                    scopedSlots: {
                        customRender: "approval_status"
                    }
                },
                {
                    dataIndex: 'delivery_status',
                    title: 'Статус отправки',
                    key: 'delivery_status',
                    width: 100,
                    scopedSlots: {
                        customRender: "delivery_status"
                    }
                },
                {
                    dataIndex: 'id',
                    title: '',
                    key: 'id',
                    width: 80,
                    scopedSlots: { customRender: 'id' }
                }
            ]
        }
    },
    created() {
        this.getList()

        eventBus.$on('update_doc_list', data => {
            this.updateDocList(data)
        })

        eventBus.$on('docTableReload', () => {
            this.getList()
        })
        
        eventBus.$on(`update_filter_${this.model}`, () => {
            this.getList()
        })
    },
    methods: {
        updateDocList(data) {
            const index = this.list.findIndex(f => f.id === data.id)
            if(index !== -1) {
                this.$set(this.list, index, data)
            }
        },
        openDocument(id) {
            const query = Object.assign({}, this.$route.query)
            if(query.document && Number(query.document) !== id || !query.document) {
                query.document = id
                this.$router.push({query})
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
        async getList() {
            try {
                this.loading = true

                let params = {
                    page: this.page,
                    page_size: this.pageSize,
                    page_name: this.page_name
                }

                const { data } = await this.$http.get('/contractor_docs/', {
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
    },
    beforeDestroy() {
        eventBus.$off('docTableReload')
        eventBus.$off(`update_filter_${this.model}`)
        eventBus.$off('update_doc_list')
    }
}
</script>

<style lang="scss" scoped>
.doc_name{
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
    text-overflow: ellipsis;
    word-break: break-word;
}
</style>