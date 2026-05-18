<template>
    <div class="sales_funnel">
        <div class="sales_funnel__head">
            <div>
                <h1>Воронка интересов</h1>
                <p>Лиды попадают в получение, интересы двигаются по фактам клиента, потребностей, контракта и заказа</p>
            </div>
            <button type="button" @click="loadData">
                Обновить
            </button>
        </div>

        <div class="sales_funnel__board" data-guide-id="sales-funnel-board">
            <div v-if="loading" class="sales_funnel__loading">
                <a-spin />
            </div>
            <template v-else>
            <section
                v-for="column in columns"
                :key="column.key"
                class="sales_funnel__column">
                <div class="sales_funnel__column_head">
                    <span>{{ column.title }}</span>
                    <b>{{ column.items.length }}</b>
                </div>

                <div class="sales_funnel__cards">
                    <article
                        v-for="item in column.items"
                        :key="item.key"
                        class="sales_funnel_card"
                        :class="`sales_funnel_card--${item.type}`">
                        <div class="sales_funnel_card__top">
                            <span>{{ item.badge }}</span>
                            <button
                                v-if="item.type === 'lead'"
                                type="button"
                                data-guide-id="sales-funnel-create-interest"
                                :disabled="creatingLeadId === item.id"
                                @click="createInterest(item)">
                                {{ creatingLeadId === item.id ? 'Анализ...' : 'Создать интерес' }}
                            </button>
                            <button
                                v-else
                                type="button"
                                @click="openInterest(item.id)">
                                Открыть
                            </button>
                        </div>
                        <h2>{{ item.title }}</h2>
                        <div class="sales_funnel_card__client">
                            {{ item.client || 'Клиент не определен' }}
                        </div>
                        <div class="sales_funnel_card__meta">
                            <span>{{ item.date || 'Без даты' }}</span>
                            <span v-if="item.needCount">{{ item.needCount }} потр.</span>
                            <span v-if="item.hasContract">Контракт</span>
                            <span v-if="item.hasOrder">Заказ</span>
                        </div>
                        <div class="sales_funnel_card__rail" data-guide-id="sales-funnel-card-rail">
                            <span
                                v-for="step in processSteps"
                                :key="step.key"
                                :class="{ done: item.steps[step.key], active: item.stageKey === step.key }"
                                :title="step.title" />
                        </div>
                    </article>

                    <div v-if="!column.items.length && !loading" class="sales_funnel__empty">
                        Нет объектов
                    </div>
                </div>
            </section>
            </template>
        </div>
    </div>
</template>

<script>
import axios from '@/config/axios'

