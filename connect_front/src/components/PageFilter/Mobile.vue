<template>
    <div>
        <a-badge :count="tagCount">
            <a-button
                class="filter-icon"
                :size="filterButtonSize"
                @click="openFilter">
                <i class="fi fi-rr-filter" />
            </a-button>
        </a-badge>
        <DrawerTemplate
            title=""
            v-model="visible"
            wrapClassName="mobile_filter_drawer"
            @afterVisibleChange="afterVisibleChange"
            :destroyOnClose="true"
            @close="visible = false">
            <template #title>
                <a-button class="px-0" type="link" @click="clearFilters()">
                    {{$t('clear')}}
                </a-button>
            </template>
            <div v-show="filterLoading" class="flex justify-center p-2">
                <a-spin />
            </div>
            <div v-show="!filterLoading" class="filter_drawer_content">
                <template v-if="showSearchInput" >
                    <div class="main_search w-full mb-2">
                        <a-input
                            :value="filtersSearch"
                            class="w-full"
                            placeholder="поиск"
                            @change="changeSearchInput">
                            <template slot="suffix">
                                <a-icon v-if="searchLoading" type="loading" />
                                <i v-else class="fi fi-rr-search"></i>
                            </template>
                        </a-input>
                    </div>
                </template>
                <div class="mb-3" v-if="checkExclude">
                    <Segmented 
                        v-model="activeTab" 
                        bgInvert
                        block
                        :options="listType" />
                </div>
                <div v-show="activeTab === 1">
                    <div 
                        class="widget_item"
                        v-for="f in includeMain" 
                        :key="f.name">
                        <WidgetsSwicth
                            :container="$refs.drawer"
                            :filter="f"
                            :page_name="page_name"
                            :zIndex="zIndex"
                            :filterPrefix="filterPrefix"
                            :injectSelectParams="injectSelectParams"
                            :windowWidth="windowWidth"
                            :name="name" />
                    </div>
                    <a-button
                        v-if="hasIncludeAdditional"
                        type="link"
                        class="mt-2 flex items-center more_filters_btn"
                        flaticon
                        block
                        :class="showIncludeAdditional && 'active_btn'"
                        icon="fi-rr-angle-small-right"
                        @click="showIncludeAdditional = !showIncludeAdditional">
                        {{ $t('more_filters') }}
                    </a-button>
                    <transition name="slide-fade">
                        <div v-if="showIncludeAdditional" class="mt-3">
                            <div v-for="f in includeAdditional" :key="f.name" class="widget_item">
                                <WidgetsSwicth
                                    :container="$refs.drawer"
                                    :filter="f"
                                    :page_name="page_name"
                                    :zIndex="zIndex"
                                    :filterPrefix="filterPrefix"
                                    :injectSelectParams="injectSelectParams"
                                    :windowWidth="windowWidth"
                                    :name="name" />
                            </div>
                        </div>
                    </transition>
                </div>
                <div v-show="activeTab === 2">
                    <div 
                        class="widget_item"
                        v-for="f in excludeMain" 
                        :key="f.name">
                        <WidgetsSwicth
                            :container="$refs.drawer"
                            :filter="f"
                            :page_name="page_name"
                            :filterPrefix="filterPrefix"
                            :zIndex="zIndex"
                            :injectSelectParams="injectSelectParams"
                            :windowWidth="windowWidth"
                            :name="name" />
                    </div>
                    <a-button
                        v-if="hasExcludeAdditional"
                        type="link"
                        class="mt-2 flex items-center more_filters_btn"
                        flaticon
                        block
                        :class="showExcludeAdditional && 'active_btn'"
                        icon="fi-rr-angle-small-right"
                        @click="showExcludeAdditional = !showExcludeAdditional">
                        {{ $t('more_filters') }}
                    </a-button>
                    <transition name="slide-fade">
                        <div v-if="showExcludeAdditional" class="mt-3">
                            <div v-for="f in excludeAdditional" :key="f.name" class="widget_item">
                                <WidgetsSwicth
                                    :container="$refs.drawer"
                                    :filter="f"
                                    :page_name="page_name"
                                    :filterPrefix="filterPrefix"
                                    :zIndex="zIndex"
                                    :injectSelectParams="injectSelectParams"
                                    :windowWidth="windowWidth"
                                    :name="name" />
                            </div>
                        </div>
                    </transition>
                </div>
            </div>
            <template #footer>
                <a-button
                    icon="search"
                    type="primary"
                    size="large"
                    block
                    @click="setFilter()">
                    {{$t('find')}}
                </a-button>
            </template>
        </DrawerTemplate>
    </div>
