<template>
    <div class="page_padding">
        <h1 v-if="showPageTitle && pageH1Title" class="m_page_title">
            {{ pageH1Title }}
        </h1>
        <div 
            class="float_add">
            <!-- <div class="filter_slot">
                <slot name="pageFilter" />
            </div> -->
            <a-button 
                flaticon
                shape="circle"
                size="large"
                type="primary"
                icon="fi-rr-plus"
                @click="addOrganization('organization')" />
        </div>
        <div>
            <ViewAccordionItemMobile
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
    </div>
</template>

<script>
import { mapActions, mapState } from 'vuex'
import eventBus from '@/utils/eventBus'
export default {
    name: 'ViewAccordionTree',
    components: {
        ViewAccordionItemMobile: () => import('./ViewAccordionItemMobile.vue'),
        InfiniteLoading: () => import('vue-infinite-loading'),
        // ModuleWrapper
    },
    props: {
        pageName: {
            type: String,
            required: true
        },
        showPageTitle: {
            type: Boolean,
            default: false
        },
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
        pageH1Title() {
            return this.$route?.meta?.title ? this.$route.meta.title : null
        },
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
        addOrganization(organization_type) {
            eventBus.$emit('create_organization', { organization_type })
        },

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
.page_padding{
    padding: 15px;
}
.custom_mb:not(:last-child) {
    margin-bottom: 1rem;
}
.wrapper_org{
    height: 100%;
    overflow: hidden;
}
</style>