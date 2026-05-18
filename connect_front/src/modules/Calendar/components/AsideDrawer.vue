<template>
    <DrawerTemplate
        title="Настройка календаря"
        width="100%"
        destroyOnClose
        v-model="visible"
        @close="visible = false">
        <div ref="eventAddBody">
            <a-spin :spinning="selectLoading">
                <div class="calendar_aside">
                    <div 
                        v-if="showAside" 
                        class="calendar_aside__scroller">
                        <div ref="antCalendar">
                            <a-calendar 
                                :value="cDate" 
                                :fullscreen="false" 
                                @change="dateChange">
                                <template slot="dateFullCellRender" slot-scope="value">
                                    <div 
                                        class="day_wrapper" 
                                        :class="getDayNumber(value) && 'weekend'">
                                        <div class="num">
                                            {{ $moment(value).format('DD') }}
                                        </div>
                                    </div>
                                </template>
                            </a-calendar>
                        </div>
                        <div 
                            v-if="!related_object" 
                            class="calendars_list">
                            <div class="calendars_list__item">
                                <a-spin :spinning="reload">
                                    <div class="item_header">
                                        <div class="title">
                                            {{ $t('calendar.my_calendars') }}
                                        </div>
                                        <a-button 
                                            type="ui" 
                                            class="gray" 
                                            style="margin-right: -8px" 
                                            flaticon 
                                            icon="fi-rr-plus"
                                            @click="addCalendarHandler()">
                                            {{ $t('calendar.add') }}
                                        </a-button>
                                    </div>
                                    <div class="item_calendars">
                                        <div v-if="!reload && !selectLoading && empty" class="flex items-center">
                                            <i class="fi fi-rr-calendar-minus mr-2"></i> {{ $t('calendar.no_calendars') }}
                                        </div>
                                        <a-checkbox-group 
                                            v-model="defaultSelect" 
                                            class="w-full" 
                                            @change="onChange">
                                            <div v-for="item in calendarList" :key="item.id" class="item_calendars__item">
                                                <a-checkbox 
                                                    :value="item.id" 
                                                    :checkboxColor="item.color">
                                                    <div 
                                                        :title="item.name.length > 25 && item.name"
                                                        class="flex items-center justify-between select-none">
                                                        <div class="name">{{ item.name }}</div>
                                                    </div>
                                                </a-checkbox>
                                                <a-dropdown :trigger="['click']" :getPopupContainer="getDropPopupContainer">
                                                    <a-button 
                                                        type="ui"
                                                        class="gray"
                                                        shape="circle"
                                                        style="margin-right: -7px" 
                                                        ghost
                                                        flaticon
                                                        icon="fi-rr-menu-dots-vertical" />
                                                    <a-menu slot="overlay">
                                                        <a-menu-item 
                                                            key="edit" 
                                                            class="flex items-center"
                                                            @click="addCalendarHandler(true, item)">
                                                            <i class="fi fi-rr-edit mr-2"></i> {{ $t('calendar.edit') }}
                                                        </a-menu-item>
                                                        <a-menu-divider />
                                                        <a-menu-item 
                                                            key="delete" 
                                                            class="text-red-500 flex items-center"
                                                            @click="deleteCalendarHandler(item)">
                                                            <i class="fi fi-rr-trash mr-2"></i> {{ $t('calendar.delete') }}
                                                        </a-menu-item>
                                                    </a-menu>
                                                </a-dropdown>
                                            </div>
                                        </a-checkbox-group>
                                    </div>
                                </a-spin>
                            </div>
                            <infinite-loading 
                                v-if="!reload" 
                                ref="calendarInfinite" 
                                @infinite="getList" 
                                v-bind:distance="5">
                                <div slot="spinner"><a-spin v-if="!reload" /></div>
                                <div slot="no-more"></div>
                                <div slot="no-results"></div>
                            </infinite-loading>
                            <div 
                                v-if="!empty2" 
                                class="calendars_list__item">
                                <a-spin :spinning="selectLoading2">
                                    <div class="item_header">
                                        <div class="title">
                                            {{ $t('calendar.public_calendars') }}
                                        </div>
                                    </div>
                                    <div class="item_calendars">
                                        <a-checkbox-group 
                                            v-model="defaultSelect2" 
                                            class="w-full" 
                                            @change="onChange2">
                                            <div v-for="item in calendarGroupList" :key="item.id" class="item_calendars__item">
                                                <a-checkbox :value="item.id" checkboxColor="#1c65c0">
                                                    <div 
                                                        :title="item.name.length > 25 && item.name"
                                                        class="flex items-center justify-between select-none">
                                                        <div class="name">{{ item.name }}</div>
                                                    </div>
                                                </a-checkbox>
                                            </div>
                                        </a-checkbox-group>
                                    </div>
                                </a-spin>
                            </div>
                        </div>
                    </div>
                    <AddCalendar 
                        ref="addCalendar" 
                        :listReload="listReload"
                        :elementUpdate="elementUpdate" />
                </div>
            </a-spin>
        </div>
        <template #footer>
            <a-button 
                type="ui_ghost" 
                ghost
                block
                @click="visible = false">
                {{ $t('close') }}
            </a-button>
        </template>
    </DrawerTemplate>
