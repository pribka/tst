<template>
    <div @click="selectTicket(item)">
        <a-card
            style="border-radius: var(--borderRadius);"
            size="small"
            :bordered="false"
            :ref="`ticket_card_${item.id}`"
            :class="[isMobile ? 'mmb mobile_card' : 'mb-2', isActive && 'active_select']"
            class="kanban-card">
            <div class="number pb-1 cursor-pointer" >
                #{{ item.number }}
            </div>
            <div class="ticket_name pb-2 cursor-pointer" >
                {{ item.name }}
            </div>
            <div class="flex items-center justify-between">
                <div class="flex items-center">
                    <template v-if="item.dead_line">
                        <i class="fi fi-rr-calendar mr-2" />
                        {{ $moment(item.dead_line).format('DD.MM.YYYY') }}
                    </template>
                </div>
                <div
                    v-if="item.author || item.specialist"
                    class="flex items-center cursor-pointer"
                    :ref="`ticket_card_users_${item.id}`">
                    <div v-if="item.author" class="flex">
                        <Profiler
                            :user="item.author"
                            :showUserName="false"
                            :avatarSize="20"
                            :getPopupContainer="getPopupContainer" />
                    </div>
                    <i v-if="item.author && item.specialist" class="fi fi-rr-angle-small-right mx-1 text-xs" />
                    <div v-if="item.specialist && item.specialist.id" class="flex">
                        <Profiler
                            :user="item.specialist"
                            :showUserName="false"
                            :avatarSize="20"
                            :getPopupContainer="getPopupContainer" />
                    </div>
                </div>
            </div>
        </a-card>
    </div>
</template>

<script>
export default {
    props: {
        item: [Object],
        selectTicket: {
            type: Function,
            default: () => {}
        },
        selectedTicket: {
            type: Object,
            default: () => {}
        }
    },
    computed: {
        isActive() {
            if(this.selectedTicket?.id === this.item.id)
                return true
            return false
        }
    },
    data() {
        return {
            isMobile: false
        }
    },
    methods: {
        getPopupContainer() {
            return this.$refs[`ticket_card_users_${this.item.id}`]
        }
    }
}
</script>

<style lang="scss" scoped>
.counter_rejected{
background: rgb(238, 42, 42);
color: white;
padding: 1px 2px;
border-radius: 4px;
}
.number{
    color: #888888;
}
.ticket_name{
    color: var(--blue);
}
.kanban-card{
    min-width: 100%;
    cursor: pointer;
    -webkit-user-select: none; 
    -khtml-user-select: none; 
    -moz-user-select: none; 
    -ms-user-select: none; 
    user-select: none;
    background: #fff;
    box-shadow: initial!important;
    border-color: #fff;
    &.mmb{
        margin-bottom: 10px;
    }
    &.active_select{
        border-color: var(--blue);
    }
}
</style>