<template>
    <div class="list-wrapper">
        <Filters 
            ref="filters" 
            :summary="summary"
            :page_name="page_name"
            :model="model"
            :setSummary="setSummary"
            :setFilters="setFilters" />
        <div class="inquiries-list">
            <MobileInquirItem
                v-for="assessment in list"
                :key="assessment.id"
                :assessment="assessment"
                class="mb-3 overflow-hidden" />
        </div>
        <infinite-loading
            :ref="getRef"
            :identifier="infiniteId"
            @infinite="getList"
            :distance="10">
            <div slot="spinner" class="mt-[30px]">
                <a-spin />
            </div>
            <div slot="no-more"></div>
            <div slot="no-results"></div>
        </infinite-loading>
        <div v-if="showEmpty" class="pt-8">
            <a-empty />
        </div>
        <div class="float_add">
            <slot name="viewButton" />
            <div class="filter_slot">
                <PageFilter 
                    :model="model"
                    :key="name"
                    :name="name"
                    size="large"
                    :page_name="page_name" />
            </div>
            <a-button
                v-if="showAddButton"
                flaticon
                shape="circle"
                size="large"
                type="primary"
                icon="fi-rr-plus"
                @click="newInquir" />
        </div>
    </div>
</template>

<script>
import MobileInquirItem from "./MobileInquirItem.vue"
import InfiniteLoading from 'vue-infinite-loading'
import methodsM from "./mixins/methods"
import eventBus from '@/utils/eventBus'
import PageFilter from '@/components/PageFilter'
import Filters from './Filters.vue'
export default {
    name: 'InquiriesList',
    components: {
        MobileInquirItem,
        InfiniteLoading,
        PageFilter,
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
        name: {
            type: String,
            default: ''
        },
        model: {
            type: String,
            default: ''
        },
        showAddButton: {
            type: Boolean,
            default: () => false
        },
        newInquir: {
            type: Function,
            default: () => {}
        }
    },
    data() {
        return {
            filters: {
                current_month: false,
                current_year: false,
                period: false,
                processed_inquiries: false,
                new_inquiries: false,
                organizations: false
            },
            infiniteId: new Date(),
            showEmpty: false,
            report: {},
            loading: false,
            list: [],
            page: 1,
            pageSize: 5,
            count: 0,
            organizationsFilter: null,
            ordering: null,
            summary: null
        }
    },
    computed: {
        filterActive() {
            return this.$store.state.filter.filterActive[this.page_name]
        },
        getRef() {
            return `infiniteLoading_${this.page_name}`
        }
    },
    methods: {
        setSummary(data) {
            this.summary = data
        },
        checkAndSetShowEmpty() {
            if(this.list && !this.list.length) 
                this.showEmpty = true
            else 
                this.showEmpty = false
        },
        async getList($state) {
            try {
                this.loading = true

                let params = {
                    page: this.page,
                    page_size: this.pageSize,
                    page_name: this.page_name
                }

                const { data } = await this.$http.get('/risk_assessment/', {
                    params
                })
                if(data?.results?.length) {
                    this.count = data.count
                    this.list.push(... await this.setActions(data.results))
                    this.summary = data.summary
                    if(data.next) {
                        this.page += 1
                        $state.loaded()
                    } else {
                        $state.complete()
                    }
                } else {
                    $state.complete()
                    this.list = []
                    this.count = 0
                }
                this.checkAndSetShowEmpty()
            } catch(e) {
                console.log(e)
            } finally {
                this.loading = false
            }
        },
        reloadList() {
            this.page = 1
            this.list = []
            
            this.$nextTick(()=>{
                if(this.$refs[`infiniteLoading_${this.page_name}`]){
                    this.$refs[`infiniteLoading_${this.page_name}`].stateChanger.reset()
                }
            })

        },
        periodChange(date, dateStrings) {
            if(this.periodStart && this.periodEnd) {
                if(this.periodStart >= this.periodEnd) {
                    this.$message.error('Период задан некорректно!')
                    return
                }
                this.setFilters()
            }
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
            eventBus.$emit(`include_fields_${this.page_name}`, {
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
    },
    created() {
        eventBus.$on('assessment_list_reload', () => {
            this.reloadList()
        })
        
        eventBus.$on(`update_filter_${this.model}_${this.name}`, () => {
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
                margin-left: unset;
                .ant-checkbox{
                    display: none;
                    & + span{
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
    .inquiries-list {
        margin-top: 8px;
    }
}
</style>