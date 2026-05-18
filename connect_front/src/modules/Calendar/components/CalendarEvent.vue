<template>
    <div 
        class="event "
        :title="eventTitle"
        :class="[eventClosed && 'before_event', props.is_finished && 'finished_event', !isMobile && 'truncate']"
        :style="`border-color: ${event.backgroundColor}`">
        <div class="event_bg" :style="`background: ${event.backgroundColor}`"></div>
        <div v-if="activeType === 'dayGridMonth'" class="wrapper flex items-center wrapper_label">
            <i 
                v-if="props.meeting"
                class="fi fi-rr-video-camera-alt mr-1" />
            <span v-if="!event.allDay" class="mr-1">{{ startTime }}</span> <span class="e_title">{{ event.title }}</span>
        </div>
        <div 
            v-if="activeType === 'timeGridWeek' || activeType === 'timeGridDay'" 
            class="wrapper"
            :class="startEndDiff && 'flex items-center'">
            <div v-if="!event.allDay" :class="startEndDiff && 'mr-1'">
                {{ startTime }} <template v-if="endTime">- {{ endTime }}</template>
            </div>
            <div class="e_title wrapper_label">
                <i 
                    v-if="props.meeting"
                    class="fi fi-rr-video-camera-alt mr-1" />
                {{ event.title }}
            </div>
        </div>
        <div v-if="activeType === 'listWeek' || activeType === 'listMonth'" class="wrapper flex items-center">
            <span class="e_title wrapper_label">
                <i 
                    v-if="props.meeting"
                    class="fi fi-rr-video-camera-alt mr-1" />
                {{ event.title }}
            </span>
        </div>
    </div>
</template>

<script>
export default {
    props: {
        event: {
            type: Object,
            required: true
        },
        activeType: {
            type: String,
            required: true
        }
    },
    computed: {
        isMobile() {
            return this.$store.state.isMobile
        },
        eventTitle() {
            if(this.activeType === 'dayGridMonth') {
                return `${!this.event.allDay ? this.startTime : ''} ${this.event.title}`
            }
            if(this.activeType === 'timeGridWeek' || this.activeType === 'timeGridDay') {
                const endTimeText = !this.event.allDay && this.endTime ? ` - ${this.endTime}` : ''
                return `${!this.event.allDay ? this.startTime : ''}${endTimeText} ${this.event.title}`
            }

            return this.event.title
        },
        startTime() {
            return this.$moment(this.event.start).format('HH:mm')
        },
        endTime() {
            return this.event.end ? this.$moment(this.event.end).format('HH:mm') : null
        },
        eventClosed() {
            if(this.event.endStr) {
                return this.$moment(this.event.endStr).isBefore(this.$moment())
            } else {
                return this.$moment(this.event.allDay ? this.event.startStr : this.event.endStr ).isBefore(this.$moment())
            }
        },
        props() {
            return this.event.extendedProps
        },
        startEndDiff() {
            if(!this.event.allDay) {
                const diff = this.$moment(this.event.end).diff(this.event.start, 'minutes')
                if(diff) {
                    return diff <= 30 ? true : false
                } else
                    return false
            } else 
                return false
        }
    }
}
</script>

<style lang="scss" scoped>
.event{
    border-left: 4px solid;
    border-radius: 4px;
    position: relative;
    overflow: hidden;
    width: 100%;
    height: 100%;
    &.before_event{
        opacity: 0.7;
    }
    .wrapper{
        z-index: 5;
        color: var(--text1);
        padding: 3px 5px;
        .e_title{
            font-weight: 600;
        }
    }
    .event_bg{
        position: absolute;
        left: 0;
        top: 0;
        width: 100%;
        height: 100%;
        opacity: 0.3;
    }
    &.finished_event{
        .wrapper_label{
            text-decoration: line-through;
        }
    }
}
</style>