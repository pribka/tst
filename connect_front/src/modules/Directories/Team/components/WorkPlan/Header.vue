<template>
    <div class="calendar_page__header">
        <p class="header__item">{{ range }}</p>
        <div class="header__item flex flex-col md:flex-row items-center">
            <div class="flex items-center md:mr-3 mb-4 md:mb-0">
                <a-button type="ui" ghost flaticon icon="fi-rr-angle-small-left" @click="prev" />
                <a-button
                    class="mx-2"
                    @click="today"
                    type="primary" 
                    :disabled="todayButtonDisabled"
                    ghost>
                    {{ $t('team.today') }}
                </a-button>
                <a-button type="ui" ghost flaticon icon="fi-rr-angle-small-right" @click="next" />
            </div>
            <a-radio-group 
                class="select-none"
                :value="activeType" 
                @change="handleChangeType($event.target.value)">
                <a-radio-button value="day">
                    {{ $t('team.day') }}
                </a-radio-button>
                <a-radio-button value="threeDays">
                    {{ $t('team.three_days') }}
                </a-radio-button>
                <a-radio-button value="week">
                    {{ $t('team.week') }}
                </a-radio-button>
            </a-radio-group>
            <transition name="fade">
                <div 
                    v-if="activeType === 'listWeek' || activeType === 'listMonth'" 
                    class="ml-4 flex items-center cursor-pointer"
                    @click="changeSwitchType(mountchActive ? 'listWeek' : 'listMonth')">
                    <a-switch :checked="mountchActive" /> 
                    <span class="ml-2">{{ $t('team.month') }}</span>
                </div>
            </transition>
        </div>
        

        <div class="header__item">
            <a-button-group>
                <a-button 
                    type="primary" 
                    icon="plus" 
                    ghost
                    @click="downloadFile()">
                    {{ $t('team.download_excel_report') }}
                </a-button>
                <a-dropdown 
                    :trigger="['click']">
                    <a-button 
                        type="primary"
                        ghost
                        icon="fi-rr-menu-dots-vertical"
                        flaticon />
                    <a-menu slot="overlay">
                        <a-menu-item key="period" @click="openModal">
                            {{ $t('team.select_period') }}
                        </a-menu-item>
                    </a-menu>
                </a-dropdown>
            </a-button-group>

            <a-modal
                :title="$t('team.select_report_period')"
                v-model="modalVisible">
                <div ref="wrap">
                    <a-range-picker 
                        v-model="dateRange"
                        :locale="locale" 
                        @calendarChange="handleCalendarChange"
                        :disabledDate="disabledDate"
                        :getCalendarContainer="() => $refs.wrap"
                        size="large" 
                        class="w-full" />
                </div>
                <template #footer>
                    <a-button
                        @click="modalVisible = false">
                        {{ $t('team.close') }}
                    </a-button>
                    <a-button
                        @click="downloadRangeFile"
                        :disabled="!dateRange?.length"
                        type="primary">
                        {{ $t('team.download_report') }}
                    </a-button>
                </template>
            </a-modal>
            <!-- <a-button
                @click="shareFile"
                type="ui" 
                ghost
                flaticon
                icon="fi-rr-share" /> -->
        </div>
    </div>
</template>

<script>
import locale from 'ant-design-vue/es/date-picker/locale/ru_RU'
export default {
    props: {
        activeType: {
            type: String,
            required: true
        },
        downloadFile: {
            type: Function,
            default: () => {}
        },
        shareFile: {
            type: Function,
            default: () => {}
        },
        todayCheck: {
            type: Boolean,
            default: true
        },
        today: {
            type: Function,
            default: () => {}
        },
        prev: {
            type: Function,
            default: () => {}
        },
        next: {
            type: Function,
            default: () => {}
        },
        handleChangeType:{
            type: Function,
            default: () => {}
        },
        addCalendar: {
            type: Function,
            default: () => {}
        },
        related_object: {
            type: [String, Number],
            default: null
        },
        relatedInfo: {
            type: Object,
            default: () => null
        },
        // uKey: {
        //     type: [String, Number],
        //     default: 'default'
        // },
        addEventCheck: {
            type: Boolean,
            default: true
        },
        startDay: {
            type: Object,
            required: true
        }
        // clearEvents: {
        //     type: Function,
        //     default: () => {}
        // }
    },
    computed: {
        todayButtonDisabled() {
            if (this.activeType === 'week') {
                return this.startDay.clone().startOf("week").isSame(this.$moment().startOf("week"), 'day')
            }
            return this.startDay.isSame(this.$moment(), 'day');
        },

        windowWidth() {
            return this.$store.state.windowWidth
        },
        range() {
            const obj = {
                day: this.startDay.format('D MMMM, YYYY'), 
                threeDays: `${this.startDay.format("D")}-${this.startDay.clone().add(2, "days").format("D MMMM - YYYY")}`, 
                week:`${this.startDay.format("D")}-${this.startDay.clone().add(6, "days").format("D MMMM - YYYY")}`, 

            }
            return obj[this.activeType]
        },
    },
    data() {
        return {
            mountchActive: false,
            modalVisible: false,
            dateRange: null,
            locale,
            tempRange: []
        }
    },
    created() {
        if(this.activeType === 'listMonth')
            this.mountchActive = true
    },
    methods: {
        handleCalendarChange(dates) {
            this.tempRange = dates;
        },
        disabledDate(current) {
            const [start] = this.tempRange;
            if (!start) return false;
            const maxEnd = start.clone().add(1, 'month');
            return current.isAfter(maxEnd);
        },
        async downloadRangeFile() {
            const start = this.dateRange[0].clone().startOf("day").format("YYYY-MM-DDTHH:mm:ssZ")
            const end = this.dateRange[1].clone().endOf("day").format("YYYY-MM-DDTHH:mm:ssZ")
            await this.downloadFile({ start, end })
            this.modalVisible = false
        },
        openModal() {
            this.modalVisible = true
        },
        changeSwitchType(value) {
            if(value === 'listMonth')
                this.mountchActive = true
            else
                this.mountchActive = false
            this.handleChangeType({
                target: {
                    value
                }
            })
        },
        // handleButtonClick() {
        //     eventBus.$emit('open_event_form', 
        //         null, 
        //         null, 
        //         null, 
        //         this.relatedInfo, 
        //         this.uKey)
        // }
    }
}
</script>

<style lang="scss" scoped>
.calendar_page__header{
    display: flex;
    align-items: center;
    flex-direction: column;
    // padding: 10px 20px;
    @media (min-width: 970px) {
        flex-direction: row;
        justify-content: space-between;
    }
    h1{
        font-weight: 300;
        font-size: 24px;
        margin: 0px;
    }
}
.header__item {
    margin-bottom: 20px;

    @media (min-width: 970px) {
        margin-bottom: 0;
    }
}
</style>