<template>
    <div
        class="ticket_card rounded-lg select-none"
        :class="[collapse && 'ticket_card_open', useInject && 'bg_invert']"
        :style="`border-left-color: ${cardTopColor};`">
        <div class="ticket_card__wrapper cursor-pointer" @click="collapseTicket()">
            <div class="flex items-start justify-between gap-5">
                <div class="truncate">
                    <div class="ticket_head_line flex items-center gap-2 mb-2 truncate" @click.stop="openTicket()">
                        <a-tag v-if="ticket.status && ticket.status.name" :color="ticket.status.color || 'default'" class="mb-0 ticket_status">
                            {{ ticket.status.name }}
                        </a-tag>
                        <span class="ticket_number shrink-0">#{{ ticket.number }}</span>
                        <span
                            class="font-semibold truncate ticket_name"
                            :title="ticket.name || $t('workplan.ticket_no_name')">
                            {{ ticket.name || $t('workplan.ticket_no_name') }}
                        </span>
                    </div>
                    <div class="ticket_meta flex items-center flex-wrap gap-x-4 gap-y-1 mt-2">
                        <div v-if="ticket.dead_line" class="flex items-center opacity-80">
                            <i class="fi fi-rr-calendar mr-1" />
                            {{ deadLineReadable }}
                        </div>
                        <div class="flex items-center opacity-80">
                            <i class="fi fi-rr-clock mr-1" />
                            {{ $t('workplan.in_work') }} {{ actualDurationDays }}
                        </div>
                        <div class="flex items-center opacity-80">
                            {{ $t('workplan.today_short') }}:<span class="font-semibold ml-1">{{ secondsFormat(ticket.duration_total_range) }}</span>
                        </div>
                        <div class="flex items-center opacity-80">
                            {{ $t('workplan.total_short') }}:<span class="font-semibold ml-1">{{ secondsFormat(ticket.duration_total_all) }}</span>
                        </div>
                        <div v-if="ticket.sla && ticket.sla.name" class="flex items-center">
                            <a-badge :color="ticket.sla.color || '#d9d9d9'" />
                            {{ ticket.sla.name }}
                        </div>
                        <div class="flex items-center gap-2">
                            <Profiler
                                v-if="ticket.author"
                                :avatarSize="22"
                                :showUserName="false"
                                hideSupportTag
                                :user="ticket.author" />
                            <i v-if="ticket.author && ticket.specialist" class="fi fi-rr-angle-small-right opacity-70" />
                            <Profiler
                                v-if="ticket.specialist"
                                :avatarSize="22"
                                :showUserName="false"
                                hideSupportTag
                                :user="ticket.specialist" />
                        </div>
                    </div>
                    <div v-if="ticket.customer_card && ticket.customer_card.name" class="ticket_customer mt-2 truncate">
                        {{ ticket.customer_card.name }}
                    </div>
                    <div v-if="isMobile && timerButtonComp" class="mt-2">
                        <component
                            :is="timerButtonComp"
                            :ticket="ticket"
                            :storeKey="storeKey"
                            :listType="listType"
                            :isActiveTab="isActiveTab"
                            mobile />
                    </div>
                </div>
                <div class="card_actions gap-2 md:gap-3">
                    <component
                        :is="timerButtonComp"
                        v-if="!isMobile && timerButtonComp"
                        :ticket="ticket"
                        :storeKey="storeKey"
                        :listType="listType"
                        :isActiveTab="isActiveTab" />
                    <a-spin v-if="loading" size="small" />
                    <i v-else class="fi fi-rr-angle-small-down card_arrow block" style="opacity: 0.5;font-size: 16px;" />
                </div>
            </div>
        </div>
        <div v-if="collapse" class="collapse_wrapper">
            <div class="collapse_wrapper__divider" style="margin-bottom: 10px" />
            <component :is="collapseBodyComp" :ticket="ticket" :detail="detail" :showResultTab="showResultTab" />
        </div>
    </div>
</template>

<script>
import { mapState } from 'vuex'
import { errorHandler } from '@/utils/index.js'
import { declOfNum, secondsFormat } from '@/utils/utils.js'

