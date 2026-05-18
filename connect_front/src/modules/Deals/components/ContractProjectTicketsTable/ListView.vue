<template>
    <div class="contract_project_tickets_mobile">
        <div v-if="empty && !loading" class="flex justify-center mb-2">
            <a-empty :description="$t('deals_contracts.requests_linked_empty')" />
        </div>
        <RequestCard
            v-for="item in list.results"
            :key="item.id"
            routerKey="ticketView"
            :item="item" />
        <infinite-loading
            ref="infiniteLoading"
            :identifier="infiniteId"
            :distance="10"
            @infinite="infiniteHandler">
            <div slot="spinner" class="flex items-center justify-center inf_spinner pb-2">
                <a-spin />
            </div>
            <div slot="no-more"></div>
            <div slot="no-results"></div>
        </infinite-loading>
    </div>
</template>

<script>
import InfiniteLoading from 'vue-infinite-loading'
import { errorHandler } from '@/utils/index.js'

export default {
    name: 'ContractProjectTicketsListView',
    components: {
        InfiniteLoading,
        RequestCard: () => import('@apps/HelpDesk/components/Request/RequestCard.vue'),
    },
    props: {
        projectId: {
            type: [String, Number],
            required: true,
        },
        contractId: {
            type: String,
            required: true,
        },
        customerCardId: {
            type: [String, Number],
            default: null,
        },
        pageName: {
            type: String,
            default: '',
        },
    },
    data() {
        return {
            list: {
                count: 0,
                next: true,
                results: [],
            },
            page: 0,
            pageSize: 15,
            empty: false,
            loading: false,
            infiniteId: Date.now(),
        }
    },
    computed: {
        normalizedPageName() {
            return this.pageName || `deals.contract_project_tickets_${this.contractId}_${this.projectId}`
        },
    },
    watch: {
        projectId() {
            this.loadData()
        },
        contractId() {
            this.loadData()
        },
    },
    methods: {
        loadData() {
            this.$nextTick(() => {
                this.page = 0
                this.empty = false
                this.list = {
                    count: 0,
                    next: true,
                    results: [],
                }
                this.infiniteId = Date.now()
                this.$refs.infiniteLoading?.stateChanger?.reset()
            })
        },
        async infiniteHandler($state) {
            if (this.loading || !this.list.next) return
            if (!this.contractId || !this.projectId) {
                this.empty = true
                this.list.next = false
                $state.complete()
                return
            }
            try {
                this.loading = true
                this.page += 1
                const { data } = await this.$http.get('/help_desk/tickets/', {
                    params: {
                        contract: this.contractId,
                        project: this.projectId,
                        page: this.page,
                        page_size: this.pageSize,
                        page_name: this.normalizedPageName,
                        model: 'help_desk.HelpDeskTicketModel',
                    },
                })
                const results = Array.isArray(data?.results) ? data.results : []
                this.list.count = data?.count || results.length
                this.list.next = Boolean(data?.next)
                if (results.length) {
                    this.list.results = this.list.results.concat(results)
                }
                if (this.page === 1 && !this.list.results.length) {
                    this.empty = true
                }
                if (this.list.next) $state.loaded()
                else $state.complete()
            } catch (error) {
                errorHandler({ error, show: false })
                $state.complete()
            } finally {
                this.loading = false
            }
        },
    },
}
</script>

<style lang="scss" scoped>
.contract_project_tickets_mobile {
    min-height: 70vh;
}
</style>
