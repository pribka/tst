<template>
    <div class="interest_contract">
        <a-spin :spinning="loading">
            <a-alert
                v-if="!customerCard"
                class="mb-3"
                type="warning"
                show-icon
                message="В интересе не указан клиент"
                description="Договор оформляется с клиентом. Сначала заполните карточку клиента в интересе." />

            <section class="interest_contract__panel">
                <div class="interest_contract__head">
                    <div>
                        <h3>Предмет договора</h3>
                        <p>Выберите потребности, по которым договорились с клиентом. В договор можно перенести не все позиции интереса.</p>
                    </div>
                    <div class="interest_contract__amount">
                        <span>Сумма договора</span>
                        <a-input-number
                            v-model="contractAmount"
                            :min="0"
                            :precision="2"
                            :disabled="!canCreateContract"
                            style="width: 160px" />
                    </div>
                </div>

                <div class="interest_contract__summary">
                    <div>
                        <span>Клиент</span>
                        <b>{{ customerCard ? customerCard.name : 'Не указан' }}</b>
                    </div>
                    <div>
                        <span>Оценка интереса</span>
                        <b>{{ formatMoney(interestAmount) }}</b>
                    </div>
                    <div>
                        <span>Выбрано в договор</span>
                        <b>{{ formatMoney(selectedAmount) }}</b>
                    </div>
                    <div>
                        <span>Договоров</span>
                        <b>{{ contracts.length }}</b>
                    </div>
                </div>

                <div class="interest_contract__table">
                    <div class="interest_contract__row interest_contract__row--head">
                        <span></span>
                        <span>Позиция</span>
                        <span>Кол-во</span>
                        <span>Цена</span>
                        <span>Сумма</span>
                        <span>Комментарий</span>
                    </div>
                    <div
                        v-for="need in needs"
                        :key="need.id"
                        class="interest_contract__row">
                        <span>
                            <a-checkbox
                                :checked="selectedNeedIds.includes(need.id)"
                                @change="toggleNeed(need.id, $event.target.checked)" />
                        </span>
                        <span>
                            <b>{{ need.name || need.goods && need.goods.name || 'Без наименования' }}</b>
                            <small>{{ need.article_number || need.goods && need.goods.article_number || '' }}</small>
                        </span>
                        <span>{{ formatQuantity(need.quantity) }}</span>
                        <span>{{ formatMoney(need.price) }}</span>
                        <span>{{ formatMoney(need.amount) }}</span>
                        <span>{{ need.comment || '...' }}</span>
                    </div>
                    <div v-if="!needs.length" class="interest_contract__empty">
                        Потребности пока не заполнены. Сначала выполните LLM-анализ или добавьте потребности вручную.
                    </div>
                </div>

                <div class="interest_contract__actions">
                    <a-button
                        type="primary"
                        :disabled="!canCreateContract"
                        :loading="saving"
                        @click="createContract">
                        Создать договор из выбранного
                    </a-button>
                    <span v-if="needs.length && !selectedNeedIds.length">Выберите хотя бы одну позицию.</span>
                </div>
            </section>

            <section
                v-for="contract in contracts"
                :key="contract.id"
                class="interest_contract__panel">
                <div class="interest_contract__head">
                    <div>
                        <h3>{{ contract.number || contract.string_view || 'Договор' }}</h3>
                        <p>{{ contract.customer_card && contract.customer_card.name ? contract.customer_card.name : 'Клиент не указан' }}</p>
                    </div>
                    <a-button
                        type="primary"
                        ghost
                        :disabled="!getOrderLines(contract).length"
                        :loading="orderLoadingId === contract.id"
                        @click="prepareOrder(contract)">
                        Оформить заказ по остатку
                    </a-button>
                </div>

                <div class="interest_contract__summary">
                    <div>
                        <span>Сумма договора</span>
                        <b>{{ formatMoney(contract.crm_orders_summary && contract.crm_orders_summary.contract_amount) }}</b>
                    </div>
                    <div>
                        <span>Предмет договора</span>
                        <b>{{ formatMoney(contract.crm_orders_summary && contract.crm_orders_summary.subject_amount) }}</b>
                    </div>
                    <div>
                        <span>Заказано</span>
                        <b>{{ formatMoney(contract.crm_orders_summary && contract.crm_orders_summary.ordered_amount) }}</b>
                    </div>
                    <div>
                        <span>Отгружено</span>
                        <b>{{ formatQuantity(contract.crm_orders_summary && contract.crm_orders_summary.delivered_quantity) }}</b>
                    </div>
                </div>

                <div class="interest_contract__table">
                    <div class="interest_contract__row interest_contract__row--head interest_contract__row--subject">
                        <span>Позиция договора</span>
                        <span>Договор</span>
                        <span>Заказано</span>
                        <span>Отгружено</span>
                        <span>Остаток</span>
                    </div>
                    <div
                        v-for="item in contract.subject_items"
                        :key="item.id"
                        class="interest_contract__row interest_contract__row--subject">
                        <span>
                            <b>{{ item.name || item.goods && item.goods.name || 'Без наименования' }}</b>
                            <small>{{ item.comment || item.article_number || '' }}</small>
                        </span>
                        <span>{{ formatQuantity(item.quantity) }} / {{ formatMoney(item.amount) }}</span>
                        <span>{{ formatQuantity(item.ordered_quantity) }} / {{ formatMoney(item.ordered_amount) }}</span>
                        <span>{{ formatQuantity(item.delivered_quantity) }} / {{ formatMoney(item.delivered_amount) }}</span>
                        <span>{{ formatQuantity(getRemainingQuantity(item)) }}</span>
                    </div>
                    <div v-if="!contract.subject_items || !contract.subject_items.length" class="interest_contract__empty">
                        Предмет договора пуст. Добавьте согласованные потребности из интереса.
                    </div>
                </div>
            </section>
        </a-spin>
    </div>
