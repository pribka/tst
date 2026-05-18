<template>
    <WidgetWrapper 
        :widget="widget" 
        :class="isMobile && 'mobile_widget'">
        <template slot="actions">
            <ProjectSelect
                ref="projectSelect"
                usePopupContainer
                inputType="avatar"
                :customPopupContainer="customPopupContainer"
                v-model="selectedProject" />
        </template>
        <div class="scroller_block meetings_widget">
            <div
                v-if="!selectedProject"
                class="empty_project">
                <i class="fi fi-rr-settings-sliders"></i>
                <p>{{ $t('dashboard.projectTaskEmptyMessage') }}</p>
                <a-button
                    type="ui"
                    size="small"
                    @click="openProjectSetting()">
                    {{ $t('dashboard.settings') }}
                </a-button>
            </div>
            <template v-else>
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
        WidgetWrapper: () => import('../WidgetWrapper.vue'),
        ProjectSelect: () => import("@apps/DrawerSelect/ProjectSelect.vue")
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
            selectedProject: null,
            initComplete: false,
            model: 'meetings.PlannedMeetingModel',
            list: {
                results: [],
                next: true,
                count: 0
            }
        }
    },
    watch: {
        selectedProject() {
            if(!this.initComplete)
                return
            this.saveProjectConfig()
            this.resetList()
        }
    },
    created() {
        if(this.widget.random_settings?.related_object)
            this.selectedProject = this.widget.random_settings.related_object
        this.initComplete = true
    },
    methods: {
        customPopupContainer() {
            return document.body
        },
        async saveProjectConfig() {
            try {
                const randomSettings = {
                    related_object: this.selectedProject || null,
                    related_model: this.selectedProject ? 'workgroups.WorkgroupModel' : null
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
        openProjectSetting() {
            this.$nextTick(() => {
                if(this.$refs.projectSelect)
                    this.$refs.projectSelect.openSelect()
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
            if(!this.selectedProject) {
                $state.complete()
                return
            }
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
                            project: this.selectedProject.id
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
.empty_project{
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
