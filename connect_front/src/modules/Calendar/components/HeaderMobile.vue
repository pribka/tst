<template>
    <div class="calendar_page__header flex items-center justify-between" :class="related_object && 'inject'">
        <div class="flex items-center">
            <a-button
                @click="today"
                type="primary" 
                :disabled="todayCheck"
                ghost>
                {{ $t('calendar.today') }}
            </a-button>
            <div class="grid gap-1 grid-cols-2 ml-2">
                <a-button type="ui" flaticon icon="fi-rr-angle-small-left" @click="prev" />
                <a-button type="ui" flaticon icon="fi-rr-angle-small-right" @click="next" />
            </div>
        </div>
        <div class="flex items-center">
            <a-button 
                icon="fi-rr-calendar" 
                flaticon 
                type="ui" 
                class="mr-1"
                @click="openAside()" />
            <a-button type="ui" class="flex items-center" @click="visible = true">
                <template v-if="activeType === 'timeGridDay'">
                    {{ $t('calendar.day') }}
                </template>
                <template v-if="activeType === 'multiMonthYear'">
                    {{ $t('calendar.year') }}
                </template>
                <template v-if="activeType === 'listWeek'">
                    {{ $t('calendar.list') }}
                </template>
                <template v-if="activeType === 'listMonth'">
                    {{ $t('calendar.list') }}
                </template>
                <i class="ml-1 fi fi-rr-angle-small-down"></i>
            </a-button>
            <HelpButton v-if="!related_object" partCode="calendar" class="ml-1" type="button" />
        </div>
        
        <ActivityDrawer v-model="visible">
            <ActivityItem key="timeGridDay" class="ct_item" :class="activeType === 'timeGridDay' && 'active'" @click="changeType('timeGridDay')">
                <i class="fi fi-rr-calendar-week"></i> {{ $t('calendar.day') }}
            </ActivityItem>
            <ActivityItem key="listWeek" class="ct_item" :class="activeType === 'listWeek' && 'active'" @click="changeType('listWeek')">
                <i class="fi fi-rr-list-timeline"></i> {{ $t('calendar.list_week') }}
            </ActivityItem>
            <ActivityItem key="listMonth" class="ct_item" :class="activeType === 'listMonth' && 'active'" @click="changeType('listMonth')">
                <i class="fi fi-rr-list-timeline"></i> {{ $t('calendar.list_month') }}
            </ActivityItem>
        </ActivityDrawer>
    </div>
</template>

<script>
import { ActivityItem, ActivityDrawer } from '@/components/ActivitySelect'
export default {
    components: {
        ActivityItem,
        ActivityDrawer,
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
        },
        openAside: {
            type: Function,
            default: () => {}
        }
    },
    computed: {
        windowWidth() {
            return this.$store.state.windowWidth
        }
    },
    data() {
        return {
            visible: false
        }
    },
    methods: {
        changeType(event) {
            if(event === 'multiMonthYear') {
                this.clearEvents()
            }
            this.handleChangeType({
                target: {
                    value: event
                }
            })
        }
    }
}
</script>

<style lang="scss" scoped>
.ct_item{
    &.active{
        color: var(--blue);
    }
}
.calendar_page__header{
    padding: 10px 15px;
    position: sticky;
    left: 0px;
    z-index: 10;
    background: #fff;
    &:not(.inject){
        top: 50px;
    }
    &.inject{
        top: 0px;
    }
}
</style>