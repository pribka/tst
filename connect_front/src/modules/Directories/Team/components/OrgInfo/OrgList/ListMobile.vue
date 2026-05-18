<template>
    <div>
        <div 
            v-if="empty && !loading" 
            class="mt-5">
            <a-empty :description="$t('team.no_data')" />
        </div>
        <OrgCard 
            v-for="item in orgs.results" 
            :key="item.id" 
            :org="org"
            :item="item" />
        <infinite-loading 
            ref="org_list_infinity"
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
    </div>
</template>

<script>
import InfiniteLoading from 'vue-infinite-loading'
import OrgCard from './OrgCard.vue'
export default {
    components: {
        InfiniteLoading,
        OrgCard
    },
    props: {
        org: {
            type: [Object],
            required: true
        }
    },
    data() {
        return {
            loading: false,
            page: 0,
            empty: false,
            infiniteId: 'org_c_list',
            isScrolling: false,
            orgs: {
                results: [],
                next: true,
                count: 0
            }
        }
    },
    methods: {
        reloadList() {
            this.$nextTick(() => {
                this.page = 0
                this.empty = false
                this.orgs = {
                    results: [],
                    next: true,
                    count: 0
                }
                this.$refs['org_list_infinity'].stateChanger.reset()
            })
        },
        async getList($state) {
            if(!this.loading && this.orgs.next) {
                try {
                    this.loading = true
                    this.page += 1
                    const { data } = await this.$http.get(`/users/my_organizations/${this.org.id}/relations/`, {
                        params: {
                            page: this.page,
                            page_size: 15
                        }
                    })

                    if(data) {
                        this.orgs.count = data.count
                        this.orgs.next = data.next
                    }

                    if(data?.results?.length)
                        this.orgs.results = this.orgs.results.concat(data.results)

                    if(this.page === 1 && !this.orgs.results.length) {
                        this.empty = true
                    }
                        
                    if(this.orgs.next)
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
    }
}
</script>