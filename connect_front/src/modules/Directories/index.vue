<template>
    <div class="directories_page">
        <component :is="mobileCatalogDrawerComponent" v-if="mobileCatalogDrawerComponent" />
        <aside v-if="!isMobile" class="directories_sidebar">
        <div class="directories_sidebar_head">
            <div class="directories_sidebar_title">
                <span>{{ $t('directories.catalog') }}</span>
            </div>
            <a-input
                v-model="search"
                class="search_input"
                :placeholder="$t('directories.searchPlaceholder')">
                <template #suffix>
                    <i class="fi fi-rr-search" style="opacity: 0.6;" />
                </template>
            </a-input>
        </div>

        <div class="directories_tree">
            <a-spin v-if="loading" class="mt-3 w-full" size="small" />
            <template v-else>
                <div v-for="section in filteredSections" :key="section.id" class="tree_group">
                    <button class="tree_group_btn" @click="toggleSection(section.id)">
                        <span class="tree_group_name">{{ section.name }}</span>
                        <i
                            class="fi fi-rr-angle-small-down tree_group_icon"
                            :class="{ opened: isSectionOpened(section.id) }" />
                    </button>

                    <transition name="group-slide">
                        <transition-group
                            v-if="isSectionOpened(section.id)"
                            name="catalog-item"
                            tag="div"
                            class="tree_catalogs">
                            <a-button
                                v-for="catalog in section.catalogs"
                                :key="catalog.id"
                                class="flex items-center justify-between"
                                :type="isActiveCatalog(catalog.model) ? 'flat_primary' : 'ui'"
                                :ghost="isActiveCatalog(catalog.model) ? false : true"
                                @click="openCatalog(catalog)">
                                <span class="tree_catalog_name">{{ catalog.name }}</span>
                                <a-badge 
                                    :count="safeCount(catalog.count)" 
                                    :number-style="isActiveCatalog(catalog.model) ? {
                                        backgroundColor: 'var(--blue)',
                                        color: '#fff',
                                        boxShadow: 'none'
                                    } : {
                                        backgroundColor: '#f0f1f6',
                                        color: '#000',
                                        boxShadow: 'none'
                                    }"
                                    :overflow-count="999" />
                            </a-button>
                        </transition-group>
                    </transition>
                </div>
            </template>
        </div>
        </aside>

        <section class="directories_content">
            <router-view />
        </section>
    </div>
</template>

<script>
import routes from './config/router'
import { errorHandler } from '@/utils/index.js'

const modelToRouteName = {
    'catalogs.ContractorModel': 'directories-team',
    'catalogs.WorkDirectionModel': 'directories-work-directions',
    'help_desk.CustomerCardModel': 'directories-clients',
    'help_desk.ContactPersonPostModel': 'directories-positions',
    'help_desk.HelpDeskTicketCategoryModel': 'directories-categories',
    'workgroups.WorkGroupModel': 'directories-groups'
}

