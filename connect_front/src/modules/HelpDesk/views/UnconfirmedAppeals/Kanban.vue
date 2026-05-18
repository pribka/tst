<template>
    <div class="flex-grow overflow-hidden">
        <div class="tickets_kanban h-full">
            <Kanban :page_name="initPageName" :queryParams="{ display: 'leads' }" />
        </div>
    </div>
</template>

<script>
import eventBus from '@/utils/eventBus'
export default {
    components: {
        Kanban: () => import('../../components/Tickets/Kanban/index.vue')
    },
    props: {
        initPageName: {
            type: String,
            default: ""
        },
        initPageModel: {
            type: String,
            default: ""
        }
    },
    methods: {
        listReload() {
            this.$nextTick(() => {
                eventBus.$emit(`update_filter_data_${this.initPageName}`)
            })
        }
    }
}
</script>

<style lang="scss" scoped>
.tickets_kanban{
    &::v-deep{
        .scroll_dummy{
            min-width: 15px;
        }
    }
}
</style>