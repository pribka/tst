<template>
    <div class="flex flex-col h-full">
        <div class="flex items-center gap-5 mb-3" :class="isKanban && 'header_pd'">
            <Segmented 
                v-model="viewType" 
                :options="listType"
                localStorageKey="ticket_unconfirmed_list_type"
                useLocalStorageSave
                @change="changeMainViewType(viewType)" />
        </div>
        <component 
            :is="viewComponent" 
            ref="listComponetn"
            :initPageName="initPageName" 
            :initPageModel="initPageModel" />
    </div>
</template>

<script>
export default {
    components: {
        Segmented: () => import('@apps/UIModules/Segmented'),
        TicketFilter: () => import('../../components/TicketFilter.vue')
    },
    props: {
        initPageName: {
            type: String,
            required: true
        },
        initPageModel: {
            type: String,
            required: true
        },
        changeMainViewType: {
            type: Function,
            default: () => {}
        }
    },
    data() {
        return {
            viewType: 'table',
            listType: [
                {
                    key: 'table',
                    title: 'Список'
                },
                {
                    key: 'kanban',
                    title: 'Канбан'
                }
            ]
        }
    },
    sockets: {
        notify({ data }) {
            if(data.event_type === 'help_desk_new_ticket' && this.$refs?.listComponetn)
                this.$refs.listComponetn.listReload()
        }
    },
    computed: {
        viewComponent() {
            if(this.viewType === 'table')
                return () => import('./List.vue')
            return () => import('./Kanban.vue')
        },
        isKanban() {
            return this.viewType === 'kanban' ? true : false
        }
    }
}
</script>

<style lang="scss" scoped>
.header_pd{
    padding: 15px 15px 0 15px;
}
</style>