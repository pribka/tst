<template>
    <div class="flex-grow request_list">
        <div v-if="empty" class="mt-5">
            <a-empty :description="$t('meeting.noData')" />
        </div>

        <RequestCard
            v-for="item in list.results"
            :key="item.id"
            routerKey="ticketView"
            :item="item" />

        <infinite-loading
            ref="list_infinity"
            @infinite="getList"
            :identifier="infiniteId"
            v-bind:distance="10">
            <div slot="spinner" class="flex items-center justify-center inf_spinner">
                <a-spin />
            </div>
            <div slot="no-more"></div>
            <div slot="no-results"></div>
        </infinite-loading>
    </div>
</template>

<script>
import { errorHandler } from '@/utils/index.js'
export default {
    components: {
        RequestCard: () => import('@apps/HelpDesk/components/Request/RequestCard.vue'),
        InfiniteLoading: () => import('vue-infinite-loading')
    },
    props: {
        chat_uid: {
            type: String,
            default: null
        },
        isUserSupport: {
            type: Boolean,
            required: true
        }
    },
    data() {
        return {
            loading: false,
            page: 0,
            empty: false,
            list: {
                results: [],
                next: true,
                count: 0
            }
        }
    },
    computed: {
        endpoint() {
            if (this.chat_uid) return 'help_desk/tickets/for_client/list/?chat=' + this.chat_uid
            return 'help_desk/tickets/'
        },
        initPageModel() {
            if (this.isUserSupport === true) return 'help_desk.HelpDeskTicketModel'
            if (this.isUserSupport === false) return 'help_desk.HelpDeskForClientTicketModel'
            return null
        },
        initPageName() {
            if (this.isUserSupport === true) return 'chat_help_desk.HelpDeskTicketModel_page'
            if (this.isUserSupport === false) return 'chat_help_desk.HelpDeskForClientTicketModel_page'
            return null
        },
        tableType() {
            if (this.isUserSupport === true) return 'helpdesk_tickets'
            if (this.isUserSupport === false) return 'helpdesk_request_tickets'
            return null
        },
        infiniteId() {
            return `${this.initPageName}_${this.tableType}_${this.chat_uid || 'all'}`
        }
    },
    methods: {
        listReload() {
            this.$nextTick(() => {
                this.page = 0
                this.empty = false
                this.list = {
                    results: [],
                    next: true,
                    count: 0
                }
                if (this.$refs.list_infinity) this.$refs.list_infinity.stateChanger.reset()
            })
        },
        async getList($state) {
            if (this.loading || !this.list.next) return

            try {
                this.loading = true
                this.page += 1

                const { data } = await this.$http.get(this.endpoint, {
                    params: {
                        page: this.page,
                        page_size: 15,
                        page_name: this.initPageName,
                        model: this.initPageModel
                    }
                })

                if (data) {
                    this.list.count = data.count
                    this.list.next = data.next
                }

                if (data?.results?.length) this.list.results = this.list.results.concat(data.results)

                if (this.page === 1 && !this.list.results.length) this.empty = true

                if (this.list.next) $state.loaded()
                else $state.complete()
            } catch (error) {
                errorHandler({error, show: false})
                $state.complete()
            } finally {
                this.loading = false
            }
        }
    }
}
</script>

<style lang="scss" scoped>
.request_list{
    &::v-deep{
        .request_card{
            transform: scale(1)!important;
            background: #f7f9fc;
        }
    }
}
</style>