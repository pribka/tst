<template>
    <div>
        <div
            v-if="listEmpty"
            class="pt-7">
            <a-empty :description="$t('team.no_data')" />
        </div>

        <MobileListCard
            v-for="item in list"
            :key="item.id"
            :item="item" />

        <infinite-loading
            ref="catalog_infinity"
            :identifier="page_name"
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

export default {
    name: 'DirectoriesTeamListMobile',
    components: {
        InfiniteLoading: () => import('vue-infinite-loading'),
        MobileListCard: () => import('./components/MobileListCard.vue')
    },
    props: {
        pageModel: {
            type: String,
            default: ''
        },
        page_name: {
            type: String,
            default: ''
        }
    },
    data() {
        return {
            loading: false,
            next: true,
            page: 0,
            pageSize: 15,
            list: [],
            listEmpty: false,
            endpoint: '/users/my_organizations/'
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
                        display: 'root',
                        page: this.page,
                        page_size: this.pageSize,
                        page_name: this.page_name
                    }
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
                this.$message.error(this.$t('team.error'))
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
                this.$refs.catalog_infinity?.stateChanger?.reset()
            })
        }
    },
    mounted() {
        eventBus.$on(`update_filter_${this.pageModel}`, this.reloadList)
        eventBus.$on(`update_filter_${this.pageModel}_${this.page_name}`, this.reloadList)
    },
    beforeDestroy() {
        eventBus.$off(`update_filter_${this.pageModel}`, this.reloadList)
        eventBus.$off(`update_filter_${this.pageModel}_${this.page_name}`, this.reloadList)
    }
}
</script>
