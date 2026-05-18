<template>
    <div class="contract_service_cards">
        <div class="contract_service_cards__head">
            <div class="contract_service_cards__head_text">
                <div class="contract_service_cards__title">
                    {{ $t('deals_contracts.service_cards_title') }}
                </div>
            </div>
            <a-button
                v-if="canEdit"
                type="flat_primary"
                icon="fi-rr-plus"
                flaticon
                :disabled="!canManageCards"
                @click="openAssignModal">
                {{ $t('deals_contracts.service_cards_assign') }}
            </a-button>
        </div>

        <a-alert
            v-if="canEdit && !canManageCards"
            type="warning"
            show-icon
            class="mb-3"
            :message="$t('deals_contracts.service_cards_unavailable')" />

        <a-spin :spinning="cardsLoading">
            <a-empty
                v-if="!displayCards.length"
                :description="$t('deals_contracts.service_cards_empty')" />

            <div v-else class="contract_service_cards__list">
                <div
                    v-for="item in displayCards"
                    :key="`service_card_${item.id}`"
                    class="contract_service_cards__item">
                    <div class="contract_service_cards__item_main">
                        <button
                            type="button"
                            class="contract_service_cards__item_title_link"
                            @click.stop="openClientCard(item.id)">
                            {{ item.name }}
                        </button>
                        <div class="contract_service_cards__item_meta">
                            <span v-if="item.inn">{{ $t('deals_contracts.service_cards_inn') }}: {{ item.inn }}</span>
                        </div>
                    </div>
                    <a-button
                        v-if="canEdit"
                        type="link"
                        size="small"
                        class="contract_service_cards__unbind_btn"
                        :loading="unbindingCardIdSet.has(item.id)"
                        @click="confirmUnbindCard(item.id)">
                        {{ $t('deals_contracts.service_cards_unbind') }}
                    </a-button>
                </div>
            </div>
        </a-spin>

        <a-modal
            class="contract_service_cards_modal"
            :visible="assignModalVisible"
            :title="$t('deals_contracts.service_cards_assign_title')"
            :width="modalWidth"
            :destroyOnClose="true"
            :dialog-style="{ top: isMobile ? '6px' : '10px' }"
            :body-style="modalBodyStyle"
            @cancel="closeAssignModal">
            <div class="contract_service_cards_modal__content">
                <div class="flex h-[38px] items-center rounded bg-[#f5f7fb] px-4">
                    <a-input
                        v-model="suggestionsQuery"
                        class="contract_service_cards_modal__search w-full"
                        :placeholder="$t('deals_contracts.service_cards_search_placeholder')"
                        allow-clear>
                        <template slot="suffix">
                            <i class="fi fi-rr-search text-[rgba(0,0,0,0.45)]" />
                        </template>
                    </a-input>
                </div>

                <div class="contract_service_cards_modal__sections">
                    <div class="contract_service_cards_modal__section">
                        <div class="contract_service_cards_modal__section_title">
                            {{ $t('deals_contracts.service_cards_matching_bin_title', { inn: contractCustomerCardInnRaw || '-' }) }}
                        </div>
                        <div class="contract_service_cards_modal__list" infinite-wrapper>
                            <div
                                v-for="item in filteredMatchingSuggestions"
                                :key="`matching_${item.id}`"
                                class="contract_service_cards_modal__item select-none"
                                :class="{ 'is-selected': selectedSuggestionIdSet.has(item.id) }"
                                :title="item.name"
                                @click="toggleSuggestion(item.id)">
                                <a-checkbox
                                    class="contract_service_cards_modal__check"
                                    :checked="selectedSuggestionIdSet.has(item.id)"
                                    @click.stop
                                    @change="toggleSuggestion(item.id)" />
                                <div class="contract_service_cards_modal__item_content">
                                    <div class="flex items-start justify-between gap-2">
                                        <div class="contract_service_cards_modal__item_name text-[rgba(0,0,0,0.88)]">
                                            {{ item.name }}
                                        </div>
                                        <a-button
                                            v-tippy
                                            type="link"
                                            size="small"
                                            class="shrink-0 !px-0"
                                            :content="$t('open')"
                                            @click.stop="openClientCard(item.id)">
                                            <i class="fi fi-rr-arrow-up-right-from-square" />
                                        </a-button>
                                    </div>
                                    <div class="contract_service_cards_modal__item_meta">
                                        <span v-if="item.inn">{{ $t('deals_contracts.service_cards_inn') }}: {{ item.inn }}</span>
                                    </div>
                                </div>
                            </div>

                            <infinite-loading
                                ref="matchingSuggestionsInfinite"
                                :identifier="matchingSuggestionsInfiniteId"
                                :distance="10"
                                :forceUseInfiniteWrapper="true"
                                @infinite="loadMatchingSuggestionsInfinite">
                                <div slot="spinner" class="contract_service_cards_modal__loading">
                                    <a-spin size="small" />
                                </div>
                                <div slot="no-more"></div>
                                <div slot="no-results"></div>
                            </infinite-loading>
                        </div>
                        <div
                            v-if="matchingSuggestionsInitialized && !filteredMatchingSuggestions.length"
                            class="pb-3 text-sm text-[rgba(0,0,0,0.45)]">
                            {{ $t('deals_contracts.service_cards_matching_bin_empty') }}
                        </div>
                    </div>

                    <div class="contract_service_cards_modal__section">
                        <div class="contract_service_cards_modal__section_title">
                            {{ $t('deals_contracts.service_cards_other_bin_title') }}
                        </div>
                        <div class="contract_service_cards_modal__list" infinite-wrapper>
                            <div
                                v-for="item in filteredOtherSuggestions"
                                :key="`other_${item.id}`"
                                class="contract_service_cards_modal__item select-none"
                                :class="{ 'is-selected': selectedSuggestionIdSet.has(item.id) }"
                                :title="item.name"
                                @click="toggleSuggestion(item.id)">
                                <a-checkbox
                                    class="contract_service_cards_modal__check"
                                    :checked="selectedSuggestionIdSet.has(item.id)"
                                    @click.stop
                                    @change="toggleSuggestion(item.id)" />
                                <div class="contract_service_cards_modal__item_content">
                                    <div class="flex items-start justify-between gap-2">
                                        <div class="contract_service_cards_modal__item_name text-[rgba(0,0,0,0.88)]">
                                            {{ item.name }}
                                        </div>
                                        <a-button
                                            v-tippy
                                            type="link"
                                            size="small"
                                            class="shrink-0 !px-0"
                                            :content="$t('open')"
                                            @click.stop="openClientCard(item.id)">
                                            <i class="fi fi-rr-arrow-up-right-from-square" />
                                        </a-button>
                                    </div>
                                    <div class="contract_service_cards_modal__item_meta">
                                        <span v-if="item.inn">{{ $t('deals_contracts.service_cards_inn') }}: {{ item.inn }}</span>
                                    </div>
                                </div>
                            </div>

                            <infinite-loading
                                ref="otherSuggestionsInfinite"
                                :identifier="otherSuggestionsInfiniteId"
                                :distance="10"
                                :forceUseInfiniteWrapper="true"
                                @infinite="loadOtherSuggestionsInfinite">
                                <div slot="spinner" class="contract_service_cards_modal__loading">
                                    <a-spin size="small" />
                                </div>
                                <div slot="no-more"></div>
                                <div slot="no-results"></div>
                            </infinite-loading>
                        </div>
                        <div
                            v-if="otherSuggestionsInitialized && !filteredOtherSuggestions.length"
                            class="text-sm text-[rgba(0,0,0,0.45)] py-3">
                            {{ $t('deals_contracts.service_cards_other_bin_empty') }}
                        </div>
                    </div>
                </div>
            </div>

            <template #footer>
                <div :class="isMobile ? 'flex w-full flex-col gap-2' : 'flex w-full items-center justify-end gap-2'">
                    <a-button
                        type="primary"
                        :block="isMobile"
                        :loading="binding"
                        :disabled="!selectedSuggestionIds.length"
                        @click="bindSelectedCards">
                        {{ $t('deals_contracts.service_cards_select') }} ({{ selectedSuggestionIds.length }})
                    </a-button>
                    <a-button type="ui_ghost" :block="isMobile" @click="closeAssignModal">{{ $t('cancel') }}</a-button>
                </div>
            </template>
        </a-modal>
    </div>