</template>

<script>
export default {
    name: 'InterestContract',
    props: {
        task: {
            type: Object,
            required: true
        },
        reloadTask: {
            type: Function,
            default: () => {}
        }
    },
    data() {
        return {
            loading: false,
            saving: false,
            orderLoadingId: '',
            interest: null,
            needs: [],
            contracts: [],
            selectedNeedIds: [],
            contractAmount: 0
        }
    },
    computed: {
        customerCard() {
            return this.interest?.customer_card || this.task?.customer_card || null
        },
        interestAmount() {
            return Number(this.interest?.amount || 0)
        },
        selectedNeeds() {
            return this.needs.filter(need => this.selectedNeedIds.includes(need.id))
        },
        selectedAmount() {
            return this.selectedNeeds.reduce((sum, need) => sum + Number(need.amount || 0), 0)
        },
        canCreateContract() {
            return Boolean(this.customerCard && this.selectedNeedIds.length && !this.saving)
        }
    },
    created() {
        this.load()
    },
    methods: {
        async load() {
            this.loading = true
            try {
                const { data } = await this.$http.get('/customer_contracts/for_interest/', {
                    params: { interest: this.task.id }
                })
                this.interest = data.interest || null
                this.needs = data.needs || []
                this.contracts = data.contracts || []
                if (!this.selectedNeedIds.length) {
                    this.selectedNeedIds = this.needs.map(need => need.id)
                }
                if (!this.contractAmount) {
                    this.contractAmount = Number(this.interest?.amount || this.selectedAmount || 0)
                }
            } catch (e) {
                this.$message?.error(this.getApiErrorMessage(e, 'Не удалось загрузить договоры интереса'))
            } finally {
                this.loading = false
            }
        },
        toggleNeed(id, checked) {
            if (checked && !this.selectedNeedIds.includes(id)) {
                this.selectedNeedIds = [...this.selectedNeedIds, id]
            }
            if (!checked) {
                this.selectedNeedIds = this.selectedNeedIds.filter(item => item !== id)
            }
            if (!this.contractAmount || Number(this.contractAmount) === Number(this.interestAmount)) {
                this.contractAmount = this.selectedAmount
            }
        },
        async createContract() {
            if (!this.canCreateContract) {
                return
            }
            this.saving = true
            try {
                await this.$http.post('/customer_contracts/create_from_interest/', {
                    interest: this.task.id,
                    need_ids: this.selectedNeedIds,
                    amount: this.contractAmount || this.selectedAmount
                })
                this.$message?.success('Договор создан, предмет договора заполнен')
                this.reloadTask({ id: this.task.id }, false)
                await this.load()
            } catch (e) {
                this.$message?.error(this.getApiErrorMessage(e, 'Не удалось создать договор из интереса'))
            } finally {
                this.saving = false
            }
        },
        async prepareOrder(contract) {
            const orderLines = this.getOrderLines(contract)
            if (!orderLines.length) {
                this.$message?.warning('По договору нет остатка для заказа')
                return
            }
            this.orderLoadingId = contract.id
            try {
                await this.$http.post('/crm/shopping_cart/clear/')
                await Promise.all(orderLines.map(line => this.$http.post('/crm/shopping_cart/', line)))
                this.$store.commit('orders/CLEAR_ORDER_CREATE_PAGE')
                this.$store.commit('orders/SET_CURRENT_CONTRCAT', null)
                this.$router.push({
                    name: 'sales-orders',
                    query: {
                        createOrder: '1',
                        interest: this.task.id,
                        customer_contract: contract.id
                    }
                })
                this.$message?.success(`Позиции договора перенесены в заказ: ${orderLines.length}`)
            } catch (e) {
                this.$message?.error(this.getApiErrorMessage(e, 'Не удалось подготовить заказ по договору'))
            } finally {
                this.orderLoadingId = ''
            }
        },
        getOrderLines(contract) {
            const items = contract?.subject_items || []
            return items
                .map(item => ({
                    goods: item.goods?.id,
                    quantity: this.getRemainingQuantity(item)
                }))
                .filter(line => line.goods && Number(line.quantity) > 0)
        },
        getRemainingQuantity(item) {
            const quantity = Number(item?.quantity || 0)
            const ordered = Number(item?.ordered_quantity || 0)
            return Math.max(quantity - ordered, 0)
        },
        formatMoney(value) {
            const amount = Number(value || 0)
            return amount.toLocaleString('ru-RU', {
                minimumFractionDigits: 2,
                maximumFractionDigits: 2
            })
        },
        formatQuantity(value) {
            const quantity = Number(value || 0)
            return quantity.toLocaleString('ru-RU', {
                maximumFractionDigits: 3
            })
        },
        getApiErrorMessage(error, fallback) {
            const data = error?.response?.data
            if (typeof data === 'string') {
                return data
            }
            if (typeof data?.detail === 'string') {
                return data.detail
            }
            if (typeof data?.message === 'string') {
                return data.message
            }
            const firstKey = data && typeof data === 'object' ? Object.keys(data)[0] : null
            if (firstKey && Array.isArray(data[firstKey])) {
                return data[firstKey][0]
            }
            if (firstKey && typeof data[firstKey] === 'string') {
                return data[firstKey]
            }
            return fallback
        }
    }
}
</script>

