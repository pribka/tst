<template>
    <div class="relation_list">
        <template v-if="items.length">
            <div
                v-for="item in items"
                :key="item.id"
                class="relation_card">
                <div class="relation_card__head">
                    <div class="relation_card__title" :title="getTitle(item)">
                        {{ getTitle(item) }}
                    </div>
                    <a-button
                        v-if="item.id"
                        type="link"
                        class="px-0"
                        @click="$emit('open', item)">
                        Открыть
                    </a-button>
                </div>
                <div v-if="getSecondary(item)" class="relation_card__secondary">
                    {{ getSecondary(item) }}
                </div>
                <div v-if="getMeta(item).length" class="relation_card__meta">
                    <a-tag
                        v-for="meta in getMeta(item)"
                        :key="meta"
                        class="relation_card__tag">
                        {{ meta }}
                    </a-tag>
                </div>
                <div v-if="getDate(item)" class="relation_card__date">
                    {{ getDate(item) }}
                </div>
            </div>
        </template>
        <a-empty v-else :description="emptyText" />
    </div>
</template>

<script>
export default {
    name: 'DealRelationList',
    props: {
        type: {
            type: String,
            required: true
        },
        items: {
            type: Array,
            default: () => []
        },
        emptyText: {
            type: String,
            default: 'Связанные элементы пока не добавлены.'
        }
    },
    methods: {
        getTitle(item) {
            const candidates = [
                item?.name,
                item?.title,
                item?.full_name,
                item?.document_name,
                item?.string_view,
                item?.request_type?.name,
                item?.document_type?.name,
                item?.document_type_name,
                item?.counter ? `#${item.counter}` : null,
                item?.number ? `#${item.number}` : null,
                item?.id,
            ]
            return candidates.find(Boolean) || 'Без названия'
        },
        getSecondary(item) {
            if (this.type === 'documents') {
                return item?.document_type?.name || item?.document_type_name || ''
            }
            if (this.type === 'approvals') {
                return item?.organization?.name || item?.request_type?.name || ''
            }
            if (this.type === 'orders') {
                return item?.contractor?.name || item?.counterparty?.name || ''
            }
            if (this.type === 'meetings') {
                return item?.author?.full_name || ''
            }
            return ''
        },
        getMeta(item) {
            const values = []
            if (item?.counter) {
                values.push(`№${item.counter}`)
            } else if (item?.number) {
                values.push(`№${item.number}`)
            }

            const statusName = item?.status?.name || item?.status?.label || item?.status
            if (statusName && typeof statusName === 'string') {
                values.push(statusName)
            }

            if (item?.amount_requested) {
                values.push(this.formatMoney(item.amount_requested))
            } else if (item?.total_amount) {
                values.push(this.formatMoney(item.total_amount))
            } else if (item?.amount) {
                values.push(this.formatMoney(item.amount))
            }

            return values.filter(Boolean)
        },
        getDate(item) {
            const raw = item?.date_begin || item?.created_at || item?.updated_at || item?.dead_line
            if (!raw) return ''
            const m = this.$moment(raw)
            return m.isValid() ? m.format('DD.MM.YYYY HH:mm') : ''
        },
        formatMoney(value) {
            const numeric = Number(value)
            if (!Number.isFinite(numeric)) return value
            return new Intl.NumberFormat('ru-RU', {
                maximumFractionDigits: 2,
            }).format(numeric)
        }
    }
}
</script>

<style lang="scss" scoped>
.relation_list {
    display: grid;
    gap: 12px;
}

.relation_card {
    border: 1px solid var(--border2);
    border-radius: 14px;
    background: #fff;
    padding: 14px 16px;
}

.relation_card__head {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    gap: 12px;
}

.relation_card__title {
    color: #111827;
    font-size: 15px;
    font-weight: 600;
    line-height: 1.35;
}

.relation_card__secondary {
    margin-top: 6px;
    color: #6b7280;
    font-size: 13px;
}

.relation_card__meta {
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
    margin-top: 10px;
}

.relation_card__tag {
    margin-right: 0;
    border-radius: 999px;
}

.relation_card__date {
    margin-top: 10px;
    color: #94a3b8;
    font-size: 12px;
}
</style>
