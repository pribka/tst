<template>
    <DrawerTemplate
        v-model="menuDrawerVisible"
        :title="$t('directories.catalog')"
        @close="closeMenuDrawer">
        <div class="directories_sidebar_head mobile">
            <a-input
                v-model="search"
                size="large"
                class="search_input_drawer"
                :placeholder="$t('directories.searchPlaceholder')">
                <template #suffix>
                    <i class="fi fi-rr-search" style="opacity: 0.6;" />
                </template>
            </a-input>
        </div>

        <div class="directories_tree mobile">
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

        <template #footer>
            <a-button type="ui" ghost block size="large" @click="closeMenuDrawer">
                {{ $t('close') }}
            </a-button>
        </template>
    </DrawerTemplate>
</template>

<script>
import eventBus from '@/utils/eventBus'
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
    name: 'DirectoriesMobileCatalogDrawer',
    components: {
        DrawerTemplate: () => import('@/components/DrawerTemplate.vue')
    },
    data() {
        return {
            menuDrawerVisible: false,
            loading: false,
            search: '',
            sections: [],
            openedSections: []
        }
    },
    computed: {
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
        '$route.name'() {
            this.closeMenuDrawer()
        },
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
        openMenuDrawer() {
            this.menuDrawerVisible = true
        },
        closeMenuDrawer() {
            this.menuDrawerVisible = false
        },
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
        openCatalog(catalog) {
            const routeName = modelToRouteName[catalog.model]
            if (!routeName) return
            this.closeMenuDrawer()
            if (routeName === this.$route.name) return
            this.$router.push({ name: routeName })
        }
    },
    async created() {
        await this.fetchCatalogInfo()
    },
    mounted() {
        eventBus.$on('directories_open_catalog_drawer', this.openMenuDrawer)
    },
    beforeDestroy() {
        eventBus.$off('directories_open_catalog_drawer', this.openMenuDrawer)
    }
}
</script>

<style lang="scss" scoped>
.search_input_drawer{
    &::v-deep{
        .ant-input{
            background: #f7f9fc;
            border-color: #f7f9fc;
            box-shadow: initial !important;
        }
    }
}
.directories_sidebar_head{
    padding: 12px;
    border-bottom: 1px solid var(--border2);
    &.mobile{
        padding-bottom: 12px;
        padding-left: 0;
        padding-right: 0;
        padding-top: 0;
        border-bottom: 0px;
    }
}
.directories_tree{
    padding: 8px 8px 16px;
    overflow: auto;
    &.mobile{
        overflow: initial;
        padding-left: 0px;
        padding-right: 0px;
    }
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
</style>
