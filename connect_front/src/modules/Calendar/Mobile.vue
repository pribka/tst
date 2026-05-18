<template>
    <div class="calendar_page">
        <Header 
            :today="today" 
            :prev="prev" 
            :next="next" 
            :related_object="related_object"
            :relatedInfo="relatedInfo"
            :addCalendar="addCalendar"
            :todayCheck="todayCheck"
            :addEventCheck="addEventCheck"
            :openAside="openAside"
            :clearEvents="clearEvents"
            :uKey="uKey"
            :activeType="activeType"
            :handleChangeType="handleChangeType" />
        <div class="calendar_page__body">
            <div class="wrapper">
                <!--<div v-if="configLoader" class="wrapper_loader">
                    <a-spin />
                </div>-->
                <template v-if="!configInit">
                    <a-spin :spinning="loading">
                        <FullCalendar
                            ref="fullCalendar"
                            :options='calendarOptions'>
                            <template v-slot:eventContent="arg">
                                <CalendarEvent 
                                    :event="arg.event" 
                                    :activeType="activeType" />
                            </template>
                        </FullCalendar>
                    </a-spin>
                </template>
                <a-drawer
                    :title="selectedDay"
                    placement="right"
                    :mask="false"
                    :width="400"
                    :maskClosable="false"
                    :visible="dayVisible"
                    :afterVisibleChange="afterVisibleChange"
                    @close="dayVisible = false">
                    <a-spin :spinning="dayLoading">
                        <a-empty v-if="dyEventsEmpty" :description="$t('calendar.no_events')" />
                        <div class="event_list_wrapper">
                            <CalendarEventList v-for="item in dayEvents" :key="item.id" :event="item" />
                        </div>
                    </a-spin>
                </a-drawer>
            </div>
        </div>
        <div class="add_event_float">
            <a-button 
                flaticon
                shape="circle"
                size="large"
                type="primary"
                icon="fi-rr-plus"
                @click="floatAddEvent()" />
        </div>
        <Aside 
            ref="aside" 
            :handleDateSelect="handleDateSelect"
            :selectOneDay="selectOneDay"
            :showAside="showAside"
            :getEvents="getEventsType"
            :addEventCheck="addEventCheck"
            :related_object="related_object"
            :activeType="activeType"
            :changeAsideShow="changeAsideShow"
            :changeDate="changeDate" />
    </div>
</template>

<script>
import cMixins from './mixins/index.js'
export default {
    mixins: [cMixins],
    components: {
        Header: () => import('./components/HeaderMobile.vue'),
        Aside: () => import('./components/AsideDrawer.vue')
    },
    methods: {
        openAside() {
            this.$refs.aside.openDrawer()
        }
    }
}
</script>

