<template>
    <div class="wrap">
        <a-select
            class="org-administrator"
            v-for="select in filters.selects"
            :key="select.id"
            :allowClear="true"
            :showSearch="windowWidth > 786 ? true : false"
            :maxTagCount="windowWidth > 786 ? 3 : 10"
            size="default"
            :placeholder="$t('dashboard.parent_organization')"
            :loading="select.loading"
            v-model="select.value"
            dropdownClassName="filter_i_select"
            :getPopupContainer="trigger => trigger.parentElement"
            @select="selectHandler(select.id)"
            :filter-option="false"
            @popupScroll="scrollHandler($event, select.id)">
            <a-select-option
                v-for="option in select.options.list"
                :key="option.id"
                :value="option.id">
                {{ option.string_view ? option.string_view : option.name }}
            </a-select-option>
            <div slot="notFoundContent" class="flex justify-center p-1">
                <a-empty :description="$t('dashboard.no_data')" />
            </div>
        </a-select>
                        
        <a-month-picker 
            class="start"
            v-model="filters.dateRange.start"
            :valueFormat="filters.dateRange.format"
            :placeholder="$t('dashboard.start')" 
            @change="$emit('updateFilters')" />
        <a-month-picker
            class="end"
            :valueFormat="filters.dateRange.format"
            v-model="filters.dateRange.end"
            :placeholder="$t('dashboard.end')" 
            @change="$emit('updateFilters')" />
    </div>
</template>

<script>
export default {
    props: {
        filters: {
            type: Object,
            required: true
        },
        currentMonth: {
            type: Boolean,
            default: false
        }
    },
    data() {
        return {
            windowWidth: 0,
            start: null,
            end: null,
            selectInitOptions: [
                {
                    name: this.$t('dashboard.option_all'),
                    id: 'all'
                },
                {
                    name: this.$t('dashboard.option_self'),
                    id: 'self'
                },
                {
                    name: this.$t('dashboard.option_descendants'),
                    id: 'descendants'
                },
            ]
        }
    },
    created() {
        const selects = this.filters.selects.find(selectItem => selectItem.id === 'parent')
        const dateRange = this.filters.dateRange
        const isOptionListEmpty = !selects.options.list?.length
        const isDataRangeEmpty = !dateRange.start || !dateRange.end
        if (isOptionListEmpty) {
            this.initParentOptions()
        }
        if (isDataRangeEmpty) {
            this.initDateRange()
        }
    },
    methods: {
        initDateRange() {
            if(this.currentMonth) {
                this.filters.dateRange.start = this.$moment()
                this.filters.dateRange.end = this.$moment()
            } else {
                this.filters.dateRange.start = this.$moment().subtract(1, 'months')
                this.filters.dateRange.end = this.$moment().subtract(1, 'months')
            }
        },
        async initParentOptions() {
            const select = this.filters.selects.find(selectItem => selectItem.id === 'parent')
            select.loading = true
            const options = await this.getSelectOptions('parent')
            select.loading = false

            select.options.list = options
            select.value = select.options.list[0].id
            this.selectHandler('parent')
        },
        resetSelectOptions(selectId) {
            const select = this.filters.selects.find(selectItem => selectItem.id === selectId)
            if (select) {
                select.options.page = 0
                select.next = true
                select.loading = false
    
                if (selectId === 'displayed') {
                    select.options.list = JSON.parse(JSON.stringify(this.selectInitOptions))
                } else if (selectId === 'parent') {
                    select.options.list = []
                }
            }
        },
        async selectHandler(selectId) {
            if (selectId === 'parent') {
                const displaySelect = this.filters.selects.find(selectItem => selectItem.id === 'displayed')
                if (displaySelect) {
                    this.resetSelectOptions('displayed')
    
                    displaySelect.loading = true
                    const options = await this.getSelectOptions('displayed')
                    displaySelect.loading = false
    
                    displaySelect.options.list.push(...options)
                    displaySelect.value = displaySelect.options.list[0].id
                }
            }
            this.$emit('updateFilters')
        },
        async getSelectOptions(selectId) {
            const url = this.getSelectURL(selectId)
            const params = {
                page_size: 'all',
            }
            try {
                const { data } = await this.$http.get(url, { params })
                if(selectId === 'parent') {
                    if (!data.length) {
                        console.error(this.$t('dashboard.error_no_results'))
                        return []
                    }
                    return data
                } else if(selectId === 'displayed') {
                    if (!data?.results) {
                        console.error(this.$t('dashboard.error_no_results'))
                        return []
                    }
                    return data.results.map(relation => relation.contractor)
                }
            } catch(error) {
                console.error(this.$t('dashboard.error_get_options'))
                return []
            }
        },
        getSelectURL(selectId) {
            if (selectId === 'displayed') {
                const parentSelect = this.filters.selects.find(selectItem => selectItem.id === 'parent')
                const parentOrganizationId = Array.isArray(parentSelect.value) ? 
                    parentSelect.value[0] : parentSelect.value
                return `/users/my_organizations/${parentOrganizationId}/relations/`
            } 
            if (selectId === 'parent') {
                return '/consolidation/get_org_administrators'
            }
        },
        async scrollHandler(event, selectId) { 
            const target = event.target
            const select = this.filters.selects.find(selectItem => selectItem.id === selectId)
            const isBottomScrolling = target.scrollTop + target.offsetHeight === target.scrollHeight

            if(select.options.next && !select.loading && isBottomScrolling) {
                try {
                    select.loading = true
                    const options = await this.getSelectOptions(selectId)
                    select.options.list.push(...options)
                } catch(error) {
                    console.error(this.$t('dashboard.error_fetching_data'), error)
                } finally {
                    select.loading = false
                }
            }
        }

    }
}
</script>
<style lang="scss" scoped>
.wrap{
    width: 400px;
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 0.5rem;
    .org-administrator{
        grid-column: span 2;
    }
    .start{}
    .end{}
}
</style>