<template>
    <ModuleWrapper :pageTitle="pageTitle">
        <template v-slot:h_left>
            <slot name="pageFilter" />
        </template>
        <template v-slot:h_right>
            <slot name="inviteButton" />
            <slot name="addButton" />
        </template>
        <div>
            <ViewAccordionItem
                v-for="organization in organizationList" 
                :key="organization.id"
                class="custom_mb"
                :organization="organization"
                :expandedKeys="expandedKeys" />
        </div>
        <infinite-loading 
            class="mt-2"
            ref="infiniteLoading"
            @infinite="getData"
            :identifier="infiniteId"
            :distance="10">
            <div 
                slot="spinner"
                class="flex items-center justify-center inf_spinner">
                <a-spin />
            </div>
            <div slot="no-more"></div>
            <div slot="no-results"></div>
        </infinite-loading>
    </ModuleWrapper>
</template>

<script>
import { mapActions, mapState } from 'vuex'
import eventBus from '@/utils/eventBus'
export default {
    name: 'ViewAccordionTree',
    components: {
        ViewAccordionItem: () => import('./ViewAccordionItem'),
        InfiniteLoading: () => import('vue-infinite-loading'),
        ModuleWrapper: () => import('@/components/ModuleWrapper/index.vue')
    },
    props: {
        pageName: {
            type: String,
            required: true
        }
    },
    data() {
        return {
            organizationLoading: false,
            pageSize: 15,
            infiniteId: 'organization_list',
            expandedKeys: []
        }
    },
    created() {
        if(this.organizationList.length) 
            this.expandFirstOrganization()
    },
    computed: {
        ...mapState({
            organizations: state => state.organization.organizations,
        }),
        isOrganizationsEmpty() {
            return !Object.keys(this.organizations).length
        },
        pageTitle() {
            return this.$route?.meta?.title || ''
        },
        nextOrganization() {
            if(this.isOrganizationsEmpty) 
                return true
            return this.organizations.next
        },
        organizationList() {
            return this.organizations.results || []
        },
        page() {
            const startPage = 0
            return this.organizations.page || startPage
        },
        filterSearch() {
            return this.$store.state.filter.filtersSearch.organizationList
        },
        params() {
            const nextPage = this.page + 1
            return {
                page: nextPage,
                page_size: this.pageSize,
                page_name: this.pageName,
                display: 'root'
            }
        }
    },
    mounted() {
        eventBus.$on(`update_filter_catalogs.ContractorModel`, () => {
            this.reload()
        })
    },
    beforeDestroy() {
        eventBus.$off(`update_filter_catalogs.ContractorModel`)
    },
    methods: {
        ...mapActions({
            getOrganizationsList: 'organization/getOrganizationsList',
            getActionInfo: 'organization/getActionInfo',
        }),
        async getData($state) {
            if(this.nextOrganization) {
                if(!this.organizationLoading) {
                    this.organizationLoading = true
                    try {
                        const organizations = await this.getOrganizationsList({ 
                            params: this.params, 
                            isSearch: this.filterSearch
                        })

                        const organizationsId = organizations.results.map(organization => organization.id)
                        await this.getActionInfo({ payload: organizationsId })

                        if(!this.expandedKeys.length && this.organizationList.length) 
                            this.expandFirstOrganization()

                        if(this.nextOrganization) 
                            $state.loaded()
                        else
                            $state.complete()
                    } catch(error) {
                        console.error(error)
                    } finally {
                        this.organizationLoading = false
                    }
                }
            } else {
                $state.complete()
            }
        },
        expandFirstOrganization() {
            eventBus.$emit('open_first_organization')
        },
        reload() {
            this.$store.commit('organization/CLEAR_ORGANIZATIONS')
            this.$nextTick(()=>{
                if(this.$refs.infiniteLoading){
                    this.$refs.infiniteLoading.stateChanger.reset(); 
                }
            })

        },

    }
}
</script>

<style scoped lang="scss">
.custom_mb:not(:last-child) {
    margin-bottom: 1rem;
}
.wrapper_org{
    height: 100%;
    overflow: hidden;
}
</style>