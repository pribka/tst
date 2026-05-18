<template>
    <div>
        <div 
            v-if="!vertical" 
            class="filter_pop_wrapper relative"
            :class="tags.length || filtersSearch.length ? 'filter_active' : ''">
            <a-button
                v-if="tags.length || filtersSearch.length"
                @click="removeFilters()"
                type="link"
                class="text_current absolute filter_clear ant-btn-icon-only">
                <i class="fi fi-rr-cross-small"></i>
            </a-button>
            <a-popover
                v-model="visible"
                :trigger="onlySearch ? 'none' : 'click'"
                :autoAdjustOverflow="autoAdjustOverflow"
                :transitionName="transitionName"
                :align="align"
                destroyTooltipOnHide
                :getPopupContainer="getPopupContainer"
                :overlayStyle="{
                    width: '100%',
                    maxWidth: filterPopupWidth,
                    zIndex: zIndex,
                }"
                :placement="placement"
                overlayClassName="filter_popover"
                :class="size"
                @visibleChange="visibleChange">
                <div 
                    v-if="mode === 'tag'" 
                    class="filter_input cursor-pointer relative flex items-center"
                    :class="showSearchInput && 'search_input'">
                    <template v-if="tags.length">
                        <a-tag
                            v-for="(filter, index) in tagsViewFilter"
                            :key="filterItemKey(filter, index)"
                            :color="checkTagColor(filter)"
                            :title="tagTitle(filter)"
                            class="cursor-pointer">
                            <div class="flex items-center filter_tag">
                                <template v-if="filter.type === 'other'">
                                    +{{filter.value.length}}
                                </template>
                                <template v-else>
                                    <span class="mr-1">{{filter.verbose_name}}:</span>
                                    <template v-if="filter.field === 'date' || filter.field === 'input'">
                                        <div class="value_name">{{filter.value}}</div>
                                    </template>
                                    <template v-else>
                                        <div 
                                            v-if="filter.value[0].full_name"
                                            class="flex items-center">
                                            <div class="mr-1">
                                                <a-avatar 
                                                    v-if="filter.value[0].avatar" 
                                                    :size="14" 
                                                    :src="filter.value[0].avatar.path" />
                                                <a-avatar 
                                                    v-else 
                                                    :size="14" 
                                                    icon="user" />
                                            </div>
                                            <div class="value_name">{{filter.value[0].full_name}}</div>
                                        </div>
                                        <span 
                                            v-else 
                                            class="truncate"
                                            style="max-width: 160px;">
                                            {{filter.value[0].string_view ? filter.value[0].string_view : filter.value[0].name}}
                                        </span>
                                        <span 
                                            v-if="filter.value.length > 1"
                                            class="ml-1">
                                            +{{filter.value.length-1}}
                                        </span>
                                    </template>
                                </template>
                            </div>
                        </a-tag>
                    </template>
                    <template v-else>
                        <template v-if="!showSearchInput" >
                            <div 
                                v-if="!filterLoading"
                                class="flex items-center">
                                <span class="text-gray font-extralight">
                                    {{$t('select_filter')}}
                                </span>
                            </div>
                        </template>
                    </template>
                    <template v-if="showSearchInput" >
                        <div 
                            v-if="tags.length && filtersSearch && filtersSearch.length" 
                            class="search_sp">
                            +
                        </div>
                        <div class="main_search w-full">
                            <a-input
                                :value="filtersSearch"
                                class="w-full"
                                ref="mainSearchInput"
                                :placeholder="inputPlaceholder"
                                @keydown="keydownSearchInput"
                                @change="changeSearchInput">
                                <template slot="suffix">
                                    <a-icon v-if="searchLoading" type="loading" />
                                    <i v-else class="fi fi-rr-search"></i>
                                </template>
                            </a-input>
                        </div>
                    </template>
                    <a-icon 
                        v-if="filterLoading" 
                        class="absolute" 
                        type="loading" />
                </div> 
                <a-button
                    v-else
                    icon="filter"
                    :type="buttonType"
                    :size="size"
                    :loading="filterLoading">
                    {{$t('filters')}}
                </a-button>
                <div slot="content">
                    <div 
                        v-show="filterLoading" 
                        class="flex justify-center p-2">
                        <a-spin />
                    </div>
                    <div v-show="!filterLoading">
                        <div class="filter_header flex items-center justify-between pb-2">
                            <div class="flex items-center">
                                <span class="font-semibold" style="color: #000;">{{$t('filter')}}</span>
                                <div class="ml-8 flex items-center" v-if="checkExclude">
                                    <Segmented 
                                        v-model="activeTab" 
                                        bgInvert
                                        class="filter_segmented"
                                        block
                                        :options="listType" />
                                </div>
                            </div>
                            <a-button type="ui" ghost icon="fi-rr-cross-small" size="small" shape="circle" flaticon @click="visible = false" />
                        </div>
                        <div class="filter_body py-4 pr-2" ref="filterBody">
                            <template v-if="filterBodyRef">
                                <div v-show="activeTab === 1">
                                    <div class="grid" :class="listColumn">
                                        <div v-for="f in includeMain" :key="f.name" class="min-width-zero">
                                            <WidgetsSwicth
                                                :filter="f"
                                                :page_name="page_name"
                                                :filterBodyRef="filterBodyRef"
                                                :injectSelectParams="injectSelectParams"
                                                :filterPrefix="filterPrefix"
                                                :modelLabel="modelLabel"
                                                :windowWidth="windowWidth"
                                                :name="name" />
                                        </div>
                                    </div>
                                    <a-button
                                        v-if="hasIncludeAdditional"
                                        type="link"
                                        class="mt-2 flex items-center more_filters_btn"
                                        flaticon
                                        block
                                        :class="showIncludeAdditional && 'active_btn'"
                                        size="small"
                                        icon="fi-rr-angle-small-right"
                                        @click="showIncludeAdditional = !showIncludeAdditional">
                                        {{ $t('more_filters') }}
                                    </a-button>
                                    <transition name="slide-fade">
                                        <div v-if="showIncludeAdditional" class="grid mt-2" :class="listColumn">
                                            <div v-for="f in includeAdditional" :key="f.name" class="min-width-zero">
                                                <WidgetsSwicth
                                                    :filter="f"
                                                    :page_name="page_name"
                                                    :filterBodyRef="filterBodyRef"
                                                    :injectSelectParams="injectSelectParams"
                                                    :filterPrefix="filterPrefix"
                                                    :modelLabel="modelLabel"
                                                    :windowWidth="windowWidth"
                                                    :name="name" />
                                            </div>
                                        </div>
                                    </transition>
                                </div>
                                <div v-show="activeTab === 2">
                                    <div class="grid" :class="listColumn">
                                        <div v-for="f in excludeMain" :key="f.name" class="min-width-zero">
                                            <WidgetsSwicth
                                                :filter="f"
                                                :page_name="page_name"
                                                :filterBodyRef="filterBodyRef"
                                                :filterPrefix="filterPrefix"
                                                :injectSelectParams="injectSelectParams"
                                                :modelLabel="modelLabel"
                                                :windowWidth="windowWidth"
                                                :name="name" />
                                        </div>
                                    </div>
                                    <a-button
                                        v-if="hasExcludeAdditional"
                                        type="link"
                                        class="mt-2 flex items-center more_filters_btn"
                                        flaticon
                                        block
                                        :class="showExcludeAdditional && 'active_btn'"
                                        size="small"
                                        icon="fi-rr-angle-small-right"
                                        @click="showExcludeAdditional = !showExcludeAdditional">
                                        {{ $t('more_filters') }}
                                    </a-button>
                                    <transition name="slide-fade">
                                        <div v-if="showExcludeAdditional" class="grid mt-2" :class="listColumn">
                                            <div v-for="f in excludeAdditional" :key="f.name" class="min-width-zero">
                                                <WidgetsSwicth
                                                    :filter="f"
                                                    :page_name="page_name"
                                                    :filterBodyRef="filterBodyRef"
                                                    :filterPrefix="filterPrefix"
                                                    :injectSelectParams="injectSelectParams"
                                                    :modelLabel="modelLabel"
                                                    :windowWidth="windowWidth"
                                                    :name="name" />
                                            </div>
                                        </div>
                                    </transition>
                                </div>
                            </template>
                        </div>
                        <div class="filter_footer flex items-center justify-end pt-2">
                            <!--<a-button type="ui" @click="resetFilters()">
                                {{$t('reset')}}
                            </a-button>-->
                            <a-button 
                                class="ml-2"
                                type="ui"
                                @click="removeFilters()">
                                {{$t('reset')}}
                            </a-button>
                            <a-button
                                icon="search"
                                type="primary"
                                class="ml-2 px-8"
                                @click="setFilter()">
                                {{$t('find')}}
                            </a-button>
                        </div>
                    </div>
                </div>
            </a-popover>
        </div>
        <!--/////////////////////////////////////// VERTICAL /////////////////////////////////////// -->
        <div v-else>
            <a-card>
                <div v-show="filterLoading" class="flex justify-center p-2">
                    <a-spin />
                </div>
                <div v-show="!filterLoading">
                    <span class="font-semibold text-base">{{$t('filters')}}</span>
                    <div class="filter_header flex items-center justify-between pb-3 mt-2">
                        <div class="flex items-center">
                            <div class=" flex items-center" v-if="checkExclude">
                                <Segmented 
                                    v-model="activeTab" 
                                    bgInvert
                                    class="filter_segmented"
                                    block
                                    :options="listType" />
                            </div>
                        </div>
                    
                    </div>
                    <div class="filter_body filter_body__vertical py-1 pr-2" ref="filterBody">
                        <template v-if="filterBodyRef">
                            <div v-show="activeTab === 1">
                                <div class="grid" :class="listColumn">
                                    <div v-for="f in includeMain" :key="f.name" class="min-width-zero">
                                        <WidgetsSwicth
                                            :filter="f"
                                            :page_name="page_name"
                                            :filterBodyRef="filterBodyRef"
                                            :injectSelectParams="injectSelectParams"
                                            :filterPrefix="filterPrefix"
                                            :modelLabel="modelLabel"
                                            :windowWidth="windowWidth"
                                            :name="name" />
                                    </div>
                                </div>
                                <a-button
                                    v-if="hasIncludeAdditional"
                                    type="link"
                                    class="mt-2 flex items-center more_filters_btn"
                                    flaticon
                                    block
                                    :class="showIncludeAdditional && 'active_btn'"
                                    size="small"
                                    icon="fi-rr-angle-small-right"
                                    @click="showIncludeAdditional = !showIncludeAdditional">
                                    {{ $t('more_filters') }}
                                </a-button>
                                <transition name="slide-fade">
                                    <div v-if="showIncludeAdditional" class="grid mt-2" :class="listColumn">
                                        <div v-for="f in includeAdditional" :key="f.name" class="min-width-zero">
                                            <WidgetsSwicth
                                                :filter="f"
                                                :page_name="page_name"
                                                :filterBodyRef="filterBodyRef"
                                                :injectSelectParams="injectSelectParams"
                                                :filterPrefix="filterPrefix"
                                                :modelLabel="modelLabel"
                                                :windowWidth="windowWidth"
                                                :name="name" />
                                        </div>
                                    </div>
                                </transition>
                            </div>
                            <div v-show="activeTab === 2">
                                <div class="grid" :class="listColumn">
                                    <div v-for="f in excludeMain" :key="f.name" class="min-width-zero">
                                        <WidgetsSwicth
                                            :filter="f"
                                            :page_name="page_name"
                                            :filterBodyRef="filterBodyRef"
                                            :filterPrefix="filterPrefix"
                                            :injectSelectParams="injectSelectParams"
                                            :modelLabel="modelLabel"
                                            :windowWidth="windowWidth"
                                            :name="name" />
                                    </div>
                                </div>
                                <a-button
                                    v-if="hasExcludeAdditional"
                                    type="link"
                                    class="mt-2 flex items-center more_filters_btn"
                                    flaticon
                                    block
                                    :class="showExcludeAdditional && 'active_btn'"
                                    size="small"
                                    icon="fi-rr-angle-small-right"
                                    @click="showExcludeAdditional = !showExcludeAdditional">
                                    {{ $t('more_filters') }}
                                </a-button>
                                <transition name="slide-fade">
                                    <div v-if="showExcludeAdditional" class="grid mt-2" :class="listColumn">
                                        <div v-for="f in excludeAdditional" :key="f.name" class="min-width-zero">
                                            <WidgetsSwicth
                                                :filter="f"
                                                :page_name="page_name"
                                                :filterBodyRef="filterBodyRef"
                                                :filterPrefix="filterPrefix"
                                                :injectSelectParams="injectSelectParams"
                                                :modelLabel="modelLabel"
                                                :windowWidth="windowWidth"
                                                :name="name" />
                                        </div>
                                    </div>
                                </transition>
                            </div>
                        </template>
                    </div>
                    <div class="filter_footer flex flex-col items-center justify-end pt-4">
                        <a-button
                            icon="search"
                            type="primary"
                            class="w-full"
                            @click="setFilter()">
                            {{$t('find')}}
                        </a-button>
                        <div class="flex justify-between items-center w-full mt-2">
                            <a-button 
                                v-if="!hideResetBtn"
                                class="w-full"
                                @click="resetFilters()">
                                <a-icon type="redo" />  {{$t('reset')}}
                            </a-button>
                            <a-button 
                                v-if="!hideClearBtn"
                                :class="!hideResetBtn && 'ml-2'"
                                :disabled="disabledClearBtn"
                                class="w-full flex items-center justify-center"
                                @click="clearFilters()">
                                <i class="fi fi-rr-trash mr-1"></i>  {{$t('clear')}} 
                            </a-button>
                        </div>
                    </div>
                </div>
            </a-card>
        </div>
    </div>
