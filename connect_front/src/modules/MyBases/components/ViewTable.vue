<template>
    <div class="w-full flex flex-col overflow-hidden">
        <div class="flex mb-4">
            <div class="mr-2" v-if="$slots.connectButton">
                <slot name="connectButton"></slot>
            </div>
            <div class="mr-2" v-if="$slots.pageFilter">
                <slot name="pageFilter"></slot>
            </div>
            
            <SettingsButton
                :pageName="pageName" />
        </div>
        <div class="flex-grow min-h-0 flex flex-col">
            <UniversalTable 
                class=""
                :model="model"
                :pageName="pageName"
                :tableType="tableType"
                :endpoint="endpoint"
                :openHandler="openViewDrawer" />
        </div>
    </div>
</template>

<script>
import UniversalTable from '@/components/TableWidgets/UniversalTable'
import SettingsButton from '@/components/TableWidgets/SettingsButton'
import eventBus from '@/utils/eventBus'

import { mapActions, mapState } from 'vuex'
export default {
    name: 'MyBasesTable',
    components: {
        UniversalTable,
        SettingsButton
    },
    props: {
        model: {
            type: String,
            default: 'tickets.TicketModel',
        },
        pageName: {
            type: String,
            default: 'IncomingServiceTicketModel'
        }
    },
    data() {
        return {
            tableType: 'tickets',
            page: 1,
            // TODO: сделать норм параметры
            // pageName: 'IncomingServiceTicketModel',
            listLoading: false
        }
    },
    computed: {
        endpoint() {
            return `/tickets/list/`
        },
    },
    methods: {
        openViewDrawer(ticket) {
            eventBus.$emit('OPEN_MY_BASES_DRAWER_VIEW', ticket.id)
        }
    }
}
</script>

