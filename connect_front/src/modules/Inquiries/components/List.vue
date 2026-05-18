<template>
    <div class="list-wrapper">
        <Filters 
            ref="filters" 
            :summary="summary"
            :page_name="page_name"
            :model="model"
            :setSummary="setSummary"
            :setFilters="setFilters" />
        <a-spin 
            :spinning="loading" 
            class="w-full">
            <div 
                v-if="list.length > 0" 
                class="inquiries-list">
                <InquirItem
                    v-for="assessment in list"
                    :key="assessment.id"
                    :assessment="assessment"
                    class="overflow-hidden" />
                <div class="flex justify-end pt-1">
                    <a-pagination
                        :current="page"
                        class="pager_wrapper"
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
            <a-empty 
                v-if="empty" 
                :description="false" />
        </a-spin>
    </div>
</template>

<script>
import InquirItem from "./InquirItem.vue"
import methodsM from "./mixins/methods"
import eventBus from '@/utils/eventBus'
import Filters from './Filters.vue'
export default {
    name: 'InquiriesList',
    components: {
        InquirItem,
        Filters
    },
    mixins: [
        methodsM,
    ],
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
    data() {
        return {
            report: {},
            loading: false,
            list: [],
            page: 1,
            pageSize: 15,
            count: 0,
            pageSizeOptions: ['15', '30', '50'],
            summary: null,
            empty: false
        }
    },
    computed: {
        filterActive() {
            return this.$store.state.filter.filterActive[this.page_name]
        }
    },
    methods: {
        setSummary(data) {
            this.summary = data
        },
        async getList() {
            try {
                this.empty = false
                this.loading = true

                let params = {
                    page: this.page,
                    page_size: this.pageSize,
                    page_name: this.page_name
                }

                const { data } = await this.$http.get('/risk_assessment/', {
                    params
                })
                if(data) {
                    if(data.count === 0 && this.page === 1)
                        this.empty = true
                }
                if(data?.results?.length) {
                    this.count = data.count
                    this.list = await this.setActions(data.results)
                    this.summary = data.summary
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
            this.getInquiries()
        },
        changePage(page) {
            this.page = page
            this.getInquiries()
        },
        setFilters({filters, organizationsFilter, summaryActive, periodStart, periodEnd}) {
            let date_values = [],
                status_value = [],
                organizations_value = ''
            
            if(filters['current_month']) {
                date_values = {
                    start: this.$moment().startOf('month').format('YYYY-MM-DD'),
                    end: this.$moment().endOf('month').format('YYYY-MM-DD')
                }
            } else if(filters['current_year']) {
                date_values = {
                    start: this.$moment().startOf('year').format('YYYY-MM-DD'),
                    end: this.$moment().endOf('year').format('YYYY-MM-DD')
                }
            } else if(filters['period']) {
                date_values = {
                    start: periodStart.format('YYYY-MM-DD'),
                    end: periodEnd.format('YYYY-MM-DD')
                }
            } else if(filters['current_day']) {
                date_values = {
                    start: this.$moment().format('YYYY-MM-DD'),
                    end: this.$moment().format('YYYY-MM-DD')
                }
            } else {
                date_values = []
            }

            if(filters['new_inquiries']) {
                status_value = ['new',]
            } else if(filters['processed_inquiries']) {
                status_value = ['processed',]
                
            } else {
                status_value = []
            }
            if(filters['organizations']) {
                organizations_value = organizationsFilter
            }
            eventBus.$emit(`send_include_fields_${this.page_name}`, {
                fields: {
                    issue_date_filter: {
                        active: filters['current_month'] || filters['current_year'] || filters['period'] || filters['current_day'],
                        values: date_values
                    },
                    status: {
                        active: filters['new_inquiries'] || filters['processed_inquiries'],
                        values: {
                            value: status_value
                        }
                    },
                    organizations_filter: {
                        active: filters['organizations'],
                        values: {
                            value: organizations_value
                        }
                    },
                    total_value_filter: {
                        active: Object.keys(summaryActive).length !== 0,
                        values: {
                            value: Object.keys(summaryActive)
                        }
                    }
                }
            })
            
        },
        reloadList() {
            this.page = 1
            this.list = []
            this.getInquiries()
        }
    },
    created() {
        this.getInquiries()

        eventBus.$on('assessment_list_reload', () => {
            this.reloadList()
        })
        
        eventBus.$on(`update_filter_${this.model}`, () => {
            this.reloadList()
        })

        eventBus.$on('update_assessment_in_list', data => {
            this.updateAssessmentInList(data)
            this.$nextTick(() => {
                this.$refs.filters.getSummary()
            })
        })

    },
    beforeDestroy() {
        eventBus.$off('assessment_list_reload')
        eventBus.$off('update_assessment_in_list')
        eventBus.$off(`update_filter_${this.model}`)

    },
}
</script>

<style lang="scss" scoped>
.list-wrapper{
    &::v-deep {
        .check_button{
            .ant-checkbox-wrapper{
                margin: 8px 8px 0 0;
                .ant-checkbox{
                    display: none;
                    & + span{
                        height: 26px;
                        padding: 2px 8px;
                        border: 1px solid var(--borderColor);
                        border-radius: 30px;
                        display: inline-block;
                        background: #e3e6ea;
                        cursor: pointer;
                        -moz-user-select: none;
                        -khtml-user-select: none;
                        user-select: none;
                        transition: all 0.3s cubic-bezier(0.645, 0.045, 0.355, 1);
                        &:hover{
                            background: var(--primaryHover);
                        }
                    }
                    &.ant-checkbox-checked{
                        & + span{
                            background: var(--primaryHover);
                            color: var(--blue);
                        }
                    }
                }
            }
    
        }
    }
}
</style>