</template>

<script>
import { errorHandler } from '@/utils/index.js'

const CUSTOMER_CARDS_ENDPOINT = '/help_desk/customer_cards/'

export default {
    name: 'ContractServiceCardsManager',
    components: {
        InfiniteLoading: () => import('vue-infinite-loading'),
    },
    props: {
        contract: {
            type: Object,
            default: () => null,
        },
        canEdit: {
            type: Boolean,
            default: true,
        },
    },
    data() {
        return {
            cardsLoading: false,
            assignedCards: [],
            assignModalVisible: false,

            suggestionsQuery: '',
            selectedSuggestionIds: [],
            binding: false,
            unbindingCardIds: [],
            otherReloadTimer: null,

            matchingSuggestionsItems: [],
            matchingSuggestionsPage: 1,
            matchingSuggestionsHasNext: true,
            matchingSuggestionsLoading: false,
            matchingSuggestionsInitialized: false,
            matchingSuggestionsInfiniteId: 1,

            otherSuggestionsItems: [],
            otherSuggestionsPage: 1,
            otherSuggestionsHasNext: true,
            otherSuggestionsLoading: false,
            otherSuggestionsInitialized: false,
            otherSuggestionsInfiniteId: 1,
        }
    },
    computed: {
        isMobile() {
            return this.$store?.state?.isMobile
        },
        modalWidth() {
            return this.isMobile ? '100vw' : 760
        },
        modalBodyStyle() {
            if (this.isMobile) {
                return {
                    height: 'calc(100vh - 116px)',
                    overflowY: 'auto',
                }
            }
            return {
                maxHeight: 'calc(100vh - 72px)',
                overflowY: 'auto',
            }
        },
        contractId() {
            return this.contract?.id ? String(this.contract.id) : null
        },
        organizationId() {
            const organization = this.contract?.organization
            if (organization && typeof organization === 'object') {
                return organization.id || organization.pk || null
            }
            return organization || this.contract?.organization_id || null
        },
        contractCustomerCardInnRaw() {
            return String(this.contract?.customer_card?.inn || '').trim()
        },
        contractCustomerCardInn() {
            return this.normalizeInn(this.contractCustomerCardInnRaw)
        },
        lowerSearchInn() {
            return this.normalizeInn(this.suggestionsQuery)
        },
        displayCards() {
            return [...this.assignedCards].sort((a, b) => String(a.name || '').localeCompare(String(b.name || '')))
        },
        assignedCardIdSet() {
            return new Set(this.assignedCards.map(item => String(item.id)))
        },
        canManageCards() {
            return Boolean(this.canEdit && this.contractId && this.organizationId)
        },
        filteredMatchingSuggestions() {
            return this.matchingSuggestionsItems
        },
        filteredOtherSuggestions() {
            return this.otherSuggestionsItems
        },
        selectedSuggestionIdSet() {
            return new Set(this.selectedSuggestionIds)
        },
        unbindingCardIdSet() {
            return new Set(this.unbindingCardIds)
        },
    },
    watch: {
        contractId: {
            immediate: true,
            handler() {
                this.loadAssignedCards()
            },
        },
        organizationId() {
            this.loadAssignedCards()
        },
        suggestionsQuery() {
            this.scheduleLowerReload()
        },
    },
    beforeDestroy() {
        if (this.otherReloadTimer) {
            clearTimeout(this.otherReloadTimer)
            this.otherReloadTimer = null
        }
    },
    methods: {
        parseResults(data) {
            return Array.isArray(data) ? data : (data?.results || [])
        },
        normalizeInn(value) {
            return String(value || '').replace(/\D+/g, '')
        },
        normalizeCard(item) {
            if (!item) return null
            const id = item?.id ? String(item.id) : null
            if (!id) return null
            return {
                id,
                name: item?.string_view || item?.full_name || item?.name || id,
                inn: item?.inn || '',
            }
        },
        mergeCards(source) {
            const map = new Map()
            source.forEach(item => {
                const normalized = this.normalizeCard(item)
                if (!normalized?.id) return
                map.set(normalized.id, normalized)
            })
            return Array.from(map.values())
        },
        mergeUniqueCards(targetList, incomingList) {
            const map = new Map(targetList.map(item => [item.id, item]))
            incomingList.forEach(item => {
                if (!item?.id) return
                map.set(item.id, item)
            })
            return Array.from(map.values())
        },
        async fetchCards(paramsBuilder) {
            const list = []
            let page = 1
            let hasNext = true

            while (hasNext && page <= 50) {
                const params = paramsBuilder(page)
                const { data } = await this.$http.get(CUSTOMER_CARDS_ENDPOINT, { params })
                const results = this.parseResults(data)
                list.push(...results)
                hasNext = Boolean(data?.next)
                page += 1
                if (Array.isArray(data)) {
                    hasNext = false
                }
            }
            return list
        },
        createCardsFilter(extra = {}) {
            return JSON.stringify({
                org_admin: this.organizationId,
                ...extra,
            })
        },
        async loadAssignedCards() {
            this.assignedCards = []
            if (!this.contractId) return

            this.cardsLoading = true
            try {
                const { data } = await this.$http.get(`/customer_contracts/${this.contractId}/service_cards/`, {
                    params: {
                        page_size: 100,
                    },
                })
                const items = this.parseResults(data)
                this.assignedCards = this.mergeCards(items)
            } catch (error) {
                this.assignedCards = []
                errorHandler({ error, show: false })
            } finally {
                this.cardsLoading = false
            }
        },
        resetSuggestions() {
            this.suggestionsQuery = ''
            this.selectedSuggestionIds = []

            this.matchingSuggestionsItems = []
            this.matchingSuggestionsPage = 1
            this.matchingSuggestionsHasNext = true
            this.matchingSuggestionsLoading = false
            this.matchingSuggestionsInitialized = false
            this.matchingSuggestionsInfiniteId += 1

            this.otherSuggestionsItems = []
            this.otherSuggestionsPage = 1
            this.otherSuggestionsHasNext = true
            this.otherSuggestionsLoading = false
            this.otherSuggestionsInitialized = false
            this.otherSuggestionsInfiniteId += 1
        },
        openAssignModal() {
            if (!this.canManageCards) return
            this.assignModalVisible = true
            this.resetSuggestions()
            this.$nextTick(() => {
                this.$refs.matchingSuggestionsInfinite?.stateChanger?.reset()
                this.$refs.otherSuggestionsInfinite?.stateChanger?.reset()
            })
        },
        closeAssignModal() {
            this.assignModalVisible = false
        },
        scheduleLowerReload() {
            if (!this.assignModalVisible) return
            if (this.otherReloadTimer) clearTimeout(this.otherReloadTimer)
            this.otherReloadTimer = setTimeout(() => {
                this.otherSuggestionsItems = []
                this.otherSuggestionsPage = 1
                this.otherSuggestionsHasNext = true
                this.otherSuggestionsLoading = false
                this.otherSuggestionsInitialized = false
                this.otherSuggestionsInfiniteId += 1
                this.$nextTick(() => this.$refs.otherSuggestionsInfinite?.stateChanger?.reset())
            }, 250)
        },
        async loadMatchingSuggestionsInfinite($state) {
            if (!this.organizationId || !this.contractCustomerCardInnRaw) {
                this.matchingSuggestionsInitialized = true
                this.matchingSuggestionsHasNext = false
                $state.complete()
                return
            }
            if (this.matchingSuggestionsLoading) return
            if (!this.matchingSuggestionsHasNext) {
                this.matchingSuggestionsInitialized = true
                $state.complete()
                return
            }

            this.matchingSuggestionsLoading = true
            try {
                const { data } = await this.$http.get(CUSTOMER_CARDS_ENDPOINT, {
                    params: {
                        filters: this.createCardsFilter({
                            inn: this.contractCustomerCardInnRaw,
                        }),
                        page_size: 30,
                        page: this.matchingSuggestionsPage,
                    },
                })
                const incoming = this.parseResults(data)
                    .map(item => this.normalizeCard(item))
                    .filter(Boolean)
                    .filter(item => !this.assignedCardIdSet.has(item.id))

                this.matchingSuggestionsItems = this.mergeUniqueCards(this.matchingSuggestionsItems, incoming)

                this.matchingSuggestionsPage += 1
                this.matchingSuggestionsHasNext = Boolean(data?.next)
                this.matchingSuggestionsInitialized = true
                if (this.matchingSuggestionsHasNext) {
                    $state.loaded()
                } else {
                    $state.complete()
                }
            } catch (error) {
                this.matchingSuggestionsInitialized = true
                this.matchingSuggestionsHasNext = false
                errorHandler({ error, show: false })
                $state.complete()
            } finally {
                this.matchingSuggestionsLoading = false
            }
        },
        async loadOtherSuggestionsInfinite($state) {
            if (!this.organizationId) {
                this.otherSuggestionsInitialized = true
                this.otherSuggestionsHasNext = false
                $state.complete()
                return
            }
            if (this.otherSuggestionsLoading) return
            if (!this.otherSuggestionsHasNext) {
                this.otherSuggestionsInitialized = true
                $state.complete()
                return
            }

            this.otherSuggestionsLoading = true
            try {
                const filterObj = {}
                if (this.lowerSearchInn) {
                    filterObj.inn__icontains = this.lowerSearchInn
                }

                const { data } = await this.$http.get(CUSTOMER_CARDS_ENDPOINT, {
                    params: {
                        filters: this.createCardsFilter(filterObj),
                        page_size: 30,
                        page: this.otherSuggestionsPage,
                    },
                })
                const incoming = this.parseResults(data)
                    .map(item => this.normalizeCard(item))
                    .filter(Boolean)
                    .filter(item => !this.assignedCardIdSet.has(item.id))
                    .filter(item => !this.matchingSuggestionsItems.some(match => match.id === item.id))
                    .filter(item => {
                        if (!this.contractCustomerCardInn) return true
                        return this.normalizeInn(item.inn) !== this.contractCustomerCardInn
                    })

                this.otherSuggestionsItems = this.mergeUniqueCards(this.otherSuggestionsItems, incoming)

                this.otherSuggestionsPage += 1
                this.otherSuggestionsHasNext = Boolean(data?.next)
                this.otherSuggestionsInitialized = true
                if (this.otherSuggestionsHasNext) {
                    $state.loaded()
                } else {
                    $state.complete()
                }
            } catch (error) {
                this.otherSuggestionsInitialized = true
                this.otherSuggestionsHasNext = false
                errorHandler({ error, show: false })
                $state.complete()
            } finally {
                this.otherSuggestionsLoading = false
            }
        },
        toggleSuggestion(id) {
            const normalizedId = String(id)
            if (this.selectedSuggestionIdSet.has(normalizedId)) {
                this.selectedSuggestionIds = this.selectedSuggestionIds.filter(item => item !== normalizedId)
                return
            }
            this.selectedSuggestionIds = [...this.selectedSuggestionIds, normalizedId]
        },
        openClientCard(id) {
            const clientId = String(id || '')
            if (!clientId) return

            const query = { ...this.$route.query }
            if (query.client !== clientId) {
                query.client = clientId
                this.$router.push({ query })
                return
            }

            delete query.client
            this.$router.replace({ query })
                .then(() => {
                    query.client = clientId
                    this.$router.replace({ query })
                })
        },
        async bindSelectedCards() {
            if (!this.selectedSuggestionIds.length || !this.contractId) return
            this.binding = true
            try {
                await this.$http.post(
                    `/customer_contracts/${this.contractId}/service_cards/bind/`,
                    {
                        customer_cards: this.selectedSuggestionIds,
                    },
                )

                this.$message.success(this.$t('deals_contracts.service_cards_bind_success', { count: this.selectedSuggestionIds.length }))
                await this.loadAssignedCards()
                this.$emit('changed')
                this.closeAssignModal()
            } catch (error) {
                errorHandler({ error })
            } finally {
                this.binding = false
            }
        },
        confirmUnbindCard(cardId) {
            this.$confirm({
                title: this.$t('deals_contracts.service_cards_unbind_confirm'),
                okText: this.$t('deals_contracts.service_cards_unbind_confirm_ok'),
                cancelText: this.$t('close'),
                onOk: () => this.unbindCard(cardId),
            })
        },
        async unbindCard(cardId) {
            if (!this.contractId || !cardId) return

            const normalizedId = String(cardId)
            if (this.unbindingCardIdSet.has(normalizedId)) return

            this.unbindingCardIds = [...this.unbindingCardIds, normalizedId]
            try {
                await this.$http.post(
                    `/customer_contracts/${this.contractId}/service_cards/unbind/`,
                    {
                        customer_cards: [normalizedId],
                    },
                )

                this.$message.success(this.$t('deals_contracts.service_cards_unbind_success'))
                await this.loadAssignedCards()
                this.$emit('changed')
            } catch (error) {
                errorHandler({ error })
            } finally {
                this.unbindingCardIds = this.unbindingCardIds.filter(item => item !== normalizedId)
            }
        },
    },
}
</script>

