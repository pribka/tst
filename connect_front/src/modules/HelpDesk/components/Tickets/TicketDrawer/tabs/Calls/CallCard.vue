<template>
    <div class="call_card">
        <div class="item_field">
            <div class="item_head">
                {{ $t('table.initiator') }}:
            </div>
            <div class="item_value">
                <Profiler
                    v-if="item.initiator"
                    :user="item.initiator"
                    :avatarSize="18"
                    :getPopupContainer="trigger => trigger.parentNode"
                    hideSupportTag />
                <span v-else>-</span>
            </div>
        </div>

        <div class="item_field">
            <div class="item_head">
                {{ $t('table.accepted_by') }}:
            </div>
            <div class="item_value">
                <Profiler
                    v-if="item.accepted_by"
                    :user="item.accepted_by"
                    :avatarSize="18"
                    :getPopupContainer="trigger => trigger.parentNode"
                    hideSupportTag />
                <span v-else>-</span>
            </div>
        </div>

        <div class="item_field">
            <div class="item_head">
                {{ $t('table.created_at') }}:
            </div>
            <div class="item_value">
                <span>{{ formatDate(item.created_at) }}</span>
            </div>
        </div>

        <div class="item_field">
            <div class="item_head">
                {{ $t('table.ended_at') }}:
            </div>
            <div class="item_value">
                <span>{{ formatDate(item.ended_at) }}</span>
            </div>
        </div>

        <div class="item_field">
            <div class="item_head">
                {{ $t('table.status') }}:
            </div>
            <div class="item_value">
                <a-tag :color="statusMeta.color" block size="large">
                    {{ statusMeta.label }}
                </a-tag>
            </div>
        </div>
    </div>
</template>

<script>
const STATUS_META = {
    new: { color: 'blue', key: 'meeting.new' },
    created: { color: 'blue', key: 'meeting.new' },
    active: { color: 'processing', key: 'table.in_process' },
    in_progress: { color: 'processing', key: 'table.in_process' },
    accepted: { color: 'green', key: 'table.activity' },
    answered: { color: 'green', key: 'table.activity' },
    ended: { color: 'green', key: 'meeting.ended' },
    finished: { color: 'green', key: 'meeting.ended' },
    declined: { color: 'red', key: 'helpdesk.reject' },
    rejected: { color: 'red', key: 'helpdesk.reject' },
    missed: { color: 'orange', key: 'helpdesk.no_answer' },
    no_answer: { color: 'orange', key: 'helpdesk.no_answer' },
    canceled: { color: 'default', key: 'helpdesk.cancel' },
    cancelled: { color: 'default', key: 'helpdesk.cancel' }
}

export default {
    props: {
        item: {
            type: Object,
            required: true
        }
    },
    computed: {
        statusMeta() {
            const rawStatus = this.item?.status
            const value = typeof rawStatus === 'object' ? (rawStatus?.code || rawStatus?.value || rawStatus?.name) : rawStatus
            const normalized = String(value || '').toLowerCase()
            const meta = STATUS_META[normalized]

            if (meta) {
                return {
                    color: meta.color,
                    label: this.$t(meta.key)
                }
            }

            return {
                color: rawStatus?.color || 'default',
                label: rawStatus?.name || rawStatus?.label || value || '-'
            }
        }
    },
    methods: {
        formatDate(value) {
            return value ? this.$moment(value).format('DD.MM.YYYY HH:mm') : '-'
        }
    }
}
</script>

<style lang="scss" scoped>
.call_card {
    &:not(:last-child){
        margin-bottom: 10px;
        padding-bottom: 10px;
        border-bottom: 1px solid var(--borderColor);
    }

    .item_field {
        margin-bottom: 8px;
    }

    .item_head {
        margin-bottom: 4px;
        font-weight: 500;
    }

    .item_value {
        min-height: 20px;
    }
}
</style>
