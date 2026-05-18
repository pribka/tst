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
                @click="addEvent()" />
        </template>
        <a-spin :spinning="loading" class="e_widget_wrap">
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
                            <a-button type="primary" @click="addEvent()">
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
        WidgetWrapper: () => import('../WidgetWrapper.vue')
    },
    computed: {
        isMobile() {
            return this.$store.state.isMobile
        }
    },
    data() {
        return {
            loading: false,
            events: [],
            empty: false
        }
    },
    created() {
        this.getEvents()
    },
    methods: {
        addEvent() {
            eventBus.$emit('open_event_form', 
                null, 
                null, 
                null, 
                null, 
                'default')
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
            try {
                this.empty = false
                this.loading = true
                const startDate = this.$moment().set('hour', 0).set('minute', 1).set('second', 1).set('millisecond', 0).toISOString(true),
                    endDate = this.$moment().set('hour', 23).set('minute', 59).set('second', 59).set('millisecond', 59).toISOString(true),
                    params = {
                        start: startDate,
                        end: endDate
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
</style>