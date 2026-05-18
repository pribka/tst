<template>
    <div>
        <div 
            v-show="filterLoading" 
            class="flex justify-center p-2">
            <a-spin />
        </div>
        <div v-show="!filterLoading">
            <div class="f_header flex items-center justify-between pb-1">
                <div class="flex items-center">
                    <div class="flex items-center" v-if="checkExclude">
                        <Segmented 
                            v-model="activeTab" 
                            bgInvert
                            class="filter_segmented"
                            block
                            :options="listType" />
                    </div>
                </div>
            </div>
            <div class="f_body py-4 pr-2">
                <div v-show="activeTab === 1">
                    <div class="grid grid-cols-2 gap-3">
                        <div v-for="f in includeMain" :key="f.name" class="min-width-zero">
                            <WidgetsSwicth
                                :filter="f"
                                :page_name="page_name"
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
                        <div v-if="showIncludeAdditional" class="grid grid-cols-2 gap-3 mt-2">
                            <div v-for="f in includeAdditional" :key="f.name" class="min-width-zero">
                                <WidgetsSwicth
                                    :filter="f"
                                    :page_name="page_name"
                                    :windowWidth="windowWidth"
                                    :name="name" />
                            </div>
                        </div>
                    </transition>
                </div>
                <div v-show="activeTab === 2">
                    <div class="grid grid-cols-2 gap-3">
                        <div v-for="f in excludeMain" :key="f.name" class="min-width-zero">
                            <WidgetsSwicth
                                :filter="f"
                                :page_name="page_name"
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
                        <div v-if="showExcludeAdditional" class="grid grid-cols-2 gap-3 mt-2">
                            <div v-for="f in excludeAdditional" :key="f.name" class="min-width-zero">
                                <WidgetsSwicth
                                    :filter="f"
                                    :page_name="page_name"
                                    :windowWidth="windowWidth"
                                    :name="name" />
                            </div>
                        </div>
                    </transition>
                </div>
            </div>
            <div class="filter_footer flex items-center justify-end pt-2">
                <!--<a-button type="ui" @click="resetFilters()">
                    {{$t('reset')}}
                </a-button>
                <a-button 
                    class="ml-2"
                    type="ui"
                    @click="removeFilters()">
                    {{$t('reset')}}
                </a-button>-->
            </div>
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

<style lang="scss" scoped>
.filter_segmented{
    &::v-deep{
        .segmented{
            &__item{
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
</style>

<style lang="scss">
.filter_item{
    &:not(:last-child){
        margin-bottom: 15px;
    }
}
</style>