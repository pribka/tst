<template>
    <div :ref="`sel_wrap_${name}_${filter.name}`" class="select-wrapper">
        <a-select
            :ref="`select_${name}_${filter.name}`"
            mode="multiple"
            :allowClear="true"
            class="w-full"
            :showSearch="windowWidth > 786 ? true : false"
            :maxTagCount="windowWidth > 786 ? 3 : 10"
            size="default"
            :placeholder="$t('f_select_p')"
            :loading="loading"
            v-model="selected"
            scrollClose
            dropdownClassName="filter_i_select"
            :default-active-first-option="false"
            :filter-option="false"
            :getPopupContainer="getPopupContainer"
            @focus="focus"
            @select="selectHandler"
            @deselect="deselectHandler"
            @search="searchHandler"
            @popupScroll="getDataScrollHandler"
            @dropdownVisibleChange="selectChange">
            <a-select-option
                v-for="option in filterData"
                :key="option.id"
                :value="option[toField]">
                <div class="flex items-center">
                    <div v-if="hasLogoKey(option)" class="mr-2">
                        <a-avatar :size="14" v-if="option.logo" :src="option.logo" />
                        <a-avatar :size="14" v-else icon="team" />
                    </div>
                    <div>
                        {{option.string_view ? option.string_view :  option.name}}
                    </div>
                </div>

            </a-select-option>
            <div slot="notFoundContent" class="flex justify-center p-1">
                <a-empty v-if="windowWidth > 786" :description="$t('no_data')" />
            </div>
            <div v-if="windowWidth > 786" slot="dropdownRender" slot-scope="menu">
                <div v-if="loading" slot="notFoundContent" class="flex justify-center p-2">
                    <a-spin size="small" />
                </div>
                <v-nodes v-if="!loading" :vnodes="menu" />
                <a-divider class="m-0" />
                <div class="p-2">
                    <a-spin :spinning="scrollLoading" size="small">
                        <div class="flex justify-end w-full">
                            <a-button @click="closeSelect()" type="ui_ghost" ghost block size="small">
                                {{$t('close')}}
                            </a-button>
                        </div>
                    </a-spin>
                </div>
            </div>
        </a-select>
        <DrawerTemplate
            v-if="windowWidth < 786"
            :width="windowWidth"
            class="filter_drawer"
            :title="filter.verbose_name"
            v-model="visible"
            @close="drawerClose()">
            <a-input-search
                v-if="filter.widget.model"
                @input="onSearch"
                v-model="search"
                size="large"
                class="mb-2 search_input"
                :loading="loading"
                :placeholder="$t('find')" />
            <ul class="bordered-items" v-if="!loading">
                <li class="cursor-pointer item py-3" @click="selectItem(item)" v-for="item in filterData" :key="item.id">
                    <div class="flex items-center justify-between">
                        <div class="flex items-center">
                            <div v-if="hasLogoKey(item)" class="mr-2">
                                <a-avatar v-if="item.logo" :src="item.logo" />
                                <a-avatar v-else icon="team" />
                            </div>
                            <div>{{item.string_view ? item.string_view :  item.name}}</div>
                        </div>
                        <div>
                            <a-radio :checked="checkSelected(item)" />
                        </div>
                    </div>
                </li>
            </ul>
            
            <infinite-loading v-if="filterData.length" @infinite="getDataScrollDrawerHandler" v-bind:distance="10">
                <div slot="spinner"><a-spin v-if="page !== 1" /></div>
                <div slot="no-more"></div>
                <div slot="no-results"></div>
            </infinite-loading>
            <template #footer>
                <a-button
                    block
                    type="ui_ghost"
                    size="large"
                    @click="drawerClose()">
                    {{$t('close')}}
                </a-button>
            </template>
        </DrawerTemplate>
    </div>
</template>

