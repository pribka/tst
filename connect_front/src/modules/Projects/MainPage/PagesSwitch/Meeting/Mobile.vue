<template>
    <div class="project-meeting-mobile">
        <div v-if="empty" class="mt-5">
            <a-empty :description="$t('meeting.noData')" />
        </div>
        <MeetingCard
            v-for="item in meetings.results"
            :key="item.id"
            :page_name="pageName"
            :item="item" />
        <infinite-loading
            ref="meetingInfinity"
            :identifier="infiniteId"
            :distance="10"
            @infinite="getMeetings">
            <div slot="spinner" class="flex items-center justify-center inf_spinner">
                <a-spin />
            </div>
            <div slot="no-more"></div>
            <div slot="no-results"></div>
        </infinite-loading>
    </div>
</template>

<script>
import eventBus from '@/utils/eventBus'
import { buildMeetingRequestParams } from './filterParams'

export default {
    name: 'ProjectMeetingMobile',
    components: {
        InfiniteLoading: () => import('vue-infinite-loading'),
        MeetingCard: () => import('@apps/vue2MeetingComponent/components/MeetingCard.vue')
    },
    props: {
        id: {
            type: [String, Number],
            required: true
        },
        pageName: {
            type: String,
            required: true
        }
    },
    data() {
        return {
            loading: false,
            page: 0,
            empty: false,
            infiniteId: this.pageName,
            meetings: {
                results: [],
                next: true,
                count: 0
            }
        }
    },
    methods: {
        async getMeetings($state) {
            if (this.loading || !this.meetings.next) {
                $state.complete()
                return
            }

            try {
                this.loading = true
                this.page += 1
                const params = buildMeetingRequestParams({
                    filterState: this.$store.state.filter,
                    pageName: this.pageName,
                    projectId: this.id,
                    page: this.page,
                    pageSize: 15
                })
                const { data } = await this.$http.get('/meetings/', { params })

                if (data) {
                    this.meetings.count = data.count
                    this.meetings.next = data.next
                }

                if (data?.results?.length)
                    this.meetings.results = this.meetings.results.concat(data.results)

                if (this.page === 1 && !this.meetings.results.length)
                    this.empty = true

                if (this.meetings.next)
                    $state.loaded()
                else
                    $state.complete()
            } catch (error) {
                console.log(error)
                $state.complete()
            } finally {
                this.loading = false
            }
        },
        resetList() {
            this.$nextTick(() => {
                this.page = 0
                this.empty = false
                this.meetings = {
                    results: [],
                    next: true,
                    count: 0
                }
                this.infiniteId = new Date().getTime()
                if (this.$refs.meetingInfinity)
                    this.$refs.meetingInfinity.stateChanger.reset()
            })
        }
    },
    mounted() {
        eventBus.$on(`update_filter_meetings.PlannedMeetingModel_${this.pageName}`, this.resetList)
        eventBus.$on(`update_filter_${this.pageName}`, this.resetList)
        eventBus.$on('reload_meetings_list', this.resetList)
    },
    beforeDestroy() {
        eventBus.$off(`update_filter_meetings.PlannedMeetingModel_${this.pageName}`, this.resetList)
        eventBus.$off(`update_filter_${this.pageName}`, this.resetList)
        eventBus.$off('reload_meetings_list', this.resetList)
    }
}
</script>

<style lang="scss" scoped>
.project-meeting-mobile {
    padding: 0 0 15px;
    min-height: 100%;
}
</style>