<style lang="scss" scoped>
.interest_contract {
    display: flex;
    flex-direction: column;
    gap: 12px;
}

.interest_contract__panel {
    border: 1px solid var(--borderColor);
    border-radius: 6px;
    background: var(--mBg);
    padding: 14px;
}

.interest_contract__head {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    gap: 12px;
    margin-bottom: 12px;
}

.interest_contract__head h3 {
    margin: 0 0 4px;
    font-size: 16px;
    font-weight: 600;
}

.interest_contract__head p {
    margin: 0;
    color: var(--grayColor);
    font-size: 12px;
}

.interest_contract__amount {
    display: flex;
    align-items: center;
    gap: 8px;
    white-space: nowrap;
}

.interest_contract__summary {
    display: grid;
    grid-template-columns: repeat(4, minmax(0, 1fr));
    gap: 8px;
    margin-bottom: 12px;
}

.interest_contract__summary div {
    border: 1px solid var(--border2);
    border-radius: 6px;
    padding: 9px 10px;
    min-width: 0;
}

.interest_contract__summary span {
    display: block;
    color: var(--grayColor);
    font-size: 12px;
    margin-bottom: 4px;
}

.interest_contract__summary b {
    display: block;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    font-weight: 600;
}

.interest_contract__table {
    border: 1px solid var(--border2);
    border-radius: 6px;
    overflow: hidden;
}

.interest_contract__row {
    display: grid;
    grid-template-columns: 42px minmax(220px, 1.4fr) 90px 110px 110px minmax(160px, 1fr);
    gap: 8px;
    align-items: center;
    min-height: 42px;
    padding: 8px 10px;
    border-bottom: 1px solid var(--border2);
}

.interest_contract__row:last-child {
    border-bottom: 0;
}

.interest_contract__row--head {
    min-height: 34px;
    background: var(--eBg);
    color: var(--grayColor);
    font-size: 12px;
}

.interest_contract__row--subject {
    grid-template-columns: minmax(220px, 1.4fr) 150px 150px 150px 90px;
}

.interest_contract__row b,
.interest_contract__row small {
    display: block;
}

.interest_contract__row small {
    color: var(--grayColor);
    font-size: 12px;
    margin-top: 2px;
}

.interest_contract__empty {
    padding: 14px;
    color: var(--grayColor);
}

.interest_contract__actions {
    display: flex;
    align-items: center;
    gap: 10px;
    margin-top: 12px;
}

.interest_contract__actions span {
    color: var(--grayColor);
    font-size: 12px;
}

@media (max-width: 900px) {
    .interest_contract__head,
    .interest_contract__actions {
        align-items: stretch;
        flex-direction: column;
    }

    .interest_contract__summary {
        grid-template-columns: repeat(2, minmax(0, 1fr));
    }

    .interest_contract__row,
    .interest_contract__row--subject {
        grid-template-columns: 1fr;
    }
}
</style>
