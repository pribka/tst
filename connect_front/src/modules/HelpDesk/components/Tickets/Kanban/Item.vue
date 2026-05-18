<template>
    <div :class="mainClass">
        <div
            size="small"
            :bordered="false"
            :ref="`ticket_card_${item.id}`"
            :class="isMobile ? 'mmb mobile_card' : 'mb-2'"
            :style="item.sla && `border-top: 4px solid ${item.sla.color};`"
            class="kanban-card ant-card">
            <div class="ant-card-body">
                <div class="number pb-1 cursor-pointer" @click="openTicket()">
                    #{{ item.number }}
                </div>
                <div class="ticket_name pb-2 cursor-pointer" @click="openTicket()">
                    {{ item.name }}
                </div>
                <div class="flex items-center gap-2 justify-between truncate">
                    <div class="flex items-center gap-2 truncate">
                        <template v-if="item.dead_line">
                            <i class="fi fi-rr-calendar" />
                            {{ $moment(item.dead_line).format('DD.MM.YYYY') }}
                        </template>
                        <div v-if="item.sla" class="flex items-center truncate" :title="item.sla.name">
                            <a-badge :color="item.sla.color" />
                            <div class="truncate">{{ item.sla.name }}</div>
                        </div>
                    </div>
                    <div
                        v-if="item.author || item.specialist"
                        class="flex items-center cursor-pointer"
                        :ref="`ticket_card_users_${item.id}`"
                        @click="openTicket()">
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
                <div v-if="item.customer_card" class="truncate mt-2" :title="item.customer_card.name">
                    {{ item.customer_card.name }}
                </div>
            </div>
        </div>
    </div>
</template>

<script>
import { mapState } from 'vuex'
import eventBus from '@/utils/eventBus'
export default {
    props: {
        item: [Object],
        isCompleted: {
            type: Boolean,
            default: false
        }
    },
    data() {
        return {
            isMobile: false
        }
    },
    computed: {
        ...mapState({
            user: state => state.user.user
        }),
        mainClass() {
            const { status, author, specialist } = this.item || {}
            const userId = this.user?.id

            /*if (status?.code === 'completed' || this.isCompleted)
                return 'not_active'*/

            const isAuthor = userId === author?.id
            const isSpecialist = userId === specialist?.id

            return isAuthor || isSpecialist ? 'active_task' : 'not_active'
        }
    },
    methods: {
        getPopupContainer() {
            return this.$refs[`ticket_card_users_${this.item.id}`]
        },
        openTicket() {
            const query = {...this.$route.query}
            if(!query.ticketView) {
                query.ticketView = this.item.id
                this.$router.push({query})
            } else {
                eventBus.$emit('ticket_drawer_close')
                setTimeout(() => {
                    query.ticketView = this.item.id
                    this.$router.push({query})
                }, 500)
            }
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
.not_active{
    .kanban-card{
        background: #edeff2;
        cursor: default;
    }
}
.active_task.drag-chosen,
.active_task.dragging-card{
    .kanban-card{
        box-shadow: 0 10px 24px rgba(21, 45, 89, 0.22) !important;
        transform-origin: center center;
    }
}
.active_task.drag-chosen{
    .kanban-card{
        transform: rotate(-1.4deg) scale(1.01);
    }
}
.active_task.dragging-card{
    .kanban-card{
        animation: cardDragWobble .9s ease-in-out infinite alternate;
    }
}
.number{
    color: #888888;
}
.ticket_name{
    color: var(--blue);
}
.kanban-card{
    min-width: 270px;
    border-radius: var(--borderRadius);
    cursor: move;
    -webkit-user-select: none; 
    -khtml-user-select: none; 
    -moz-user-select: none; 
    -ms-user-select: none; 
    user-select: none;
    background: #f7f9fc;
    box-shadow: initial!important;
    &.mobile_card{
        transition: all 0.5s cubic-bezier(0.645, 0.045, 0.355, 1);
        &.touch{
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
            transform: scale(0.97);
        }
    }
    &.mmb{
        margin-bottom: 10px;
    }
}

@keyframes cardDragWobble {
    0% {
        transform: rotate(-1.5deg) scale(1.01);
    }
    100% {
        transform: rotate(1.5deg) scale(1.02);
    }
}
</style>
