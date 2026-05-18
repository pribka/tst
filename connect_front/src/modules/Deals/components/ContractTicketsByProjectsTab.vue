<template>
    <div class="contract_tickets_tab">
        <div class="contract_tickets_tab__head">
            <div>
                <div class="contract_tickets_tab__title">{{ $t('deals_contracts.requests_tab') }}</div>
                <div class="contract_tickets_tab__subtitle">{{ $t('deals_contracts.requests_subtitle') }}</div>
            </div>
            <a-button
                type="ui"
                ghost
                icon="fi-rr-refresh"
                flaticon
                :loading="loading"
                @click="loadTickets">
                {{ $t('deals_contracts.refresh') }}
            </a-button>
        </div>

        <a-spin :spinning="loading" class="w-full">
            <div v-if="projectGroups.length" class="contract_tickets_tab__groups">
                <div
                    v-for="group in projectGroups"
                    :key="group.id"
                    class="contract_tickets_tab__group">
                    <div class="contract_tickets_tab__group_head">
                        <div class="contract_tickets_tab__group_title">{{ group.projectName }}</div>
                        <a-tag>{{ group.tickets.length }}</a-tag>
                    </div>

                    <a-table
                        v-if="!isMobile"
                        :columns="columns"
                        :data-source="group.tickets"
                        :pagination="false"
                        :row-key="record => record.id"
                        class="contract_tickets_tab__table">
                        <template slot="number" slot-scope="text">
                            <span class="text-slate-500">#{{ text || '-' }}</span>
                        </template>
                        <template slot="name" slot-scope="text, record">
                            <a-button type="link" class="px-0" @click="$emit('open', record.id)">
                                {{ text || '-' }}
                            </a-button>
                        </template>
                        <template slot="status" slot-scope="statusObj">
                            <a-tag :color="statusObj?.color || 'blue'">{{ statusObj?.name || '-' }}</a-tag>
                        </template>
                        <template slot="priority" slot-scope="priorityObj">
                            {{ priorityObj?.name || '-' }}
                        </template>
                        <template slot="date" slot-scope="text">
                            {{ formatDate(text) || '-' }}
                        </template>
                        <template slot="actions" slot-scope="text, record">
                            <a-button type="link" class="px-0" @click="$emit('open', record.id)">
                                {{ $t('deals_contracts.requests_open') }}
                            </a-button>
                        </template>
                    </a-table>

                    <div v-else class="contract_tickets_tab__mobile">
                        <div
                            v-for="ticket in group.tickets"
                            :key="ticket.id"
                            class="contract_tickets_tab__mobile_card">
                            <div class="contract_tickets_tab__mobile_top">
                                <span class="text-slate-500">#{{ ticket.number || '-' }}</span>
                                <a-button type="link" class="px-0" @click="$emit('open', ticket.id)">
                                    {{ $t('deals_contracts.requests_open') }}
                                </a-button>
                            </div>
                            <div class="contract_tickets_tab__name">{{ ticket.name || '-' }}</div>
                            <div class="contract_tickets_tab__meta">
                                <span>{{ ticket.status?.name || '-' }}</span>
                                <span>{{ ticket.priority?.name || '-' }}</span>
                                <span>{{ formatDate(ticket.receipt_date || ticket.created_at) || '-' }}</span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            <a-empty v-else :description="$t('deals_contracts.requests_empty')" />
        </a-spin>
    </div>
</template>

<script>
import { errorHandler } from '@/utils/index.js'

