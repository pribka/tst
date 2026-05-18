<template>
    <a-dropdown>
        <template v-if="filterLoading">
            <a-spin size="small" />
        </template>
        <a-button
            v-else
            :type="type" 
            :size="size"
            class="text-current prod_sort flex items-center">
            {{active.name}}
            <i class="fi fi-rr-angle-small-down ml-1"></i>
        </a-button>
        <a-menu 
            :selectedKeys="[active.param]" 
            slot="overlay">
            <a-menu-item 
                v-for="item in sortedItems" 
                :key="item.param"
                class="flex items-center"
                @click="changeSort(item)">
                <i 
                    class="fi mr-2" 
                    :class="item.icon"></i>
                {{item.name}}
            </a-menu-item>
        </a-menu>
    </a-dropdown>
</template>

<script>
import { isArray } from 'lodash'
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
        },
        type: {
            type: String,
            default: 'link'
        }
    },
    computed: {
        filterLoading() {
            if(this.$store.state.filter.filterLoading?.[this.page_name])
                return this.$store.state.filter.filterLoading[this.page_name]
            else
                return false
        },
        activeFilters() {
            return this.$store.state.filter.filterActive[this.model]
        },
        selected() {
            return this.$store.state.filter.filterSelected[this.page_name]
        },
        search() {
            if(this.$store.state.filter.filtersSearch?.[this.page_name]?.length)
                return this.$store.state.filter.filtersSearch[this.page_name]
            else
                return ''
        },
        activeSort: {
            get() {
                if(this.$store.state.filter.filterOrdering?.[this.page_name]?.length)
                    return this.$store.state.filter.filterOrdering[this.page_name]
                else
                    return ''
            },
            set(value) {
                this.$store.commit('filter/SET_FILTERS_ORDERING', {
                    name: this.page_name,
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
                    return {
                        name: 'Новинки',
                        param: '-created_at',
                        icon: 'fi-rr-calendar-check'
                    }
            } else
                return {
                    name: 'Новинки',
                    param: '-created_at',
                    icon: 'fi-rr-calendar-check'
                }
        }
    },
    data() {
        return {
            filterInclude: [],
            filterExclude: [],
            tags: [],
            sortedItems: [
                {   
                    name: 'Популярные',
                    param: '-popularity',
                    icon: 'fi-rr-star'
                },
                {
                    name: 'Новинки',
                    param: '-created_at',
                    icon: 'fi-rr-calendar-check'
                },
                {
                    name: 'Сначала дешевые',
                    param: 'price_by_catalog',
                    icon: 'fi-rr-sort-numeric-down'
                },
                {
                    name: 'Сначала дорогие',
                    param: '-price_by_catalog',
                    icon: 'fi-rr-sort-numeric-down-alt'
                }
            ]
        }
    },
    methods: {
        async changeSort(item) {
            try {
                this.activeSort = [item.param]

                let sendData = {
                    key: this.model,
                    fields: {},
                    filterTags: [],
                    ordering: this.activeSort,
                    page_name: this.page_name,
                    search: this.search
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
        }
    }
}
</script>