</template>

<script>
import { mapActions } from 'vuex'
import computedM from './mixins/computed'
import methodsM from './mixins/methods'
import propsM from './mixins/props'
import eventBus from '@/utils/eventBus'
export default {
    props: {
        filterButtonSize: {
            type: String,
            default: 'large'
        }
    },
    components: {
        WidgetsSwicth: () => import('./widgets/WidgetsSwicth'),
        DrawerTemplate: () => import("@/components/DrawerTemplate.vue"),
        Segmented: () => import('@apps/UIModules/Segmented')
    },
    mixins: [
        methodsM,
        computedM,
        propsM
    ],
    data() {
        return {
            visible: false,
            filterLoading: false,
            tags: [],
            first: true,
            input: '',
            name: this.model,
            activeTab: 1,
            filterInclude: [],
            filterExclude: [],
            searchLoading: false,
            filterIncludeData: null,
            showIncludeAdditional: false,
            showExcludeAdditional: false
        }
    },
    computed: {
        listType() {
            return [
                {
                    key: 1,
                    title: `${this.$t('select')} ${this.includeLenght > 0 ? `(${this.includeLenght})` : ''}`
                },
                {
                    key: 2,
                    title: `${this.$t('exclude')} ${this.excludeLenght > 0 ? `(${this.excludeLenght})` : ''}`
                }
            ]
        },
        tagCount() {
            if(this.filtersSearch?.length) {
                return this.tags.length + 1
            } else 
                return this.tags.length
        }
    },
    methods: {
        ...mapActions({
            getFiltersByKey: "filter/getFiltersByKey"
        }),
        searchFocus() {
            
        },
        openFilter() {
            this.openDrawer() 
        },
        openDrawer() {
            this.visible = true
        },
        close() {
            // const query = Object.assign({}, this.$route.query)
            // if(query.filter)
            //     delete query.filter
            
            // this.$router.push({query})
        },
        afterVisibleChange(visible) {
            if(!visible)
                this.close()
        },
    },
    async created(){
        this.filterLoading = true
        this.name = this.page_name

        if(!this.checkLoaded){ 
            await this.getFiltersByKey(
                {
                    name: this.model,
                    page_name: this.page_name,
                    params:  this.queryParams,
                    excludeFields: this.excludeFields
                })
        } 
        this.setFilterData()
        await this.tagGenerate()
        this.filterLoading = false
    },
    mounted() {
        eventBus.$on(`include_fields_${this.page_name}`, data => {
            this.filterIncludeData = data
            this.setFilter()
        })
        eventBus.$on(`send_include_fields_${this.page_name}`, data => {
            this.filterIncludeData = data
            this.setFilter()
        })
        eventBus.$on(`set_include_data_${this.page_name}`, data => {
            this.filterIncludeData = data
        })
    },
    beforeDestroy() {
        eventBus.$off(`include_fields_${this.page_name}`)
        eventBus.$off(`send_include_fields_${this.page_name}`)
        eventBus.$off(`set_include_data_${this.page_name}`)
    }

}
</script>

<style lang="scss">
.mobile_filter_drawer{
    .ant-drawer-content{
        .ant-drawer-wrapper-body{
            .ant-drawer-body{
                .drawer_body{
                    &.padding{
                        padding-top: 0px;
                    }
                }
            }
        }
    }
}
</style>

<style scoped lang="scss">
.slide-fade-enter-active {
  transition: all .3s ease;
}
.slide-fade-leave-active {
  transition: all .3s cubic-bezier(1.0, 0.5, 0.8, 1.0);
}
.slide-fade-enter, .slide-fade-leave-to{
  transform: translateY(10px);
  opacity: 0;
}
.more_filters_btn{
    background: #F8F9FD;
    opacity: 0.8;
    color: var(--text1);
    &:hover{
        opacity: 1;
    }
    &.active_btn{
        opacity: 1;
        &::v-deep{
            .flaticon{
                transform: rotate(90deg);
            }
        }
    }
}
.filter-icon {
    display: flex;
    align-items: center;
}
.widget_item {
    &:not(:last-child) {
        margin-bottom: 0.75rem;
    }
}
</style>