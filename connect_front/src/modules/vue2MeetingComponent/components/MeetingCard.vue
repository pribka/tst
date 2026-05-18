<template>
    <div 
        v-touch:longtap="longtapHandler"
        class="meeting_card" 
        :class="isMobile && 'is_mobile'"
        @click="open()">
        <div class="truncate flex items-center justify-between">
            <div class="font-medium truncate pr-3">
                {{ item.name }}
            </div>
            <Status :status="item.status" />
        </div>
        <div class="flex items-center justify-between mt-2">
            <div class="begin_date whitespace-nowrap">
                {{ $t('meeting.formated_start_date', { date: $moment(item.date_begin).format('DD.MM.YYYY'), time: $moment(item.date_begin).format('HH:mm') }) }}
                - {{ dFormat }}
            </div>
            <Members :item="item" />
        </div>
        <CardActions
            v-if="showActions"
            :ref="`meeting_action_${item.id}`"
            :item="item" 
            :page_name="page_name" />
    </div>
</template>

<script>
import { durationFormat } from '../utils/index.js'
import { mapState } from 'vuex'
export default {
    name: "MeetingCard",
    components: {
        Status: () => import('./Status.vue'),
        Members: () => import('./Members.vue'),
        CardActions: () => import('./CardActions.vue')
    },
    props: {
        item: {
            type: Object,
            required: true
        },
        isScrolling: {
            type: Boolean,
            default: false
        },
        page_name: {
            type: String,
            default: 'page_list_meetings.PlannedMeetingModel'
        },
        actionsEnabled: {
            type: Boolean,
            default: true
        },
        showActions: {
            type: Boolean,
            default: true
        }
    },
    computed: {
        ...mapState({
            isMobile: state => state.isMobile
        }),
        dFormat() { 
            return durationFormat(this.item.duration)
        }
    },
    methods: {
        longtapHandler() {
            if(this.actionsEnabled) {
                this.$refs[`meeting_action_${this.item.id}`].openActionsDrawer()
            }
        },
        open() {
            const query = JSON.parse(JSON.stringify(this.$route.query))
            if(!query?.meeting) {
                query.meeting = this.item.id
                this.$router.push({query})
            }
        }
    }
}
</script>

<style lang="scss" scoped>
.meeting_card{
    padding: 12px;
    zoom: 1;
    font-size: 14px;
    font-variant: tabular-nums;
    line-height: 1.5;
    list-style: none;
    font-feature-settings: 'tnum';
    background: #f7f9fc;
    border-radius: var(--borderRadius);
    margin-bottom: 10px;
    -webkit-user-select: none; 
    -khtml-user-select: none; 
    -moz-user-select: none; 
    -ms-user-select: none; 
    user-select: none;
    transition: all 0.5s cubic-bezier(0.645, 0.045, 0.355, 1);
    cursor: pointer;
    &.is_mobile{
        background: #fff;
    }
    &.touch{
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
        transform: scale(0.97);
    }
    .begin_date{
        font-size: 13px;
    }
}
</style>