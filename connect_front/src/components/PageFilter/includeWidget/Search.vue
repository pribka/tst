<template>
    <a-input-search 
        class="products_search"
        v-model="search"
        :placeholder="placeholder"
        :size="size"
        allowClear
        @change="searchHandler"/>
</template>

<script>
import { isArray } from 'lodash'
let timer;
export default {
    props: {
        model: {
            type: [String, Number],
            required: true
        },
        page_name: {
            type: [String, Number],
            required: true
        },
        placeholder: {
            type: [String, Number],
            default: 'Поиск'
        },
        size: {
            type: String,
            default: 'large'
        }
    },
    computed: {
        activeFilters() {
            return this.$store.state.filter.filterActive[this.model]
        },
        selected() {
            return this.$store.state.filter.filterSelected[this.page_name]
        },
        search: {
            get() {
                if(this.$store.state.filter.filtersSearch?.[this.page_name]?.length)
                    return this.$store.state.filter.filtersSearch[this.page_name]
                else
                    return ''
            },
            set(value) {
                this.$store.commit('filter/SET_FILTERS_SEARCH', {
                    name: this.page_name,
                    value
                })
            }
        },
        activeSort() {
            if(this.$store.state.filter.filterOrdering?.[this.page_name]?.length)
                return this.$store.state.filter.filterOrdering[this.page_name]
            else
                return ''
        }
    },
    data() {
        return {
            filterInclude: [],
            filterExclude: [],
            tags: []
        }
    },
    methods: {
        searchHandler() {
            clearTimeout(timer)

            timer = setTimeout(async () => {
                try {
                    let sendData = {
                        key: this.model,
                        fields: {},
                        filterTags: [],
                        ordering: this.activeSort,
                        search: this.search,
                        page_name: this.page_name
                    }

                    sendData['filterTags'] =

                {
                    structure: this.$store.state.filter.filterTags[this.page_name],
                    data: this.tags
                }


                    Object.keys(this.selected).forEach(el => {

                        let findFilter = this.filterInclude.find(f => f.name === el)

                        if (findFilter === undefined) findFilter = this.filterExclude.find(f => f.name === el)


                        // Отключаем фильтры в которых нет значений
                        if (this.selected[el] === null || (isArray(this.selected[el]) && this.selected[el].length === 0)) {
                            this.$store.commit("filter/SET_ACTIVE_FILTERS", { name: this.page_name, filterName: el, value: false })
                        }


                        // Для полей с макс и мин
                        if (this.selected[el]?.start || this.selected[el]?.end) {
                            sendData.fields[el] = { values: {} }
                            sendData.fields[el].values = this.selected[el]
                            sendData.fields[el].active = this.$store.state.filter.filterActive[this.page_name][el]
                        }

                        else if (
                        // this.selected[el] !== null &&
                            this.selected[el] !== "Invalid date" ||
                        this.selected[el] === true ||
                        this.selected[el] === false


                        ) {
                            sendData.fields[el] = { values: {} }
                            let active = this.$store.state.filter.filterActive[this.page_name][el]
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
                    console.log(e)
                }
            }, 800)
        }
    }
}
</script>