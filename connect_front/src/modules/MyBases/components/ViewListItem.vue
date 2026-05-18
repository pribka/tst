<template>
    
    <a-card 
        :ref="`ticket_card_${ticket.id}`" 
        @click="openViewDrawer">
        <div class="mb-1 flex justify-between">
            <a-tag
                :color="ticket.status.color">
                {{ ticket.status.name }}
            </a-tag>
        </div>
        <div class="mb-1">
            <span class="font-semibold">
                Тип подключения:
            </span>
            <span>
                {{ ticket.connection_option.name }}
            </span>
        </div>
        <div
            v-if="ticket.user_count" 
            class="mb-1">
            <span class="font-semibold">
                Кол-во пользователей:
            </span>
            <span>
                {{ ticket.user_count }}
            </span>
        </div>
        <div class="mb-1 ">
            <span class="font-semibold mb-1 last:mb-0">
                Конфигурация:
            </span>
            <span>
                {{ ticket.config_1c.name }}
            </span>
        </div>  
        <!-- <div
            class="flex justify-end blue_color text-right text-xl" >
            <i 
                class="fi fi-rr-edit cursor-pointer"
                @click="openConnectDrawer">
            </i>
        </div> -->
        <ViewMobileActions
            class="text-green"
            :ref="`ticket_actions_${ticket.id}`"
            :showButton="false"
            :showStatus="false"
            :record="ticket">

        </ViewMobileActions>
    </a-card>
</template>

<script>
import eventBus from '@/utils/eventBus'
import ViewMobileActions from './ViewMobileActions.vue'
import { onLongPress } from '@vueuse/core'
export default {
    name: 'MyBasesListItem',
    props: {
        ticket: {
            type: Object,
            required: true
        }
    },
    components: {
        ViewMobileActions
    },
    data() {
        return {
        }
    },
    computed: {
        // statusColor() {
        //     if(this.ticket.status.code === 'under_review')
        //         return 'blue'
        //     return null
        // }
    },
    methods: {
        openConnectDrawer() {
            eventBus.$emit('OPEN_MY_BASES_DRAWER', { ticket: this.ticket })
        },    
        openViewDrawer() {
            eventBus.$emit('OPEN_MY_BASES_DRAWER_VIEW', this.ticket.id)
        }
    },
    mounted() {
        onLongPress(this.$refs[`ticket_card_${this.ticket.id}`], event => {
            event.preventDefault()
            event.stopPropagation()
            event.stopImmediatePropagation()
            this.$refs[`ticket_actions_${this.ticket.id}`].openDrawer()
        }, { modifiers: { prevent: true } })
    }
}
</script>

