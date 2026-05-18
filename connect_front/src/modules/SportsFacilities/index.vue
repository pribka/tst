<template>
    <ModuleWrapper :pageTitle="pageTitle" :headerBg="!isMobile" class="project_list">
        <template v-if="!isMobile" v-slot:h_left>
            <PageFilter
                :model="model"
                :key="page_name"
                size="large"
                :page_name="page_name" />
        </template>
        <template v-if="!isMobile" v-slot:h_right>
            <a-button 
                type="primary" 
                ghost
                :loading="reportLoading"
                class="mr-1"
                @click="downloadReport()">
                {{ $t('sports.downloadReport') }}
            </a-button>
            <a-button 
                v-if="addCheck" 
                type="primary" 
                icon="plus" 
                @click="addProject()">
                {{$t('sports.add')}}
            </a-button>
            <SettingsButton
                v-if="isTable"
                :pageName="page_name"
                size="default"
                class="ml-2" />
        </template>
        <Statistic 
            v-if="!isMap"
            ref="statisticRef" 
            :page_name="page_name"
            :statusFilter="statusFilter" />
        <div class="view mb-3" :class="isMobile && 'view--mobile'">
            <div class="status-filter" :class="!isMobile && 'dc_filter'">
                <StatusFilter
                    :page_name="page_name"
                    @setFilter="setFilter"/>
            </div>
            <div v-if="!isMobile" class="view-mode">
                <Segmented
                    v-model="viewMode" 
                    :options="viewModes"
                    localStorageKey="sportsFacilitiesDisplayMode"
                    useLocalStorageSave />
            </div>
        </div>
        <template v-if="isMap">
            <MapView 
                :page_name="page_name" 
                :statusFilter="statusFilter"
                :model="model" />
        </template>
        <template v-else>
            <a-empty v-if="empty && isCards" :description="$t('sports.noProjects')" />
            <div v-if="isCards" :class="{'mobile-cards' : isMobile}">
                <template v-if="isMobile">
                    <div class="list_grid--mobile grid-cols-1">
                        <MobileCard
                            v-for="item in list.results"
                            :key="item.id"
                            :item2="item"
                            :item="item" />
                    </div>
                </template>
                <template v-else>
                    <div class="list_grid grid-cols-1 lg:grid-cols-2 2xl:grid-cols-3">
                        <Card
                            v-for="item in list.results"
                            :key="item.id"
                            :item2="item"
                            :item="item" />
                    </div>
                </template>
                <infinite-loading
                    ref="project_infinity"
                    @infinite="getList"
                    v-bind:distance="10">
                    <div
                        slot="spinner"
                        class="flex items-center justify-center inf_spinner">
                        <a-spin />
                    </div>
                    <div slot="no-more"></div>
                    <div slot="no-results"></div>
                </infinite-loading>
                <div v-if="chcGroup.length" class="float_dummy"></div>
            </div>
            <div v-if="isTable" class="table">
                <Table
                    :model="model"
                    :page_name="page_name"
                    :params="queryParams" />
            </div>
        </template>
        <div v-if="isMobile" class="float_add">
            <a-button
                flaticon
                shape="circle"
                size="large"
                class="fixed_button"
                :icon="isMap ? 'fi-rr-list' : 'fi-rr-map-marker'"
                @click="setViewMode(isMap ? 'cards' : 'map')" />
            <a-button
                flaticon
                shape="circle"
                size="large"
                class="fixed_button"
                :loading="reportLoading"
                icon="fi-rr-chart-histogram"
                @click="downloadReport()" />
            <div class="filter_slot">
                <PageFilter
                    :model="model"
                    :key="page_name"
                    :name="page_name"
                    size="large"
                    :page_name="page_name" />
            </div>
            <a-button
                v-if="addCheck"
                flaticon
                shape="circle"
                size="large"
                type="primary"
                icon="fi-rr-plus"
                @click="addProject()" />
        </div>
        <StatisticDrawer />
    </ModuleWrapper>
</template>

