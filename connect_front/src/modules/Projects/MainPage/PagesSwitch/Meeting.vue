<template>
    <div ref="meetingTab" class="project-meetings" :class="!isMobile && 'h-full flex flex-col min-h-0'">
        <div v-if="!isMobile" class="flex items-center justify-between gap-3 pb-3">
            <div class="flex items-center gap-3">
                <PageFilter
                    :key="pageName"
                    model="meetings.PlannedMeetingModel"
                    :page_name="pageName"
                    size="large"
                    :excludeFields="excludeFields"
                    :popoverMaxWidth="600"
                    :getPopupContainer="getPopupContainer" />
            </div>
            <SettingsButton
                :pageName="pageName"
                size="default"
                class="flex items-center justify-center" />
        </div>
        <component
            :is="viewComponent"
            :id="id"
            :page-name="pageName"
            class="min-h-0 flex-grow" />
        <div v-if="isMobile" class="float_add">
            <div class="filter_slot">
                <PageFilter
                    :key="pageName"
                    model="meetings.PlannedMeetingModel"
                    :page_name="pageName"
                    size="large"
                    :popoverMaxWidth="600"
                    :getPopupContainer="getPopupContainer" />
            </div>
        </div>
    </div>
</template>

<script>
export default {
    name: 'ProjectMeetingsPage',
    components: {
        PageFilter: () => import('@/components/PageFilter/index.vue'),
        SettingsButton: () => import('@/components/TableWidgets/SettingsButton'),
        ProjectMeetingDesktop: () => import('./Meeting/Desktop.vue'),
        ProjectMeetingMobile: () => import('./Meeting/Mobile.vue')
    },
    props: {
        id: {
            type: [String, Number],
            required: true
        }
    },
    computed: {
        excludeFields() {
            return ['project__exclude', 'project']
        },
        isMobile() {
            return this.$store.state.isMobile
        },
        pageName() {
            return `page_project_meetings.${this.id}`
        },
        viewComponent() {
            return this.isMobile ? 'ProjectMeetingMobile' : 'ProjectMeetingDesktop'
        }
    },
    methods: {
        getPopupContainer() {
            return this.$refs.meetingTab
        }
    }
}
</script>

<style lang="scss" scoped>
.project-meetings {
    height: 100%;
    position: relative;
}
</style>