<style lang="scss" scoped>
.calendar_page{
    .add_event_float{
        --safe-area-inset-bottom: env(safe-area-inset-bottom);
        position: fixed;
        bottom: calc(85px + var(--safe-area-inset-bottom));
        right: 15px;
        z-index: 50;
        &::v-deep{
            .ant-btn{
                width: 50px;
                height: 50px;
                .flaticon{
                    font-size: 22px;
                }
            }
        }
    }
    &__body{
        border-top: 1px solid var(--fc-border-color);
        position: relative;
        .wrapper{
            width: 100%;
            position: relative;
            .wrapper_loader{
                position: absolute;
                left: 0;
                width: 100%;
                z-index: 5;
                top: 0;
                padding: 15px;
                display: flex;
                justify-content: center;
                align-items: center;
            }
            &::v-deep{
                .fc .fc-more-popover .fc-popover-body{
                    max-height: 250px;
                    overflow-y: auto;
                }
                .fc {
                    direction: ltr;
                    text-align: left;
                }
                .fc table {
                    border-collapse: collapse;
                    border-spacing: 0;
                    }
                    
                html .fc,
                .fc table {
                    font-size: 1em;
                }
                .fc-listWeek-view{
                    .fc-list-day{
                        .fc-list-day-cushion{
                            display: flex;
                            align-items: center;
                            a{
                                font-size: 15px;
                                margin-right: 5px;
                                font-weight: 500;
                                color: var(--gray);
                            }
                        }
                        &.fc-day-today{
                            a{
                                color: var(--blue);
                            }
                        }
                    }
                }
                    
                .fc td,
                .fc th {
                    vertical-align: top;
                    .fc-list-day-cushion,
                    &.fc-list-event-time{
                        padding: 8px;
                    }
                    &.fc-list-event-graphic{
                        padding: 8px 5px;
                        padding-right: 0px;
                        padding-left: 0px;
                    }
                    .fc-list-event-title{
                        padding: 8px;
                    }
                }

                .fc-header td {
                    white-space: nowrap;
                    }

                .fc-header-left {
                    width: 25%;
                    text-align: left;
                    }
                    
                .fc-header-center {
                    text-align: center;
                    }
                    
                .fc-header-right {
                    width: 25%;
                    text-align: right;
                    }
                    
                .fc-header-title {
                    display: inline-block;
                    vertical-align: top;
                    }
                    
                .fc-header-title h2 {
                    margin-top: 0;
                    white-space: nowrap;
                    }
                    
                .fc .fc-header-space {
                    padding-left: 10px;
                    }
                    
                .fc-header .fc-button {
                    margin-bottom: 1em;
                    vertical-align: top;
                    }
                    
                /* buttons edges butting together */

                .fc-header .fc-button {
                    margin-right: -1px;
                    }
                    
                .fc-header .fc-corner-right {
                    margin-right: 1px; /* back to normal */
                    }
                    
                .fc-header .ui-corner-right {
                    margin-right: 0; /* back to normal */
                    }
                    
                /* button layering (for border precedence) */
                    
                .fc-header .fc-state-hover,
                .fc-header .ui-state-hover {
                    z-index: 2;
                    }
                    
                .fc-header .fc-state-down {
                    z-index: 3;
                    }

                .fc-header .fc-state-active,
                .fc-header .ui-state-active {
                    z-index: 4;
                    }
                    
                    
                    
                /* Content
                ------------------------------------------------------------------------*/
                    
                .fc-content {
                    clear: both;
                    }
                    
                .fc-view {
                    width: 100%; /* needed for view switching (when view is absolute) */
                    overflow: hidden;
                    }
                .fc-v-event{
                    background-color: initial!important;
                    border: 0px!important;
                }
                .fc-multiMonthYear-view,
                .fc-listWeek-view{
                    border: 0px;
                    .fc-list-day{
                        .fc-list-day-cushion{
                            background: #ffffff;
                        }
                    }
                    .fc-event{
                        background: #ffffff;
                    }
                }
                .fc-timeGridWeek-view,
                .fc-dayGridMonth-view{
                    .fc-day{
                        &.fc-day-sun,
                        &.fc-day-sat{
                            background: rgba(239, 242, 245, 0.2);
                        }
                    }
                }
                .fc-multiMonthYear-view{
                    .fc-daygrid-event-harness-abs{
                        display: none;
                    }
                    .fc-daygrid-day-bg{
                        position: relative;
                    }
                    .fc-day{
                        &:not(.fc-day-disabled){
                            cursor: pointer;
                            transition: all 0.3s cubic-bezier(0.645, 0.045, 0.355, 1);
                            &:hover{
                                background-color: var(--primaryHover);
                            }
                            &.fc-day-sun,
                            &.fc-day-sat{
                                background: rgba(239, 242, 245, 0.2);
                            }
                        }
                        &.fc-day-disabled{
                            background: var(--fc-neutral-bg-color);
                        }
                    }
                }
                .fc-event{
                    &.fc-event-draggable{
                        &:hover{
                            .fc-event-resizer{
                                &.fc-event-resizer-end{
                                    display: flex;
                                    justify-content: center;
                                    &::after{
                                        content: "";
                                        background: #ffffff;
                                        opacity: 0.8;
                                        border-radius: 5px;
                                        width: 50px;
                                        height: 2px;
                                        display: block;
                                    }
                                }
                            }
                        }   
                    }
                }
                .fc-theme-standard{
                    .fc-timegrid-event.fc-event-mirror{
                        box-shadow: initial;
                        .event{
                            border-color: #c3c3c3;
                            .event_bg{
                                background: #c3c3c3;
                            }
                        }
                    }
                    .fc-scrollgrid{
                        border-left: 0px;
                    }
                    .fc-popover-header{
                        background: #ffffff;
                        .fc-popover-title{
                            color: var(--gray);
                            font-weight: 600;
                            font-size: 15px;
                        }
                        .fc-popover-close{
                            &::before{
                                font-family: 'icomoon' !important;
                                speak: never;
                                font-style: normal;
                                font-weight: normal;
                                font-variant: normal;
                                text-transform: none;
                                line-height: 1;
                                -webkit-font-smoothing: antialiased;
                                -moz-osx-font-smoothing: grayscale;
                                content: "\ecad";
                            }
                        }
                    }
                }
                .fc-popover{
                    border-radius: var(--borderRadius);
                    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
                    border: 0px;
                    &.fc-more-popover{
                        max-width: 300px;
                    }
                }
                .fc-event-selected::after,
                .fc-event:focus::after,
                .fc-daygrid-dot-event.fc-event-mirror, 
                .fc-daygrid-dot-event:hover{
                    background: rgba(0, 0, 0, 0);
                }
                .fc-daygrid-event{
                    border-radius: initial;
                    border: initial!important;
                    background-color: initial!important;
                }
                .fc-direction-ltr{
                    .fc-timegrid-axis-cushion{
                        &.fc-scrollgrid-shrink-cushion{
                            &.fc-scrollgrid-sync-inner{
                                color: var(--gray);
                            }
                        }
                    }
                    .fc-timegrid-slot-label-frame{
                        color: var(--gray);
                    }
                }
                .fc{
                    .fc-daygrid-day,
                    .fc-timegrid-col{
                        background-color: var(--fc-today-bg-color);
                    }
                    .fc-list-event{
                        &:hover{
                            td{
                                background-color: transparent;
                            } 
                        }
                    }
                    .fc-daygrid-more-link{
                        transition: all 0.3s cubic-bezier(0.645, 0.045, 0.355, 1);
                        color: var(--blue);
                        &:hover{
                            background: #e3e6ea;
                        }
                    }
                    .fc-highlight{
                        background: var(--primaryHover);
                    }
                    .fc-list-day-cushion{
                        .fc-list-day-side-text,
                        .fc-list-day-text{
                            color: var(--text);
                            font-size: 16px;
                            cursor: default;
                            &::first-letter {
                                text-transform: uppercase;
                            }
                        }
                    }
                    .fc-col-header-cell{
                        &.fc-day{
                            a{
                                color: var(--text);
                                font-size: 16px;
                                cursor: default;
                                &::first-letter {
                                    text-transform: uppercase;
                                }
                            }
                        }
                    }
                    .fc-daygrid-day-number{
                        width: 22px;
                        height: 22px;
                        border-radius: 50%;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        color: var(--text);
                    }
                    .fc-day-today{
                        .fc-daygrid-day-number{
                            color: #fff;
                            background: var(--blue);
                        }
                    }
                    .fc-day-other{
                        background: rgba(239, 242, 245, 0.4);
                    }
                }
                .fc-theme-standard{
                    .fc-scrollgrid{
                        border-top: 0px;
                        border-bottom: 0px;
                    }
                    .fc-col-header-cell{
                        &.fc-day-today{
                            a{
                                color: var(--blue);
                            }
                        }
                    }
                }
            }
        }
    }
}
</style>