<style lang="scss" scoped>
.contract_service_cards {
    margin-top: 8px;
    border: 1px solid var(--border2);
    border-radius: 12px;
    padding: 12px;
}

.contract_service_cards__head {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    gap: 10px;
    margin-bottom: 10px;
}

.contract_service_cards__head_text {
    min-width: 0;
}

.contract_service_cards__title {
    font-size: 14px;
    font-weight: 600;
    color: rgba(0, 0, 0, 0.85);
}

.contract_service_cards__list {
    display: grid;
    gap: 8px;
}

.contract_service_cards__item {
    border: 1px solid #eef2f7;
    border-radius: 10px;
    padding: 10px 12px;
    background: #fafcff;
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    gap: 10px;
}

.contract_service_cards__item_main {
    min-width: 0;
    flex: 1;
}

.contract_service_cards__item_title {
    font-size: 13px;
    font-weight: 600;
    color: rgba(0, 0, 0, 0.88);
}

.contract_service_cards__item_title_link {
    background: transparent;
    border: 0;
    padding: 0;
    cursor: pointer;
    text-align: left;
    font-size: 13px;
    font-weight: 600;
    line-height: 1.35;
    color: rgba(0, 0, 0, 0.88);
}

.contract_service_cards__item_title_link:hover {
    color: #2f5ff5;
}

