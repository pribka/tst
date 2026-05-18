<template>
    <div>
        <div :class="isMobileTemplate ? 'mobile_list' : 'templates-grid'">
            <TemplateGridCard
                v-for="item in list" 
                :key="item.id"
                :item="item"
                :isMobileTemplate="isMobileTemplate"
                class="h-full"
                :templatesSource="templatesSource" />
        </div>
        <infinite-loading 
            @infinite="getTemplates"
            :identifier="infiniteId"
            :distance="50"
            ref="group_infinity">
            <div 
                slot="spinner"
                class="flex items-center justify-center inf_spinner mt-3">
                <a-spin />
            </div>
            <div slot="no-more"></div>
            <div slot="no-results"></div>
        </infinite-loading>
        <div
            v-if="showEmptyState"
            class="mt-6 flex items-center justify-center">
            <a-empty :description="$t('no_data')" />
        </div>
    </div>
</template>

<script>
export default {
    components: {
        InfiniteLoading: () => import('vue-infinite-loading'),
        TemplateGridCard: () => import('./TemplateGridCard.vue')
    },
    props: {
        templatesSource: {
            type: String,
            default: 'templates'
        },
        displaySectionCode: {
            type: String,
            default: ''
        },
        searchQuery: {
            type: String,
            default: ''
        },
        useMobile: {
            type: Boolean,
            default: false
        }
    },
    data() {
        return {
            isLoading: false,
            firstPageLoaded: false,
            params: {
                page: 1,
                page_size: 10,
                page_name: 'productivity-reports'
            },
        }
    },
    computed: {
        isMobile() { 
            return this.$store.state.isMobile
        },
        infiniteId() {
            return this.$store.state.reports.infiniteId[this.templatesSource]
        },
        isMobileTemplate() {
            if(this.useMobile || this.isMobile)
                return true
            return false
        },
        getDataURL() {
            const URLs = {
                'my_templates': '/reports/user_report_settings/',
                'templates': '/reports/report_settings/'
            }
            return URLs[this.templatesSource]
        },
        list() {
            return this.$store.state.reports.templates[this.templatesSource].results
        },
        requestParams() {
            const params = {}

            if (this.displaySectionCode) {
                const filters = this.templatesSource === 'my_templates'
                    ? { base_report__category: this.displaySectionCode }
                    : { category: this.displaySectionCode }

                params.filters = JSON.stringify(filters)
            }

            if (this.searchQuery) {
                params.search = this.searchQuery
            }

            return params
        },
        showEmptyState() {
            return this.firstPageLoaded && !this.isLoading && this.list.length === 0
        }
    },
    methods: {
        reload() {
            this.$store.commit('reports/RESET_TEMPLATES', { listKey: this.templatesSource })
            this.params.page = 1
            this.firstPageLoaded = false
        },
        getTemplates($state) {
            const url = this.getDataURL
            this.isLoading = true
            this.$http(url, { params: this.requestParams })
                .then(({ data }) => {
                    this.$store.commit('reports/LOAD_TEMPLATES', { loadedData: data, listKey: this.templatesSource })
                    this.firstPageLoaded = true
                    if (data.next) {
                        $state.loaded()
                    } else {
                        $state.complete()
                    }
                })
                .catch(error => {
                    console.error(error)
                    this.firstPageLoaded = true
                    this.$message.error(this.$t('Failed to get templates list'))
                })
                .finally(() => {
                    this.isLoading = false
                })
        },
    },
    beforeDestroy() {
        this.$store.commit('reports/RESET_ALL_TEMPLATES')
    }
}
</script>

<style lang="scss" scoped>
.mobile_list{
    &::v-deep{
        .template{
            &:not(:last-child){
                margin-bottom: 10px;
            }
        }
    }
}
.templates-grid {
    display: grid;
    grid-template-columns: repeat(1, 1fr);
    gap: 20px;
    @media (min-width: 840px) {
        grid-template-columns: repeat(2, 1fr);
    }
    @media (min-width: 1240px) {
        grid-template-columns: repeat(3, 1fr);
    }
    @media (min-width: 1536px) {
        grid-template-columns: repeat(4, 1fr);
    }
}
</style>