</template>

<script>
import { mapActions } from 'vuex'
import eventBus from '@/utils/eventBus'
import computedM from './mixins/computed'
import methodsM from './mixins/methods'
import propsM from './mixins/props'
export default {
    components: {
        WidgetsSwicth: () => import('./widgets/WidgetsSwicth'),
        Segmented: () => import('@apps/UIModules/Segmented')
    },
    mixins: [
        methodsM,
        computedM,
        propsM
    ],
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
        }
    },
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
            filterBodyRef: null,
            showIncludeAdditional: false,
            showExcludeAdditional: false
        }
    },
    created() {
        this.filterInit()
    },
    methods: {
        ...mapActions({
            getFiltersByKey: "filter/getFiltersByKey"
        }),
        async visibleChange(vis) {
            if(vis) {
                await this.awaitFilterBody()
            } else {
                this.filterBodyRef = null
            }
        },
        async awaitFilterBody() {
            for (let i = 0; i < 15; i++) {
                await this.$nextTick()
                if (this.$refs.filterBody) {
                    this.filterBodyRef = this.$refs.filterBody
                    return
                }
                await new Promise(r => setTimeout(r, 16))
            }
            this.filterBodyRef = null
        },
        searchFocus() {
            this.$nextTick(() => {
                if(this.$refs.mainSearchInput)
                    this.$refs.mainSearchInput.focus()
            })
        },
        tagTitle(filter) {
            if (filter.type === 'other') return ''
            const label = filter.verbose_name ? `${filter.verbose_name}: ` : ''
            if (filter.field === 'date' || filter.field === 'input') return `${label}${filter.value}`
            const first = filter.value && filter.value[0] ? filter.value[0] : null
            if (!first) return label
            const firstText = first.full_name ? first.full_name : first.string_view ? first.string_view : first.name
            const extra = filter.value.length > 1 ? ` +${filter.value.length - 1}` : ''
            return `${label}${firstText}${extra}`
        },
        checkTagColor(filter) {
            if(filter.name)
                return filter.name.includes("_exclude") ? 'purple' : 'blue'
            
            return ''
        },
        filterItemKey(filter, index) {
            switch (filter.field) {
            case 'array':
                return filter.value?.[0]?.id ? filter.value?.[0]?.code ? `${filter.value[0].code}_${filter.name}` : `${filter.value[0].id}_${filter.name}` : `${filter.name}_${filter.field}`
                break;
            default:
                return index
            }
        },
        async filterInit() {
            try {
                this.filterLoading = true
                this.$store.commit('filter/SET_FILTER_LOADING', {
                    name: this.page_name,
                    value: true
                })
                this.name = this.page_name
                if(!this.checkLoaded || this.forceInit){ 
                    await this.getFiltersByKey(
                        {
                            name: this.model,
                            page_name: this.page_name,
                            params:  this.queryParams,
                            excludeFields: this.excludeFields
                        })
                } else {
                    eventBus.$emit(`filter_active_${this.page_name}`, this.activeFilters)
                }
                this.setFilterData()
                await this.tagGenerate()
                if(this.initInputFocus) {
                    this.searchFocus()
                }
            } catch(e) {
                console.log(e)
            } finally {
                this.$store.commit('filter/SET_FILTER_LOADING', {
                    name: this.page_name,
                    value: false
                })
                this.filterLoading = false
            }
        }
    },
    mounted() {
        eventBus.$on(`send_include_fields_${this.page_name}`, data => {
            this.filterIncludeData = data
            this.setFilter()
        })
        eventBus.$on(`set_include_data_${this.page_name}`, data => {
            this.filterIncludeData = data
        })
    },
    beforeDestroy() {
        eventBus.$off(`send_include_fields_${this.page_name}`)
        eventBus.$off(`set_include_data_${this.page_name}`)
    }
}
</script>

