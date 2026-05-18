<template>
    <div class="h-full flex items-center">
        <component 
            :is="memberWidget"
            :item="record" />
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
        isMeeting() {
            return this.model === 'meetings.PlannedMeetingModel'
        },
        memberWidget() {
            if(this.isMeeting)
                return () => import('../components/MeetingMembers.vue')
            return () => import('../components/Members.vue')
        }
    },
    components: {
        Members: () => import('../components/Members.vue')
    }
}
</script>