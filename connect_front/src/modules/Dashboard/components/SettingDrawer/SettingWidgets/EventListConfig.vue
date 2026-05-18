<template>
    <div class="event_config">
        <Aside 
            :showCalendar="false" 
            :page_name="pageName"
            activeType="listWeek" />
    </div>
</template>

<script>
export default {
    props: {
        widget: {
            type: Object,
            required: true
        },
        closeSettingDrawer: {
            type: Function,
            default: () => {}
        }
    },
    components: {
        Aside: () => import('@apps/Calendar/components/Aside.vue')
    },
    computed: {
        pageName() {
            return (this.widget.page_name || this.widget.id) || this.widget.widget.id
        }
    },
    methods: {
        saveConfig() {
            this.closeSettingDrawer()
        },
        resetConfig() {
            this.closeSettingDrawer()
        }
    }
}
</script>

<style lang="scss" scoped>
.event_config{
    &::v-deep{
        .calendars_list{
            padding: 0px!important;
        }
        .calendar_aside{
            width: 100%!important;
            border: 0px!important;
        }
        .calendar_aside__scroller{
            height: initial;
            overflow: initial;
        }
        .calendar_aside__toggle{
            display: none;
        }
    }
}
</style>