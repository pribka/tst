<template>
    <div class="project-meeting-desktop">
        <UniversalTable
            tableType="meetings"
            model="meetings.PlannedMeetingModel"
            :pageName="pageName"
            endpoint="/meetings/"
            :params="requestParams"
            :openHandler="openMeeting" />
    </div>
</template>

<script>
import { buildMeetingRequestParams } from './filterParams'

export default {
    name: 'ProjectMeetingDesktop',
    components: {
        UniversalTable: () => import('@/components/TableWidgets/UniversalTable.vue')
    },
    props: {
        id: {
            type: [String, Number],
            required: true
        },
        pageName: {
            type: String,
            required: true
        }
    },
    computed: {
        requestParams() {
            return buildMeetingRequestParams({
                filterState: this.$store.state.filter,
                pageName: this.pageName,
                projectId: this.id
            })
        }
    },
    methods: {
        openMeeting(record) {
            const query = { ...this.$route.query }
            if (!query.meeting) {
                query.meeting = record.id
                this.$router.push({ query })
            }
        }
    }
}
</script>

<style lang="scss" scoped>
.project-meeting-desktop {
    position: relative;
    overflow: hidden;
    display: flex;
    flex-direction: column;
    height: 100%;
    min-height: 0;
}
</style>