</template>

<script>
import { errorHandler } from '@/utils/index.js'
import InfiniteLoading from 'vue-infinite-loading'
let checkTimer,
    checkTimer2;
export default {
    components: {
        AddCalendar: () => import('./AddCalendar.vue'),
        InfiniteLoading,
        DrawerTemplate: () => import("@/components/DrawerTemplate.vue")
    },
    props: {
        activeType: {
            type: String,
            required: true
        },
        changeDate: {
            type: Function,
            default: () => {}
        },
        handleDateSelect: {
            type: Function,
            default: () => {}
        },
        selectOneDay: {
            type: Function,
            default: () => {}
        },
        showAside: {
            type: Boolean,
            default: true
        },
        changeAsideShow: {
            type: Function,
            default: () => {}
        },
        getEvents: {
            type: Function,
            default: () => {}
        },
        related_object: {
            type: [String, Number],
            default: null
        },
        addEventCheck: {
            type: Boolean,
            default: true
        }
    },
    data() {
        return {
            loading: false,
            loading2: false,
            cDate: this.$moment(),
            calendarList: [],
            calendarGroupList: [],
            page: 0,
            next: true,
            empty: false,
            reload: false,
            empty2: true,
            selectLoading: false,
            selectLoading2: false,
            defaultSelect: [],
            defaultSelect2: [],
            visible: false,
            drawerLoading: false
        }
    },
    created() {
        this.getGroupList()
    },
    methods: {
        getDropPopupContainer() {
            return this.$refs.eventAddBody
        },
        openDrawer() {
            this.visible = true
        },
        selectCalDay(value) {
            this.cDate = value
            this.selectOneDay(value)
        },
        getDayNumber(value) {
            return this.$moment(value).day() === 0 || this.$moment(value).day() === 6 ? true : false
        },
        getPopupContainer() {
            return this.$refs['antCalendar']
        },
        elementUpdate(item) {
            const index = this.calendarList.findIndex(f => f.id === item.id)
            if(index !== -1) {
                this.$set(this.calendarList, index, item)
            }
        },
        listReload() {
            this.reload = true
            this.page = 0
            this.next = true
            this.empty = false
            this.$nextTick(() => {
                if(this.$refs.calendarInfinite)
                    this.$refs.calendarInfinite.stateChanger.reset()
            })
            this.getList()
        },
        onChange(event) {
            clearTimeout(checkTimer)
            checkTimer = setTimeout(() => {
                this.selectMyCalendars(event)
            }, 700)
        },
        onChange2(event) {
            clearTimeout(checkTimer2)
            checkTimer2 = setTimeout(() => {
                this.selectGroupCalendars(event)
            }, 700)
        },
        async selectMyCalendars(event) {
            try {
                this.selectLoading = true
                await this.$http.post('/calendars/check_personal/', event)
                this.getEvents(false)
            } catch(error) {
                errorHandler({error})
            } finally {
                this.selectLoading = false
            }
        },
        async selectGroupCalendars(event) {
            try {
                // this.selectLoading2 = true
                await this.$http.post('/calendars/check_group/', event)
                this.getEvents(false)
            } catch(error) {
                errorHandler({error})
            } finally {
                // this.selectLoading2 = false
            }
        },
        calendarDefault(date = null) {
            if(date) {
                this.cDate = this.$moment(date)
            } else {
                this.cDate = this.$moment()
            }
        },
        dateChange(event) {
            this.changeDate(event)
            this.cDate = event
            this.visible = false
        },
        setDate(date) {
            this.cDate = this.$moment(date)
        },
        addCalendarHandler(edit = false, item = null) {
            this.$refs['addCalendar'].openModal(edit, item)
        },
        deleteCalendarHandler(item) {
            this.$confirm({
                title: this.$t('calendar.confirm_delete_calendar_title'),
                content: '',
                okText: this.$t('calendar.confirm_ok'),
                okType: 'danger',
                zIndex: 2000,
                closable: true,
                cancelText: this.$t('calendar.confirm_cancel'),
                onOk: () => {
                    return new Promise((resolve, reject) => {
                        this.$http.post('/table_actions/update_is_active/', {
                            id: item.id,
                            is_active: false
                        })
                            .then(() => {
                                this.listReload()
                                this.$message.success(this.$t('calendar.calendar_deleted'))
                                this.getEvents(false)
                                resolve()
                            })
                            .catch(error => {
                                errorHandler({error})
                                reject(e)
                            })
                    })
                }
            })
        },
        async getGroupList() {
            try {
                this.defaultSelect2 = []
                this.loading2 = true
                const { data } = await this.$http.get('/calendars/group_calendars/')
                if(data?.length) {
                    this.calendarGroupList = data

                    data.forEach(chc => {
                        if(chc.checked) {
                            this.defaultSelect2.push(chc.id)
                        }
                    })

                    if(this.empty2)
                        this.empty2 = false
                } else {
                    this.empty2 = true
                }
            } catch(e) {
                console.log(e)
            } finally {
                this.loading2 = false
            }
        },
        async getList($state = null) {
            if(!this.loading && this.next) {
                try {
                    this.loading = true
                    this.page = this.page+1
                    const { data } = await this.$http.get('/calendars/', {
                        params: {
                            page_size: 12,
                            page: this.page
                        }
                    })
                    if(data && data.results.length) {
                        this.empty = false
                        if(this.reload) {
                            this.defaultSelect = []
                            this.calendarList = data.results
                        } else {
                            this.calendarList = this.calendarList.concat(data.results)
                        }
                        data.results.forEach(chc => {
                            if(chc.checked) {
                                const find = this.defaultSelect.find(f => f === chc.id)
                                if(!find)
                                    this.defaultSelect.push(chc.id)
                            }
                        })
                    } else {
                        this.empty = true
                    }
                    if(!data.next) {
                        if($state)
                            $state.complete()
                        this.next = false
                    } else {
                        if($state)
                            $state.loaded()
                    }
                } catch(e) {
                    console.log(e)
                } finally {
                    this.loading = false
                    this.reload = false
                }
            } else {
                this.reload = false
                if($state)
                    $state.complete()
            }
        }
    }
}
</script>

