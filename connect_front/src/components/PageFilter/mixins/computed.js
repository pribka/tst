import { isArray } from 'lodash'
export default {
    computed: {
        includeMain() {
            return this.filterInclude.filter(f => !f.is_additional)
        },
        includeAdditional() {
            return this.filterInclude.filter(f => f.is_additional)
        },
        excludeMain() {
            return this.filterExclude.filter(f => !f.is_additional)
        },
        excludeAdditional() {
            return this.filterExclude.filter(f => f.is_additional)
        },
        hasIncludeAdditional() {
            return this.includeAdditional.length > 0
        },
        hasExcludeAdditional() {
            return this.excludeAdditional.length > 0
        },
        isMobile() { 
            return this.$store.state.isMobile
        },
        inputPlaceholder() {
            if(this.onlySearch) {
                return this.$t('find')
            }
            return this.tags.length ? this.$t('f_search') : this.$t('f_search_and_filter')
        },
        listColumn() {
            if (this.filterInclude.length >= 6)
                return 'grid-cols-2 gap-3'
            else
                return 'grid-cols-1 gap-4'
        },
        filterPopupWidth() {
            if(this.popoverMaxWidth)
                return `${this.popoverMaxWidth}px`
            if (this.width) {
                return this.width
            } else if (this.filterInclude.length > 4) {
                if (this.filterInclude.length >= 6) {
                    return '650px'
                } else {
                    return '400px'
                }
            } else
                return '400px'
        },
        user() {
            return this.$store.state.user.user
        },
        filterTagsLength() {
            let count = 0
            for (let prop in this.filterTags) {
                if (isArray(this.filterTags[prop])) {
                    if (this.filterTags[prop].length)
                        count = count + 1
                } else {
                    if (this.filterTags[prop])
                        count = count + 1
                }
            }
            return count
        },
        checkLoaded() {
            if (this.$store.state.filter.filter[this.name] !== undefined)
                return true
            else
                return false

        },
        checkExclude() {
            return this.filterExclude.length > 0
        },


        filterStatus() {
            return this.$store.state.filter.filterStatus[this.name]
        },


        selected() {
            return this.$store.state.filter.filterSelected[this.name]
        },

        showSearchInput() {
            return this.$store.state.filter.filterShowSearch?.[this.name] ? true : false
        },

        filtersSearch() {
            return this.$store.state.filter.filtersSearch?.[this.name] ? this.$store.state.filter.filtersSearch[this.name] : ''
        },

        activeFilters() {
            return this.$store.state.filter.filterActive[this.name]
        },

        disabledClearBtn() {
            if ((this.includeLenght + this.excludeLenght) === 0) return true
            return false
        },

        includeLenght() {
            return this.generateLength(false)
        },


        excludeLenght() {
            return this.generateLength(true)
        },


        filterTags() {
            return this.$store.state.filter.filterTags[this.name]
        },


        windowWidth() {
            return this.$store.state.windowWidth
        },

        tagsViewFilter() {
            let array = [],
                other = [],
                max = 1;

            if(this.windowWidth < 1356)
                max = 0 

            if (this.tags.length) {
                this.tags.forEach((tag, index) => {
                    if(this.windowWidth < 1068) {
                        other.push(tag)
                    } else {
                        if (index <= max) {
                            array.push(tag)
                        } else {
                            other.push(tag)
                        }
                    }
                })
            }
            if (other.length)
                array.push({ type: 'other', value: other })

            return array
        }
    }
}