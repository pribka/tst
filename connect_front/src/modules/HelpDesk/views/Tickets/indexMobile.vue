<template>
    <ModuleWrapper
        :pageTitle="pageTitle"
        :headerBg="!isMobile">
        <!--<div class="mb-3">
            <MyOrgSelect
                :orgInit="orgInit"
                :setOrgInit="setOrgInit" />
        </div>-->
        <div
            v-if="empty"
            class="mt-5">
            <a-empty :description="$t('meeting.noData')" />
        </div>
        <RequestCard
            routerKey="ticketView"
            v-for="item in list.results"
            :key="item.id"
            :item="item" />
        <infinite-loading
            ref="list_infinity"
            @infinite="getList"
            :identifier="infiniteId"
            v-bind:distance="10">
            <div
                slot="spinner"
                class="flex items-center justify-center inf_spinner">
                <a-spin />
            </div>
            <div slot="no-more"></div>
            <div slot="no-results"></div>
        </infinite-loading>
        <div
            class="float_add">
            <div class="filter_slot">
                <PageFilter
                    :model="initPageModel"
                    :key="initPageName"
                    size="large"
                    :popoverMaxWidth="400"
                    :page_name="initPageName" />
            </div>
            <a-button
                flaticon
                shape="circle"
                size="large"
                type="primary"
                icon="fi-rr-plus"
                @click="addRequestTicket()" />
        </div>
    </ModuleWrapper>
</template>

<script>
import eventBus from '@/utils/eventBus'
export default {
    components: {
        PageFilter: () => import('@/components/PageFilter'),
        ModuleWrapper: () => import('@/components/ModuleWrapper/index.vue'),
        InfiniteLoading: () => import('vue-infinite-loading' ),
        RequestCard: () => import('../../components/Request/RequestCard.vue'),
        //MyOrgSelect: () => import('../../components/Request/MyOrgSelect.vue')
    },
    computed: {
        apiRoute() {
            return this.$store.state.navigation?.apiRoute || []
        },
        pageTitle() {
            return this.$route?.meta?.title || ''
        },
        isMobile() {
            return this.$store.state.isMobile
        },
        initPageModel() {
            return 'help_desk.HelpDeskTicketModel'
        },
        initPageName() {
            return 'help_desk.HelpDeskTicketModel_page'
        },
    },
    data() {
        return {
            orgInit: false,
            loading: false,
            page: 0,
            empty: false,
            infiniteId: this.initPageName,
            list: {
                results: [],
                next: true,
                count: 0
            }
        }
    },
    methods: {
        setOrgInit(init) {
            this.orgInit = init
        },
        addRequestTicket() {
            eventBus.$emit('helpdesc_add_tickets')
        },
        listReload() {
            this.$nextTick(() => {
                this.page = 0
                this.empty = false
                this.list = {
                    results: [],
                    next: true,
                    count: 0
                }
                this.$refs['list_infinity'].stateChanger.reset()
            })
        },
        async getList($state) {
            if(!this.loading && this.list.next) {
                try {
                    this.loading = true
                    this.page += 1
                    const { data } = await this.$http.get('/help_desk/tickets/', {
                        params: {
                            page: this.page,
                            page_size: 15,
                            page_name: this.initPageName,
                            model: this.initPageModel
                        }
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
        }
    },
    mounted() {
        eventBus.$on(`update_filter_${this.initPageModel}_${this.initPageName}`, () => this.listReload())
        eventBus.$on(`update_filter_${this.initPageName}`, () => this.listReload())
    },
    beforeDestroy() {
        eventBus.$off(`update_filter_${this.initPageModel}_${this.initPageName}`)
        eventBus.$off(`update_filter_${this.initPageName}`)
    }
}
</script>