<script>
import filtersCheckbox from '../mixins/filtersCheckbox'
import { errorHandler } from '@/utils/index.js'
let searchTimer;
export default {
    props: {
        filter: {
            type: Object,
            required: true
        },
        name: {
            type: String,
            required: true
        },
        windowWidth: {
            type: Number,
            default: 0
        },
        page_name: {
            type: [String, Number],
            default: ''
        },
        filterPrefix: {
            type: String,
            default: ''
        },
        modelLabel: {
            type: String,
            default: ''
        },
        injectSelectParams: {
            type: Object,
            default: () => {}
        },
        filterBodyRef: { type: [HTMLElement, Object], default: null }
    },
    mixins: [filtersCheckbox],
    data() {
        return {
            page_size: this.windowWidth > 786 ? 10 : 15,
            loading: false,
            scrollLoading: false,
            page: 1,
            next: null,
            search: '',
            update: true,
            visible: false
        }
    },
    watch: {
        visible(val) {
            if(!val && this.search.length) {
                this.page = 1
                this.next = null
                this.$store.commit('filter/CLEAR_FILTER_DATA', {name: this.name, filterName: this.filter.name})
                this.$store.commit("filter/SET_ACTIVE_FILTERS", 
                    {name: this.name, filterName: this.filter.name, value: false})
                this.update = true
                this.search = ''
            }
        },
        selected(val) {
            if(val?.length && !this.filterData.length && !this.loading)
                this.getDataHandler()
        }
    },
    computed: {
        scrollNum() {
            if(this.page_size >= 10) {
                return 100
            }
            return 50
        },
        filterData() {
            return  this.$store.state.filter.filterData[this.name][this.filter.name]
        },
        selectRef() {
            return this.$refs[`select_${this.name}_${this.filter.name}`]
        },
        toField(){
            return this.filter.widget.toField
        },
        filtersFilterData(){
            let filters = this.filter.widget.filters
            let result = {}
            if(filters && filters.length > 0){
                filters.forEach(el=>{
                    if(el.type === 'defined')
                        result[el.name] = el.value
                })
            }
            return result
        },
        selected: {
            get() {
                return this.$store.state.filter.filterSelected[this.name][this.filter.name] || []
            },
            set(val) {
                const normalized = Array.isArray(val) ? val.map(v => String(v)) : []
                this.$store.commit('filter/SET_SELECTED_FILTER', {
                    name: this.name,
                    filterName: this.filter.name,
                    value: normalized
                })
                if(normalized.length < 1){
                    this.$store.commit('filter/CLEAR_FILTER_TAG', {name: this.name, filterName: this.filter.name})
                    this.$store.commit('filter/SET_ACTIVE_FILTERS', {name: this.name, filterName: this.filter.name, value: false})
                }
                if(this.search.length) this.closeSelect()
            }
        }
    },
    methods: {
        getPopupContainer() {
            return this.filterBodyRef || this.$refs[`sel_wrap_${this.name}_${this.filter.name}`]
        },
        hasLogoKey(item) {
            return item && Object.prototype.hasOwnProperty.call(item, 'logo')
        },
        selectItem(item) {
            this.$store.commit('filter/TOGGLE_FILTER_VALUE', {value: item[this.toField], name: this.name, filterName: this.filter.name})
        },
        checkSelected(item) {
            const index = this.selected.findIndex(elem => elem === item[this.toField])
            if(index !== -1)
                return true
            else
                return false
        },
        drawerClose() {
            this.visible = false
        },
        deselectHandler(value) {
            this.$store.commit('filter/SPLICE_FILTER_TAG', {value, name: this.name, filterName: this.filter.name, toField: this.toField})
        },
        selectHandler(value) {
            this.$store.commit('filter/PUSH_FILTER_TAG', {value, name: this.name, filterName: this.filter.name, toField: this.toField})
        },
        closeSelect() {
            this.selectRef.$refs.vcSelect.setOpenState(false)
        },
        onSearch() {
            if(this.filter.widget.model) {
                clearTimeout(searchTimer)
                searchTimer = setTimeout(() => {
                    this.page = 1
                    this.next = null
                    this.$store.commit('filter/CLEAR_FILTER_DATA', {name: this.name, filterName: this.filter.name})
                    this.update = true
                    this.selectChange(true)
                }, 500)
            }
        },
        searchHandler(value) {
            if(this.filter.widget.model) {
                if(!this.loading)
                    this.loading = true

                this.search = value

                clearTimeout(searchTimer)
                searchTimer = setTimeout(() => {
                    this.page = 1
                    this.next = null
                    this.$store.commit('filter/CLEAR_FILTER_DATA', {name: this.name, filterName: this.filter.name})
                    this.update = true
                    this.selectChange(true)
                }, 500)
            }
        },
        selectChange(open) {
            if(open && this.windowWidth < 786)
                this.visible = true

            if(!open) {
                if(this.search.length) {
                    this.search = ''
                    this.page = 1
                    this.next = null
                    this.update = true
                }
            }
            if(open) {
                this.getDataHandler()
            }
        },
        async getDataScrollHandler(event) { 
            if(this.next) {
                let target = event.target
                if(this.filter.widget.model && this.next && !this.loading && !this.scrollLoading && (target.scrollTop + target.offsetHeight) + this.scrollNum >= target.scrollHeight) {
                    this.page = this.page + 1

                    let query = {
                        model: this.filter.widget.model,
                        name: this.name,
                        filterName: this.filter.name,
                        filters: this.filtersFilterData,
                        page_size: this.page_size,
                        page: this.page,
                        next: this.next,
                        search: this.search,
                        page_name: this.page_name,
                        injectSelectParams: this.injectSelectParams
                    }
                    try {
                        this.scrollLoading = true

                        if(this.filterPrefix)
                            query.prefix = this.filterPrefix
                        if(this.modelLabel)
                            query.model_label = this.modelLabel

                        if(this.filter.param) {
                            query.param = this.filter.param
                        }

                        const res = await this.$store.dispatch('filter/getFilterSelectScrollData', query)
                        if(res && res.next) {
                            this.next = res.next
                        } else {
                            this.next = null
                        }
                    } catch(error) {
                        errorHandler({error, show: false})
                    } finally {
                        this.scrollLoading = false
                    }
                }
            }
        },
        async getDataScrollDrawerHandler($state = null) {
            if(this.next && this.filter.widget.model) {
                if(this.filter.widget.model && this.next && !this.loading && !this.scrollLoading) {
                    this.page = this.page + 1
                    try {
                        this.scrollLoading = true
                        let query = {
                            model: this.filter.widget.model,
                            name: this.name,
                            filterName: this.filter.name,
                            filters: this.filtersFilterData,
                            page_size: this.page_size,
                            page: this.page,
                            next: this.next,
                            search: this.search,
                            injectSelectParams: this.injectSelectParams
                        }

                        if(this.filter.param)
                            query.param = this.filter.param

                        const res = await this.$store.dispatch('filter/getFilterSelectScrollData', query)
                        if(res && res.next) {
                            if($state)
                                $state.loaded()
                            this.next = res.next
                        } else {
                            if($state)
                                $state.complete()
                            this.next = null
                        }
                    } catch(error) {
                        errorHandler({error, show: false})
                    } finally {
                        this.scrollLoading = false
                    }
                }
            }
        },
        async getDataHandler() {
            if(this.update && this.filter.widget.model) {
                try {
                    this.page = 1
                    this.loading = true

                    let query = {
                        model: this.filter.widget.model,
                        name: this.name,
                        filterName: this.filter.name,
                        filters: this.filtersFilterData,
                        page_size: this.page_size,
                        page: this.page,
                        search: this.search,
                        page_name: this.page_name,
                        injectSelectParams: this.injectSelectParams
                    }

                    if(this.filterPrefix)
                        query.prefix = this.filterPrefix
                    if(this.modelLabel)
                        query.model_label = this.modelLabel

                    if(this.filter.param) {
                        query.param = this.filter.param
                    }

                    const res = await this.$store.dispatch('filter/getFilterSelectData', query)
                    if(res && res.next) {
                        this.next = res.next
                    } else {
                        this.next = null
                    }
                } catch(error) {
                    errorHandler({error, show: false})
                } finally {
                    if(this.update)
                        this.update = false

                    this.loading = false
                }
            } else

            if( this.filter.widget.choices){
                this.$store.commit('filter/SET_CHOICES_FROM_FILTERDATA',
                    {name: this.name, filterName: this.filter.name, choices: this.filter.widget.choices})
            }
        }
    },
    async created(){
        this.loading = true
        if(this.selected.length > 0)
            await   this.getDataHandler()
        this.loading = false
    },
    components: {
        InfiniteLoading: () => import("vue-infinite-loading"),
        DrawerTemplate: () => import("@/components/DrawerTemplate.vue"),
        VNodes: {
            functional: true,
            render: (h, ctx) => ctx.props.vnodes,
        },
    },
}
</script>

<style lang="scss" scoped>
.search_input{
    &::v-deep{
        .ant-input{
            background: #f7f9fc;
            border-color: #f7f9fc;
            box-shadow: initial!important;
        }
    }
}
.select-wrapper{
    min-width: 0;
    &::v-deep{
        li.ant-select-dropdown-menu-item{
            overflow: visible;
            text-overflow: clip;
            white-space: normal;
        }
    }
}
::v-deep{
    .filter_i_select{
        .ant-select-dropdown-menu{
            @media (max-height: 650px) {
                max-height: 130px;
            }
        }
    }
}
</style>