<style lang="scss" scoped>
.calendar_aside{
    height: 100%;
    position: relative;
    &.show{
        width: 100%;
    }
    &__scroller{
        overflow-y: auto;
        height: 100%;
    }
    &__toggle{
        position: absolute;
        width: 11px;
        height: 20px;
        background: #848484;
        z-index: 5;
        color: #ffffff;
        opacity: 0.6;
        display: flex;
        align-items: center;
        justify-content: center;
        top: 50%;
        margin-top: -10px;
        font-size: 10px;
        right: -11px;
        transition: all 0.3s cubic-bezier(0.645, 0.045, 0.355, 1);
        border-radius: 0 3px 3px 0;
        cursor: pointer;
        &:hover{
            opacity: 1;
        }
    }
    &::v-deep{
        .ant-fullcalendar{
            border-bottom: 1px solid var(--fc-border-color);
            .day_wrapper{
                display: flex;
                align-items: center;
                justify-content: center;
                cursor: pointer;
                .num{
                    border-radius: 50%;
                    width: 28px;
                    height: 28px;
                    font-size: 14px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    border: 1px solid transparent;
                }
            }
            .ant-fullcalendar-last-month-cell, 
            .ant-fullcalendar-next-month-btn-day{
                .day_wrapper{
                    opacity: 0.4;
                }
            }
            .ant-fullcalendar-cell{
                &:not(.ant-fullcalendar-last-month-cell):not(.ant-fullcalendar-next-month-btn-day){
                    .day_wrapper{
                        &.weekend{
                            color: var(--gray);
                        }
                    }
                }
            }
            .ant-fullcalendar-today{
                .day_wrapper{
                    .num{
                        border-color: var(--blue);
                        color: var(--blue);
                    }
                }
            }
            .ant-fullcalendar-selected-day{
                .day_wrapper{
                    .num{
                        color: #ffffff;
                        background: var(--blue);
                        border-color: var(--blue);
                    }
                }
            }
            .ant-fullcalendar-column-header{
                .ant-fullcalendar-column-header-inner{
                    color: var(--gray);
                    font-weight: 600;
                }
            }
        }
    }
    .calendars_list{
        padding: 10px 18px;
        &__item{
            &:not(:last-child){
                margin-bottom: 20px;
            }
            .item_calendars{
                .item_calendars__item{
                    text-overflow: ellipsis;
                    white-space: nowrap;
                    display: flex;
                    align-items: center;
                    width: 100%;
                    justify-content: space-between;
                    &:not(:last-child){
                        margin-bottom: 9px;
                    }
                    &::v-deep{
                        .ant-dropdown-trigger{
                            transition: all 0.3s cubic-bezier(0.645, 0.045, 0.355, 1);
                            &.ant-dropdown-open{
                                opacity: 1;
                            }
                        }
                        &:hover{
                            .ant-dropdown-trigger{
                                opacity: 1;
                            }
                        }
                        .ant-checkbox-inner{
                            width: 20px;
                            height: 20px;
                        }
                        .ant-checkbox-wrapper{
                            display: flex;
                            align-items: center;
                            text-overflow: ellipsis;
                            white-space: nowrap;  
                            width: 100%;
                            max-width: 85%;
                            .ant-checkbox{
                                margin-top: 3px;
                            }
                            .ant-checkbox + span{
                                text-overflow: ellipsis;
                                white-space: nowrap;   
                            }
                            .name{
                                overflow: hidden;
                                text-overflow: ellipsis;
                                white-space: nowrap;
                            }
                            .name{
                                font-size: 15px;
                            }
                            .ant-checkbox + span{
                                width: 100%;
                                padding-right: 0px;
                            }
                        }
                    }
                }
            }
            .item_header{
                display: flex;
                align-items: center;
                justify-content: space-between;
                margin-bottom: 10px;
                .title{
                    color: var(--gray);
                    font-size: 15px;
                    font-weight: 300;
                }
            }
        }
    }
}
</style>