export default {
    props: {
        ticket: {
            type: Object,
            required: true
        },
        storeKey: {
            type: String,
            required: true
        },
        listType: {
            type: String,
            default: 'ticketList'
        },
        isActiveTab: {
            type: Boolean,
            default: false
        },
        useInject: {
            type: Boolean,
            default: false
        }
    },
    computed: {
        ...mapState({
            user: state => state.user.user
        }),
        isMobile() { 
            return this.$store.state.isMobile
        },
        canShowTimerButton() {
            const userId = this.user?.id
            if(!userId) return false
            return this.ticket?.specialist?.id === userId || this.ticket?.author?.id === userId
        },
        timerButtonComp() {
            if(this.canShowTimerButton)
                return () => import('./TicketTimerButton.vue')
            return null
        },
        cardTopColor() {
            if(this.ticket.sla?.color)
                return this.ticket.sla.color
            return 'transparent'
        },
        deadLineReadable() {
            if(!this.ticket.dead_line) return ''
            return this.$moment(this.ticket.dead_line).format('DD.MM.YYYY')
        },
        actualDurationDays() {
            return `${this.ticket.actual_duration_days} ${declOfNum(this.ticket.actual_duration_days, [this.$t('workplan.day_one'), this.$t('workplan.day_few'), this.$t('workplan.day_many')])}`
        },
        detailTicket() {
            return this.detail || this.ticket
        },
        showResultTab() {
            const statusCode = this.detailTicket?.status?.code
            const hasResult = !!this.detailTicket?.execution_result
            return hasResult && ['completed', 'rejected'].includes(statusCode)
        },
        collapseBodyComp() {
            if(this.collapse)
                return () => import('./CollapseBody.vue')
            return null
        },
        ticketRefreshKey() {
            return [
                this.ticket?.id || '',
                this.ticket?.updated_at || '',
                this.ticket?.status?.code || '',
                this.ticket?.duration_total_range || 0,
                this.ticket?.duration_total_all || 0,
                this.ticket?.actual_duration_days || 0
            ].join('|')
        },
        collapse: {
            get() {
                return this.ticket.collapse || false
            },
            set(value) {
                this.$store.commit('workplan/CHANGE_COLLAPSE', {
                    storeKey: this.storeKey,
                    value,
                    item: this.ticket,
                    list: this.listType
                })
            }
        }
    },
    data() {
        return {
            loading: false,
            detail: null,
            refreshLoading: false
        }
    },
    watch: {
        ticket() {
            this.refreshOpenedCardData()
        },
        ticketRefreshKey() {
            this.refreshOpenedCardData()
        }
    },
    methods: {
        secondsFormat,
        async refreshOpenedCardData() {
            if(!this.collapse || this.loading || this.refreshLoading) return
            try {
                this.refreshLoading = true
                await Promise.all([
                    this.getActions(true),
                    this.getTicketDetail()
                ])
            } finally {
                this.refreshLoading = false
            }
        },
        async getTicketDetail() {
            try {
                const { data } = await this.$http.get(`/help_desk/tickets/${this.ticket.id}/`)
                if(data)
                    this.detail = data
            } catch(error) {
                errorHandler({error, show: false})
            }
        },
        async getActions(force = false) {
            try {
                await this.$store.dispatch('workplan/getTicketActions', {
                    storeKey: this.storeKey,
                    item: this.ticket,
                    list: this.listType,
                    force
                })
            } catch(error) {
                errorHandler({error, show: false})
            }
        },
        async collapseTicket() {
            try {
                this.loading = true
                if(!this.collapse) {
                    if(!this.ticket.actions)
                        await this.getActions()
                    await this.getTicketDetail()
                }
            } finally {
                this.loading = false
            }
            this.collapse = !this.collapse
        },
        openTicket() {
            const query = JSON.parse(JSON.stringify(this.$route.query))
            query.ticketView = this.ticket.id
            this.$router.replace({ query })
        }
    }
}
</script>

<style lang="scss" scoped>
.collapse_wrapper{
    padding-left: 15px;
    padding-right: 15px;
    padding-bottom: 15px;
    @media (min-width: 768px) {
        padding-left: 20px;
        padding-right: 20px;
        padding-bottom: 20px;
    }
    &__divider{
        margin-bottom: 15px;
        height: 1px;
        background: #e8e8e8;
        @media (min-width: 768px) {
            margin-bottom: 20px;
        }
        &.no_mb{
            margin-bottom: 0;
        }
    }
}
.ticket_card{
    background: #fff;
    border-left: 4px solid transparent;
    &.bg_invert{
        background: #f7f9fc;
    }
    .card_arrow{
        transition: all 0.3s cubic-bezier(0.645, 0.045, 0.355, 1);
    }
    &__wrapper{
        padding: 15px;
        @media (min-width: 768px) {
            padding: 20px;
        }
    }
    &:not(:last-child){
        margin-bottom: 10px;
        @media (min-width: 768px) {
            margin-bottom: 15px;
        }
    }
    &.ticket_card_open{
        .card_arrow{
            transform: rotate(180deg);
        }
    }
}
.ticket_name{
    transition: all 0.3s cubic-bezier(0.645, 0.045, 0.355, 1);
    &:hover{
        color: var(--blue);
    }
}
.ticket_number{
    color: #888888;
    font-weight: 600;
}
.ticket_status{
    border-radius: 30px;
    padding-inline: 10px;
    line-height: 24px;
}
.ticket_meta{
    font-size: 13px;
}
.ticket_customer{
    color: #888888;
}
.card_actions{
    display: flex;
    align-items: center;
}
</style>
