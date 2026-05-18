<template>
    <div>
        <h1 v-if="pageH1Title" class="m_page_title">
            {{ pageH1Title }}
        </h1>
        <div 
            v-if="empty && !loading" 
            class="mt-5">
            <a-empty :description="$t('team.no_data')" />
        </div>
        <MobileCard 
            v-for="item in org.results" 
            :key="item.id" 
            :openOrgDrawer="openOrgDrawer"
            :reloadMainList="reloadList"
            :isScrolling="isScrolling"
            :item="item" />
        <infinite-loading 
            ref="org_infinity"
            @infinite="getList"
            :identifier="infiniteId"
            v-bind:distance="10">
            <div 
                slot="spinner"
                class="flex items-center justify-center inf_spinner">
                <a-spin />
            </div>
            <div slot="no-more"></div>
            <div slot="no-results"></div>
        </infinite-loading>
        <MobileOrgInfo 
            ref="mobileOrgInfo" 
            :reloadMainList="reloadList"
            :minusUserCount="minusUserCount" />
    </div>
</template>

<script>
import { useScroll } from '@vueuse/core'
import eventBus from '@/utils/eventBus'
export default {
    components: {
        InfiniteLoading: () => import('vue-infinite-loading'),
        MobileCard: () => import('./MobileCard.vue'),
        MobileOrgInfo: () => import('./OrgInfo/MobileOrgInfo.vue')
    },
    computed: {
        pageH1Title() {
            return this.$route?.meta?.title ? this.$route.meta.title : null
        }
    },
    data() {
        return {
            loading: false,
            page: 0,
            empty: false,
            page_name: 'organization_list',
            infiniteId: 'organization_list',
            isScrolling: false,
            org: {
                results: [],
                next: true,
                count: 0
            }
        }
    },
    methods: {
        minusUserCount(record) {
            const index = this.org.results.findIndex(f => f.id === record.id)
            if(index !== -1) {
                const newCount = this.org.results[index].members_count - 1
                this.$set(this.org.results[index], 'members_count', newCount)
            }
        },
        reloadList() {
            this.$nextTick(() => {
                this.page = 0
                this.empty = false
                this.org = {
                    results: [],
                    next: true,
                    count: 0
                }
                this.$refs['org_infinity'].stateChanger.reset()
            })
        },
        openOrgDrawer(org) {
            this.$refs.mobileOrgInfo.openDrawer(org)
        },
        async getList($state) {
            if(!this.loading && this.org.next) {
                try {
                    this.loading = true
                    this.page += 1
                    const { data } = await this.$http.get('/users/my_organizations/', {
                        params: {
                            page: this.page,
                            page_size: 15,
                            page_name: this.page_name
                        }
                    })

                    if(data) {
                        this.org.count = data.count
                        this.org.next = data.next
                    }

                    if(data?.results?.length)
                        this.org.results = this.org.results.concat(data.results)

                    if(this.page === 1 && !this.org.results.length) {
                        this.empty = true
                    }
                        
                    if(this.org.next)
                        $state.loaded()
                    else
                        $state.complete()
                } catch(e) {
                    console.log(e)
                } finally {
                    this.loading = false
                }
            }
        },
    },
    mounted () {
        eventBus.$on(`update_filter_${this.catalogs.ContractorModel}`, () =>{
            this.page = 0
            this.$nextTick(() => {
                const { isScrolling } = useScroll(document)
                this.isScrolling = isScrolling
            })
        })
    },
    beforeDestroy() {
        eventBus.$off(`update_filter_${this.catalogs.ContractorModel}`)
    },
}
</script>