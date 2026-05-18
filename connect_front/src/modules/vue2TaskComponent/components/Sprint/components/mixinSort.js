import { isArray } from 'lodash'
export default {
    computed: {
        filterLoading() {
            if(this.$store.state.filter.filterLoading?.[this.pageName])
                return this.$store.state.filter.filterLoading[this.pageName]
            else
                return false
        },
        activeFilters() {
            return this.$store.state.filter.filterActive[this.model]
        },
        selected() {
            return this.$store.state.filter.filterSelected[this.pageName]
        },
        search() {
            if(this.$store.state.filter.filtersSearch?.[this.pageName]?.length)
                return this.$store.state.filter.filtersSearch[this.pageName]
            else
                return ''
        },
        activeSort: {
            get() {
                if(this.$store.state.filter.filterOrdering?.[this.pageName]?.length)
                    return this.$store.state.filter.filterOrdering[this.pageName]
                else
                    return ''
            },
            set(value) {
                this.$store.commit('filter/SET_FILTERS_ORDERING', {
                    name: this.pageName,
                    value
                })
            }
        },
        active() {
            if(this.activeSort?.length) {
                const find = this.sortedItems.find(f => f.param === this.activeSort[0])
                if(find)
                    return find
                else
                    return this.sortedItems[0]
            } else
                return this.sortedItems[0]
        }
    },
    data() {
        return {
            filterInclude: [],
            filterExclude: [],
            tags: [],
        }
    },
    methods: {
        async changeSort(sort) {
            try {
                this.activeSort = sort

                let sendData = {
                    key: this.model,
                    fields: {},
                    filterTags: [],
                    ordering: this.activeSort,
                    page_name: this.pageName,
                    search: this.search
                }

                sendData['filterTags'] = {
                    structure: this.$store.state.filter.filterTags[this.pageName],
                    data: this.tags
                }

                Object.keys(this.selected).forEach(el => {

                    let findFilter = this.filterInclude.find(f => f.name === el)

                    if (findFilter === undefined) findFilter = this.filterExclude.find(f => f.name === el)


                    // Отключаем фильтры в которых нет значений
                    if (this.selected[el] === null || (isArray(this.selected[el]) && this.selected[el].length === 0)) {
                        this.$store.commit("filter/SET_ACTIVE_FILTERS", { name: this.pageName, filterName: el, value: false })
                    }


                    // Для полей с макс и мин
                    if (this.selected[el]?.start || this.selected[el]?.end) {
                        sendData.fields[el] = { values: {} }
                        sendData.fields[el].values = this.selected[el]
                        sendData.fields[el].active = this.$store.state.filter.filterActive[this.pageName][el]
                    }

                    else if (
                    // this.selected[el] !== null &&
                        this.selected[el] !== "Invalid date" ||
                    this.selected[el] === true ||
                    this.selected[el] === false


                    ) {
                        sendData.fields[el] = { values: {} }
                        let active = this.$store.state.filter.filterActive[this.pageName][el]
                        let value = this.selected[el]
                        if (isArray(this.selected[el]) && this.selected[el].length === 0 && active === true) {
                            value = [null]
                        }
                        sendData.fields[el].values = { value }
                        sendData.fields[el].active = active

                    }
                })
                await this.$store.dispatch('filter/sendFilters', sendData)
            } catch(e) {
                console.error(e)
            }
        }
    }
}