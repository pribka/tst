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
            <a-button
                v-if="selectedProject"
                type="ui" 
                ghost 
                flaticon
                :disabled="!calendarInfo"
                shape="circle"
                icon="fi-rr-plus"
                @click="addEvent()" />
        </template>
        <div v-if="!selectedProject" class="empty_project">
            <i class="fi fi-rr-settings-sliders"></i>
            <p>{{ $t('dashboard.projectEventEmptyMessage') }}</p>
            <a-button
                type="ui"
                size="small"
                @click="openProjectSetting()">
                {{ $t('dashboard.settings') }}
            </a-button>
        </div>
        <a-spin v-else :spinning="loading" class="e_widget_wrap">
            <RecycleScroller
                :items="events"
                size-field="height"
                :buffer="100"
                class="scroller"
                emitUpdate
                :item-size="54.04"
                key-field="id">
                <template #before>
                    <a-empty v-if="empty">
                        <template slot="description">
                            <p class="mb-2">{{ $t('dashboard.eventsAbsent') }}</p>
                            <a-button type="primary" :disabled="!calendarInfo" @click="addEvent()">
                                {{ $t('dashboard.addEvent') }}
                            </a-button>
                        </template>
                    </a-empty>
                </template>
                <template #default="{ item }">
                    <div 
                        :key="item.id" 
                        class="event_card truncate"
                        @click="openEvent(item.id)">
                        <div class="event_card__wrap truncate">
                            <div class="event_line" :style="`background: ${item.color};`" />
                            <div class="mr-3 gray text-sm">
                                <span v-if="item.all_day">{{ $t('dashboard.allDay') }}</span>
                                <span v-else>{{ $moment(item.start_at).format('HH:mm') }} <template v-if="item.end_at">- {{ $moment(item.end_at).format('HH:mm') }}</template></span>
                            </div>
                            <div class="flex items-center truncate" :class="eventClosed(item) && 'opacity-70'">
                                <div class="event_drop_name truncate flex items-center" :class="eventClosed(item) && 'line-through'">
                                    <i v-if="item.meeting" class="fi fi-rr-video-camera-alt mr-1" :style="`color: ${item.color};`" />{{ item.name }}
                                </div>
                            </div>
                        </div>
                    </div>
                </template>
            </RecycleScroller>
        </a-spin>
    </WidgetWrapper>
</template>

<script>
import 'vue-virtual-scroller/dist/vue-virtual-scroller.css'
import { RecycleScroller } from 'vue-virtual-scroller'
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
        RecycleScroller,
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
            loading: false,
            selectedProject: null,
            calendarInfo: null,
            initComplete: false,
            events: [],
            empty: false
        }
    },
    created() {
        if(this.widget.random_settings?.related_object)
            this.selectedProject = this.widget.random_settings.related_object
        this.initComplete = true
        if(this.selectedProject) {
            this.getCalendarInfo()
            this.getEvents()
        }
    },
    watch: {
        selectedProject() {
            if(!this.initComplete)
                return
            this.saveProjectConfig()
            this.events = []
            this.empty = false
            this.calendarInfo = null
            if(this.selectedProject) {
                this.getCalendarInfo()
                this.getEvents()
            }
        }
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
        addEvent() {
            eventBus.$emit('open_event_form', 
                null, 
                null, 
                null, 
                this.calendarInfo, 
                'default')
        },
        async getCalendarInfo() {
            if(!this.selectedProject?.id)
                return
            try {
                const { data } = await this.$http.get(`calendars/related/${this.selectedProject.id}/`)
                if(data) {
                    this.calendarInfo = data
                }
            } catch(error) {
                errorHandler({ error, show: false })
            }
        },
        openEvent(id) {
            let query = Object.assign({}, this.$route.query)
            if(query.event && Number(query.event) !== id || !query.event) {
                query.event = id
                this.$router.push({query})
            }
        },
        eventClosed(event) {
            if(event.end_at) {
                return this.$moment(event.end_at).isBefore(this.$moment())
            } else {
                return this.$moment(event.all_day ? event.start_at : event.end_at).isBefore(this.$moment())
            }
        },
        async getEvents() {
            if(!this.selectedProject)
                return
            try {
                this.empty = false
                this.loading = true
                const startDate = this.$moment().set('hour', 0).set('minute', 1).set('second', 1).set('millisecond', 0).toISOString(true),
                    endDate = this.$moment().set('hour', 23).set('minute', 59).set('second', 59).set('millisecond', 59).toISOString(true),
                    params = {
                        start: startDate,
                        end: endDate,
                        related_object: this.selectedProject.id
                    }

                const { data } = await this.$http.get('/calendars/events/top/', {
                    params
                })
                if(data?.length) {
                    this.events = data
                } else {
                    this.empty = true
                }
            } catch(error) {
                errorHandler({error, show: false})
            } finally {
                this.loading = false
            }
        },
        deleteEventHandler(id) {
            if(this.events?.length) {
                const index = this.events.findIndex(f => f.id === id)
                if(index !== -1) {
                    this.events.splice(index, 1)
                }
            }
            if(!this.events?.length) {
                this.empty = true
            }
        }
    },
    mounted() {
        eventBus.$on('header_event_update', () => {
            this.getEvents()
        })
        eventBus.$on('delete_event', id => {
            this.deleteEventHandler(id)
        })
    },
    beforeDestroy() {
        eventBus.$off('header_event_update')
        eventBus.$off('delete_event')
    }
}
</script>

<style lang="scss" scoped>
.e_widget_wrap{
    height: 100%;
    &::v-deep{
        .scroller,
        .ant-spin-container{
            height: 100%;
        }
    }
}
.event_card{
    padding-bottom: 10px;
    cursor: pointer;
    &__wrap{
        position: relative;
        padding-left: 15px;
        padding-top: 2px;
        padding-bottom: 2px;
    }
    .event_line{
        height: 100%;
        width: 4px;
        border-radius: 4px;
        position: absolute;
        left: 0;
        top: 0;
    }
}
.mobile_widget{
    .scroller{
        height: 350px;
    }
}
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
</style>
