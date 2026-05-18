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
            <!-- <a-dropdown>
                <a-button size="large" class="mr-3 flex items-center">
                    {{$t('invest.download')}}
                    <i class="fi fi-rr-angle-small-down ml-1"></i>
                </a-button>
                <a-menu slot="overlay">
                    <a-menu-item :disabled="empty" key="download" @click="generateExcel()">
                        <i class="fi fi-rr-download mr-2"></i>{{$t('invest.downloadExport')}}
                    </a-menu-item>
                    <a-menu-item :disabled="empty" key="map" @click="generateExcel('roadmap')">
                        <i class="fi fi-rr-download mr-2"></i>{{$t('invest.roadmap')}}
                    </a-menu-item>
                </a-menu>
            </a-dropdown> -->
            <a-button type="primary" size="large" icon="plus" @click="addProject()">
                {{$t('invest.addProject')}}
            </a-button>
            <SettingsButton
                v-if="isTable"
                :pageName="page_name"
                class="ml-2" />
        </template>
        <Statistic />
        <div class="view" :class="isMobile && 'view--mobile'">
            <div class="status-filter">
                <StatusFilter
                    @setFilter="setFilter"/>
            </div>
            <div v-if="!isMobile" class="view-mode">
                <a-button class="view-mode__button" :type="isCards ? 'primary' : 'default'" icon="fi-rr-apps" flaticon @click="setViewMode('cards')"/>
                <a-button class="view-mode__button" :type="isTable ? 'primary' : 'default'" icon="fi-rr-list" flaticon @click="setViewMode('table')"/>
            </div>
        </div>
        <a-empty v-if="empty && isCards" :description="$t('invest.noProjects')" />
        <div v-if="isCards" :class="{'mobile-cards' : isMobile}">
            <a-checkbox-group
                v-model="chcGroup"
                name="investgroup">
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
                    <div class="list_grid grid-cols-1 2xl:grid-cols-2">
                        <Card
                            v-for="item in list.results"
                            :key="item.id"
                            :item2="item"
                            :item="item" />
                    </div>
                </template>
            </a-checkbox-group>
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
            <!--<transition name="button_fade">
                <div v-if="chcGroup.length" class="add_widget_float">
                    <a-badge
                        :number-style="{ backgroundColor: '#52c41a' }"
                        :count="chcGroup.length > 1 ? chcGroup.length : 0">
                        <a-button
                            flaticon
                            icon="fi-rr-download"
                            size="large">
                            {{$t('invest.downloadExport')}}
                        </a-button>
                    </a-badge>
                </div>
            </transition>-->
        </div>
        <div v-if="isTable" class="table">
            <Table
                :model="model"
                :page_name="page_name"
                :params="queryParams" />
        </div>
        <div v-if="isMobile" class="float_add">
            <div class="filter_slot">
                <PageFilter
                    :model="model"
                    :key="page_name"
                    :name="page_name"
                    size="large"
                    :page_name="page_name" />
            </div>
            <!-- <a-button
                flaticon
                :disabled="empty"
                shape="circle"
                size="large"
                class="mb-2"
                icon="fi-rr-download"
                @click="activity = true" />
            <a-button
                flaticon
                shape="circle"
                size="large"
                type="primary"
                icon="fi-rr-plus"
                @click="addProject()" /> -->
        </div>
        <!-- <ActivityDrawer
            v-if="isMobile"
            :vis="activity"
            useVis
            :cDrawer="closeDrawer">
            <ActivityItem @click="generateExcel()">
                <i class="fi fi-rr-download icon"></i>{{$t('invest.downloadExport')}}
            </ActivityItem>
            <ActivityItem @click="generateExcel('roadmap')">
                <i class="fi fi-rr-download icon"></i>{{$t('invest.roadmap')}}
            </ActivityItem>
        </ActivityDrawer> -->
    </ModuleWrapper>
</template>

<script>
// import { ActivityItem, ActivityDrawer } from '@/components/ActivitySelect'
import InfiniteLoading from 'vue-infinite-loading'
import eventBus from '@/utils/eventBus'

