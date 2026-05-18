<template>
    <div>
        <div v-if="showPageHeader && pageH1Title" class="flex items-center justify-between gap-2 m_page_head">
            <h1 class="m_page_title">
                {{ pageH1Title }}
            </h1>
            <HelpButton v-if="showHelpButton" partCode="meetings" type="button" />
        </div>
        <div 
            v-if="empty" 
            class="mt-5">
            <a-empty :description="$t('meeting.noData')" />
        </div>
        <component
            :is="resolvedItemComponent"
            v-for="item in displayedMeetings" 
            :key="item.id" 
            v-bind="buildItemProps(item)"
            @select="$emit('select', $event)" />
        <infinite-loading 
            ref="meeting_infinity"
            @infinite="getMeetings"
            :identifier="infiniteId"
            :force-use-infinite-wrapper="infiniteWrapperSelector"
            v-bind:distance="10">
            <div 
                slot="spinner"
                class="flex items-center justify-center inf_spinner">
                <a-spin />
            </div>
            <div slot="no-more"></div>
            <div slot="no-results"></div>
        </infinite-loading>
    </div>
</template>

<script>
import eventBusGlobal from '@/utils/eventBus'
import eventBus from '../utils/eventBus'
export default {
    name: 'MeetingTypeList',
    components: {
        HelpButton: () => import('@apps/Support/components/HelpButton.vue'),
        InfiniteLoading: () => import('vue-infinite-loading')
    },
    props: {
        pageModel: {
            type: String,
            default: 'meetings.PlannedMeetingModel'
        },
        page_name: {
            type: String,
            default: 'page_list_meetings.PlannedMeetingModel'
        },
        isScrolling: {
            type: Boolean,
            default: false
        },
        itemComponent: {
            type: [Object, Function, String],
            default: null
        },
        itemPropsResolver: {
            type: Function,
            default: () => ({})
        },
        prependItems: {
            type: Array,
            default: () => []
        },
        showPageHeader: {
            type: Boolean,
            default: true
        },
        showHelpButton: {
            type: Boolean,
            default: true
        },
        infiniteWrapperSelector: {
            type: String,
            default: ''
        }
    },
    computed: {
        pageH1Title() {
            return this.$route?.meta?.title ? this.$route.meta.title : null
        },
        resolvedItemComponent() {
            return this.itemComponent || (() => import('./MeetingCard.vue'))
        },
        displayedMeetings() {
            const uniq = new Map()

            ;[...this.prependItems, ...this.meetings.results].forEach(item => {
                if (item?.id && !uniq.has(item.id)) {
                    uniq.set(item.id, item)
                }
            })

            return Array.from(uniq.values())
        }
    },
    data() {
        return {
            loading: false,
            page: 0,
            empty: false,
            infiniteId: this.page_name,
            meetings: {
                results: [],
                next: true,
                count: 0
            }
        }
    },
    methods: {
        buildItemProps(item) {
            return {
                item,
                isScrolling: this.isScrolling,
                page_name: this.page_name,
                ...this.itemPropsResolver(item)
            }
        },
        async getMeetings($state) {
            if(!this.loading && this.meetings.next) {
                try {
                    this.loading = true
                    this.page += 1
                    const { data } = await this.$http.get('/meetings/', {
                        params: {
                            page: this.page,
                            page_size: 15,
                            page_name: this.page_name,
                            model: this.pageModel
                        }
                    })

                    if(data) {
                        this.meetings.count = data.count
                        this.meetings.next = data.next
                    }

                    if(data?.results?.length)
                        this.meetings.results = this.meetings.results.concat(data.results)

                    if(this.page === 1 && !this.displayedMeetings.length) {
                        this.empty = true
                    }  
                    if(this.meetings.next)
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
        endConference(id) {
            const index = this.meetings.results.findIndex(f => f.id === id)
            if(index !== -1)
                this.meetings.results[index].status = 'ended'
        },
        restartConference(id) {
            const index = this.meetings.results.findIndex(f => f.id === id)
            if(index !== -1)
                this.meetings.results[index].status = 'new'
        },
        listReload() {
            this.$nextTick(() => {
                this.page = 0
                this.empty = false
                this.meetings = {
                    results: [],
                    next: true,
                    count: 0
                }
                this.$refs['meeting_infinity'].stateChanger.reset()
            })
        }
    },
    mounted() {
        eventBusGlobal.$on(`update_filter_${this.pageModel}`, () => {
            this.listReload()
        })
        eventBus.$on(`reload_list_${this.page_name}`, (page_default = false) => {
            this.listReload()
        })
        eventBus.$on('reload_meetings_list',  (page_default = false) => {
            this.listReload()
        })
        eventBus.$on('END_CONFERENCE', id => {
            this.endConference(id)
        })
        eventBus.$on('RESTART_CONFERENCE', id => {
            this.restartConference(id)
        })
    },
    beforeDestroy() {
        eventBusGlobal.$off(`update_filter_${this.pageModel}`)
        eventBus.$off(`reload_list_${this.page_name}`)
        eventBus.$off('reload_meetings_list')
        eventBus.$off('END_CONFERENCE')
        eventBus.$off('RESTART_CONFERENCE')
    }
}
</script>
