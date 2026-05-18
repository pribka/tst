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
                @click="addRequest()" />
        </template>
        <div ref="scroller" class="scroller_block">
            <a-empty 
                v-if="empty" 
                :description="$t('no_data')" />

            <RequestCard
                routerKey="ticketView"
                v-for="item in list.results"
                :key="item.id"
                :page_name="page_name"
                :pageModel="model"
                :item="item" />

            <infinite-loading
                v-if="loadingRun"
                ref="infiniteLoading"
                @infinite="getTaskList"
                :identifier="infiniteId"
                :immediate-check="false"
                :check-scrollbar="false"
                :distance="100">
                <div slot="spinner" class="flex items-center justify-center">
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
        RequestCard: () => import('@apps/RequestApprovals/components/RequestCard.vue'),
        WidgetWrapper: () => import('../WidgetWrapper.vue'),
        InfiniteLoading: () => import('vue-infinite-loading')
    },
    computed: {
        isMobile() {
            return this.$store.state.isMobile
        },
        scrollerWrapper() {
            return this.$refs.scroller
        }
    },
    data() {
        return {
            infiniteId: new Date(),
            loading: false,
            page: 0,
            page_name: "page_list_processes.WorkflowRequestModel",
            loadingRun: true,
            empty: false,
            model: 'processes.WorkflowRequestModel',
            list: {
                results: [],
                next: true,
                count: 0
            }
        }
    },
    methods: {
        addRequest() {
            eventBus.$emit('add_request_approvals')
        },
        updateRequestInList(request) {
            if(!request?.id || !this.list.results?.length) {
                return
            }

            const index = this.list.results.findIndex(item => item.id === request.id)
            if(index !== -1) {
                this.$set(this.list.results, index, request)
            }
        },
        handleWorkflowRequestUpdateSocket(payload) {
            this.updateRequestInList(payload?.data || payload)
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
        async getTaskList($state) {
            if(!this.loading && this.list.next) {
                try {
                    this.loadingRun = false
                    this.loading = true
                    this.page += 1
                    const { data } = await this.$http.get('/processes/workflow_requests/', {
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
                    errorHandler({error})
                } finally {
                    this.loading = false
                }
            } else
                $state.complete()
        }
    },
    mounted() {
        eventBus.$on(`update_filter_${this.model}_${this.widget.page_name || this.widget.id}`, () => {
            this.resetList()
        })
        eventBus.$on(`update_filter_${this.model}_${this.page_name}`, () => {
            this.resetList()
        })
        this.$socket.client.on('workflow_request_update', this.handleWorkflowRequestUpdateSocket)
    },
    beforeDestroy() {
        eventBus.$off(`update_filter_${this.model}_${this.widget.page_name || this.widget.id}`)
        eventBus.$off(`update_filter_${this.model}_${this.page_name}`)
        this.$socket.client.off('workflow_request_update', this.handleWorkflowRequestUpdateSocket)
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
        }
    }
}
.mobile_widget{
    .scroller_block{
        height: 350px;
    }
}
</style>