export default {
    name: 'ContractTicketsByProjectsTab',
    props: {
        contract: {
            type: Object,
            default: () => null,
        },
    },
    data() {
        return {
            loading: false,
            tickets: [],
        }
    },
    computed: {
        isMobile() {
            return this.$store.state.isMobile
        },
        contractId() {
            return this.contract?.id || null
        },
        projectGroups() {
            const grouped = new Map()
            this.tickets.forEach((ticket) => {
                const projectMeta = this.getProjectMeta(ticket)
                const key = projectMeta.id
                const projectName = projectMeta.name
                if (!grouped.has(key)) {
                    grouped.set(key, {
                        id: key,
                        isNoProject: key === 'no_project',
                        projectName,
                        tickets: [],
                    })
                }
                grouped.get(key).tickets.push(ticket)
            })

            return Array.from(grouped.values()).sort((a, b) => {
                if (a.isNoProject !== b.isNoProject) {
                    return a.isNoProject ? 1 : -1
                }
                return a.projectName.localeCompare(b.projectName)
            })
        },
        columns() {
            return [
                {
                    title: this.$t('deals_contracts.requests_col_number'),
                    dataIndex: 'number',
                    key: 'number',
                    width: 120,
                    scopedSlots: { customRender: 'number' },
                },
                {
                    title: this.$t('deals_contracts.requests_col_name'),
                    dataIndex: 'name',
                    key: 'name',
                    scopedSlots: { customRender: 'name' },
                },
                {
                    title: this.$t('deals_contracts.requests_col_status'),
                    dataIndex: 'status',
                    key: 'status',
                    width: 150,
                    scopedSlots: { customRender: 'status' },
                },
                {
                    title: this.$t('deals_contracts.requests_col_priority'),
                    dataIndex: 'priority',
                    key: 'priority',
                    width: 150,
                    scopedSlots: { customRender: 'priority' },
                },
                {
                    title: this.$t('deals_contracts.requests_col_receipt_date'),
                    dataIndex: 'receipt_date',
                    key: 'receipt_date',
                    width: 160,
                    scopedSlots: { customRender: 'date' },
                },
                {
                    title: '',
                    key: 'actions',
                    width: 110,
                    scopedSlots: { customRender: 'actions' },
                },
            ]
        },
    },
    watch: {
        contract: {
            immediate: true,
            handler() {
                this.loadTickets()
            },
        },
    },
    methods: {
        getProjectMeta(ticket) {
            const key = ticket?.analytics_key
            if (key?.project?.id) {
                return {
                    id: key.project.id,
                    name: key.project.string_view || key.project.name || this.$t('deals_contracts.requests_no_project'),
                }
            }

            const stringView = String(key?.string_view || '').trim()
            if (stringView && stringView.includes('/')) {
                const chunks = stringView.split('/').map(item => item.trim()).filter(Boolean)
                if (chunks.length > 1) {
                    const projectName = chunks.slice(1).join(' / ')
                    return {
                        id: `parsed:${projectName}`,
                        name: projectName || this.$t('deals_contracts.requests_no_project'),
                    }
                }
            }

            return {
                id: 'no_project',
                name: this.$t('deals_contracts.requests_no_project'),
            }
        },
        async loadTickets() {
            if (!this.contractId) {
                this.tickets = []
                return
            }

            try {
                this.loading = true
                const { data } = await this.$http.get('/help_desk/tickets/short_list/', {
                    params: {
                        no_pagination: 'true',
                        contract: this.contractId,
                    },
                })
                const source = Array.isArray(data) ? data : (data?.results || [])
                this.tickets = source.sort((a, b) => {
                    const bDate = new Date(b?.updated_at || b?.receipt_date || b?.created_at || 0).getTime()
                    const aDate = new Date(a?.updated_at || a?.receipt_date || a?.created_at || 0).getTime()
                    return bDate - aDate
                })
            } catch (error) {
                this.tickets = []
                errorHandler({ error, show: false })
            } finally {
                this.loading = false
            }
        },
        formatDate(value) {
            if (!value) return ''
            const m = this.$moment(value)
            return m.isValid() ? m.format('DD.MM.YYYY') : ''
        },
    },
}
</script>

<style lang="scss" scoped>
.contract_tickets_tab__head {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    gap: 16px;
    margin-bottom: 14px;
}

.contract_tickets_tab__title {
    font-size: 16px;
    font-weight: 600;
    color: #111827;
}

.contract_tickets_tab__subtitle {
    margin-top: 4px;
    color: #6b7280;
    font-size: 13px;
}

.contract_tickets_tab__groups {
    display: grid;
    gap: 12px;
}

.contract_tickets_tab__group {
    border: 1px solid var(--border2);
    border-radius: 14px;
    background: #fff;
    overflow: hidden;
}

.contract_tickets_tab__group_head {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
    padding: 10px 12px;
    border-bottom: 1px solid var(--border2);
    background: #f8fafc;
}

.contract_tickets_tab__group_title {
    color: #0f172a;
    font-size: 14px;
    font-weight: 600;
}

.contract_tickets_tab__table {
    margin-bottom: 0;
}

.contract_tickets_tab__mobile {
    display: grid;
    gap: 10px;
    padding: 10px;
}

.contract_tickets_tab__mobile_card {
    border: 1px solid var(--border2);
    border-radius: 12px;
    padding: 10px 12px;
    background: #fff;
}

.contract_tickets_tab__mobile_top {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 10px;
}

.contract_tickets_tab__name {
    margin-top: 4px;
    color: #0f172a;
    font-weight: 500;
}

.contract_tickets_tab__meta {
    margin-top: 8px;
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
    color: #64748b;
    font-size: 12px;
}

@media (max-width: 767px) {
    .contract_tickets_tab__head {
        flex-direction: column;
        align-items: stretch;
    }
}
</style>
