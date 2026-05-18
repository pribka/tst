<template>
    <div class="h-full" ref="bodyWrapper">
        <a-row :gutter="{xs: 15, md: 20, lg: 30, xxl: 30}" class="h-full">
            <a-col
                :xs="24"
                :md="24"
                :xl="24"
                :xxl="24"
                class="h-full flex flex-wrap flex-col">
                <div ref="clientHeaderWrapper" class="flex items-center gap-5 mb-3">
                    <PageFilter
                        :model="listModel"
                        :key="listPageName"
                        size="large"
                        :excludeFields="excludeFields"
                        :getPopupContainer="getPopupContainer"
                        :page_name="listPageName" />
                </div>
                <component
                    :is="taskComponent"
                    ref="taskListWidget"
                    :client="client"
                    :model="listModel"
                    :actions="actions"
                    :page_name="listPageName" />
            </a-col>
        </a-row>
    </div>
</template>

<script>
import eventBus from '@/utils/eventBus'
export default {
    computed:{
        taskComponent() {
            return () => import('./components/Table.vue')
        }
    },
    components: {
        DrawerAside: () => import('@apps/UIModules/DrawerAside'),
        InfiniteLoading: () => import('vue-infinite-loading'),
        CardKanban: () => import('./components/TicketCard.vue'),
        ChatList: () => import('../../Tickets/TicketDrawer/components/ChatList/index.vue'),
        TicketInfo: () => import('./components/TicketInfo.vue'),
        PageFilter: () => import('@/components/PageFilter')
    },
    props: {
        client: {
            type: Object,
            required: true
        },
        actions: {
            type: Object,
            default: () => null
        },
    },
    data() {
        return {
            loading: false,
            selectedTicket: null,
            selectedKey: null,
            page: 0,
            showAside: false,
            empty: false,
            listModel: 'help_desk.HelpDeskTicketModel',
            page_name: 'tickets_history_tab',
            listPageName: `list_help_desk.tickets_${this.client.id}`,
            excludeFields: [],
            chatLoading: false,
            list: {
                next: true,
                count: 0,
                results: []
            }
        }
    },
    methods: {
        getPopupContainer() {
            return this.$refs.clientHeaderWrapper
        },
        changeShowAside(value) {
            this.showAside = value
        },
        selectTicket(ticket) {
            if(this.selectedTicket?.id === ticket?.id) {
                this.selectedTicket = null
                this.selectedKey = null
            } else {
                this.getTicket(ticket)
            }
        },
        async getTicket(ticket) {
            try {
                this.chatLoading = true
                const { data } = await this.$http.get(`/help_desk/tickets/${ticket.id}/`)
                if(data) {
                    this.selectedTicket = data
                    this.selectedKey = data.id
                }
            } catch(e) {
                console.log(e)
            } finally {
                this.chatLoading = false
            }
        },
        async getList($state) {
            if(!this.loading && this.list.next) {
                try {
                    this.loading = true
                    this.page += 1
                    const params = {
                        page: this.page,
                        page_size: 10,
                        page_name: this.page_name,
                        customer_card: this.client.id
                    }
                    const { data } = await this.$http.get('/help_desk/tickets/', { params })

                    if(data) {
                        this.list.count = data.count
                        this.list.next = data.next
                    }

                    if(data.results?.length) {
                        this.list.results = this.list.results.concat(data.results)
                    }

                    if(this.page === 1 && !this.list.results.length) {
                        this.empty = true
                    }

                    if (!data.next) {
                        $state.complete()
                    } else {
                        $state.loaded()
                    }
                } catch (error) {
                    this.$message.error(this.$t('helpdesk.error'))
                } finally {
                    this.loading = false
                }
            } else {
                $state.complete()
            }
        },
        listReload() {
            this.selectedTicket = null
            this.selectedKey = null
            this.page = 0
            this.empty = false
            this.list = {
                next: true,
                count: 0,
                results: []
            }
            this.$nextTick(() => {
                this.$refs['tickets_infinity'].stateChanger.reset()
            })
        }
    },
    mounted() {
        eventBus.$on(`update_filter_${this.listModel}_${this.page_name}`, () => {
            this.listReload()
        })
    },
    beforeDestroy() {
        eventBus.$off(`update_filter_${this.listModel}_${this.page_name}`)
    }
}
</script>

<style lang="scss" scoped>
.tickets_aside{
    overflow-y: auto;
    &::v-deep{
        .filter_pop_wrapper{
            max-width: 100%;
            min-width: 100%;
        }
    }
}
.chat_spinning{
    height: 100%;
    &::v-deep{
        .ant-spin-container{
            height: 100%;
        }
    }
}
.tickets_list{
    padding-top: 15px;
    margin-top: 15px;
    border-top: 1px solid var(--border2);
}
</style>