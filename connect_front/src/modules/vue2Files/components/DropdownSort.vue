<template>
    <div ref="sortWrapper">
        <template v-if="isMobile">
            <a-button
                flaticon
                icon="fi-rr-sort-alt"
                shape="circle"
                @click="activity = true" />
            <ActivityDrawer 
                :vis="activity" 
                useVis
                :cDrawer="closeDrawer">
                <ActivityItem v-for="item in sortedItems" :key="item.param" @click="changeSort(item)">
                    <i class="fi icon" :class="item.icon" />
                    {{item.name}}
                </ActivityItem>
            </ActivityDrawer>
        </template>
        <a-dropdown v-else :getPopupContainer="getPopupContainer">
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
    </div>
</template>

<script>
import { isArray } from 'lodash'
import { ActivityItem, ActivityDrawer } from '@/components/ActivitySelect'
export default {
    components: {
        ActivityItem,
        ActivityDrawer
    },
    props: {
        model: {
            type: [String, Number],
            required: true
        },
        page_name: {
            type: [String, Number],
            required: true
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
        isMobile() {
            return this.$store.state.isMobile
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
                        name: this.$t('Newest first'),
                        param: '-created_at',
                        icon: 'fi-rr-calendar-check'
                    }
            } else
                return {
                    name: this.$t('Newest first'),
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
            activity: false,
            sortedItems: [
                {   
                    name: this.$t('By name'),
                    param: 'name',
                    icon: 'fi-rr-sort-alpha-down'
                },
                {   
                    name: this.$t('By name'),
                    param: '-name',
                    icon: 'fi-rr-sort-alpha-up'
                },
                {
                    name: this.$t('Newest first'),
                    param: '-created_at',
                    icon: 'fi-rr-calendar-check'
                },
                {
                    name: this.$t('Oldest first'),
                    param: 'created_at',
                    icon: 'fi-rr-calendar-check'
                }
            ]
        }
    },
    methods: {
        getPopupContainer() {
            return this.$refs.sortWrapper
        },
        closeDrawer() {
            this.activity = false
        },
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
                if(this.activity)
                    this.activity = false
            } catch(e) {
                console.log(e)
            }
        }
    }
}
</script>