.contract_service_cards__item_meta {
    margin-top: 4px;
    display: flex;
    align-items: center;
    gap: 8px;
    color: #6b7280;
    font-size: 12px;
}

.contract_service_cards__unbind_btn {
    padding: 0;
    height: auto;
}

.contract_service_cards_modal__content {
    display: grid;
    gap: 10px;
}

.contract_service_cards_modal__search::v-deep {
    .ant-input-affix-wrapper {
        border: 0;
        box-shadow: none;
        background: transparent;
        padding: 0;
    }

    .ant-input {
        border: 0;
        box-shadow: none;
        background: transparent;
        color: #000;
        padding-left: 0;
        padding-right: 20px;
    }

    .ant-input::placeholder {
        font-weight: 400;
        font-size: 15px;
        color: #000;
    }

    .ant-input:hover,
    .ant-input:focus,
    .ant-input-affix-wrapper:hover,
    .ant-input-affix-wrapper:focus,
    .ant-input-affix-wrapper-focused {
        border-color: transparent;
        box-shadow: none;
    }

    .ant-input-suffix {
        right: 3px;
        opacity: 0.6;
        margin-top: 1px;
    }
}

.contract_service_cards_modal__sections {
    display: grid;
    gap: 12px;
}

.contract_service_cards_modal__section {
    display: grid;
    gap: 8px;
}