const messageKey = 'file_loading'
export default {
    name: 'InvestProjectsIndex',
    components: {
        // ActivityDrawer,
        // ActivityItem,
        Card: () => import('./components/Card.vue'),
        InfiniteLoading,
        MobileCard: () => import('./components/MobileCard.vue'),
        ModuleWrapper: () => import('@/components/ModuleWrapper/index.vue'),
        PageFilter: () => import('@/components/PageFilter'),
        SettingsButton: () => import('@/components/TableWidgets/SettingsButton'),
        Statistic: () => import('./components/Statistic.vue'),
        StatusFilter: () => import('./components/StatusFilter.vue'),
        Table: () => import('./components/Table')
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
        isTable() {
            return this.viewMode === 'table'
        }
    },
    data() {
        return {
            activity: false,
            chcGroup: [],
            empty: false,
            loading: false,
            model: 'invest_projects_info.InvestProjectInfoModel',
            page: 0,
            page_name: 'invest_project_list',
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
        const savedDisplayMode = localStorage.getItem('investProjectsDisplayMode')
        if (savedDisplayMode) {
            this.viewMode = savedDisplayMode
        }
        const savedStatusFilter = localStorage.getItem('investProjectsStatusFilter')
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
        setViewMode(mode='cards') {
            this.viewMode = mode
            localStorage.setItem('investProjectsDisplayMode', this.viewMode)
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
            this.listReload()
        },
        closeDrawer() {
            this.activity = false
        },
        async generateExcel(file_type = null) {
            try {
                this.$message.loading({ content: this.$t('invest.fileLoading'), key: messageKey })
                const params = {
                    exclude: this.chcGroup.length ? this.chcGroup.join(',') : '',
                    page_name: this.page_name
                }
                if(file_type)
                    params.file_type = file_type
                const { data } = await this.$http.get('/invest_projects_info/file/', {
                    responseType: 'blob',
                    params
                })

                const url = window.URL.createObjectURL(new Blob([data]))
                const link = document.createElement('a')
                link.href = url
                const fileName = file_type === 'roadmap' ? this.$t('invest.downloadRoadmap') : this.$t('invest.downloadFile')
                link.setAttribute('download', `${fileName} от ${this.$moment().format('DD.MM.YYYY HH:mm')}.XLSX`)
                document.body.appendChild(link)
                link.click()

                this.$message.success({ content: this.$t('invest.fileCreatedSuccess'), key: messageKey })
                this.chcGroup = []
            } catch(e) {
                console.log(e)
                this.$message.success({ content: this.$t('invest.fileCreationError'), key: messageKey })
            }
        },
        async getList($state) {
            if(!this.loading && this.list.next) {
                try {
                    this.loading = true
                    this.page += 1
                    let params = {
                        page: this.page,
                        page_size: 8,
                        page_name: this.page_name,
                    }
                    if(this.statusFilter) {
                        params.filters = {
                            status: this.statusFilter
                        }
                    }
                    const { data } = await this.$http.get('/invest_projects_info/', {
                        params: params
                    })

                    if(data) {
                        this.list.count = data.count
                        this.list.next = data.next
                    }

                    if(data?.results?.length)
                        this.list.results = this.list.results.concat(data.results)

                    if(this.page === 1 && !this.list.results.length) {
                        this.empty = true
                    }
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
            eventBus.$emit('add_invest_project')
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
        }
    },
    mounted() {
        eventBus.$on(`update_filter_${this.model}_${this.page_name}`, () => {
            this.listReload()
        })
        eventBus.$on('update_invest_list', () => {
            this.listReload()
        })
    },
    beforeDestroy() {
        eventBus.$off(`update_filter_${this.model}_${this.page_name}`)
        eventBus.$off('update_invest_list')
    }
}
</script>

<style lang="scss" scoped>
.view{
    display: grid;
    grid-template-columns: 1fr auto;
    grid-template-areas: "filter buttons";
    column-gap: 30px;
    .status-filter{
        grid-area: filter;
    }
    .view-mode{
        grid-area: buttons;
        display: grid;
        grid-template-columns: repeat(2, auto);
        column-gap: 5px;
        &__button::v-deep{
            height: 37px;
            width: 37px;
            .anticon{
                color: rgba(29, 101, 192, 1);
            }
        }
        .selected::v-deep{
            border-color: rgba(29, 101, 192, 1);
            background-color: rgba(29, 101, 192, 1);
            .anticon{
                color: rgb(255, 255, 255);
            }
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
    gap: 15px;
    @media (min-width: 1700px) {
        gap: 30px;
    }
}
.list_grid--mobile{
    display: grid;
    gap: 15px;

}
</style>