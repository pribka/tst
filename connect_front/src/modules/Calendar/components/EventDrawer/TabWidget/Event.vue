<template>
    <div v-if="event">
        <div class="event_datetime"><i class="fi fi-rr-calendar-clock"></i>{{ eventDateTime }}</div>

        <Aside
            v-if="isMobile"
            :event="event"
            :actions="actions"
            :createMeeting="createMeeting"
            :toggleMeetingStatus="toggleMeetingStatus"
            :refreshEventDetails="refreshEventDetails" />

        <TextViewer v-if="event.description" :body="event.description" />
        <div 
            v-else
            class="gray mt-1"
            :class="isMobile && 'py-2'">
            {{ $t('calendar.no_description') }}
        </div>
        <!-- Comments -->
        <div class="mt-5">
            <div class="mb-1 font-semibold">
                {{ $t('calendar.comments') }}
            </div>
            <vue2CommentsComponent
                bodySelector=".event_body_wrap"
                :related_object="event.id"
                model="events" />
        </div>
    </div>
</template>

<script>
export default {
    props: {
        event: {
            type: Object,
            required: true
        },
        actions: {
            type: Object,
            default: () => null
        },
        createMeeting: {
            type: Function,
            default: () => {}
        },
        toggleMeetingStatus: {
            type: Function,
            default: () => {}
        },
        refreshEventDetails: {
            type: Function,
            default: async () => null
        }
    },
    components: {
        TextViewer: () => import('@apps/CKEditor/TextViewer.vue'),
        vue2CommentsComponent: () => import('@apps/vue2CommentsComponent'),
        Aside: () => import('../Aside.vue')
    },
    computed: {
        isMobile() {
            return this.$store.state.isMobile
        },
        eventDateTime() {
            if(this.event) {
                if(this.$moment(this.event.start_at).format('DD.MM.YYYY') === this.$moment(this.event.end_at).format('DD.MM.YYYY')) {
                    if(this.event.all_day) {
                        return `${this.$moment(this.event.start_at).format('dddd, DD MMMM')}, ${this.$t('calendar.all_day')}`
                    } else {
                        return `${this.$moment(this.event.start_at).format('dddd, DD MMMM HH:mm')} - ${this.$moment(this.event.end_at).format('HH:mm')}`
                    }
                } else {
                    if(this.event.all_day) {
                        if(this.$moment(this.event.start_at).format('ddd, DD MMM') === this.$moment(this.event.end_at).format('ddd, DD MMM')) {
                            return `${this.$moment(this.event.start_at).format('dddd, DD MMMM')}, ${this.$t('calendar.all_day')}`
                        } else {
                            return `${this.$moment(this.event.start_at).format('ddd, DD MMM')} - ${this.$moment(this.event.end_at).format('ddd, DD MMM')}`
                        }
                    } else {
                        return `${this.$moment(this.event.start_at).format('ddd, DD MMM HH:mm')} - ${this.$moment(this.event.end_at).format('ddd, DD MMM HH:mm')}`
                    }
                }
            } else {
                return null
            }
        }
    }
}
</script>

<style lang="scss" scoped>
.event_datetime{
    font-weight: 500;
    font-size: 18px;
    margin-bottom: 15px;
    color: #000;
    display: flex;
    align-items: center;
    i{
        margin-right: 8px;
        color: var(--gray);
    }
}
</style>
