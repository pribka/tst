<template>
    <div class="sales_desktop">
        <aside class="sales_left">
            <div class="sales_left__head">
                <div class="sales_left__title">
                    Мои списки
                </div>
                <div class="sales_left__subtitle">
                    Продажи сегодня
                </div>
            </div>

            <div class="sales_left__section" data-guide-id="sales-left-filters">
                <div class="sales_left__group">
                    Требуют действия
                </div>
                <button
                    v-for="item in sideFilters"
                    :key="item.key"
                    type="button"
                    class="sales_left__item"
                    :class="{ 'sales_left__item--active': activeFilter === item.key }"
                    @click="setFilter(item.key)">
                    <i class="fi" :class="item.icon" />
                    <span>{{ item.title }}</span>
                    <b>{{ item.value }}</b>
                </button>
            </div>

            <div class="sales_left__section" data-guide-id="sales-left-chain">
                <div class="sales_left__group">
                    Цепочка CRM
                </div>
                <button
                    v-for="step in chain"
                    :key="step.key"
                    type="button"
                    class="sales_flow_item"
                    :data-guide-id="step.key === 'lead' ? 'sales-chain' : null"
                    @click="goTo(step.route)">
                    <span>
                        <i class="fi" :class="step.icon" />
                        {{ step.label }}
                    </span>
                    <i class="fi fi-rr-angle-small-right" />
                </button>
            </div>
        </aside>

        <main class="sales_center">
            <section class="sales_panel sales_panel--chains" data-guide-id="sales-seven-chains">
                <div class="sales_panel__head">
                    <div>
                        <h2>7 рабочих цепочек CRM</h2>
                        <p>Каждая строка показывает путь объекта от лида до заказа и следующий автоматический шаг</p>
                    </div>
                    <div class="sales_panel__actions">
                        <button
                            type="button"
                            :disabled="!automaticChainCount || Boolean(busyActionKey)"
                            @click="autoProcessChains">
                            Авторазбор {{ automaticChainCount || '' }}
                        </button>
                        <button type="button" @click="goTo('sales-funnel')">
                            Воронка
                        </button>
                    </div>
                </div>
                <div class="sales_chain_list">
                    <article
                        v-for="(chainItem, index) in crmChains"
                        :key="chainItem.key"
                        class="sales_chain_card"
                        :data-guide-id="index === 0 ? 'sales-seven-chain-card' : null">
                        <button
                            type="button"
                            class="sales_chain_card__main"
                            @click="openChainObject(chainItem)">
                            <span class="sales_chain_card__badge">{{ chainItem.typeLabel }}</span>
                            <span class="sales_chain_card__title">{{ chainItem.title }}</span>
                            <span class="sales_chain_card__meta">{{ chainItem.client || 'Клиент не определен' }}</span>
                            <span class="sales_chain_card__reason">{{ chainItem.reason }}</span>
                        </button>
                        <div class="sales_chain_steps">
                            <span
                                v-for="step in chainItem.steps"
                                :key="step.key"
                                class="sales_chain_step"
                                :class="{
                                    'sales_chain_step--done': step.done,
                                    'sales_chain_step--active': step.active
                                }">
                                <i class="fi" :class="step.icon" />
                                {{ step.label }}
                            </span>
                        </div>
                        <button
                            type="button"
                            class="sales_decision sales_chain_card__action"
                            :class="`sales_decision--${chainItem.actionTone}`"
                            :disabled="busyActionKey === chainItem.key || busyActionKey === 'auto-chains'"
                            @click="handleChainAction(chainItem)">
                            {{ busyActionKey === chainItem.key || busyActionKey === 'auto-chains' ? 'Делаю...' : chainItem.actionLabel }}
                        </button>
                    </article>
                    <div v-if="!crmChains.length && !loading" class="sales_empty">
                        Нет CRM-цепочек для обработки.
                    </div>
                </div>
            </section>

            <section class="sales_kpi" data-guide-id="sales-kpi">
                <button
                    v-for="item in kpi"
                    :key="item.key"
                    type="button"
                    class="sales_kpi__item"
                    @click="handleKpi(item)">
                    <span class="sales_kpi__icon">
                        <i class="fi" :class="item.icon" />
                    </span>
                    <span class="sales_kpi__content">
                        <span class="sales_kpi__value">{{ item.value }}</span>
                        <span class="sales_kpi__title">{{ item.title }}</span>
                        <span class="sales_kpi__hint">{{ item.hint }}</span>
                    </span>
                </button>
            </section>

            <section class="sales_panel sales_panel--main" data-guide-id="sales-attention">
                <div class="sales_panel__head">
                    <div>
                        <h2>Сегодня требует внимания</h2>
                        <p>Лиды, интересы и заказы, где нужен следующий шаг</p>
                    </div>
                    <div class="sales_panel__actions">
                        <button type="button" @click="setFilter('all')">Все</button>
                        <button type="button" @click="setFilter('leads')">Лиды</button>
                        <button type="button" @click="setFilter('overdue')">Просрочено</button>
                        <button type="button" @click="setFilter('ready')">К оформлению</button>
                    </div>
                </div>
                <div class="sales_attention">
                    <div class="sales_attention__row sales_attention__row--head">
                        <span>Тип</span>
                        <span>Объект</span>
                        <span>Клиент</span>
                        <span>Почему здесь</span>
                        <span>Срок</span>
                        <span>Ответств.</span>
                        <span></span>
                    </div>
                    <article
                        v-for="(row, index) in filteredAttentionRows"
                        :key="row.key"
                        class="sales_attention__row sales_attention__row--clickable"
                        role="button"
                        tabindex="0"
                        @click="openAttention(row)"
                        @keydown.enter.prevent="openAttention(row)"
                        @keydown.space.prevent="openAttention(row)">
                        <span>
                            <i class="fi" :class="row.icon" />
                            {{ row.type }}
                        </span>
                        <span class="sales_attention__open">{{ row.title }}</span>
                        <span>{{ row.client || 'Не определен' }}</span>
                        <span>{{ row.action }}</span>
                        <span>{{ row.due || 'Сегодня' }}</span>
                        <span>{{ row.responsible || 'Я' }}</span>
                        <span>
                            <button
                                type="button"
                                class="sales_decision"
                                :data-guide-id="index === 0 ? 'sales-next-action' : null"
                                :class="`sales_decision--${row.decision.tone}`"
                                :disabled="busyActionKey === row.key"
                                @click.stop="handleDecision(row)">
                                {{ busyActionKey === row.key ? 'Делаю...' : row.decision.label }}
                            </button>
                        </span>
                    </article>
                    <div v-if="!filteredAttentionRows.length && !loading" class="sales_empty">
                        Нет объектов, требующих действия.
                    </div>
                </div>
            </section>

            <section class="sales_panel sales_panel--main" data-guide-id="sales-active-interests">
                <div class="sales_panel__head">
                    <div>
                        <h2>Мои активные интересы</h2>
                        <p>Потребности клиента, стадия, следующий шаг и заказ</p>
                    </div>
                    <button type="button" class="sales_link" @click="goTo('sales-interest')">
                        Все интересы
                    </button>
                </div>
                <div class="sales_table">
                    <div class="sales_table__row sales_table__row--head">
                        <span>№</span>
                        <span>Название</span>
                        <span>Клиент</span>
                        <span>Стадия</span>
                        <span>Сумма</span>
                        <span>Следующий шаг</span>
                        <span>Заказ</span>
                    </div>
                    <button
                        v-for="interest in interestRows"
                        :key="interest.id"
                        type="button"
                        class="sales_table__row"
                        @click="openTask(interest.id)">
                        <span>{{ interest.counter || interest.id || '—' }}</span>
                        <span>{{ interest.name || 'Без названия' }}</span>
                        <span>{{ getClientName(interest) || 'Не определен' }}</span>
                        <span>{{ interest.status?.name || interest.stage?.name || 'Без стадии' }}</span>
                        <span>{{ formatMoney(getAmount(interest)) }}</span>
                        <span>{{ getNextStep(interest) }}</span>
                        <span>{{ interest.has_order ? 'Есть' : 'Нужен' }}</span>
                    </button>
                    <div v-if="!interestRows.length && !loading" class="sales_empty">
                        Активные интересы не найдены.
                    </div>
                </div>
            </section>

            <div class="sales_bottom_grid">
                <section class="sales_panel" data-guide-id="sales-new-leads">
                    <div class="sales_panel__head">
                        <div>
                            <h2>Новые лиды</h2>
                            <p>Входящие обращения до квалификации</p>
                        </div>
                        <button type="button" class="sales_link" @click="goTo('sales-leads')">Все</button>
                    </div>
                    <div class="sales_leads">
                        <button
                            v-for="lead in leadRows"
                            :key="lead.id"
                            type="button"
                            class="sales_lead"
                            @click="openLead(lead.id)">
                            <span class="sales_lead__title">{{ lead.name || `Лид ${lead.number || ''}` }}</span>
                            <span>{{ getChannelName(lead) }} · {{ formatDate(lead.created_at) }}</span>
                            <span>{{ getClientName(lead) || 'Клиент еще не определен' }}</span>
                        </button>
                        <div v-if="!leadRows.length && !loading" class="sales_empty">
                            Новых лидов нет.
                        </div>
                    </div>
                </section>

                <section class="sales_panel" data-guide-id="sales-ready-orders">
                    <div class="sales_panel__head">
                        <div>
                            <h2>Ожидают оформления</h2>
                            <p>Интересы, готовые к заказу или следующему шагу</p>
                        </div>
                        <button type="button" class="sales_link" @click="goTo('sales-orders')">Заказы</button>
                    </div>
                    <div class="sales_ready">
                        <button
                            v-for="row in readyRows"
                            :key="row.id"
                            type="button"
                            class="sales_ready__row"
                            @click="openTask(row.id)">
                            <span>{{ row.counter || row.id || '—' }}</span>
                            <b>{{ row.name || 'Без названия' }}</b>
                            <em>{{ row.has_order ? 'Заказ создан' : 'Нужен заказ' }}</em>
                        </button>
                        <div v-if="!readyRows.length && !loading" class="sales_empty">
                            Нет объектов на оформление.
                        </div>
                    </div>
                </section>
            </div>
        </main>

        <aside class="sales_right">
            <section class="sales_right__block">
                <div class="sales_right__label">Менеджер</div>
                <div class="sales_manager">
                    <div class="sales_manager__avatar">{{ managerInitials }}</div>
                    <div>
                        <div class="sales_manager__name">{{ managerName }}</div>
                        <div class="sales_manager__role">Продажи</div>
                    </div>
                </div>
            </section>

            <section class="sales_right__block" data-guide-id="sales-right-summary">
                <div class="sales_right__label">Активность сегодня</div>
                <div class="sales_stat"><span>Внимание</span><b>{{ attentionRows.length }}</b></div>
                <div class="sales_stat"><span>Новые лиды</span><b>{{ leads.count }}</b></div>
                <div class="sales_stat"><span>Без шага</span><b>{{ withoutStepCount }}</b></div>
                <div class="sales_stat"><span>К заказу</span><b>{{ readyRows.length }}</b></div>
            </section>

            <section class="sales_right__block" data-guide-id="sales-right-pipeline">
                <div class="sales_right__label">Воронка</div>
                <div
                    v-for="stage in pipelineRows"
                    :key="stage.name"
                    class="sales_pipeline">
                    <span>{{ stage.name }}</span>
                    <b>{{ stage.count }}</b>
                </div>
                <div class="sales_stat sales_stat--total">
                    <span>Сумма в работе</span>
                    <b>{{ formatMoney(totalInterestAmount) }}</b>
                </div>
            </section>

            <section class="sales_right__block" data-guide-id="sales-shortcuts">
                <div class="sales_right__label">Быстрые действия</div>
                <div class="sales_shortcuts">
                    <button type="button" @click="goTo('sales-funnel')">
                        <i class="fi fi-rr-diagram-project" />
                        Воронка
                    </button>
                    <button type="button" @click="goTo('sales-leads')">
                        <i class="fi fi-rr-comment-exclamation" />
                        Обработать лиды
                    </button>
                    <button type="button" @click="goTo('sales-clients')">
                        <i class="fi fi-rr-id-card-clip-alt" />
                        Клиенты
                    </button>
                </div>
            </section>
        </aside>
    </div>