export default {
    name: 'DirectoriesIndex',
    data() {
        return {
            routes,
            loading: false,
            search: '',
            sections: [],
            openedSections: []
        }
    },
    computed: {
        isMobile() {
            return this.$store.state.isMobile
        },
        mobileCatalogDrawerComponent() {
            if (!this.isMobile) return null
            return () => import('./components/MobileCatalogDrawer.vue')
        },
        filteredSections() {
            const query = (this.search || '').toLowerCase().trim()
            if (!query) return this.sections

            return this.sections
                .map(section => {
                    const catalogs = (section.catalogs || []).filter(catalog => {
                        return String(catalog.name || '').toLowerCase().includes(query)
                    })

                    return {
                        ...section,
                        catalogs
                    }
                })
                .filter(section => section.catalogs?.length)
        }
    },
    watch: {
        sections: {
            immediate: true,
            handler(nextSections) {
                if (!this.openedSections.length) {
                    this.openedSections = nextSections.map(item => item.id)
                }
            }
        }
    },
    methods: {
        safeCount(value) {
            const count = Number(value) || 0
            return count < 0 ? 0 : count
        },
        isSectionOpened(id) {
            return this.openedSections.includes(id)
        },
        toggleSection(id) {
            if (this.isSectionOpened(id)) {
                this.openedSections = this.openedSections.filter(item => item !== id)
                return
            }
            this.openedSections = this.openedSections.concat(id)
        },
        isActiveCatalog(model) {
            const routeName = modelToRouteName[model]
            return routeName && this.$route.name === routeName
        },
        async fetchCatalogInfo() {
            this.loading = true
            try {
                const { data } = await this.$http.get('/catalog_info/list/')
                this.sections = Array.isArray(data) ? data : []
            } catch (error) {
                errorHandler({ error, show: true })
                this.sections = []
            } finally {
                this.loading = false
            }
        },
        getDefaultRouteName() {
            for (const section of this.sections) {
                for (const catalog of (section.catalogs || [])) {
                    const routeName = modelToRouteName[catalog.model]
                    if (routeName) return routeName
                }
            }
            return 'directories-team'
        },
        ensureCurrentRoute() {
            const isKnownRoute = this.routes.some(route => route.name === this.$route.name)
            if (isKnownRoute) return

            const defaultRouteName = this.getDefaultRouteName()
            this.$router.replace({ name: defaultRouteName })
        },
        openCatalog(catalog) {
            const routeName = modelToRouteName[catalog.model]
            if (!routeName) return
            if (routeName === this.$route.name) return
            this.$router.push({ name: routeName })
        }
    },
    async created() {
        await this.fetchCatalogInfo()
        this.ensureCurrentRoute()
    }
}
</script>

<style lang="scss" scoped>
.search_input{
    &::v-deep{
        .ant-input{
            border: 0px;
            box-shadow: initial;
        }
    }
}
.directories_page{
    display: grid;
    grid-template-columns: 300px 1fr;
    height: 100%;
    min-height: 0;
}
.directories_sidebar{
    border-right: 1px solid var(--border2);
    display: flex;
    flex-direction: column;
    min-height: 0;
}
.directories_sidebar_head{
    padding: 12px;
    border-bottom: 1px solid var(--border2);
}
.directories_sidebar_title{
    display: flex;
    align-items: center;
    font-weight: 700;
    text-transform: uppercase;
    font-size: 14px;
    margin-bottom: 12px;
}
.directories_tree{
    padding: 8px 8px 16px;
    overflow: auto;
}
.tree_group{
    margin-bottom: 8px;
}
.tree_group_btn{
    width: 100%;
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 8px 10px;
    border: 0;
    border-radius: 10px;
    background: transparent;
    cursor: pointer;
    text-align: left;
}
.tree_group_name{
    font-size: 12px;
    font-weight: 700;
    text-transform: uppercase;
    opacity: .7;
}
.tree_group_icon{
    font-size: 13px;
    transition: transform .2s ease;
    &.opened{
        transform: rotate(180deg);
    }
}
.tree_catalogs{
    display: flex;
    flex-direction: column;
    gap: 4px;
    margin-top: 4px;
}
.tree_catalog_name{
    display: block;
}
.directories_content{
    min-width: 0;
    overflow: hidden;
}
.group-slide-enter-active,
.group-slide-leave-active{
    overflow: hidden;
    transition: max-height .24s ease, opacity .2s ease, transform .2s ease;
}
.group-slide-enter,
.group-slide-leave-to{
    max-height: 0;
    opacity: 0;
    transform: translateY(-6px);
}
.group-slide-enter-to,
.group-slide-leave{
    max-height: 700px;
    opacity: 1;
    transform: translateY(0);
}
.catalog-item-enter-active,
.catalog-item-leave-active{
    transition: opacity .2s ease, transform .2s ease;
}
.catalog-item-move{
    transition: transform .2s ease;
}
.catalog-item-enter,
.catalog-item-leave-to{
    opacity: 0;
    transform: translateY(-4px);
}
@media (max-width: 991px){
    .directories_page{
        grid-template-columns: 1fr;
        height: 100%;
    }
    .directories_content{
        min-height: 0;
    }
}
</style>
