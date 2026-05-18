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
                @click="$store.commit('meeting/SET_EDIT_MODAL', { show: true, model: model })" />
        </template>
        <div class="scroller_block meetings_widget">
            <a-empty 
                v-if="empty" 
                :description="$t('dashboard.meetingsAbsent')" />

            <MeetingCard
                v-for="item in list.results"
                :key="item.id"
                :page_name="widget.page_name || widget.id"
                :showActions="false"
                :item="item" />

            <infinite-loading 
                v-if="loadingRun"
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
        InfiniteLoading: () => import('vue-infinite-loading'),
        MeetingCard: () => import('@apps/vue2MeetingComponent/components/MeetingCard.vue'),
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
            loadingRun: true,
            loading: false,
            page: 0,
            empty: false,
            model: 'meetings.PlannedMeetingModel',
            list: {
                results: [],
                next: true,
                count: 0
            }
        }
    },
    methods: {
        getTodayRangeParams() {
            return {
                date_begin_gte: this.$moment().startOf('day').format(),
                date_begin_lte: this.$moment().endOf('day').format()
            }
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
                    const { data } = await this.$http.get('/meetings/', {
                        params: {
                            page: this.page,
                            page_size: 15,
                            page_name: this.widget.page_name || this.widget.id,
                            ...this.getTodayRangeParams()
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
        eventBus.$on('reload_meetings_list', () => {
            this.resetList()
        })
    },
    beforeDestroy() {
        eventBus.$off(`update_filter_${this.model}_${this.widget.page_name || this.widget.id}`)
        eventBus.$off('reload_meetings_list')
    }
}
</script>

<style lang="scss" scoped>
.meetings_widget{
    &::v-deep{
        .meeting_card{
            &:not(:last-child){
                margin-bottom: 10px;
            }
            &.touch{
                box-shadow: initial;
                transform: scale(1);
            }
        }
    }
}
.scroller_block{
    overflow-y: auto;
    height: 100%;
}
.mobile_widget{
    .scroller_block{
        height: 350px;
    }
}
</style>
