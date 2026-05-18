<template>
    <div class="nav_calendar" ref="navCalendar">
        <a-dropdown 
            :getPopupContainer="getPopupContainer"
            placement="bottomLeft"
            :trigger="['hover']">
            <div class="wrapper select-none">
                <div class="current" @click="openCalendar()">
                    <i class="fi fi-rr-calendar mr-2"/> {{ $moment().format('dd, DD.MM.YYYY') }}
                    <div v-if="events.length" class="events_badge">
                        {{events.length}}
                    </div>
                </div>
                <!--<div v-if="loading" class="calendar_events">
                    <a-skeleton 
                        active 
                        size="small" 
                        :title="{ width: '70%' }"
                        :paragraph="{ rows: 1, width: '100%' }" />
                </div>
                <template v-else>
                    <div v-if="firstEvent" class="calendar_events">
                        <div class="label truncate" @click="openEvent(firstEvent.id)">{{ firstEvent.name }}</div>
                        <div class="event_dates flex items-center justify-between">
                            <div v-if="firstEvent.all_day" @click="openEvent(firstEvent.id)">
                                {{ $t('calendar.all_day') }}
                            </div>
                            <div v-else @click="openEvent(firstEvent.id)">
                                {{ firstEventDays }}
                            </div>
                            <div v-if="events.length" style="color: #000;" class="pl-3 text-xs" @click="openCalendar()">
                                {{ eventsMoreLabel() }}
                            </div>
                            <div v-else @click="addEvent()" class="pl-3 flex items-center add_i_event">
                                <i class="fi fi-rr-add" />
                            </div>
                        </div>
                    </div>
                    <div v-else class="calendar_events">
                        <div class="label" @click="openCalendar()">{{ $t('calendar.calendar') }}</div>
                        <div class="add_event" @click="addEvent()">
                            <i class="fi fi-rr-add mr-1" />{{ $t('calendar.add_event') }}
                        </div>
                    </div>
                </template>-->
            </div>
            <a-menu 
                v-if="events.length" 
                slot="overlay">
                <a-menu-item v-for="event in events" :key="event.id" :title="event.name.length > 25 && event.name" @click="openEvent(event.id)">
                    <div class="mr-3 gray text-sm">
                        <span v-if="event.all_day">{{ $t('calendar.all_day') }}</span>
                        <span v-else>
                            {{ $moment(event.start_at).format('HH:mm') }} 
                            <template v-if="event.end_at">- {{ $moment(event.end_at).format('HH:mm') }}</template>
                        </span>
                    </div>
                    <div class="flex items-center" :class="eventClosed(event) && 'opacity-70'">
                        <a-badge :color="event.color" />
                        <div class="event_drop_name truncate" :class="event.is_finished && 'line-through'">
                            {{ event.name }}
                        </div>
                    </div>
                </a-menu-item>
                <template v-if="events.length > 10">
                    <a-menu-divider />
                    <a-menu-item class="gray flex items-center justify-center" @click="openCalendar()">
                        <i class="fi fi-rr-calendar-lines mr-2"></i> {{ $t('calendar.all_events') }}
                    </a-menu-item>
                </template>
            </a-menu>
        </a-dropdown>
        <div 
            class="add_event ml-3" 
            v-tippy
            :content="$t('calendar.add_event_tooltip')"
            @click="addEvent()">
            <i class="fi fi-rr-plus" />
        </div>
    </div>
</template>

