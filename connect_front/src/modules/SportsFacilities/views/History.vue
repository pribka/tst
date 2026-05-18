<template>
    <div>
        <div class="mb-10" style="max-width: 600px;">
            <PageFilter 
                :model="model"
                :key="page_name"
                size="large"
                :injectSelectParams="{
                    related_object: $route.params.id
                }"
                :page_name="page_name" />
        </div>
        <a-empty v-if="empty" :description="$t('sports.noHistory')" />
        <a-timeline :mode="timelineMode" :pending="loading" class="project_timeline">
            <a-timeline-item 
                v-for="time in list.results" 
                :key="time.id">
                <template slot="dot">
                    <div class="dot" />
                </template>
                <div class="flex timeline_item w-full mb-2">
                    <div class="timeline_card">
                        <div class="timeline_card__header">
                            <div class="date">{{ $moment(time.action_date).format('DD.MM.YYYY') }}</div>
                            <div class="author md:flex items-center">
                                <div class="mb-1 md:mb-0 md:mr-2">{{ $t('sports.changeAuthor') }}</div>
                                <Profiler :user="time.author" :avatarSize="18" />
                            </div>
                        </div>
                        <div v-if="time.object_property" class="timeline_card__body">
                            <div class="prp_list">
                                <div class="prp_list__item">
                                    <div class="name">
                                        {{ time.object_property.name }}:
                                    </div>
                                    <div class="value">
                                        {{ time.after }}
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </a-timeline-item>
        </a-timeline>
        <infinite-loading 
            ref="timeline_infinity"
            @infinite="getList"
            v-bind:distance="10">
            <div slot="spinner"></div>
            <div slot="no-more"></div>
            <div slot="no-results"></div>
        </infinite-loading>
    </div>
</template>

<script>
import { mapState } from 'vuex'
import InfiniteLoading from 'vue-infinite-loading'
import eventBus from '@/utils/eventBus'
export default {
    components: {
        InfiniteLoading,
        PageFilter: () => import('@/components/PageFilter')
    },
    computed: {
        ...mapState({
            windowWidth: state => state.windowWidth
        }),
        timelineMode() {
            if(this.windowWidth > 1100) {
                return 'alternate'
            } else {
                return 'left'
            }
        }
    },
    data() {
        return {
            list: {
                results: [],
                next: true,
                count: 0
            },
            page: 0,
            empty: false,
            loading: false,
            model: "change_history.ChangeHistoryModel",
            page_name: 'sports_timeline_history'
        }
    },
    methods: {
        async getList($state) {
            if(!this.loading && this.list.next) {
                try {
                    this.loading = true
                    this.page += 1
                    const { data } = await this.$http.get('/change_history/', {
                        params: {
                            page: this.page,
                            page_size: 8,
                            page_name: this.page_name,
                            related_object: this.$route.params.id
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
        },
        listReload() {
            this.$nextTick(() => {
                this.list = {
                    results: [],
                    next: true,
                    count: 0
                }
                this.page = 0
                this.empty = false
                this.$refs['timeline_infinity'].stateChanger.reset()
            })
        }
    },
    mounted() {
        eventBus.$on(`update_filter_${this.model}`, () => {
            this.listReload()
        })
    },
    beforeDestroy() {
        eventBus.$off(`update_filter_${this.model}`)
    }
}
</script>

<style lang="scss" scoped>
.timeline_card{
    background: #fff;
    padding: 15px;
    border-radius: var(--borderRadius);
    text-align: left;
    margin-top: -10px;
    position: relative;
    @media (min-width: 768px) {
        background: #eff2f5;
        padding: 20px;
        min-width: 450px;
    }
    &__header{
        padding-bottom: 10px;
        margin-bottom: 10px;
        border-bottom: 1px solid #d7dadc;
        @media (min-width: 768px) {
            padding-bottom: 20px;
         margin-bottom: 20px;
        }
        .author{
            font-size: 16px;
            color: #000000;
        }
    }
    .prp_list{
        &__item{
            @media (min-width: 768px) {
                display: flex;
                align-items: center;
            }
            .name{
                min-width: 210px;
                max-width: 210px;
                color: #000000;
                opacity: 0.6;
                padding-right: 20px;
                word-break: break-word;
                @media (max-width: 767px) {
                    padding-bottom: 5px;
                }
                @media (min-width: 768px) {
                    padding-right: 20px;
                }
            }
        }
    }
}
.project_timeline{
    .dot{
        background: #1D65C0;
        width: 20px;
        height: 20px;
        border-radius: 50%;
    }
    &::v-deep{
        .ant-timeline-item-head{
            @media (max-width: 767px) {
                background: #eff2f5;
            }
        }
        .ant-timeline-item{
            &.ant-timeline-item-right{
                .timeline_item{
                    justify-content: flex-end;
                    padding-right: 20px;
                }
                .timeline_card{
                    &::after {
                        left: 100%;
                        top: 22px;
                        border: solid transparent;
                        content: "";
                        height: 0;
                        width: 0;
                        position: absolute;
                        pointer-events: none;
                        border-color: rgba(239, 242, 245, 0);
                        border-left-color: #eff2f5;
                        border-width: 10px;
                        margin-top: -10px;
                    }
                }
            }
            &.ant-timeline-item-left{
                .timeline_item{
                    padding-left: 20px;
                }
                .timeline_card{
                    &::after {
                        right: 100%;
                        top: 22px;
                        border: solid transparent;
                        content: "";
                        height: 0;
                        width: 0;
                        position: absolute;
                        pointer-events: none;
                        border-color: rgba(239, 242, 245, 0);
                        border-right-color: #eff2f5;
                        border-width: 10px;
                        margin-top: -10px;
                    }
                }
            }
        }
    }
}
</style>