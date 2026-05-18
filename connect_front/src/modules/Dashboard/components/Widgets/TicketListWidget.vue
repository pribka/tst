<template>
    <WidgetWrapper 
        :widget="widget" 
        :class="isMobile && 'mobile_widget'">
        <template slot="actions">
            <TicketSelect
                ref="ticketSelect"
                usePopupContainer
                :customPopupContainer="customPopupContainer"
                inputType="icon"
                :placeholder="$t('dashboard.select')"
                v-model="selectedTicket" />
            <a-button
                v-if="selectedTicket"
                type="ui" 
                ghost 
                flaticon
                shape="circle"
                icon="fi-rr-plus"
                @click="addTask()" />
        </template>
        <div ref="scroller" class="scroller_block">
            <div
                v-if="!selectedTicket"
                class="empty_ticket">
                <i class="fi fi-rr-settings-sliders"></i>
                <p>{{ $t('dashboard.ticketTaskEmptyMessage') }}</p>
                <a-button
                    type="ui"
                    size="small"
                    @click="openTicketSetting()">
                    {{ $t('dashboard.settings') }}
                </a-button>
            </div>
            <template v-else>
                <a-empty 
                    v-if="empty" 
                    :description="$t('dashboard.tasks_empty')" />

                <KanbanItem 
                    v-for="item in list.results"
                    :key="item.id"
                    :item="item" 
                    :isScrolling="false"
                    activeMobile
                    responsiveDeadline
                    :myTaskEnabled="false"
                    showStatus />

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
        WidgetWrapper: () => import('../WidgetWrapper.vue'),
        InfiniteLoading: () => import('vue-infinite-loading'),
        KanbanItem: () => import('@apps/vue2TaskComponent/components/Kanban/Item.vue'),
        TicketSelect: () => import('@apps/DrawerSelect/TicketSelect.vue')
    },
    computed: {
        isMobile() {
            return this.$store.state.isMobile
        },
        ticketPageName() {
            if(!this.selectedTicket?.id)
                return ''
            return `tasks.TaskModel.Tickets_${this.selectedTicket.id}`
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
            selectedTicket: null,
            prevTicketPageName: '',
            loadingRun: true,
            empty: false,
            task_type: 'task',
            model: 'tasks.TaskModel',
            initComplete: false,
            list: {
                results: [],
                next: true,
                count: 0
            }
        }
    },
    sockets: {
        task_update({ data }) {
            if(data)
                this.updateTaskInList(data)
        }
    },
    watch: {
        selectedTicket() {
            if(!this.initComplete)
                return
            this.bindTicketEvents()
            this.saveTicketConfig()
            this.resetList()
        }
    },
    created() {
        if(this.widget.random_settings?.related_object)
            this.selectedTicket = this.widget.random_settings.related_object
        this.initComplete = true
    },
    methods: {
        customPopupContainer() {
            return document.body
        },
        bindTicketEvents() {
            if(this.prevTicketPageName)
                eventBus.$off(`update_filter_${this.prevTicketPageName}`, this.ticketFilterHandler)
            if(this.ticketPageName)
                eventBus.$on(`update_filter_${this.ticketPageName}`, this.ticketFilterHandler)
            this.prevTicketPageName = this.ticketPageName
        },
        ticketFilterHandler() {
            this.resetList()
        },
        openTicketSetting() {
            this.$nextTick(() => {
                if(this.$refs.ticketSelect?.openSelect)
                    this.$refs.ticketSelect.openSelect()
            })
        },
        async saveTicketConfig() {
            try {
                const randomSettings = {
                    related_object: this.selectedTicket || null,
                    related_model: this.selectedTicket ? 'help_desk_tickets' : null
                }
                await this.$http.patch(`/widgets/user_widgets_on_desktop/${this.widget.id}/`, {
                    random_settings: randomSettings
                })
                this.$store.commit('dashboard/UPDATE_ACTIVE_WIDGET', {
                    widgetId: this.widget.id, 
                    key: 'random_settings', 
                    value: randomSettings
                })
            } catch(error) {
                errorHandler({ error, show: false })
            }
        },
        addTask() {
            if(!this.selectedTicket)
                return
            const form = {
                reason: this.selectedTicket.id
            }
            this.$store.commit('task/SET_TASK_TYPE', 'task')
            this.$store.commit('task/SET_PAGE_NAME', {
                pageName: this.ticketPageName
            })
            eventBus.$emit(this.isMobile ? 'ADD_WATCH' : 'add_task_modal_watch', {
                type: 'add_task',
                data: form
            })
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
                this.infiniteId = new Date()
                if(this.$refs.infiniteLoading)
                    this.$refs.infiniteLoading.stateChanger.reset()
            })
        },
        async getTaskList($state) {
            if(!this.selectedTicket) {
                $state.complete()
                return
            }
            if(!this.loading && this.list.next) {
                try {
                    this.loadingRun = false
                    this.loading = true
                    this.page += 1
                    const { data } = await this.$http.get('/tasks/task/list/', {
                        params: {
                            page: this.page,
                            page_size: 15,
                            page_name: this.ticketPageName,
                            filters: {
                                reason: this.selectedTicket.id
                            }
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
        },
        updateTaskInList(task) {
            if(!task?.id || !this.list?.results?.length)
                return

            const index = this.list.results.findIndex(item => item.id === task.id)
            if(index === -1)
                return

            this.$set(this.list.results, index, {
                ...this.list.results[index],
                ...task
            })
        }
    },
    mounted() {
        eventBus.$on(`update_filter_${this.model}_${this.widget.page_name || this.widget.id}`, () => {
            this.resetList()
        })
        eventBus.$on(`TASK_CREATED_${this.task_type}_${this.widget.page_name || this.widget.id}`, () => {
            this.resetList()
        })
        eventBus.$on("TASK_CREATED_task", () => {
            this.resetList()
        })
        this.bindTicketEvents()
    },
    beforeDestroy() {
        eventBus.$off(`update_filter_${this.model}_${this.widget.page_name || this.widget.id}`)
        eventBus.$off(`TASK_CREATED_${this.task_type}_${this.widget.page_name || this.widget.id}`)
        eventBus.$off("TASK_CREATED_task")
        if(this.prevTicketPageName)
            eventBus.$off(`update_filter_${this.prevTicketPageName}`, this.ticketFilterHandler)
    }
}
</script>

<style lang="scss" scoped>
.scroller_block{
    overflow-y: auto;
    height: 100%;
    &::v-deep{
        .kanban-card{
            margin-bottom: 0px;
        }
        .active_task{
            padding-bottom: 8px;
        }
    }
}
.empty_ticket{
    text-align: center;
    padding-top: 20px;
    i{
        font-size: 42px;
        color: var(--gray);
    }
    p{
        margin-top: 15px;
        margin-bottom: 20px;
        max-width: 280px;
        margin-left: auto;
        margin-right: auto;
    }
}
.mobile_widget{
    .scroller_block{
        height: 350px;
    }
}
</style>