<script>
import eventBus from '@/utils/eventBus'
export default {
    name: 'SportsFacilitiesIndex',
    components: {
        ModuleWrapper: () => import('@/components/ModuleWrapper/index.vue'),
        PageFilter: () => import('@/components/PageFilter'),
        SettingsButton: () => import('@/components/TableWidgets/SettingsButton'),
        StatusFilter: () => import('./components/StatusFilter.vue'),
        Card: () => import('./components/Card.vue'),
        InfiniteLoading: () => import('vue-infinite-loading'),
        MobileCard: () => import('./components/MobileCard.vue'),
        Table: () => import('./components/Table'),
        StatisticDrawer: () => import('./components/StatisticDrawer'),
        Statistic: () => import('./components/Statistic.vue'),
        MapView: () => import('./components/MapView/Map.vue'),
        Segmented: () => import('@apps/UIModules/Segmented')
    },
    computed: {
        pageTitle() {
            return this.$route?.meta?.title || ''
        },
        isMobile() {
            return this.$store.state.isMobile
        },
        isCards() {
            return this.viewMode === 'cards'
        },
        isMap() {
            return this.viewMode === 'map'
        },
        isTable() {
            return this.viewMode === 'table'
        },
        getRouteInfo() {
            return this.$store.getters['navigation/getRouteInfo'](this.$route.name)
        },
        addCheck() {
            return this.getRouteInfo?.pageActions?.add || false
        }
    },
    data() {
        return {
            viewModes: [
                {
                    key: 'map',
                    title: this.$t('sports.Map')
                },
                {
                    key: 'cards',
                    title: this.$t('sports.List')
                },
                {
                    key: 'table',
                    title: this.$t('sports.Table')
                }
            ],
            reportLoading: false,
            activity: false,
            chcGroup: [],
            empty: false,
            loading: false,
            model: 'sports_facilities_info.SportFacilityInfoModel',
            page: 0,
            page_name: 'sports_facilities_list',
            statusFilter: '',
            viewMode: 'cards',
            queryParams: {},
            list: {
                results: [],
                next: true,
                count: 0
            }
        }
    },
    created() {
        const savedDisplayMode = localStorage.getItem('sportsFacilitiesDisplayMode')
        if (savedDisplayMode) {
            this.viewMode = savedDisplayMode
        }
        const savedStatusFilter = localStorage.getItem('sportsFacilitiesStatusFilter')
        if (savedStatusFilter === null || savedStatusFilter === '') {
            this.statusFilter = ''
        } else {
            this.statusFilter = savedStatusFilter
            this.queryParams.filters = {
                status: this.statusFilter
            }
        }
    },
    methods: {
        async downloadReport() {
            try {
                this.reportLoading = true
                const { data } = await this.$http.get('/sports_facilities/report/', {
                    responseType: 'blob'
                })
                if(data) {
                    const url = window.URL.createObjectURL(new Blob([data]))
                    const link = document.createElement('a')
                    link.href = url
                    link.setAttribute('download', `${this.$t('sports.reportFileName', { date: this.$moment().format("DD-MM-YYYY HH:mm") })}.xlsx`)
                    document.body.appendChild(link)
                    link.click()
                    link.remove()
                }
            } catch(e) {
                console.log(e)
            } finally {
                this.reportLoading = false
            }
        },
        setViewMode(mode='cards') {
            this.viewMode = mode
            localStorage.setItem('sportsFacilitiesDisplayMode', this.viewMode)
            this.listReload()
        },
        setFilter(status) {
            if(status === 'total') {
                this.statusFilter = ''
                delete this.queryParams.filters
            } else {
                this.statusFilter = status
                this.queryParams.filters = {
                    status: status
                }
            }
            eventBus.$emit(`update_map_${this.model}_${this.page_name}`)
            this.listReload()
        },
        closeDrawer() {
            this.activity = false
        },
        async getList($state) {
            if(!this.loading && this.list.next) {
                try {
                    this.loading = true
                    this.page += 1
                    let params = {
                        page: this.page,
                        page_size: 9,
                        page_name: this.page_name,
                    }
                    if(this.statusFilter) {
                        params.filters = {
                            status: this.statusFilter
                        }
                    }
                    const { data } = await this.$http.get('/sports_facilities/', {
                        params: params
                    })

                    if(data) {
                        this.list.count = data.count
                        this.list.next = data.next
                    }

                    if(data?.results?.length)
                        this.list.results = this.list.results.concat(data.results)

                    if(this.page === 1 && !this.list.results.length)
                        this.empty = true
                    if(this.list.next)
                        $state.loaded()
                    else
                        $state.complete()
                } catch(e) {
                    console.log(e)
                } finally {
                    this.loading = false
                }
            }
        },
        addProject() {
            eventBus.$emit('add_sports_facilities')
        },
        listReload() {
            if(this.isCards) {
                this.chcGroup = []
                this.page = 0
                this.empty = false
                this.list = {
                    results: [],
                    next: true,
                    count: 0
                }
                this.$nextTick(() => {
                    this.$refs['project_infinity'].stateChanger.reset()
                })
            } else if(this.isTable) {
                eventBus.$emit(`update_filter_${this.model}`)
            }
            this.$nextTick(() => {
                if(this.$refs.statisticRef)
                    this.$refs.statisticRef.getStat()
            })
        }
    },
    mounted() {
        eventBus.$on(`update_filter_${this.model}_${this.page_name}`, () => {
            this.listReload()
        })
        eventBus.$on('update_sports_facilities_list', () => {
            this.listReload()
        })
    },
    beforeDestroy() {
        eventBus.$off(`update_filter_${this.model}_${this.page_name}`)
        eventBus.$off('update_sports_facilities_list')
    }
}
</script>

<style lang="scss" scoped>
.view{
    display: flex;
    align-items: center;
    justify-content: space-between;
    .status-filter{
        grid-area: filter;
        &.dc_filter{
            max-height: 36px;
        }
    }
}
.view--mobile{
    grid-template-columns: 1fr;
    column-gap: unset;
    margin-bottom: 15px;
}
.mobile-cards{
    .ant-checkbox-group{
        width: 100%;
    }
}
.table{
    display: flex;
    flex-direction: column;
    flex-grow: 1;
}
.project_list{
    .button_fade-enter-active, .button_fade-leave-active {
        transition: all 0.3s;
    }
    .button_fade-enter, .button_fade-leave-to {
        opacity: 0;
        transform: translateY(30px);
    }
}
.float_dummy{
    min-height: 60px;
}
.add_widget_float{
    --safe-area-inset-bottom: env(safe-area-inset-bottom);
    position: fixed;
    bottom: calc(65px + var(--safe-area-inset-bottom));
    left: 50%;
    z-index: 50;
    display: flex;
    flex-direction: column;
    margin-left: -100px;
    @media (min-width: 768px) {
        bottom: calc(15px + var(--safe-area-inset-bottom));
    }
    &::v-deep{
        .ant-btn{
            border-radius: 30px;
            padding-left: 20px;
            padding-right: 20px;
            width: 200px;
            border-color: #000000;
            color: #000000;
            -webkit-backdrop-filter: saturate(180%) blur(20px);
            backdrop-filter: saturate(180%) blur(20px);
            background: rgba(251, 251, 253, 0.8);
        }
    }
}
.list_grid{
    display: grid;
    gap: 10px;
    @media (min-width: 1700px) {
        gap: 15px;
    }
}
.list_grid--mobile{
    display: grid;
    gap: 10px;

}
</style>