<style lang="scss">
.filter_popover{
    .ant-popover-arrow{
        display: none;
    }
    &.ant-popover-placement-bottom, &.ant-popover-placement-bottomLeft, &.ant-popover-placement-bottomRight{
        padding-top: 0px;
    }
    .ant-popover-inner{
        box-shadow: 0 0 0 1px #e6e6e8;
    }
}
.filter_body{
    overflow-y: auto;
    max-height: 60vh;
    overscroll-behavior: contain;
    .min-width-zero{
        min-width: 0;
    }
    
}
.filter_body__vertical{
        max-height: 60vh !important;
 }
.filters_drawer{
    .ant-drawer-header{
        padding: 15px;
    }
    .ant-drawer-body{
        padding: 0px;
        height: calc(100% - 53px);
    }
    .ant-drawer-content,
    .ant-drawer-wrapper-body{
        overflow: hidden;
    }
    .body_wrapper{
        overflow: auto;
        padding: 15px;
        height: calc(100% - 55px);
    }
    .footer_wrapper{
        border-top: 1px solid var(--borderColor);
        background: var(--bgColor);
        position: relative;
        z-index: 5;
        padding: 15px;
        height: 55px;
    }
}
.filter_tag{
    .value_name{
        max-width: 110px;
        text-overflow: ellipsis;
        white-space: nowrap;
        overflow: hidden;
    }
}
.ant-popover{
    .filter_header{
        border-bottom: 1px solid var(--borderColor);
    }
}
.filter_item{
    &:not(:last-child){
        margin-bottom: 15px;
    }
}
.filter_pop_wrapper{
    .filter_clear{
        top: 1px;
        right: 1px;
        z-index: 5;
        height: 31px;
        background: #fff;
        max-width: 33px;
        min-width: 33px;
    }
}
.filter_input{
    .filter_tag,
    .ant-tag{
        height: 100%;
    }
    .anticon-loading{
        color: var(--loadingColor);
    }
    .search_sp{
        font-weight: 400;
        margin-right: 4px;
        color: #000;
    }
    .main_search{
        .ant-input-affix-wrapper{
            .ant-input{
                padding-right: 20px;
            }
        }
        input{
            border: 0px;
            padding-left: 0px;
            color: #000;
            &::placeholder{
                font-weight: 400;
                font-size: 15px;
                color: #000;
            }
            &:hover,
            &:focus{
                outline: none;
                box-shadow: initial;
                border-color: initial;
            }
        }
        .ant-input-suffix{
            right: 3px;
            opacity: 0.6;
            margin-top: 1px;
            i{
                display: flex;
                align-items: center;
            }
        }
    }
}
.filter_drawer{
    .ant-drawer-wrapper-body{
        overflow: hidden;
    }
    .ant-drawer-body{
        padding: 0px;
        height: calc(100% - 55px);
    }
    .drawer_body{
        &.hide_search{
            height: calc(100% - 50px);
        }
        &:not(.hide_search) {
            height: calc(100% - 92px);
        }
        .drawer_scroll{
            height: 100%;
            overflow-y: auto;
            overflow-x: hidden;
        }
    }
    .drawer_header{
        border-bottom: 1px solid var(--borderColor);
        .ant-input{
            border-radius: 0px;
            height: 42px;
            border: 0px;
            padding-right: 30px;
        }
    }
    .drawer_footer{
        border-top: 1px solid var(--borderColor);
        height: 50px;
        background: var(--bgColor);
        padding: 4px 11px;
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
.filter_segmented{
    &::v-deep{
        .segmented{
            padding: 4px;
            &__item{
                height: 22px;
                white-space: nowrap;
            }
        }
    }
}
.more_filters_btn{
    background: #F8F9FD;
    justify-content: flex-start;
    height: 34px;
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
.filter_pop_wrapper{
    max-width: 1200px;
    min-width: 300px;
    width: 100%;
}
.filter_active{
    .filter_input{
        padding-right: 31px;
    }
}
.filter_input{
    padding: 6px 10px 6px 11px;
    font-size: 16px;
    color: var(--textColor);
    line-height: 1.5;
    background-color: var(--bgColor);
    background-image: none;
    border: 1px solid var(--borderColor);
    border-radius: var(--borderRadius);
    height: 32px;
    display: flex;
    flex-wrap: nowrap;
    overflow: hidden;
    &::v-deep{
        .ant-tag{
            flex-shrink: 0;
            max-width: 100%;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }
    }
    &.large{
        height: 38px;
    }
    &.small{
        height: 24px;
    }
    .search_input{
        outline: none;
        height: 100%;
        width: 100%;
        padding-left: 8px;
    }
}
</style>