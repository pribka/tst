<template>
    <a-spin :spinning="loading">
        <template v-if="isMobile">
            <div class="mobile-wrapper">
                <div class="title">{{$t('invest.filterTitle')}}:</div>
                <div class="select">
                    <a-select
                        size="large"
                        class="w-full"
                        v-model="selected"
                        :loading="loading"
                        :default-active-first-option="true"
                        :filter-option="false"
                        :not-found-content="null"
                        dropdownClassName="custom-dropdown"
                        @select="setFilter"
                        @dropdownVisibleChange="handleOpenChange">
                        <div slot="suffixIcon" class="circle-button" :class="{ rotated: isOpen }">
                            <img
                                :data-src="arrow" 
                                class="lazyload" >
                        </div>
                        <a-select-option 
                            v-for="(filter, index) in filters" 
                            :key="index" 
                            :value="filter.status.code">
                            {{ `${filter.status.name} (${filter.count})` }}
                        </a-select-option>
                    </a-select>
                </div>
            </div>
        </template>
        <template v-else>
            <div class="wrapper">
                <div class="filters">
                    <div
                        v-for="(filter, index) in filters"
                        :key="index" class="filter"
                        :class="selected === filter.status.code && 'selected'"
                        @click="setFilter(filter.status.code)">
                        {{ `${filter.status.name} (${filter.count})` }}
                    </div>
                </div>
            </div>
        </template>
    </a-spin>
</template>

<script>
import eventBus from '@/utils/eventBus'

export default {
    name: 'StatusFilter',
    data() {
        return {
            loading: false,
            selected: 'total',
            filters: [],
            isOpen: false,
            page_name: 'invest_project_list',
            model: 'invest_projects_info.InvestProjectInfoModel',
        }
    },
    computed: {
        isMobile() {
            return this.$store.state.isMobile
        },
        arrow() {
            return require(`@/assets/images/arrow_blue.svg`)
        },
    },
    created() {
        this.getFilters()
        const savedStatusFilter = localStorage.getItem('investProjectsStatusFilter')
        if (savedStatusFilter) {
            this.selected = savedStatusFilter
        }
    },
    mounted() {
        eventBus.$on(`update_filter_${this.model}_${this.page_name}`, () => {
            this.getFilters()
        })
        eventBus.$on('reload_filters', () => {
            this.reloadFilters()
        })
    },
    beforeDestroy() {
        eventBus.$off(`update_filter_${this.model}_${this.page_name}`)
        eventBus.$off('reload_filters')
    },
    methods: {
        handleOpenChange(open) {
            this.isOpen = open
        },
        setFilter(status) {
            this.selected = status
            localStorage.setItem('investProjectsStatusFilter', status === 'total' ? '' : status)
            this.$emit('setFilter', status)
        },
        reloadFilters() {
            this.selected = 'total'
            this.filters = []
            this.getFilters()
        },
        async getFilters() {
            try {
                this.loading = true
                const { data } = await this.$http.get(`/invest_projects_info/status_statistics/`)
                if(data) {
                    this.filters = data
                }
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
    .mobile-wrapper{
        .title{
            font-size: 16px;
            font-weight: 400;
        }
        .select::v-deep{
            margin-top: 10px;
            width: 100%;
            .ant-select-selection{
                background-color: rgba(29, 101, 192, 1);
                color: rgba(255, 255, 255, 1);
                font-size: 13px;
                font-weight: 400;
                line-height: 13px;
            }
            .ant-select-arrow {
                margin-top: -9px;
                right: 20px;
            }
            .ant-select-selection__rendered{
                margin-left: 20px;
            }
            .circle-button {
                width: 18px;
                height: 18px;
                font-size: 14px;
                background-color: rgb(255, 255, 255);
                border: none;
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                transform: rotate(-90deg);
                transition: transform 0.3s ease;
            }
            .circle-button.rotated {
                transform: rotate(0deg);
            }
        }
    }
    .wrapper{
        margin-bottom: 25px;
        display: flex;
        gap: 15px;
        .title{
            width: 115px;
            font-size: 16px;
            font-weight: 400;
            line-height: 17px;
            text-align: left;
        }
        .filters{
            display: flex;
            flex-wrap: wrap;
            gap: 5px;
        }
        .filter{
            border: 1px solid rgba(48, 54, 62, 1);
            border-radius: 4px;
            height: 36px;
            display: flex;
            align-items: center;
            font-size: 13px;
            font-weight: 400;
            line-height: 13px;
            padding-left: 15px;
            padding-right: 15px;
            cursor: pointer;
        }
        .selected{
            border-color: rgba(29, 101, 192, 1);
            background-color: rgba(29, 101, 192, 1);
            color: rgba(255, 255, 255, 1)
        }
    }
</style>
<style lang="scss">
.custom-dropdown .ant-select-dropdown-content{
    .ant-select-dropdown-menu-item{
        padding: 5px 20px;
    }
}
</style>