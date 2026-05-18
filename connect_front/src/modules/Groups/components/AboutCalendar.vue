<template>
    <div class="flex_basis">
        <div class="events flex-column">
            <div class="flex items-center place-content-between w-full">
                <h6>{{ $t("project.week_events") }}</h6>
                <a-button
                    type="ui" 
                    ghost 
                    flaticon
                    :disabled="!calendarInfo"
                    shape="circle"
                    icon="fi-rr-plus"
                    @click="addEvent" />
            </div>
            <Week_Calendar 
                defaultType="listWeek"
                :related_object="requestData.id"
                ref="calendar"
                :page_name="requestData.id"
                :startDate="startDate"
                :endDate="endDate"
                class="calendar_widget" />
        </div>
    </div>
</template>

<script>
import eventBus from "@/utils/eventBus"
export default {
    components: {
        Week_Calendar: () => import('@apps/Calendar/Widget.vue')
    },
    props: {
        requestData: {
            type: Object,
            required: true
        }
    },
    computed: {
        startDate() {
            return this.$moment().startOf('day').toISOString()
        },
        endDate() {
            return this.$moment().endOf('week').toISOString()
        }
    },
    data() {
        return {
            calendarInfo: null
        }
    },
    created() {
        this.getCalendarInfo()
    },
    methods: {
        async getCalendarInfo() {
            try {
                const { data } = await this.$http.get(`calendars/related/${this.requestData.id}/`)
                if(data) {
                    this.calendarInfo = data
                }
            } catch(e) {
                console.log(e)
            }
        },
        addEvent() {
            eventBus.$emit('open_event_form', 
                this.$moment().format('YYYY-MM-DD[T]HH:mm:ss'),
                this.$moment().add(1, 'hours').format('YYYY-MM-DD[T]HH:mm:ss'),
                null,
                this.calendarInfo,
                'default')
        }
    }
}
</script>

<style lang="scss" scoped>
.calendar_widget{
    height: 250px !important;
    margin-top: 10px;
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