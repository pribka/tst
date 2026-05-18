<template>
    <vue2MeetingComponent>
        <template>
            <PageFilter 
                model="meetings.PlannedMeetingModel"
                key="page_list_meetings.PlannedMeetingModel"
                size="large"
                :popoverMaxWidth="600"
                page_name="page_list_meetings.PlannedMeetingModel" />
        </template>
    </vue2MeetingComponent>
</template>

<script>
import pageMeta from '@/mixins/pageMeta'
export default {
    mixins: [pageMeta],
    components: {
        vue2MeetingComponent: () => import('@apps/vue2MeetingComponent'),
        PageFilter: () => import('@/components/PageFilter/index.vue')
    }
}
</script>