</template>

<script>
import axios from '@/config/axios'

export default {
    name: 'SalesDashboardPage',
    data() {
        return {
            activeFilter: 'all',
            loading: false,
            busyActionKey: null,
            leads: { count: 0, results: [] },
            interests: { count: 0, results: [] },
            orders: { count: 0, results: [] },
            clients: { count: 0, results: [] },
            interestNeedCounts: {},
            interestNeedGoodsCounts: {}
        }
    },
    computed: {
        chain() {
            return [
                {
                    key: 'lead',
                    label: 'Лид',
                    hint: 'входящее обращение',
                    route: 'sales-leads',
                    icon: 'fi-rr-comment-exclamation'
                },
                {
                    key: 'interest',
                    label: 'Интерес',
                    hint: 'потребность клиента',
                    route: 'sales-interest',
                    icon: 'fi-rr-memo-circle-check'
                },
                {
                    key: 'client',
                    label: 'Клиент',
                    hint: 'карточка CRM',
                    route: 'sales-clients',
                    icon: 'fi-rr-id-card-clip-alt'
                },
                {
                    key: 'needs',
                    label: 'Потребности',
                    hint: 'товары и услуги',
                    route: 'sales-interest',
                    icon: 'fi-rr-box-open'
                },
                {
                    key: 'order',
                    label: 'Заказ',
                    hint: 'оформление',
                    route: 'sales-orders',
                    icon: 'fi-rr-shopping-bag'
                }
            ]
        },
        kpi() {
            return [
                {
                    key: 'leads',
                    title: 'Разобрать лиды',
                    hint: 'LLM найдет интерес',
                    value: this.leads.count,
                    route: 'sales-leads',
                    filter: 'leads',
                    icon: 'fi-rr-comment-exclamation'
                },
                {
                    key: 'interests',
                    title: 'Интересы в работе',
                    hint: 'центр сделки',
                    value: this.interests.count,
                    route: 'sales-interest',
                    icon: 'fi-rr-memo-circle-check'
                },
                {
                    key: 'withoutClient',
                    title: 'Уточнить клиента',
                    hint: 'нет карточки CRM',
                    value: this.withoutClientCount,
                    route: 'sales-interest',
                    filter: 'no-client',
                    icon: 'fi-rr-id-card-clip-alt'
                },
                {
                    key: 'withoutNeeds',
                    title: 'Выявить потребности',
                    hint: 'LLM + каталог',
                    value: this.withoutNeedsCount,
                    route: 'sales-interest',
                    filter: 'no-needs',
                    icon: 'fi-rr-box-open'
                },
                {
                    key: 'withoutOrder',
                    title: 'Оформить заказ',
                    hint: 'потребности готовы',
                    value: this.readyRows.length,
                    route: 'sales-orders',
                    filter: 'ready',
                    icon: 'fi-rr-shopping-bag'
                }
            ]
        },
        sideFilters() {
            return [
                {
                    key: 'all',
                    title: 'Все',
                    icon: 'fi-rr-list',
                    value: this.attentionRows.length
                },
                {
                    key: 'leads',
                    title: 'Новые лиды',
                    icon: 'fi-rr-comment-exclamation',
                    value: this.leads.count
                },
                {
                    key: 'overdue',
                    title: 'Просрочено',
                    icon: 'fi-rr-time-fast',
                    value: this.overdueCount
                },
                {
                    key: 'no-client',
                    title: 'Нет клиента',
                    icon: 'fi-rr-id-card-clip-alt',
                    value: this.withoutClientCount
                },
                {
                    key: 'no-needs',
                    title: 'Нет потребностей',
                    icon: 'fi-rr-box-open',
                    value: this.withoutNeedsCount
                },
                {
                    key: 'ready',
                    title: 'К заказу',
                    icon: 'fi-rr-shopping-bag',
                    value: this.readyRows.length
                }
            ]
        },
        leadRows() {
            return this.leads.results || []
        },
        interestRows() {
            return this.interests.results || []
        },
        orderRows() {
            return this.orders.results || []
        },
        overdueCount() {
            return this.interestRows.filter(item => item.is_overdue).length
        },
        withoutClientCount() {
            return this.interestRows.filter(item => !this.getClientName(item)).length
        },
        withoutNeedsCount() {
            return this.interestRowsWithoutNeeds.length
        },
        interestRowsWithoutNeeds() {
            return this.interestRows.filter(item => this.getNeedCount(item) === 0)
        },
        withoutStepCount() {
            return this.interestRows.filter(item => !item.dead_line && !item.nearest_event).length
        },
        readyRows() {
            return this.interestRows
                .filter(item => this.canPrepareOrder(item))
                .slice(0, 5)
        },
        crmChains() {
            const chains = []

            this.leadRows.forEach(item => {
                chains.push(this.buildLeadChain(item))
            })

            this.buildInterestAttentionRows().forEach(item => {
                chains.push(this.buildInterestChain(item))
            })

            this.interestRows.forEach(item => {
                if (!chains.some(chainItem => chainItem.key === `interest-${item.id}`)) {
                    chains.push(this.buildInterestChain(item))
                }
            })

            this.orderRows.forEach(item => {
                chains.push(this.buildOrderChain(item))
            })

            return chains.filter(Boolean).slice(0, 7)
        },
        automaticChainCount() {
            return this.crmChains.filter(item => item.canAutoProcess).length
        },
        totalInterestAmount() {
            return this.interestRows.reduce((total, item) => total + this.getAmount(item), 0)
        },
        pipelineRows() {
            const stages = this.interestRows.reduce((acc, item) => {
                const name = this.getStageName(item)
                acc[name] = (acc[name] || 0) + 1
                return acc
            }, {})

            return Object.entries(stages)
                .map(([name, count]) => ({ name, count }))
                .slice(0, 6)
        },
        filteredAttentionRows() {
            if (this.activeFilter === 'all') return this.attentionRows
            return this.attentionRows.filter(row => row.group === this.activeFilter)
        },
        managerName() {
            const user = this.$store.state.user?.user
                || this.$store.state.user?.profile
                || this.$store.state.auth?.user
                || {}
            return user.full_name || user.name || user.email || 'Менеджер'
        },
        managerInitials() {
            const words = this.managerName.split(' ').filter(Boolean)
            return words.slice(0, 2).map(word => word[0]).join('').toUpperCase() || 'М'
        },
        attentionRows() {
            const leads = this.leadRows.slice(0, 3).map(item => ({
                key: `lead-${item.id}`,
                group: 'leads',
                type: 'Лид',
                icon: 'fi-rr-comment-exclamation',
                title: item.name || `Лид ${item.number || ''}`,
                client: this.getClientName(item),
                action: this.getLeadInterestId(item) ? 'Интерес уже создан' : 'Лид еще не стал интересом',
                due: this.formatDate(item.created_at),
                responsible: this.getResponsible(item),
                decision: this.getLeadInterestId(item)
                    ? { label: 'Открыть интерес', tone: 'open' }
                    : { label: 'LLM-анализ', tone: 'ai' },
                route: 'lead',
                id: item.id,
                relatedInterestId: this.getLeadInterestId(item)
            }))
            const interests = this.buildInterestAttentionRows().map(item => ({
                key: `interest-${item.id}`,
                group: this.getAttentionGroup(item),
                type: 'Интерес',
                icon: 'fi-rr-memo-circle-check',
                title: item.name || `Интерес ${item.counter || ''}`,
                client: this.getClientName(item),
                action: this.getInterestAction(item),
                due: this.formatDate(item.dead_line || item.updated_at),
                responsible: this.getResponsible(item),
                decision: this.getInterestDecision(item),
                route: 'interest',
                id: item.id
            }))
            const orders = this.orderRows.slice(0, 2).map(item => ({
                key: `order-${item.id}`,
                group: 'ready',
                type: 'Заказ',
                icon: 'fi-rr-shopping-bag',
                title: item.number || item.name || 'Заказ',
                client: this.getClientName(item),
                action: 'Проверить оплату и отгрузку',
                due: this.formatDate(item.created_at),
                responsible: this.getResponsible(item),
                decision: {
                    label: 'Открыть заказ',
                    tone: 'open'
                },
                route: 'order',
                id: item.id
            }))
            return [...leads, ...interests, ...orders].slice(0, 8)
        }
    },
    created() {
        this.loadData()
    },
    methods: {
        async loadData() {
            this.loading = true
            const requests = {
                leads: '/help_desk/tickets/?display=leads&page=1&page_size=5&page_name=help_desk.UnconfirmedAppealsPage',
                interests: '/tasks/task/list/?task_type=interest&page=1&page_size=12&page_name=page_list_interest_task.TaskModel',
                orders: '/crm/orders/?page=1&page_size=4&page_name=crm.GoodsOrderModel_list',
                clients: '/help_desk/customer_cards/?page=1&page_size=1&page_name=list_help_desk.CustomerCardModel'
            }

            await Promise.all(Object.entries(requests).map(async ([key, url]) => {
                try {
                    const { data } = await axios.get(url)
                    this[key] = {
                        count: data?.count || 0,
                        results: data?.results || []
                    }
                } catch (e) {
                    this[key] = { count: 0, results: [] }
                }
            }))
            await this.loadInterestNeedCounts()
            this.loading = false
        },
        async loadInterestNeedCounts() {
            const interests = this.interestRows
            const pairs = await Promise.all(interests.map(async interest => {
                try {
                    const { data } = await axios.get(`/tasks/interest_needs/?task=${interest.id}&page=1&page_size=100`)
                    const results = data?.results || []
                    const goodsCount = results.filter(need => this.getNeedGoodsId(need)).length
                    return [interest.id, data?.count || 0, goodsCount]
                } catch (e) {
                    return [interest.id, 0, 0]
                }
            }))
            this.interestNeedCounts = pairs.reduce((acc, [id, count]) => {
                acc[id] = count
                return acc
            }, {})
            this.interestNeedGoodsCounts = pairs.reduce((acc, [id, count, goodsCount]) => {
                acc[id] = goodsCount
                return acc
            }, {})
        },
        goTo(name) {
            if (!name || this.$route.name === name) return
            this.$router.push({ name })
        },
        setFilter(filter) {
            this.activeFilter = filter
        },
        buildInterestAttentionRows() {
            const groups = ['no-client', 'no-needs', 'ready', 'overdue', 'all']
            const selected = []
            groups.forEach(group => {
                const row = this.interestRowsByAttentionGroup(group)
                    .find(item => !selected.some(selectedItem => selectedItem.id === item.id))
                if (row) selected.push(row)
            })
            this.interestRows.forEach(item => {
                if (selected.length >= 5) return
                if (!selected.some(selectedItem => selectedItem.id === item.id)) {
                    selected.push(item)
                }
            })
            return selected
        },
        interestRowsByAttentionGroup(group) {
            return this.interestRows.filter(item => this.getAttentionGroup(item) === group)
        },
        handleKpi(item) {
            if (item.route && ['leads', 'interests'].includes(item.key)) {
                this.goTo(item.route)
                return
            }
            if (item.filter) {
                this.setFilter(item.filter)
                return
            }
            if (item.route) {
                this.goTo(item.route)
            }
        },
        openAttention(row) {
            if (row.route === 'lead') return this.openLead(row.id)
            if (row.route === 'interest') return this.openTask(row.id)
            if (row.route === 'order') return this.openOrder(row.id)
        },
        buildLeadChain(lead) {
            const relatedInterestId = this.getLeadInterestId(lead)
            const hasClient = Boolean(this.getClientName(lead))

            return {
                key: `lead-${lead.id}`,
                kind: 'lead',
                typeLabel: 'Лид',
                title: lead.name || `Лид ${lead.number || ''}`,
                client: this.getClientName(lead),
                reason: relatedInterestId ? 'Интерес уже создан' : 'Нужно разобрать обращение и создать интерес',
                actionLabel: relatedInterestId ? 'Открыть интерес' : 'Создать интерес',
                actionTone: relatedInterestId ? 'open' : 'ai',
                id: lead.id,
                object: lead,
                relatedInterestId,
                canAutoProcess: !relatedInterestId,
                steps: this.getChainSteps({
                    lead: true,
                    interest: Boolean(relatedInterestId),
                    client: hasClient,
                    needs: false,
                    contract: false,
                    order: false
                })
            }
        },
        buildInterestChain(interest) {
            const needCount = this.getNeedCount(interest)
            const goodsCount = this.getNeedGoodsCount(interest)
            const hasClient = Boolean(this.getClientName(interest))
            const hasNeeds = needCount > 0
            const hasMatchedNeeds = hasNeeds && goodsCount === needCount
            const hasContract = Boolean(this.getCustomerContractId(interest))
            const hasOrder = Boolean(interest.has_order || this.getOrderId(interest))
            const decision = this.getInterestDecision(interest)

            return {
                key: `interest-${interest.id}`,
                kind: 'interest',
                typeLabel: 'Интерес',
                title: interest.name || `Интерес ${interest.counter || ''}`,
                client: this.getClientName(interest),
                reason: this.getInterestChainReason(interest, {
                    hasClient,
                    hasNeeds,
                    hasMatchedNeeds,
                    hasContract,
                    hasOrder
                }),
                actionLabel: decision.label,
                actionTone: decision.tone,
                id: interest.id,
                object: interest,
                canAutoProcess: hasClient && !hasMatchedNeeds && !hasOrder,
                steps: this.getChainSteps({
                    lead: true,
                    interest: true,
                    client: hasClient,
                    needs: hasMatchedNeeds,
                    contract: hasContract,
                    order: hasOrder
                })
            }
        },
        buildOrderChain(order) {
            return {
                key: `order-${order.id}`,
                kind: 'order',
                typeLabel: 'Заказ',
                title: order.number || order.name || 'Заказ',
                client: this.getClientName(order),
                reason: 'Заказ создан, нужно контролировать оплату и отгрузку',
                actionLabel: 'Открыть заказ',
                actionTone: 'open',
                id: order.id,
                object: order,
                canAutoProcess: false,
                steps: this.getChainSteps({
                    lead: true,
                    interest: true,
                    client: Boolean(this.getClientName(order)),
                    needs: true,
                    contract: Boolean(this.getCustomerContractId(order)),
                    order: true
                })
            }
        },
        getChainSteps(state) {
            const steps = [
                { key: 'lead', label: 'Лид', icon: 'fi-rr-comment-exclamation' },
                { key: 'interest', label: 'Интерес', icon: 'fi-rr-memo-circle-check' },
                { key: 'client', label: 'Клиент', icon: 'fi-rr-id-card-clip-alt' },
                { key: 'needs', label: 'Потребности', icon: 'fi-rr-box-open' },
                { key: 'contract', label: 'Контракт', icon: 'fi-rr-document-signed' },
                { key: 'order', label: 'Заказ', icon: 'fi-rr-shopping-bag' }
            ]
            const activeKey = steps.find(step => !state[step.key])?.key || 'order'

            return steps.map(step => ({
                ...step,
                done: Boolean(state[step.key]),
                active: step.key === activeKey
            }))
        },
        getInterestChainReason(interest, state) {
            if (!state.hasClient) return 'Не хватает клиента: нужно выбрать или создать карточку CRM'
            if (!state.hasNeeds) return 'Нужно выявить потребности и сопоставить их с каталогом'
            if (!state.hasMatchedNeeds) return 'Потребности есть, но не все связаны с товарами или услугами'
            if (!state.hasContract) return 'Потребности готовы, но договор клиента еще не выбран'
            if (!state.hasOrder) return 'Можно оформить заказ по готовым потребностям'
            return this.getInterestAction(interest)
        },
        openChainObject(chainItem) {
            if (chainItem.kind === 'lead') {
                if (chainItem.relatedInterestId) return this.openTask(chainItem.relatedInterestId)
                return this.openLead(chainItem.id)
            }
            if (chainItem.kind === 'interest') return this.openTask(chainItem.id)
            if (chainItem.kind === 'order') return this.openOrder(chainItem.id)
        },
        async handleChainAction(chainItem) {
            if (chainItem.kind === 'lead') {
                if (chainItem.relatedInterestId) {
                    this.openTask(chainItem.relatedInterestId)
                    return
                }
                await this.createInterestFromLead({
                    id: chainItem.id,
                    key: chainItem.key,
                    relatedInterestId: chainItem.relatedInterestId
                })
                return
            }
            if (chainItem.kind === 'interest') {
                await this.runInterestNextAction(chainItem.object, chainItem.key)
                return
            }
            if (chainItem.kind === 'order') {
                this.openOrder(chainItem.id)
            }
        },
        async autoProcessChains() {
            const targets = this.crmChains.filter(item => item.canAutoProcess)
            if (!targets.length) return

            this.busyActionKey = 'auto-chains'
            let processed = 0
            const errors = []

            try {
                for (const chainItem of targets) {
                    try {
                        if (chainItem.kind === 'lead') {
                            await axios.post(`/help_desk/tickets/${chainItem.id}/create_interest/`, {
                                force_create: true
                            })
                            processed += 1
                        }
                        if (chainItem.kind === 'interest') {
                            await axios.post(`/tasks/task/${chainItem.id}/analyze_interest/`, {
                                force_create: true
                            })
                            processed += 1
                        }
                    } catch (e) {
                        errors.push(this.getApiErrorMessage(e, `Не удалось обработать ${chainItem.title}`))
                    }
                }

                await this.loadData()

                if (processed) {
                    this.$message?.success(`Авторазбор выполнен: ${processed}`)
                }
                if (errors.length) {
                    this.$message?.warning(`${errors.length} не обработано: ${errors[0]}`)
                }
            } finally {
                this.busyActionKey = null
            }
        },
        async handleDecision(row) {
            if (row.route === 'lead') {
                if (row.relatedInterestId) {
                    this.openTask(row.relatedInterestId)
                    return
                }
                await this.createInterestFromLead(row)
                return
            }
            if (row.route === 'interest') {
                const interest = this.interestRows.find(item => item.id === row.id)
                await this.runInterestNextAction(interest, row.key)
                return
            }
            if (row.route === 'order') {
                this.openOrder(row.id)
            }
        },
        async runInterestNextAction(interest, key = `interest-${interest?.id || ''}`) {
            if (!interest) return
            if (!this.hasNeedCount(interest)) {
                await this.loadInterestNeedCounts()
            }
            if (!this.getClientName(interest)) {
                this.openTask(interest.id)
                return
            }
            if (this.canPrepareOrder(interest)) {
                await this.prepareOrderFromInterest(interest, key)
                return
            }
            if (!interest.has_order && !this.getOrderId(interest)) {
                await this.analyzeInterest(interest, key)
                return
            }
            const orderId = this.getOrderId(interest)
            if (orderId) {
                this.openOrder(orderId)
                return
            }
            this.openTask(interest.id)
        },
        async createInterestFromLead(row) {
            this.busyActionKey = row.key
            try {
                const { data } = await axios.post(`/help_desk/tickets/${row.id}/create_interest/`, {
                    force_create: true
                })
                await this.loadData()
                if (data?.task?.id) {
                    this.$router.push({ name: 'sales-interest', query: { task: data.task.id } })
                }
                this.$message?.success(data?.created ? 'Интерес создан, потребности разобраны' : 'Интерес уже был создан')
            } catch (e) {
                const message = e?.response?.data?.detail || e?.response?.data || 'Не удалось создать интерес из лида'
                this.$message?.error(typeof message === 'string' ? message : 'Не удалось создать интерес из лида')
            } finally {
                this.busyActionKey = null
            }
        },
        async analyzeInterest(interest, key = `interest-${interest.id}`) {
            this.busyActionKey = key
            try {
                await axios.post(`/tasks/task/${interest.id}/analyze_interest/`, {
                    force_create: true
                })
                await this.loadData()
                this.$message?.success('Потребности выявлены и сопоставлены с каталогом')
            } catch (e) {
                const message = e?.response?.data?.detail || e?.response?.data || 'Не удалось разобрать потребности'
                this.$message?.error(typeof message === 'string' ? message : 'Не удалось разобрать потребности')
            } finally {
                this.busyActionKey = null
            }
        },
        async prepareOrderFromInterest(interest, key = `interest-${interest.id}`) {
            this.busyActionKey = key
            try {
                const { data } = await axios.get(`/tasks/interest_needs/?task=${interest.id}&page=1&page_size=100`)
                const needs = data?.results || []
                const orderLines = needs
                    .map(need => ({
                        goods: this.getNeedGoodsId(need),
                        quantity: Number(need.quantity) > 0 ? need.quantity : 1
                    }))
                    .filter(line => line.goods)

                if (!needs.length) {
                    this.$message?.warning('В интересе нет потребностей для заказа')
                    this.openTask(interest.id)
                    return
                }

                if (orderLines.length !== needs.length) {
                    this.$message?.warning('Не все потребности сопоставлены с товарами каталога')
                    this.openTask(interest.id)
                    return
                }

                const orderSourceLines = await Promise.all(
                    orderLines.map(line => axios.post('/crm/orders/build_order_line/', line))
                )
                this.$store.commit('orders/CLEAR_ORDER_CREATE_PAGE')
                this.$store.commit('orders/SET_ORDER_SOURCE_LINES', orderSourceLines.map(({ data }) => data))
                this.$store.commit('orders/SET_CURRENT_CONTRCAT', null)
                const query = {
                    createOrder: '1',
                    interest: interest.id
                }
                const contractId = this.getCustomerContractId(interest)
                if (contractId) {
                    query.customer_contract = contractId
                    this.$store.commit('orders/SET_CURRENT_CONTRCAT', contractId)
                }
                this.$router.push({ name: 'sales-orders', query })
                this.$message?.success(`Потребности перенесены в заказ: ${orderLines.length}`)
            } catch (e) {
                this.$message?.error(this.getApiErrorMessage(e, 'Не удалось подготовить заказ из интереса'))
            } finally {
                this.busyActionKey = null
            }
        },
        openTask(id) {
            this.$router.push({ name: 'sales-interest', query: { task: id } })
        },
        openLead(id) {
            this.$router.push({ name: 'sales-leads', query: { ticketView: id } })
        },
        openOrder(id) {
            this.$router.push({ name: 'sales-orders', query: { order: id } })
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
        getChannelName(lead) {
            return lead.channel?.name || lead.ticket_type?.name || 'HelpDesk'
        },
        getLeadInterestId(lead) {
            return lead.related_tasks?.[0]?.id || lead.relatedTasks?.[0]?.id || ''
        },
        getStageName(interest) {
            return interest.status?.name || interest.stage?.name || interest.stage || 'Без стадии'
        },
        getNeedCount(interest) {
            return this.interestNeedCounts[interest.id] || 0
        },
        getNeedGoodsCount(interest) {
            return this.interestNeedGoodsCounts[interest.id] || 0
        },
        canPrepareOrder(interest) {
            const needCount = this.getNeedCount(interest)
            return Boolean(interest && needCount > 0 && this.getNeedGoodsCount(interest) === needCount && !interest.has_order)
        },
        hasNeedCount(interest) {
            return Boolean(interest?.id) && Object.prototype.hasOwnProperty.call(this.interestNeedCounts, interest.id)
        },
        getNeedGoodsId(need) {
            if (!need) return ''
            if (typeof need.goods === 'string') return need.goods
            return need.goods?.id || need.goods_id || ''
        },
        getCustomerContractId(item) {
            return this.normalizeUuid(
                item?.customer_contract?.id
                || item?.customer_contract
                || item?.customer_contract_id
                || item?.contract?.id
                || item?.contract_id
                || item?.crm_contract?.id
                || item?.crm_contract_id
            )
        },
        getOrderId(item) {
            return this.normalizeUuid(
                item?.order?.id
                || item?.order
                || item?.order_id
                || item?.goods_order?.id
                || item?.goods_order_id
                || item?.crm_order?.id
                || item?.crm_order_id
            )
        },
        normalizeUuid(value) {
            const id = typeof value === 'string' ? value : value?.id
            if (!id) return ''
            return /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i.test(id)
                ? id
                : ''
        },
        getApiErrorMessage(e, fallback) {
            const data = e?.response?.data
            if (typeof data === 'string') return data
            if (data?.detail) return data.detail
            if (Array.isArray(data?.non_field_errors)) {
                const message = data.non_field_errors.join(', ')
                if (message === 'No remnants.') {
                    return 'На складе нет остатков по товарам потребности'
                }
                return message
            }
            return fallback
        },
        getNextStep(interest) {
            if (!this.getClientName(interest)) return 'Указать клиента'
            if (this.getNeedCount(interest) === 0 || (!this.canPrepareOrder(interest) && !interest.has_order)) return 'Выявить потребности'
            if (this.canPrepareOrder(interest)) return 'Оформить заказ'
            if (interest.nearest_event?.name) return interest.nearest_event.name
            if (interest.dead_line) return `До ${this.formatDate(interest.dead_line)}`
            return 'Назначить шаг'
        },
        getAttentionGroup(interest) {
            if (interest.is_overdue) return 'overdue'
            if (!this.getClientName(interest)) return 'no-client'
            if (this.getNeedCount(interest) === 0) return 'no-needs'
            if (this.canPrepareOrder(interest)) return 'ready'
            if (!interest.has_order) return 'no-needs'
            return 'all'
        },
        getInterestAction(interest) {
            if (!this.getClientName(interest)) return 'Не хватает клиента'
            if (this.getNeedCount(interest) === 0) return 'Не выявлены потребности'
            if (this.canPrepareOrder(interest)) return 'Потребности готовы, заказа нет'
            if (!interest.has_order) return 'Потребности нужно сопоставить с каталогом'
            return 'Продвинуть по воронке'
        },
        getInterestDecision(interest) {
            if (!this.getClientName(interest)) {
                return {
                    label: 'Указать клиента',
                    tone: 'client'
                }
            }
            if (this.getNeedCount(interest) === 0) {
                return {
                    label: 'LLM-потребности',
                    tone: 'ai'
                }
            }
            if (this.canPrepareOrder(interest)) {
                return {
                    label: 'Оформить заказ',
                    tone: 'order'
                }
            }
            if (!interest.has_order) {
                return {
                    label: 'LLM-потребности',
                    tone: 'ai'
                }
            }
            return {
                label: 'Открыть',
                tone: 'open'
            }
        },
        getResponsible(item) {
            return item.responsible?.full_name
                || item.responsible?.name
                || item.executor?.full_name
                || item.executor?.name
                || item.author?.full_name
                || item.author?.name
                || ''
        },
        getAmount(item) {
            const value = item.amount || item.sum || item.total || item.price || 0
            const amount = Number(value)
            return Number.isFinite(amount) ? amount : 0
        },
        formatMoney(value) {
            if (!value) return '—'
            return new Intl.NumberFormat('ru-RU', {
                maximumFractionDigits: 0
            }).format(value)
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
.sales_desktop {
    height: 100%;
    min-height: 0;
    display: grid;
    grid-template-columns: 178px minmax(0, 1fr) 220px;
    overflow: hidden;
    background: #eeedea;
    color: #1a1a1a;
}

.sales_left,
.sales_right {
    min-height: 0;
    overflow-y: auto;
    background: #fff;
}

.sales_left {
    border-right: 1px solid #e0dfd8;
}

.sales_right {
    border-left: 1px solid #e0dfd8;
}

.sales_center {
    min-width: 0;
    min-height: 0;
    overflow-y: auto;
    padding: 12px 13px 14px;
}

.sales_left__head,
.sales_right__block {
    padding: 10px 12px;
    border-bottom: 1px solid #e0dfd8;
}

.sales_left__section {
    padding-bottom: 4px;
}

.sales_left__title {
    font-size: 13px;
    font-weight: 500;
}

.sales_left__subtitle {
    margin-top: 2px;
    font-size: 11px;
    color: #666660;
}

.sales_left__group,
.sales_right__label {
    padding: 10px 12px 5px;
    font-size: 10px;
    font-weight: 600;
    letter-spacing: .4px;
    text-transform: uppercase;
    color: #99998f;
}

.sales_right__label {
    padding: 0;
    margin-bottom: 7px;
}

.sales_left__item,
.sales_flow_item,
.sales_kpi__item,
.sales_attention__row,
.sales_table__row,
.sales_lead,
.sales_ready__row,
.sales_shortcuts button,
.sales_panel__actions button,
.sales_link {
    font: inherit;
}

.sales_left__item,
.sales_flow_item {
    width: calc(100% - 14px);
    min-height: 30px;
    display: flex;
    align-items: center;
    gap: 7px;
    margin: 0 7px 3px;
    padding: 0 8px;
    border: 0;
    border-radius: 6px;
    background: transparent;
    color: #666660;
    text-align: left;
    cursor: pointer;
}

.sales_left__item:hover,
.sales_flow_item:hover,
.sales_left__item--active {
    background: #f5f5f4;
    color: #1a1a1a;
}

.sales_left__item b {
    margin-left: auto;
    min-width: 22px;
    padding: 1px 6px;
    border-radius: 9px;
    background: #f5f5f4;
    color: #666660;
    font-size: 10px;
    text-align: center;
}

.sales_left__item--active {
    box-shadow: inset 2px 0 0 #e67e2e;
}

.sales_flow_item {
    justify-content: space-between;
}

.sales_flow_item span {
    min-width: 0;
    display: flex;
    align-items: center;
    gap: 7px;
}

.sales_kpi {
    display: grid;
    grid-template-columns: repeat(5, minmax(0, 1fr));
    gap: 8px;
    margin-bottom: 10px;
}

.sales_kpi__item {
    display: flex;
    gap: 10px;
    min-height: 76px;
    padding: 10px;
    border: 1px solid #e0dfd8;
    border-radius: 8px;
    background: #fff;
    text-align: left;
    cursor: pointer;
}

.sales_kpi__item:hover,
.sales_attention__row:not(.sales_attention__row--head):hover,
.sales_table__row:not(.sales_table__row--head):hover,
.sales_lead:hover,
.sales_ready__row:hover,
.sales_shortcuts button:hover {
    border-color: #e67e2e;
}

.sales_kpi__icon {
    width: 34px;
    height: 34px;
    display: flex;
    align-items: center;
    justify-content: center;
    flex: 0 0 auto;
    border-radius: 8px;
    background: #fdf0e6;
    color: #c45f18;
}

.sales_kpi__content {
    min-width: 0;
    display: flex;
    flex-direction: column;
}

.sales_kpi__value {
    font-size: 22px;
    line-height: 1.2;
    font-weight: 600;
}

.sales_kpi__title,
.sales_lead__title {
    font-size: 13px;
    color: #1a1a1a;
}

.sales_kpi__hint,
.sales_panel__head p,
.sales_lead span:not(.sales_lead__title) {
    margin: 0;
    font-size: 12px;
    line-height: 1.35;
    color: #666660;
}

.sales_panel--chains {
    padding-bottom: 10px;
}

.sales_chain_list {
    display: grid;
    grid-template-columns: 1fr;
    gap: 7px;
    padding-bottom: 2px;
}

.sales_chain_card {
    display: grid;
    grid-template-columns: minmax(210px, .9fr) minmax(340px, 1.2fr) 122px;
    align-items: center;
    gap: 8px;
    padding: 7px 8px;
    border: 1px solid #e0dfd8;
    border-radius: 8px;
    background: #fafaf8;
}

.sales_chain_card:hover {
    border-color: #e67e2e;
}

.sales_chain_card__main {
    min-width: 0;
    display: grid;
    grid-template-columns: auto minmax(0, 1fr);
    grid-template-areas:
        "badge title"
        "meta meta"
        "reason reason";
    column-gap: 6px;
    row-gap: 1px;
    align-items: center;
    padding: 0;
    border: 0;
    background: transparent;
    color: inherit;
    font: inherit;
    text-align: left;
    cursor: pointer;
}

.sales_chain_card__badge {
    grid-area: badge;
    width: fit-content;
    padding: 1px 5px;
    border-radius: 5px;
    background: #fdf0e6;
    color: #b95716;
    font-size: 10px;
    font-weight: 600;
}

.sales_chain_card__title {
    grid-area: title;
    font-size: 13px;
    line-height: 1.3;
    font-weight: 500;
    color: #1a1a1a;
    overflow: hidden;
    display: -webkit-box;
    -webkit-line-clamp: 1;
    -webkit-box-orient: vertical;
}

.sales_chain_card__meta,
.sales_chain_card__reason {
    font-size: 11px;
    line-height: 1.35;
    color: #666660;
    overflow: hidden;
    display: -webkit-box;
    -webkit-line-clamp: 1;
    -webkit-box-orient: vertical;
}

.sales_chain_card__meta {
    grid-area: meta;
}

.sales_chain_card__reason {
    grid-area: reason;
    color: #3f3f3b;
}

.sales_chain_steps {
    display: flex;
    flex-wrap: wrap;
    gap: 3px;
}

.sales_chain_step {
    min-height: 20px;
    display: flex;
    align-items: center;
    gap: 5px;
    padding: 0 5px;
    flex: 1 1 74px;
    border: 1px solid #e0dfd8;
    border-radius: 5px;
    background: #fff;
    color: #8a8a82;
    font-size: 9px;
    white-space: nowrap;
}

.sales_chain_step--done {
    border-color: #b8dcc8;
    background: #effaf3;
    color: #1f7a45;
}

.sales_chain_step--active {
    border-color: #9cc7f2;
    background: #eef6ff;
    color: #185fa5;
}

.sales_panel {
    min-width: 0;
    margin-bottom: 10px;
    padding: 12px;
    border: 1px solid #e0dfd8;
    border-radius: 8px;
    background: #fff;
}

.sales_panel__head {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    gap: 10px;
    margin-bottom: 10px;
}

.sales_panel__head h2 {
    margin: 0 0 3px;
    font-size: 14px;
    line-height: 1.2;
    font-weight: 500;
}

.sales_panel__actions,
.sales_shortcuts {
    display: flex;
    gap: 5px;
    flex-wrap: wrap;
}

.sales_panel__actions button,
.sales_link,
.sales_shortcuts button {
    min-height: 28px;
    border: 1px solid #cccbc3;
    border-radius: 6px;
    background: #fff;
    color: #1a1a1a;
    cursor: pointer;
}

.sales_panel__actions button:disabled {
    opacity: .55;
    cursor: default;
}

.sales_panel__actions button,
.sales_link {
    padding: 0 9px;
}

.sales_link {
    color: #e67e2e;
}

.sales_attention,
.sales_table {
    min-width: 0;
    overflow-x: auto;
}

.sales_attention__row,
.sales_table__row {
    width: 100%;
    display: grid;
    align-items: center;
    gap: 10px;
    min-height: 39px;
    border: 0;
    border-bottom: 1px solid #eeedea;
    background: transparent;
    color: #1a1a1a;
    text-align: left;
}

.sales_attention__row {
    grid-template-columns: 92px minmax(150px, 1.2fr) minmax(120px, 1fr) minmax(170px, 1.2fr) 70px 75px 122px;
}

.sales_table__row {
    grid-template-columns: 70px minmax(170px, 1.4fr) minmax(130px, 1fr) 118px 90px minmax(150px, 1fr) 70px;
}

.sales_table__row:not(.sales_table__row--head) {
    cursor: pointer;
}

.sales_attention__row--clickable {
    cursor: pointer;
}

.sales_attention__row span,
.sales_table__row span {
    min-width: 0;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    font-size: 12px;
}

.sales_attention__row span:first-child {
    display: flex;
    align-items: center;
    gap: 6px;
}

.sales_attention__row span:last-child {
    overflow: visible;
    justify-self: end;
}

.sales_attention__row--head,
.sales_table__row--head {
    min-height: 30px;
    color: #99998f;
    cursor: default;
}

.sales_attention__row--head span,
.sales_table__row--head span {
    font-size: 10px;
    font-weight: 600;
}

.sales_attention__open {
    color: #185fa5;
}

.sales_decision {
    min-height: 28px;
    max-width: 100%;
    padding: 0 9px;
    border: 1px solid #cbd5e1;
    border-radius: 6px;
    background: #fff;
    color: #1f2937;
    font: inherit;
    font-size: 11px;
    line-height: 1;
    white-space: nowrap;
    cursor: pointer;
}

.sales_decision:hover {
    border-color: #1d65a6;
    color: #1d65a6;
}

.sales_decision:disabled {
    opacity: .62;
    cursor: default;
}

.sales_decision--ai {
    border-color: #9cc7f2;
    background: #eef6ff;
    color: #185fa5;
}

.sales_decision--client {
    border-color: #d6c4f0;
    background: #f6f0ff;
    color: #6844a3;
}

.sales_decision--order {
    border-color: #b8dcc8;
    background: #effaf3;
    color: #1f7a45;
}

.sales_decision--open {
    border-color: #d1d5db;
    background: #fff;
    color: #374151;
}

.sales_bottom_grid {
    display: grid;
    grid-template-columns: minmax(0, 1fr) minmax(0, 1fr);
    gap: 10px;
}

.sales_leads,
.sales_ready,
.sales_shortcuts {
    display: flex;
    flex-direction: column;
    gap: 7px;
}

.sales_lead,
.sales_ready__row {
    width: 100%;
    display: flex;
    flex-direction: column;
    gap: 3px;
    padding: 9px;
    border: 1px solid #eeedea;
    border-radius: 8px;
    background: #fafaf8;
    text-align: left;
    cursor: pointer;
}

.sales_ready__row span,
.sales_ready__row em {
    font-size: 11px;
    font-style: normal;
    color: #666660;
}

.sales_ready__row b {
    font-size: 13px;
    font-weight: 500;
}

.sales_manager {
    display: flex;
    align-items: center;
    gap: 8px;
}

.sales_manager__avatar {
    width: 30px;
    height: 30px;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 50%;
    background: #e6f1fb;
    color: #185fa5;
    font-size: 11px;
    font-weight: 600;
}

.sales_manager__name {
    font-size: 12px;
    font-weight: 500;
}

.sales_manager__role {
    margin-top: 1px;
    font-size: 10px;
    color: #666660;
}

.sales_stat,
.sales_pipeline {
    display: flex;
    justify-content: space-between;
    gap: 8px;
    padding: 3px 0;
    font-size: 11px;
    color: #666660;
}

.sales_stat b,
.sales_pipeline b {
    color: #1a1a1a;
    font-weight: 500;
}

.sales_stat--total {
    margin-top: 6px;
    padding-top: 7px;
    border-top: 1px solid #e0dfd8;
}

.sales_shortcuts button {
    width: 100%;
    display: flex;
    align-items: center;
    gap: 7px;
    padding: 7px 9px;
    text-align: left;
}

.sales_empty {
    padding: 16px 0;
    color: #666660;
    font-size: 12px;
}

@media (max-width: 1500px) {
    .sales_desktop {
        grid-template-columns: 170px minmax(0, 1fr);
    }

    .sales_right {
        display: none;
    }

    .sales_kpi {
        grid-template-columns: repeat(3, minmax(0, 1fr));
    }
}

@media (max-width: 900px) {
    .sales_desktop {
        display: flex;
        flex-direction: column;
        overflow-y: auto;
    }

    .sales_left {
        border-right: 0;
        border-bottom: 1px solid #e0dfd8;
    }

    .sales_center {
        overflow: visible;
    }

    .sales_kpi,
    .sales_bottom_grid {
        grid-template-columns: 1fr;
    }

    .sales_chain_card {
        grid-template-columns: 1fr;
    }

    .sales_attention__row,
    .sales_table__row {
        grid-template-columns: 1fr;
        gap: 4px;
        padding: 9px 0;
    }

    .sales_attention__row--head,
    .sales_table__row--head {
        display: none;
    }
}
</style>
