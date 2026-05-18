<template>
    <div class="meeting_page">
        <div class="meeting_list flex-grow">
            <component 
                :is="listComponent" 
                :isScrolling="isScrolling" />
        </div>
        <div 
            class="float_add">
            <div class="filter_slot">
                <slot />
            </div>
            <a-button 
                v-if="getRouteInfo && getRouteInfo.pageActions && getRouteInfo.pageActions.add"
                flaticon
                shape="circle"
                size="large"
                type="primary"
                icon="fi-rr-plus"
                @click="$store.commit('meeting/SET_EDIT_DRAWER', { show: true, model: model })" />
        </div>
    </div>
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
        AddButton: () => import('./AddButton.vue'),
        SettingsButton: () => import('@/components/TableWidgets/SettingsButton')
    },
    computed: {
        getRouteInfo() {
            return this.$store.getters['navigation/getRouteInfo'](this.$route.name)
        },
        listComponent() {
            return () => import(/* webpackMode: "lazy" */'./List.vue')
        }
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

<style lang="scss" scoped>
.meeting_page{
    padding: 15px;
}
</style>