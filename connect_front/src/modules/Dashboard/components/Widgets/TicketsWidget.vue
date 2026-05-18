<template>
    <WidgetWrapper 
        :widget="widget" 
        :class="isMobile && 'mobile_widget'">
        <template slot="actions">
            <a-button
                type="ui" 
                ghost 
                flaticon
                shape="circle"
                icon="fi-rr-plus"
                @click="addHandler()" />
        </template>
        <div class="scroller_block">
            <a-empty 
                v-if="empty" 
                :description="$t('no_data')" />
            <RequestCard
                v-for="item in list.results"
                :key="item.id"
                routerKey="ticketView"
                :item="item" />
            <infinite-loading 
                v-if="loadingRun"
                ref="infiniteLoading"
                @infinite="getList"
                :identifier="infiniteId"
                :distance="1">
                <div 
                    slot="spinner"
                    class="flex items-center justify-center inf_spinner">
                    <a-spin size="small" />
                </div>
                <div slot="no-more"></div>
                <div slot="no-results"></div>
            </infinite-loading>
            <template v-else>
                <div v-if="loading" class="flex items-center justify-center">
                    <a-spin size="small" />
                </div>
            </template>
        </div>
    </WidgetWrapper>
</template>

<script>
import eventBus from '@/utils/eventBus'
import { errorHandler } from '@/utils/index.js'
export default {
    props: {
        widget: {
            type: Object,
            required: true
        }
    },
    components: {
        RequestCard: () => import('@apps/HelpDesk/components/Request/RequestCard.vue'),
        WidgetWrapper: () => import('../WidgetWrapper.vue'),
        InfiniteLoading: () => import('vue-infinite-loading')
    },
    computed: {
        isMobile() {
            return this.$store.state.isMobile
        }
    },
    data() {
        return {
            infiniteId: new Date(),
            loading: false,
            page: 0,
            loadingRun: true,
            empty: false,
            page_name: 'help_desk.HelpDeskTicketModel_page',
            model: 'help_desk.HelpDeskTicketModel',
            list: {
                results: [],
                next: true,
                count: 0
            }
        }
    },
    methods: {
        addHandler() {
            eventBus.$emit('helpdesc_add_tickets')
        },
        updateTicketInList(ticket) {
            if(!ticket?.id || !this.list.results?.length) {
                return
            }

            const index = this.list.results.findIndex(item => item.id === ticket.id)
            if(index !== -1) {
                this.$set(this.list.results, index, ticket)
            }
        },
        handleTicketUpdateSocket(payload) {
            this.updateTicketInList(payload?.data || payload)
        },
        resetList() {
            this.$nextTick(() => {
                this.page = 0
                this.empty = false
                this.list = {
                    results: [],
                    next: true,
                    count: 0
                }
                this.$refs.infiniteLoading.stateChanger.reset()
            })
        },
        async getList($state) {
            if(!this.loading && this.list.next) {
                try {
                    this.loadingRun = false
                    this.loading = true
                    this.page += 1
                    const { data } = await this.$http.get('/help_desk/tickets/', {
                        params: {
                            page: this.page,
                            page_size: 15,
                            page_name: this.widget.page_name || this.widget.id
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

                    setTimeout(() => {
                        this.$nextTick(() => {
                            this.loadingRun = true
                        })
                    }, 200)
                } catch(error) {
                    $state.complete()
                    errorHandler({error})
                } finally {
                    this.loading = false
                }
            } else {
                $state.complete()
            }
        }
    },
    mounted() {
        eventBus.$on(`update_filter_${this.model}_${this.widget.page_name || this.widget.id}`, () => {
            this.resetList()
        })
        eventBus.$on(`update_filter_${this.model}_${this.page_name}`, () => {
            this.resetList()
        })
        eventBus.$on('UPDATE_TICKET_KANBAN', kanbanObj => {
            this.updateTicketInList(kanbanObj)
        })
        this.$socket.client.on('ticket_update', this.handleTicketUpdateSocket)
    },
    beforeDestroy() {
        eventBus.$off(`update_filter_${this.model}_${this.widget.page_name || this.widget.id}`)
        eventBus.$off(`update_filter_${this.model}_${this.page_name}`)
        eventBus.$off('UPDATE_TICKET_KANBAN')
        this.$socket.client.off('ticket_update', this.handleTicketUpdateSocket)
    }
}
</script>

<style lang="scss" scoped>
.scroller_block{
    overflow-y: auto;
    height: 100%;
    &::v-deep{
        .request_card{
            background: #f7f9fc;
            box-shadow: initial!important;
            transform: initial!important;
            &:not(:last-child){
                margin-bottom: 10px;
            }
        }
    }
}
.mobile_widget{
    .scroller_block{
        height: 350px;
    }
}
</style>
