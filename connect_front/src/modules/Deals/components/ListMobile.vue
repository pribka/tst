<template>
    <div class="contracts_mobile_list">
        <div
            v-if="listEmpty"
            class="pt-7">
            <a-empty :description="$t('team.no_data')" />
        </div>

        <MobileContractCard
            v-for="item in list"
            :key="item.id"
            :item="item"
            @open="openContract" />

        <infinite-loading
            ref="contractsInfinity"
            :identifier="pageName"
            :distance="250"
            @infinite="getList">
            <div
                slot="spinner"
                class="flex items-center justify-center inf_spinner mt-3">
                <a-spin />
            </div>
            <div slot="no-more"></div>
            <div slot="no-results"></div>
        </infinite-loading>
    </div>
</template>

<script>
import eventBus from '@/utils/eventBus'
import { errorHandler } from '@/utils/index.js'

export default {
    name: 'DealsContractsListMobile',
    components: {
        InfiniteLoading: () => import('vue-infinite-loading'),
        MobileContractCard: () => import('./MobileContractCard.vue'),
    },
    props: {
        pageModel: {
            type: String,
            default: '',
        },
        pageName: {
            type: String,
            default: '',
        },
    },
    data() {
        return {
            loading: false,
            next: true,
            page: 0,
            pageSize: 15,
            list: [],
            listEmpty: false,
            endpoint: '/customer_contracts/',
        }
    },
    methods: {
        async getList($state) {
            if (!this.next || this.loading) {
                $state.complete()
                return
            }

            try {
                this.loading = true
                this.page += 1
                const { data } = await this.$http.get(this.endpoint, {
                    params: {
                        page: this.page,
                        page_size: this.pageSize,
                        page_name: this.pageName,
                    },
                })

                const results = data?.results || []
                if (results.length) {
                    this.list = this.list.concat(results)
                }

                this.next = Boolean(data?.next)

                if (this.page === 1 && !results.length) {
                    this.listEmpty = true
                }

                if (this.next) {
                    $state.loaded()
                } else {
                    $state.complete()
                }
            } catch (error) {
                errorHandler({ error, show: false })
                $state.complete()
            } finally {
                this.loading = false
            }
        },
        reloadList() {
            this.page = 0
            this.next = true
            this.list = []
            this.listEmpty = false

            this.$nextTick(() => {
                this.$refs.contractsInfinity?.stateChanger?.reset()
            })
        },
        async openContract(id) {
            if (!id) return
            if (String(this.$route.query.contract || '') === String(id)) return
            await this.$router.push({ query: { ...this.$route.query, contract: id } })
        },
    },
    mounted() {
        eventBus.$on(`update_filter_${this.pageModel}_${this.pageName}`, this.reloadList)
        eventBus.$on(`update_filter_${this.pageName}`, this.reloadList)
        eventBus.$on(`update_filter_${this.pageModel}`, this.reloadList)
    },
    beforeDestroy() {
        eventBus.$off(`update_filter_${this.pageModel}_${this.pageName}`, this.reloadList)
        eventBus.$off(`update_filter_${this.pageName}`, this.reloadList)
        eventBus.$off(`update_filter_${this.pageModel}`, this.reloadList)
    },
}
</script>

<style lang="scss" scoped>
.contracts_mobile_list {
    min-height: 100%;
    padding-bottom: 110px;
}
</style>
