<template>
    <ModuleWrapper :pageTitle="pageTitle">
        <template v-slot:h_left>
            <slot />
        </template>
        <template v-slot:h_right>
            <AddButton :getRouteInfo="getRouteInfo" :model="model" />
            <HelpButton partCode="meetings" type="button" class="ml-2" />
            <component
                :is="settingsButtonWidget"   
                :pageName="pageName"
                size="default"
                class="ml-2" />
        </template>
        <component 
            :is="listComponent" 
            :isScrolling="isScrolling" />
    </ModuleWrapper>
</template>

<script>
import { useScroll } from '@vueuse/core'
export default {
    name: "MeetingList",
    props: {
        model: {
            type: String,
            default: 'main'
        },
        pageName: {
            type: String,
            default: 'page_list_meetings.PlannedMeetingModel'
        },
        pageModel: {
            type: String,
            default: 'meetings.PlannedMeetingModel'
        }
    },
    components: {
        HelpButton: () => import('@apps/Support/components/HelpButton.vue'),
        AddButton: () => import('./AddButton.vue'),
        SettingsButton: () => import('@/components/TableWidgets/SettingsButton'),
        ModuleWrapper: () => import('@/components/ModuleWrapper/index.vue')
    },
    computed: {
        getRouteInfo() {
            return this.$store.getters['navigation/getRouteInfo'](this.$route.name)
        },
        listComponent() {
            return () => import(/* webpackMode: "lazy" */'./TestTable.vue')
        },
        pageTitle() {
            return this.$route?.meta?.title || ''
        },
        settingsButtonWidget() {
            return () => import(/* webpackMode: "lazy" */'@/components/TableWidgets/SettingsButton')
        },
    },
    data() {
        return {
            isScrolling: false
        }
    },
    mounted() {
        this.$nextTick(() => {
            const { isScrolling } = useScroll(document)
            this.isScrolling = isScrolling
        })
    }
}
</script>