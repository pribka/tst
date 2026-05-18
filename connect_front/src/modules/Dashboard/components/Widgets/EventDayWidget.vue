<template>
    <WidgetWrapper :widget="widget">
        <template slot="actions">
            <a-button
                type="ui" 
                ghost 
                flaticon
                shape="circle"
                icon="fi-rr-plus"
                @click="addEvent()" />
        </template>
        <Calendar 
            defaultType="timeGridDay"
            ref="calendar"
            class="day_calendar"
            :page_name="pageName" />
    </WidgetWrapper>
</template>

<script>
import eventBus from '@/utils/eventBus'
export default {
    props: {
        widget: {
            type: Object,
            required: true
        }
    },
    computed: {
        pageName() {
            return (this.widget.page_name || this.widget.id) || this.widget.widget.id
        }
    },
    components: {
        WidgetWrapper: () => import('../WidgetWrapper.vue'),
        Calendar: () => import('@apps/Calendar/Widget.vue')
    },
    methods: {
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
        eventBus.$on(`update_calendar_${this.pageName}`, () => {
            this.$nextTick(() => {
                this.$refs.calendar.getEvents(false)
            })
        })
    },
    beforeDestroy() {
        eventBus.$off(`update_calendar_${this.pageName}`)
    }
}
</script>

<style lang="scss" scoped>
.day_calendar{
    &::v-deep{
        .fc-event,
        .fc-v-event{
            background-color: transparent!important;
            border-color: transparent!important;
        }
    }
}
</style>