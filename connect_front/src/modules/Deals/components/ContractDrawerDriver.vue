<template>
    <ContractDrawer
        :value="drawerVisible"
        :loading="detailLoading"
        :saving="false"
        :savingProjects="savingProjects"
        :contract="activeContract"
        :actions="actions"
        :isNew="isCreatingContract"
        :edit="isEditMode"
        :routeTab="routeContractTab"
        @close="closeDrawer"
        @reload="reloadActiveContract"
        @edit="editActiveContract"
        @delete="deleteActiveContract"
        @tab-change="syncTabToRoute"
        @save-projects="saveContractProjects"
        @open-related="openRelatedEntity" />
</template>

<script>
import eventBus from '@/utils/eventBus'
import { errorHandler } from '@/utils/index.js'

export default {
    name: 'DealsContractDrawerDriver',
    components: {
        ContractDrawer: () => import('./ContractDrawer.vue'),
    },
    data() {
        return {
            drawerVisible: false,
            detailLoading: false,
            savingProjects: false,
            activeContractId: null,
            activeContract: null,
            actions: null,
            requestSeq: 0,
            model: 'customer_contracts.CustomerContractModel',
            pageName: 'page_list_contracts_v3_customer_contracts.CustomerContractModel',
        }
    },
    computed: {
        routeContractId() {
            return this.$route.query.contract || null
        },
        routeContractTab() {
            return this.normalizeTab(this.$route.query.ctab)
        },
        isCreatingContract() {
            const value = String(this.routeContractId || '').toLowerCase()
            return value === 'new' || value === 'create'
        },
        isEditMode() {
            return Boolean(this.activeContractId) && !this.isCreatingContract
        },
    },
    watch: {
        routeContractId: {
            immediate: true,
            async handler(value) {
                if (!value) {
                    this.resetState()
                    return
                }
                this.drawerVisible = true
                if (this.isCreatingContract) {
                    this.activeContractId = null
                    this.activeContract = null
                    this.actions = null
                    this.detailLoading = false
                    return
                }
                this.activeContractId = value
                await this.loadContractDetail(value)
            },
        },
    },
    methods: {
        normalizeTab(tab) {
            const tabs = new Set(['overview', 'projects', 'files'])
            const key = String(tab || '')
            return tabs.has(key) ? key : 'overview'
        },
        resetState() {
            this.drawerVisible = false
            this.activeContractId = null
            this.activeContract = null
            this.actions = null
        },
        async loadContractDetail(id) {
            if (!id) return
            const seq = ++this.requestSeq
            try {
                this.detailLoading = true
                this.actions = null
                const { data } = await this.$http.get(`/customer_contracts/${id}/`)
                if (seq !== this.requestSeq) return
                this.activeContract = data
                await this.loadContractActions(id, seq)
            } catch (error) {
                if (seq !== this.requestSeq) return
                errorHandler({ error })
                this.closeDrawer()
            } finally {
                if (seq === this.requestSeq) {
                    this.detailLoading = false
                }
            }
        },
        async loadContractActions(id, seq = this.requestSeq) {
            if (!id) return
            try {
                const { data } = await this.$http.get(`/customer_contracts/${id}/action_info/`)
                if (seq !== this.requestSeq) return
                this.actions = data?.actions || null
            } catch (error) {
                if (seq !== this.requestSeq) return
                this.actions = null
                errorHandler({ error, show: false })
            }
        },
        async reloadActiveContract() {
            if (this.activeContractId) {
                await this.loadContractDetail(this.activeContractId)
            }
        },
        emitTableUpdate() {
            eventBus.$emit(`update_filter_${this.model}_${this.pageName}`)
        },
        async saveContractProjects(payload) {
            if (!this.activeContractId) return
            try {
                this.savingProjects = true
                await this.$http.patch(`/customer_contracts/${this.activeContractId}/`, {
                    projects: payload?.projects || [],
                })
                await this.loadContractDetail(this.activeContractId)
                eventBus.$emit('DEALS_CONTRACT_UPDATED', { id: this.activeContractId })
                this.emitTableUpdate()
                this.$message.success(this.$t('deals_contracts.projects_saved'))
            } catch (error) {
                errorHandler({ error })
            } finally {
                this.savingProjects = false
            }
        },
        editActiveContract() {
            if (!this.activeContract) return
            eventBus.$emit('DEALS_EDIT_CONTRACT', this.activeContract)
        },
        deleteActiveContract() {
            if (!this.activeContractId) return
            this.$confirm({
                title: this.$t('deals_contracts.delete_confirm'),
                closable: true,
                maskClosable: true,
                cancelText: this.$t('cancel'),
                okText: this.$t('remove'),
                okType: 'danger',
                zIndex: 999999,
                onOk: () => {
                    return new Promise((resolve, reject) => {
                        this.$http.post('/table_actions/update_is_active/', [{ id: this.activeContractId, is_active: false }])
                            .then(() => {
                                this.$message.success(this.$t('deals_contracts.delete_success'))
                                this.emitTableUpdate()
                                this.closeDrawer()
                                resolve()
                            })
                            .catch((error) => {
                                errorHandler({ error })
                                reject()
                            })
                    })
                },
            })
        },
        closeDrawer() {
            const query = { ...this.$route.query }
            delete query.contract
            delete query.ctab
            this.$router.replace({ query })
        },
        async syncTabToRoute(tab) {
            if (!this.routeContractId) return
            const nextTab = this.normalizeTab(tab)
            if (String(this.$route.query.ctab || 'overview') === nextTab) return
            await this.$router.push({
                query: {
                    ...this.$route.query,
                    ctab: nextTab,
                },
            })
        },
        async openRelatedEntity(payload) {
            const routeMap = {
                task: 'task',
                ticket: 'ticketView',
            }
            const key = routeMap[payload?.type]
            if (!key || !payload?.id) return
            await this.$router.push({ query: { ...this.$route.query, [key]: payload.id } })
        },
        handleContractUpdated(payload) {
            const updatedId = payload?.id
            if (!this.activeContractId || (updatedId && String(updatedId) !== String(this.activeContractId))) return
            this.reloadActiveContract()
        },
    },
    mounted() {
        eventBus.$on('DEALS_CONTRACT_UPDATED', this.handleContractUpdated)
    },
    beforeDestroy() {
        eventBus.$off('DEALS_CONTRACT_UPDATED', this.handleContractUpdated)
    },
}
</script>
