<template>
    <div :ref="`sel_wrap_${name}_${filter.name}`" class="select-wrapper">
        <a-tree-select
            :ref="`select_${name}_${filter.name}`"
            v-model="selected"
            style="width: 100%"
            size="default"
            tree-data-simple-mode
            :dropdown-style="{ maxHeight: '250px', overflowY: 'auto' }"
            multiple
            :tree-data="filterData"
            dropdownClassName="filter_i_select"
            :getPopupContainer="getPopupContainer"
            :load-data="onLoadData"
            :searchValue="search"
            :placeholder="`Категории (${filterData.length})`"
            :filterTreeNode="false"
            dropdownMatchSelectWidth
            allowClear
            show-search
            :maxTagCount="windowWidth > 786 ? 3 : 10"
            @select="selectHandler"
            @deselect="deselectHandler"
            @search="searchHandler" >
            <template #suffixIcon>
                <i class="fi fi-rr-angle-down" />
            </template>
            <template slot="notFoundContent">
                <a-empty :description="$t('no_data')" />
            </template>
        </a-tree-select>
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
            loading: false,
            search: ''
        }
    },
    watch: {
        selected(val) {
            if(val?.length && !this.filterData.length && !this.loading)
                this.getDataHandler()
        }
    },
    computed: {
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
                return this.$store.state.filter.filterSelected[this.name][this.filter.name] ?
                    this.$store.state.filter.filterSelected[this.name][this.filter.name] : []
            },
            set(val) {
               
                this.$store.commit('filter/SET_SELECTED_FILTER', {
                    name: this.name,
                    filterName: this.filter.name,
                    value: val
                })
                if(val.length < 1){ 
                    this.$store.commit('filter/CLEAR_FILTER_TAG', {name: this.name, filterName: this.filter.name})
                    this.$store.commit("filter/SET_ACTIVE_FILTERS", 
                        {name: this.name, filterName: this.filter.name, value: false})
                }

                if(this.search.length)
                    this.closeSelect()
            }
        }
    },
    methods: {
        onLoadData(treeNode) {
            return new Promise((resolve, reject) => {
                const dataRef = treeNode.dataRef
                if(!dataRef.loaded) {
                    const params = {
                        model: this.filter.widget.model,
                        parent: dataRef.id,
                        ordering: ['sort', 'name']
                    }
                    this.$http.get('/app_info/select_list/', { params })
                        .then(({data}) => {
                            if (data?.selectList?.length) {
                                const index = this.filterData.findIndex(f => f.value === dataRef.id)
                                if(index !== -1)
                                    this.$set(this.filterData[index], 'loaded', true)
                                data.selectList.forEach(item => {
                                    const find = this.filterData.find(f => f.value === item.id)
                                    if(!find) {
                                        this.addFilterData({
                                            ...item,
                                            id: item.id,
                                            value: item.id,
                                            title: item.string_view,
                                            isLeaf: item.isLeaf,
                                            pId: dataRef.id,
                                            loaded: false
                                        })
                                    }
                                })
                            }
                            resolve()
                        })
                        .catch(error => {
                            errorHandler({error, show: false})
                            reject()
                        })
                }
            })
        },
        getPopupContainer() {
            return this.filterBodyRef || this.$refs[`sel_wrap_${this.name}_${this.filter.name}`]
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
        deselectHandler(value) {
            this.$store.commit('filter/SPLICE_FILTER_TAG', {value, name: this.name, filterName: this.filter.name})
        },
        selectHandler(value) {
            this.$store.commit('filter/PUSH_FILTER_TAG', {value, name: this.name, filterName: this.filter.name, toField: this.toField})
            if (!this.activeFilter)
                this.$store.commit("filter/SET_ACTIVE_FILTERS",
                    { name: this.name, filterName: this.filter.name, value: true })
        },
        addFilterData(value) {
            this.$store.commit('filter/ADD_FILTER_DATA', {value, name: this.name, filterName: this.filter.name})
        },
        closeSelect() {
            this.selectRef.$refs.vcSelect.setOpenState(false)
        },
        onSearch() {
            if(this.filter.widget.model) {
                clearTimeout(searchTimer)
                searchTimer = setTimeout(() => {
                    this.$store.commit('filter/CLEAR_FILTER_DATA', {name: this.name, filterName: this.filter.name})
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
                    this.$store.commit('filter/CLEAR_FILTER_DATA', {name: this.name, filterName: this.filter.name})
                    this.selectChange(true)
                }, 500)
            }
        },
        selectChange(open) {
            if(!open) {
                if(this.search.length) {
                    this.search = ''
                }
            }
            if(open) {
                this.getDataHandler()
            }
        },
        async getDataHandler() {
            if(this.filter.widget.model) {
                try {
                    this.loading = true

                    let query = {
                        model: this.filter.widget.model,
                        name: this.name,
                        filterName: this.filter.name,
                        search: this.search,
                        filters: this.filtersFilterData,
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

                    await this.$store.dispatch('filter/getTreeFilterSelectData', query)
                } catch(error) {
                    errorHandler({error, show: false})
                } finally {
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
        await this.getDataHandler()
    }
}
</script>

<style lang="scss" scoped>
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