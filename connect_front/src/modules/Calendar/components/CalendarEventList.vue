<template>
    <div 
        class="list_event truncate" 
        :title="event.title"
        :class="[eventClosed && 'before_event', event.is_finished && 'finished_event']"
        :style="`border-color: ${event.color}`"
        @click="openEvent()">
        <div class="event_bg" :style="`background: ${event.color}`"></div>
        <div class="flex items-center wrapper_label">
            <span v-if="!event.allDay" class="mr-1">{{ startTime }} <template v-if="endTime">- {{ endTime }}</template></span> <span class="e_title">{{ event.title }}</span>
        </div>
    </div>
</template>

<script>
export default {
    props: {
        event: {
            type: Object,
            required: true
        }
    },
    computed: {
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
        }
    },
    methods: {
        openEvent() {
            const { id } = this.event
            let query = Object.assign({}, this.$route.query)
            if(query.event && Number(query.event) !== id || !query.event) {
                query.event = id
                this.$router.push({query})
            }
        }
    }
}
</script>

<style lang="scss" scoped>
.list_event{
    border-left: 4px solid;
    border-radius: 4px;
    position: relative;
    padding: 5px 10px;
    cursor: pointer;
    &:not(:last-child){
        margin-bottom: 8px;
    }
    &.before_event{
        opacity: 0.7;
    }
    .e_title{
        font-weight: 600;
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