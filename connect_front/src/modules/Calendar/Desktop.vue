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
            :clearEvents="clearEvents"
            :uKey="uKey"
            :activeType="activeType"
            :handleChangeType="handleChangeType" />
        <div class="calendar_page__body">
            <div class="h-full flex">
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
                <div ref="calendarWrapper" class="wrapper">
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
                        class="sel_day_drawer"
                        :maskClosable="false"
                        destroyOnClose
                        :visible="dayVisible"
                        :get-container="dayDrawerContainer"
                        :afterVisibleChange="afterVisibleChange"
                        :wrap-style="{ position: related_object ? 'fixed' : 'absolute' }"
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
        </div>
    </div>
</template>

<script>
import cMixins from './mixins/index.js'
export default {
    mixins: [cMixins],
    components: {
        Header: () => import('./components/Header.vue'),
        Aside: () => import('./components/Aside.vue')
    }
}
</script>

<style lang="scss" scoped>
.calendar_page{
    overflow: hidden;
    display: flex;
    flex-direction: column;
    height: 100%;
    &__body{
        background: #fff;
        flex-grow: 1;
        width: 100%;
        overflow: hidden;
        border-top: 1px solid var(--fc-border-color);
        .wrapper{
            height: 100%;
            width: 100%;
            position: relative;
            overflow: hidden;
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
                .fc{
                    .fc-popover{
                        z-index: 700;
                    }
                }
                .fc .fc-list-sticky .fc-list-day > *{
                    z-index: 10;
                }
                .fc-v-event{
                    background-color: initial!important;
                    border: 0px!important;
                }
                .fc-multiMonthYear-view,
                .fc-listWeek-view{
                    border: 0px;
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
                .ant-spin-container,
                .ant-spin-nested-loading{
                    height: 100%;
                    & > div{
                        height: 100%;
                        position: absolute;
                        top: 0;
                        left: 0;
                        width: 100%;
                        .ant-spin{
                            max-height: 100%;
                        }
                    }
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
                                font-weight: 400;
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