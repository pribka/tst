<template>
    <WidgetWrapper 
        :widget="widget"
        :class="isMobile && 'mobile_widget'">
        <div ref="scroller" class="scroller_block">
            <a-empty 
                v-if="empty" 
                :description="$t('dashboard.projectsAbsent')" />

            <MobileCard 
                v-for="item in list.results"
                listProject
                :key="item.id"
                :item="item" />

            <infinite-loading 
                ref="infiniteLoading"
                @infinite="getTaskList"
                :identifier="infiniteId"
                :distance="10">
                <div 
                    slot="spinner"
                    class="flex items-center justify-center inf_spinner">
                    <a-spin size="small" />
                </div>
                <div slot="no-more"></div>
                <div slot="no-results"></div>
            </infinite-loading>
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
        MobileCard: () => import('@apps/Projects/components/MobileCard.vue')
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
            empty: false,
            model: 'workgroups.WorkgroupModel',
            list: {
                results: [],
                next: true,
                count: 0
            }
        }
    },
    methods: {
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
                    this.loading = true
                    this.page += 1
                    const { data } = await this.$http.get('/work_groups/workgroups/', {
                        params: {
                            page: this.page,
                            page_size: 15,
                            is_project: 1,
                            my: 1,
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
                } catch(error) {
                    errorHandler({error, show: false})
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
    },
    beforeDestroy() {
        eventBus.$off(`update_filter_${this.model}_${this.widget.page_name || this.widget.id}`)
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
.mobile_widget{
    .scroller_block{
        height: 350px;
    }
}
</style>