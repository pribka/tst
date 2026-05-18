<template>
    <component :is="listComponent" :pageName="pageName" :pageModel="pageModel">
        <slot />
    </component>
</template>

<script>
export default {
    name: "MeetingIndex",
    props: {
        pageName: {
            type: String,
            default: 'page_list_meetings.PlannedMeetingModel'
        },
        pageModel: {
            type: String,
            default: 'meetings.PlannedMeetingModel'
        }
    },
    computed: {
        isMobile() {
            return this.$store.state.isMobile
        }
    },
    data() {
        return {
            listComponent: null
        }
    },
    created() {
        this.listComponent = this.isMobile
            ? () => import('./components/MeetingListMobile.vue')
            : () => import('./components/MeetingList.vue')
    }
}
</script>