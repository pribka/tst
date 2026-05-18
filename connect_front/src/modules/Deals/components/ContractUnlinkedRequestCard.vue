<template>
    <div
        class="contract_unlinked_request"
        :class="{ 'is-selected': selected }"
        @click="$emit('toggle', ticket.id)">
        <div class="request_card">
            <div class="request_card__title_row">
                <a-checkbox
                    class="contract_unlinked_request__checkbox"
                    :checked="selected"
                    @click.stop
                    @change="$emit('toggle', ticket.id)" />
                <div class="request_card__name blue_color truncate" @click.stop="$emit('open', ticket.id)">
                    #{{ ticket.number || '-' }} {{ ticket.name || '-' }}
                </div>
            </div>

            <div v-if="ticket.category" class="request_card__info">
                <span class="request_card__label">{{ $t('helpdesk.category') }}:</span> {{ ticket.category.name }}
            </div>

            <div v-if="ticket.channel" class="request_card__info flex items-center">
                <span class="request_card__label">{{ $t('helpdesk.communication_channel') }}:</span>
                <template v-if="ticket.channel?.icon">
                    <img
                        v-if="isSVG"
                        :src="require(`@/assets/svg/${ticket.channel.icon}`)"
                        class="mr-2 channel_icon" />
                    <i
                        v-else
                        class="mr-2 fi"
                        :class="ticket.channel.icon" />
                </template>
                {{ ticket.channel.name }}
            </div>

            <div v-if="ticket.related_tasks && ticket.related_tasks.length" class="request_card__info">
                <span class="request_card__label">{{ $t('table.related_tasks') }}:</span>
                <div class="flex flex-wrap gap-x-2 gap-y-1">
                    <div
                        v-for="(task, index) in ticket.related_tasks"
                        :key="task.id"
                        class="blue_color cursor-pointer"
                        @click.stop="$emit('open-task', task.id)">
                        #{{ task.counter }}<span v-if="index !== ticket.related_tasks.length - 1">, </span>
                    </div>
                </div>
            </div>

            <div class="flex items-center justify-between gap-2">
                <div class="truncate flex items-center request_card__date">
                    <i class="fi fi-rr-calendar mr-2" />
                    {{ formatDate(ticket.created_at || ticket.receipt_date) }}
                </div>
                <div class="flex items-center gap-2">
                    <ViewRating :rating="ticket.rating" />
                    <Profiler
                        v-if="ticket.specialist"
                        :avatarSize="20"
                        :showUserName="false"
                        :user="ticket.specialist" />
                    <a-tag v-if="ticket.status" :color="ticket.status.color">
                        {{ ticket.status.name || ticket.status.code || ticket.status.string_view }}
                    </a-tag>
                </div>
            </div>
        </div>
    </div>
</template>

<script>
export default {
    name: 'ContractUnlinkedRequestCard',
    components: {
        ViewRating: () => import('@apps/HelpDesk/components/Request/RequestDrawer/components/ViewRating.vue'),
    },
    props: {
        ticket: {
            type: Object,
            required: true,
        },
        selected: {
            type: Boolean,
            default: false,
        },
    },
    computed: {
        isSVG() {
            return this.ticket.channel?.icon?.endsWith('.svg')
        },
    },
    methods: {
        formatDate(value) {
            if (!value) return '-'
            const m = this.$moment(value)
            return m.isValid() ? m.format('DD.MM.YYYY') : '-'
        },
    },
}
</script>

<style lang="scss" scoped>
.contract_unlinked_request {
    border: 1px solid transparent;
    border-radius: var(--borderRadius);
    cursor: pointer;
    transition: border-color .2s ease, box-shadow .2s ease;

    &.is-selected {
        border-color: #2f5ff5;
        box-shadow: 0 6px 16px rgba(47, 95, 245, 0.12);
    }
}

.request_card {
    padding: 12px;
    zoom: 1;
    font-size: 14px;
    font-variant: tabular-nums;
    line-height: 1.5;
    list-style: none;
    font-feature-settings: 'tnum';
    background: #ffffff;
    border-radius: var(--borderRadius);
    user-select: none;
}

.request_card__title_row {
    display: flex;
    align-items: center;
    min-width: 0;
    margin-bottom: 8px;
}

.request_card__name {
    cursor: pointer;
    min-width: 0;
}

.contract_unlinked_request__checkbox {
    flex-shrink: 0;
    margin-right: 8px;
}

.request_card__info {
    margin-bottom: 8px;
    font-size: 13px;
    line-height: 15px;
}

.request_card__label,
.request_card__date {
    color: #656565;
}

.request_card__date {
    font-size: 13px;
    line-height: 15px;
}

.channel_icon {
    max-width: 16px;
}
</style>
