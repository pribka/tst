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
            defaultType="listWeek" 
            ref="calendar"
            :page_name="pageName"
            class="calendar_widget" />
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
    components: {
        WidgetWrapper: () => import('../WidgetWrapper.vue'),
        Calendar: () => import('@apps/Calendar/Widget.vue')
    },
    computed: {
        pageName() {
            return (this.widget.page_name || this.widget.id) || this.widget.widget.id
        }
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
.calendar_widget{
    &::v-deep{
        .fc-list-table {
            display: block;
            tbody{
                display: block;
                tr{
                    display: flex;
                }
                th{
                    display: block;
                }
                th{
                    width: 100%;
                    .fc-list-day-side-text{
                        font-weight: 500;
                        color: var(--text_current);
                        font-size: 13px;
                        cursor: default;
                    }
                    .fc-list-day-text{
                        cursor: default;
                    }
                }
                td{
                    display: flex;
                    align-items: center;
                  &.fc-list-event-time{
                    width: 90px;
                    padding-left: 5px;
                  }  
                  &.fc-list-event-graphic{
                    padding-left: 5px;
                    width: 20px;
                  }
                  &.fc-list-event-title{
                    width: 100%;
                    overflow: hidden;
                    text-overflow: ellipsis;
                    white-space: nowrap;
                    cursor: pointer;
                    padding-right: 5px;
                    .e_title,
                    .wrapper{
                        overflow: hidden;
                        text-overflow: ellipsis;
                        white-space: nowrap;
                    }
                  }
                }
            }
        }
    }
}
</style>