.contract_service_cards_modal__section_title {
    font-size: 12px;
    font-weight: 600;
    color: rgba(0, 0, 0, 0.65);
}

.contract_service_cards_modal__list {
    display: grid;
    gap: 8px;
    max-height: 460px;
    overflow-y: auto;
    padding-right: 2px;
}

.contract_service_cards_modal__item {
    display: flex;
    align-items: flex-start;
    gap: 10px;
    border: 1px solid transparent;
    border-radius: 10px;
    background: #f7f9fc;
    padding: 10px 12px;
    cursor: pointer;
}

.contract_service_cards_modal__item.is-selected {
    border-color: #2f5ff5;
    box-shadow: 0 6px 16px rgba(47, 95, 245, 0.12);
}

.contract_service_cards_modal__check {
    flex-shrink: 0;
    margin-top: 2px;
}

.contract_service_cards_modal__item_content {
    min-width: 0;
    flex: 1;
}

.contract_service_cards_modal__item_name {
    font-size: 13px;
    font-weight: 600;
    line-height: 1.35;
    color: rgba(0, 0, 0, 0.88);
}

.contract_service_cards_modal__item_meta {
    margin-top: 3px;
    color: #6b7280;
    font-size: 12px;
}

.contract_service_cards_modal__loading {
    display: flex;
    justify-content: center;
    padding: 8px;
}

@media (max-width: 991px) {
    .contract_service_cards_modal::v-deep {
        .ant-modal {
            width: 100vw !important;
            max-width: 100vw;
            margin: 0;
            padding-bottom: 0;
            top: 0;
        }

        .ant-modal-content {
            min-height: 100vh;
            border-radius: 0;
            display: flex;
            flex-direction: column;
        }

        .ant-modal-body {
            flex: 1;
            min-height: 0;
        }
    }

    .contract_service_cards__head {
        flex-direction: column;
        align-items: stretch;
    }

    .contract_service_cards__item {
        flex-direction: column;
        align-items: stretch;
    }

    .contract_service_cards__unbind_btn {
        align-self: flex-start;
    }

    .contract_service_cards_modal__list {
        max-height: 360px;
    }
}
</style>
