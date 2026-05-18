<template>
    <div class="calendar_page__header flex items-center justify-between">
        <h1 v-if="!related_object">{{ $t('calendar.calendar') }}</h1>
        <div class="flex items-center">
            <a-button
                @click="today"
                type="primary" 
                :disabled="todayCheck"
                ghost>
                {{ $t('calendar.today') }}
            </a-button>
            <div class="flex items-center mx-3">
                <a-button type="ui" ghost shape="circle" flaticon icon="fi-rr-angle-small-left" @click="prev" />
                <a-button type="ui" ghost shape="circle" flaticon icon="fi-rr-angle-small-right" @click="next" />
            </div>
            <Segmented 
                :value="activeType" 
                :options="listType"
                :bgInvert="related_object ? true : false"
                localStorageKey="calendar_active_type"
                :useLocalStorageSave="related_object ? false : true"
                @change="changeType" />

            <!--<a-radio-group 
                class="select-none"
                :value="activeType" 
                @change="changeType">
                <a-radio-button value="dayGridMonth">
                    {{ $t('calendar.month') }}
                </a-radio-button>
                <a-radio-button value="timeGridWeek">
                    {{ $t('calendar.week') }}
                </a-radio-button>
                <a-radio-button value="timeGridDay">
                    {{ $t('calendar.day') }}
                </a-radio-button>
                <a-radio-button value="multiMonthYear">
                    {{ $t('calendar.year') }}
                </a-radio-button>
                <a-radio-button :value="mountchActive ? 'listMonth' : 'listWeek'">
                    {{ $t('calendar.list') }}
                </a-radio-button>
            </a-radio-group>-->
            <transition name="fade">
                <div 
                    v-if="activeType === 'listWeek' || activeType === 'listMonth'" 
                    class="ml-4 flex items-center cursor-pointer"
                    @click="changeSwitchType(mountchActive ? 'listWeek' : 'listMonth')">
                    <a-switch :checked="mountchActive" /> 
                    <span class="ml-2">{{ $t('calendar.month') }}</span>
                </div>
            </transition>
        </div>
        <div class="flex items-center gap-2">
            <div 
                v-if="addEventCheck" 
                ref="calendarHeaderButton">
                <a-dropdown 
                    :getPopupContainer="getPopupContainer"
                    :trigger="['hover']">
                    <a-button 
                        type="primary" 
                        icon="fi-rr-plus-small" 
                        flaticon
                        @click="handleButtonClick">
                        <template v-if="windowWidth > 1086">{{ $t('calendar.add_event') }}</template>
                    </a-button>
                    <a-menu v-if="!related_object" slot="overlay">
                        <a-menu-item key="1" class="flex items-center" @click="addCalendar()">
                            <i class="fi fi-rr-calendar-plus mr-2"></i>
                            {{ $t('calendar.add_calendar') }}
                        </a-menu-item>
                    </a-menu>
                </a-dropdown>
            </div>
            <HelpButton v-if="!related_object" partCode="calendar" type="button" />
        </div>
    </div>
</template>

<script>
import eventBus from '@/utils/eventBus'
export default {
    components: {
        Segmented: () => import('@apps/UIModules/Segmented'),
        HelpButton: () => import('@apps/Support/components/HelpButton.vue')
    },
    props: {
        activeType: {
            type: String,
            required: true
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
        uKey: {
            type: [String, Number],
            default: 'default'
        },
        addEventCheck: {
            type: Boolean,
            default: true
        },
        clearEvents: {
            type: Function,
            default: () => {}
        }
    },
    computed: {
        windowWidth() {
            return this.$store.state.windowWidth
        },
        listType() {
            return [
                {
                    key: 'dayGridMonth',
                    title: this.$t('calendar.month')
                },
                {
                    key: 'timeGridWeek',
                    title: this.$t('calendar.week')
                },
                {
                    key: 'timeGridDay',
                    title: this.$t('calendar.day')
                },
                {
                    key: this.mountchActive ? 'listMonth' : 'listWeek',
                    title: this.$t('calendar.list')
                },
            ]
        }
    },
    data() {
        return {
            mountchActive: false
        }
    },
    created() {
        if(this.activeType === 'listMonth')
            this.mountchActive = true
    },
    methods: {
        changeType(value) {
            if(value === 'multiMonthYear') {
                this.clearEvents()
            }
            this.handleChangeType({
                target: {
                    value
                }
            })
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
        getPopupContainer() {
            return this.$refs.calendarHeaderButton
        },
        handleButtonClick() {
            eventBus.$emit('open_event_form', 
                null, 
                null, 
                null, 
                this.relatedInfo, 
                this.uKey,
                false,
                this.related_object)
        }
    }
}
</script>

<style lang="scss" scoped>
.calendar_page__header{
    padding: 10px 20px;
    h1{
        font-weight: 400;
        font-size: 18px;
        margin: 0px;
    }
}
</style>