<script>
import eventBus from '@/utils/eventBus'
import { declOfNum } from '@/utils/utils.js'
export default {
    computed: {
        firstEventDays() {
            if (!this.firstEvent) return ''

            if (this.firstEvent.end_at) {
                if (this.$moment().isSame(this.$moment(this.firstEvent.start_at), 'day')) {
                    if (this.$moment(this.firstEvent.start_at).isSame(this.$moment(this.firstEvent.end_at), 'day')) {
                        return `${this.$moment(this.firstEvent.start_at).format('HH:mm')} - ${this.$moment(this.firstEvent.end_at).format('HH:mm')}`
                    } else {
                        return this.$t('calendar.start_in', { time: this.$moment(this.firstEvent.start_at).format('HH:mm') })
                    }
                } else {
                    if (this.$moment().isSame(this.$moment(this.firstEvent.end_at), 'day')) {
                        return this.$t('calendar.until', { time: this.$moment(this.firstEvent.end_at).format('HH:mm') })
                    } else {
                        return this.$t('calendar.whole_day')
                    }
                }
            } else {
                if (this.$moment().isSame(this.$moment(this.firstEvent.start_at), 'day')) {
                    return this.$moment(this.firstEvent.start_at).format('HH:mm')
                } else {
                    return this.$t('calendar.whole_day')
                }
            }
        }
    },
    data() {
        return {
            loading: false,
            events: [],
            firstEvent: null
        }
    },
    created() {
        this.getEvents()
    },
    methods: {
        eventClosed(event) {
            if(event.end_at) {
                return this.$moment(event.end_at).isBefore(this.$moment())
            } else {
                return this.$moment(event.all_day ? event.start_at : event.end_at).isBefore(this.$moment())
            }
        },
        openEvent(id) {
            let query = Object.assign({}, this.$route.query)
            if(query.event && Number(query.event) !== id || !query.event) {
                query.event = id
                this.$router.push({query})
            }
        },
        getPopupContainer() {
            return this.$refs.navCalendar
        },
        eventsMoreLabel() {
            const word = declOfNum(this.events.length, [this.$t('calendar.event_name'), this.$t('calendar.event_name'), this.$t('calendar.event_name')])
            return this.$t('calendar.events_more_template', { count: this.events.length, word })
        },
        async getEvents() {
            try {
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
                    const dEvents = data
                    // this.firstEvent = dEvents.shift()
                    this.events = dEvents
                }
            } catch(e) {
                console.log(e)
            } finally {
                this.loading = false
            }
        },
        deleteEventHandler(id) {
            if(this.firstEvent?.id === id) {
                if(this.events?.length) {
                    const dEvents = JSON.parse(JSON.stringify(this.events))
                    this.firstEvent = dEvents.shift()
                    this.events = dEvents
                } else {
                    this.firstEvent = null
                }
            } else {
                if(this.events?.length) {
                    const index = this.events.findIndex(f => f.id === id)
                    if(index !== -1) {
                        this.events.splice(index, 1)
                    }
                }
            }
        },
        openCalendar() {
            this.$router.push({ name: 'calendar' })
        },
        addEvent() {
            eventBus.$emit('open_event_form', 
                null, 
                null, 
                null, 
                null, 
                'default')
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
.event_drop_name{
    max-width: 200px;
}
.add_event{
    color: #000;
    text-align: left;
    display: flex;
    align-items: center;
    transition: all 0.3s cubic-bezier(0.645, 0.045, 0.355, 1);
    font-size: 15px;
    cursor: pointer;
    opacity: 0;
    &:hover{
        color: var(--blue);
    }
}
.nav_calendar{
    position: relative;
    margin-right: 70px;
    display: flex;
    align-items: center;
    &:hover{
        .add_event{
            opacity: 1;
        }
    }
    &::v-deep{
        .ant-dropdown{
            width: 100%;
            min-width: 230px;
            .ant-dropdown-menu{
                max-height: 400px;
                overflow-y: auto;
            }
        }
    }
    .link{
        display: block;
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
    }
    .current{
        background: #fff;
        height: 32px;
        border-radius: 8px;
        padding-left: 15px;
        padding-right: 15px;
        display: flex;
        align-items: center;
        color: #1D1F23;
        font-size: 15px;
        text-transform: capitalize;
        .events_badge{
            background: #f3a719;
            color: #000;
            border-radius: 3px;
            height: 20px;
            min-width: 20px;
            margin-left: 10px;
            display: flex;
            align-items: center;
            justify-content: center;
            padding-left: 5px;
            padding-right: 5px;
        }
    }
    .add_i_event{
        transition: all 0.3s cubic-bezier(0.645, 0.045, 0.355, 1);
        &:hover{
            color: var(--blue);
        }
    }
    .wrapper{
        display: flex;
        align-items: center;
        cursor: pointer;
        overflow: hidden;
    }
    .calendar_events{
        padding-left: 13px;
        display: flex;
        align-items: center;
        flex-direction: column;
        justify-content: flex-start;
        &::v-deep{
            .ant-skeleton{
                width: 100px;
                .ant-skeleton-title{
                    height: 10px;
                    margin: 0px;
                    border-radius: var(--borderRadius);
                }
                .ant-skeleton-paragraph{
                    margin-top: 9px;
                    li{
                        height: 10px;
                        width: 100%;
                        border-radius: var(--borderRadius);
                    }
                }
            }
        }
        .event_dates{
            text-align: left;
            color: var(--gray);
            width: 100%;
        }
        .label{
            color: #000000;
            font-size: 15px;
            line-height: 18px;
            width: 100%;
            text-align: left;
            max-width: 160px;
        }
    }
}
</style>