export default {
    name: 'SalesFunnelPage',
    data() {
        return {
            loading: false,
            creatingLeadId: null,
            leads: [],
            interests: [],
            interestSources: {},
            needCounts: {}
        }
    },
    computed: {
        processSteps() {
            return [
                { key: 'lead', title: 'Источник' },
                { key: 'client', title: 'Клиент' },
                { key: 'needs', title: 'Потребности' },
                { key: 'contract', title: 'Контракт' },
                { key: 'order', title: 'Заказ' }
            ]
        },
        leadCards() {
            return this.leads
                .filter(lead => !this.interestSources[lead.id])
                .map(lead => ({
                    key: `lead-${lead.id}`,
                    id: lead.id,
                    type: 'lead',
                    badge: `Лид ${lead.number || ''}`.trim(),
                    title: lead.name || 'Без названия',
                    client: this.getClientName(lead),
                    date: this.formatDate(lead.created_at),
                    stageKey: 'lead',
                    steps: {
                        lead: true
                    },
                    raw: lead
                }))
        },
        interestCards() {
            return this.interests.map(interest => {
                const needCount = this.needCounts[interest.id] || 0
                const hasClient = Boolean(interest.customer_card || this.getClientName(interest))
                const hasContract = Boolean(interest.contract)
                const hasOrder = Boolean(interest.has_order)
                const stageKey = this.getInterestStageKey({ hasClient, needCount, hasContract, hasOrder })
                return {
                    key: `interest-${interest.id}`,
                    id: interest.id,
                    type: 'interest',
                    badge: `Интерес ${interest.counter || ''}`.trim(),
                    title: interest.name || 'Без названия',
                    client: this.getClientName(interest),
                    date: this.formatDate(interest.created_at),
                    needCount,
                    hasContract,
                    hasOrder,
                    stageKey,
                    steps: {
                        lead: true,
                        client: hasClient,
                        needs: needCount > 0,
                        contract: hasContract,
                        order: hasOrder
                    },
                    raw: interest
                }
            })
        },
        columns() {
            const interestsByStage = this.interestCards.reduce((acc, item) => {
                if (!acc[item.stageKey]) acc[item.stageKey] = []
                acc[item.stageKey].push(item)
                return acc
            }, {})

            return [
                {
                    key: 'lead',
                    title: 'Получение',
                    items: [...this.leadCards, ...(interestsByStage.lead || [])]
                },
                {
                    key: 'client',
                    title: 'Клиент',
                    items: interestsByStage.client || []
                },
                {
                    key: 'needs',
                    title: 'Потребности',
                    items: interestsByStage.needs || []
                },
                {
                    key: 'contract',
                    title: 'Контракт',
                    items: interestsByStage.contract || []
                },
                {
                    key: 'order',
                    title: 'Заказ',
                    items: interestsByStage.order || []
                }
            ]
        }
    },
    created() {
        this.loadData()
    },
    methods: {
        async loadData() {
            this.loading = true
            try {
                const [leadsResponse, interestsResponse] = await Promise.all([
                    axios.get('/help_desk/tickets/?display=leads&page=1&page_size=50&page_name=help_desk.UnconfirmedAppealsPage'),
                    axios.get('/tasks/task/list/?task_type=interest&page=1&page_size=100&page_name=page_list_interest_task.TaskModel')
                ])
                this.leads = leadsResponse.data?.results || []
                this.interests = interestsResponse.data?.results || []
                await Promise.all([
                    this.loadInterestSources(),
                    this.loadNeedCounts()
                ])
            } finally {
                this.loading = false
            }
        },
        async loadInterestSources() {
            const pairs = await Promise.all(this.interests.map(async interest => {
                try {
                    const { data } = await axios.get(`/tasks/task/${interest.id}/`)
                    const reason = data?.reason
                    if (reason?.type === 'help_desk.HelpDeskTicketModel' && reason.id) {
                        return [reason.id, interest.id]
                    }
                } catch (e) {
                    return null
                }
                return null
            }))
            this.interestSources = pairs.reduce((acc, pair) => {
                if (pair) acc[pair[0]] = pair[1]
                return acc
            }, {})
        },
        async loadNeedCounts() {
            const pairs = await Promise.all(this.interests.map(async interest => {
                try {
                    const { data } = await axios.get(`/tasks/interest_needs/?task=${interest.id}&page=1&page_size=1`)
                    return [interest.id, data?.count || 0]
                } catch (e) {
                    return [interest.id, 0]
                }
            }))
            this.needCounts = pairs.reduce((acc, [id, count]) => {
                acc[id] = count
                return acc
            }, {})
        },
        getInterestStageKey({ hasClient, needCount, hasContract, hasOrder }) {
            if (hasOrder) return 'order'
            if (hasContract) return 'contract'
            if (needCount > 0) return 'needs'
            if (hasClient) return 'client'
            return 'lead'
        },
        async createInterest(item) {
            this.creatingLeadId = item.id
            try {
                const { data } = await axios.post(`/help_desk/tickets/${item.id}/create_interest/`, {
                    force_create: true
                })
                await this.loadData()
                if (data?.task?.id) {
                    this.openInterest(data.task.id)
                }
                if (data?.created) {
                    this.$message?.success('Интерес создан из лида')
                } else {
                    this.$message?.info('Интерес уже был создан')
                }
            } catch (e) {
                const message = e?.response?.data?.detail || e?.response?.data || 'Не удалось создать интерес'
                this.$message?.error(typeof message === 'string' ? message : 'Не удалось создать интерес')
            } finally {
                this.creatingLeadId = null
            }
        },
        openInterest(id) {
            this.$router.push({ name: 'sales-interest', query: { task: id } })
        },
        getClientName(item) {
            if (item.customer_card?.name) return item.customer_card.name
            if (item.customer_name) return item.customer_name
            if (item.contractor_name) return item.contractor_name
            if (item.potential_contractor?.name) return item.potential_contractor.name
            if (item.contact_person?.full_name) return item.contact_person.full_name
            if (item.contact_person?.name) return item.contact_person.name
            return ''
        },
        formatDate(value) {
            if (!value) return ''
            const date = new Date(value)
            if (Number.isNaN(date.getTime())) return ''
            return date.toLocaleDateString('ru-RU', {
                day: '2-digit',
                month: '2-digit'
            })
        }
    }
}
</script>

