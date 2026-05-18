<template>
    <WidgetWrapper 
        :widget="widget"
        :class="isMobile && 'mobile_widget'">
        <DynamicScroller
            :items="list.results"
            :min-item-size="60"
            class="scroller_block workgroups_widgets"
            :emit-update="true">
            <template #before>
                <a-empty 
                    v-if="empty" 
                    :description="$t('dashboard.teamsAbsent')" />
            </template>
            <template #default="{ item, index, active }">
                <DynamicScrollerItem
                    :item="item"
                    :active="active"
                    :size-dependencies="[
                        item.name
                    ]"
                    :data-index="index"
                    :data-active="active">
                    <div class="pb-2">
                        <MobileCard 
                            listProject
                            :item="item" />
                    </div>
                </DynamicScrollerItem>
            </template>
            <template #after>
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
            </template>
        </DynamicScroller>
    </WidgetWrapper>
</template>

<script>
import eventBus from '@/utils/eventBus'
import { DynamicScroller, DynamicScrollerItem } from 'vue-virtual-scroller'
import 'vue-virtual-scroller/dist/vue-virtual-scroller.css'
import { errorHandler } from '@/utils/index.js'
export default {
    props: {
        widget: {
            type: Object,
            required: true
        }
    },
    components: {
        DynamicScroller,
        DynamicScrollerItem,
        InfiniteLoading: () => import('vue-infinite-loading'),
        MobileCard: () => import('@apps/Groups/components/MobileCard.vue'),
        WidgetWrapper: () => import('../WidgetWrapper.vue')
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
                            is_project: 0,
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