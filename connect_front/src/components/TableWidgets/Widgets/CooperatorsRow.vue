<template>
    <div class="h-full flex items-center">
        <component 
            :is="memberWidget"
            :item="task" />
    </div>
</template>

<script>
export default {
    props: {
        record: {
            type: Object,
            required: true
        },
        model: {
            type: String
        },
    },
    computed: {
        task() {
            return { users: this.record?.cooperators?.map(item => item.user) }
        },
        isMeeting() {
            return this.model === 'meetings.PlannedMeetingModel'
        },
        memberWidget() {
            if(this.isMeeting)
                return () => import('../components/MeetingMembers.vue')
            return () => import('../components/Members.vue')
        }
    },
}
</script>