<style lang="scss" scoped>
.sales_funnel {
    height: 100%;
    min-height: 0;
    display: flex;
    flex-direction: column;
    overflow: hidden;
    background: #eeedea;
    color: #1a1a1a;
}

.sales_funnel__head {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    gap: 12px;
    padding: 12px 14px;
    border-bottom: 1px solid #e0dfd8;
    background: #fff;
}

.sales_funnel__head h1 {
    margin: 0 0 3px;
    font-size: 15px;
    line-height: 1.2;
    font-weight: 500;
}

.sales_funnel__head p {
    margin: 0;
    font-size: 12px;
    color: #666660;
}

.sales_funnel__head button,
.sales_funnel_card__top button {
    min-height: 28px;
    padding: 0 9px;
    border: 1px solid #cccbc3;
    border-radius: 6px;
    background: #fff;
    color: #1a1a1a;
    font: inherit;
    font-size: 11px;
    cursor: pointer;
}

.sales_funnel_card__top button {
    border-color: #e67e2e;
    color: #e67e2e;
}

.sales_funnel_card__top button:disabled {
    border-color: #e0dfd8;
    color: #99998f;
    cursor: default;
}

.sales_funnel__board {
    flex: 1;
    min-height: 0;
    display: grid;
    grid-template-columns: repeat(6, minmax(235px, 1fr));
    gap: 8px;
    padding: 10px;
    overflow-x: auto;
    overflow-y: hidden;
}

.sales_funnel__loading {
    grid-column: 1 / -1;
    min-height: 240px;
    display: flex;
    align-items: center;
    justify-content: center;
}

.sales_funnel__column {
    min-height: 0;
    display: flex;
    flex-direction: column;
    border: 1px solid #e0dfd8;
    border-radius: 8px;
    background: #f7f7f5;
}

.sales_funnel__column_head {
    display: flex;
    align-items: center;
    justify-content: space-between;
    min-height: 38px;
    padding: 0 10px;
    border-bottom: 1px solid #e0dfd8;
    background: #fff;
    border-radius: 8px 8px 0 0;
}

.sales_funnel__column_head span {
    font-size: 13px;
    font-weight: 500;
}

.sales_funnel__column_head b {
    min-width: 24px;
    padding: 1px 7px;
    border-radius: 9px;
    background: #f5f5f4;
    color: #666660;
    font-size: 11px;
    text-align: center;
}

.sales_funnel__cards {
    flex: 1;
    min-height: 0;
    display: flex;
    flex-direction: column;
    gap: 8px;
    padding: 8px;
    overflow-y: auto;
}

.sales_funnel_card {
    padding: 9px;
    border: 1px solid #e0dfd8;
    border-radius: 8px;
    background: #fff;
}

.sales_funnel_card--lead {
    border-left: 3px solid #e67e2e;
}

.sales_funnel_card--interest {
    border-left: 3px solid #185fa5;
}

.sales_funnel_card__top,
.sales_funnel_card__meta {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 6px;
}

.sales_funnel_card__top span,
.sales_funnel_card__meta span {
    font-size: 10px;
    color: #666660;
}

.sales_funnel_card h2 {
    margin: 8px 0 5px;
    font-size: 13px;
    line-height: 1.3;
    font-weight: 500;
}

.sales_funnel_card__client {
    min-height: 16px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    font-size: 12px;
    color: #666660;
}

.sales_funnel_card__meta {
    justify-content: flex-start;
    flex-wrap: wrap;
    margin-top: 7px;
}

.sales_funnel_card__meta span {
    padding: 1px 5px;
    border-radius: 5px;
    background: #f5f5f4;
}

.sales_funnel_card__rail {
    display: grid;
    grid-template-columns: repeat(6, 1fr);
    gap: 3px;
    margin-top: 9px;
}

.sales_funnel_card__rail span {
    height: 5px;
    border-radius: 4px;
    background: #e0dfd8;
}

.sales_funnel_card__rail span.done {
    background: #2d7a3a;
}

.sales_funnel_card__rail span.active {
    background: #e67e2e;
}

.sales_funnel__empty {
    padding: 16px 0;
    color: #99998f;
    font-size: 12px;
    text-align: center;
}

@media (max-width: 900px) {
    .sales_funnel__head {
        flex-direction: column;
    }

    .sales_funnel__board {
        grid-template-columns: repeat(6, minmax(220px, 85vw));
    }
}
</style>
