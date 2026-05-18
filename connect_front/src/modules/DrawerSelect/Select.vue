<template>
    <div ref="selectWrapper" class="flex items-center" :class="search.length && 'search_active'">
        <div v-if="$scopedSlots.prefixIcon" slot="prefixIcon" class="mr-3">
            <slot name="prefixIcon" />
        </div>
        <a-select
            ref="select"
            :value="value"
            :loading="loading"
            :open="openSelect"
            class="w-full ant_select"
            :class="[usePlaceholder]"
            :mode="multiple ? 'tags' : 'default'"
            :size="size"
            :placeholder="placeholder"
            :allow-clear="allowClear"
            :list-height="listHeight"
            :show-search="showSearch"
            :placement="placement"
            :inputType="inputType"
            :default-open="defaultOpen"
            :auto-clear-search-value="autoClearSearchValueCom"
            :disabled="disabled"
            :getPopupContainer="getPopupContainer"
            :dropdown-class-name="popupClassName"
            :max-tag-count="maxTagCount"
            :filter-option="filterOptionHandler"
            showArrow
            @change="listChange"
            @dropdownVisibleChange="dropdownVisibleChange"
            @focus="selectFocus"
            @blur="selectBlur"
            @search="searchHandler"
            @deselect="deselect"
            @select="selectHandler"
            @popupScroll="popupScroll">
            <slot name="options" />
            <a-select-option
                v-for="item in optionList"
                :key="item[valueKey]"
                :value="item[valueKey]"
                :title="getItemTitle(item)">
                <slot 
                    v-if="$scopedSlots.option_item" 
                    name="option_item"
                    :data="item" />
                <div v-else class="truncate" :class="useOptionFlex && 'flex items-center'">
                    <a-badge v-if="useOptionsBadge" :color="item[badgeColorKey]" /> {{ getItemTitle(item) }}
                </div>
            </a-select-option>
            <template slot="dropdownRender" slot-scope="menu">
                <v-nodes :vnodes="menu" />
                <div v-if="showDropdownClose" class="flex justify-center">
                    <a-spin :spinning="loading" size="small" />
                </div>

                <a-button
                    v-if="showAllHandler" 
                    type="link"
                    block
                    size="large"
                    flaticon
                    iconRight
                    icon="fi-rr-arrow-up-right-from-square"
                    @mousedown.stop.prevent="showAllHandler">
                    Показать все
                </a-button>
            </template>
            <template slot="notFoundContent">
                <template v-if="!$scopedSlots.notFoundContent">
                    <div v-if="loading" class="flex justify-center p-2">
                        <a-spin size="small" />
                    </div>
                </template>
                <template v-else>
                    <slot name="notFoundContent" />
                </template>
            </template>
            <template slot="suffixIcon">
                <i class="fi" :class="suffixIcon" />
            </template>
            <template v-if="$scopedSlots.removeIcon" slot="removeIcon">
                <slot name="removeIcon" />
            </template>
            <template v-if="$scopedSlots.clearIcon" slot="clearIcon">
                <slot name="clearIcon" />
            </template>
            <template v-if="$scopedSlots.placeholder" slot="placeholder">
                <slot name="placeholder" />
            </template>
        </a-select>
        <div v-if="$scopedSlots.suffixSlot" slot="suffixSlot" class="ml-2">
            <slot name="suffixSlot" />
        </div>
    </div>
</template>

<script>
import eventBus from '@/utils/eventBus'
let searchTimer;
const filterOption = (input, option) => {
    const chld = option.children()?.[0] || null
    if(chld) {
        const { children } = chld
        return children[1].children.toLowerCase().indexOf(input.toLowerCase()) >= 0
    } else
        return false
}
export default {
    props: {
        value: {
            type: [Array, String, Number],
            default: null,
        },
        showAllHandler: {
            type: [Function, Boolean],
            default: false
        },
        apiUrl: {
            type: String,
            default: '/app_info/select_list/',
        },
        params: {
            type: Object,
            default: () => ({}),
        },
        useOptionFlex: {
            type: Boolean,
            default: true
        },
        multiple: {
            type: Boolean,
            default: false,
        },
        initList: {
            type: Boolean,
            default: true,
        },
        // Список для инициализации опций списка
        initOptionList: {
            type: Array,
            default: () => []
        },
        valueKey: {
            type: String,
            default: 'id',
        },
        labelKey: {
            type: String,
            default: 'string_view',
        },
        oneSelect: {
            type: Boolean,
            default: false
        },
        size: {
            type: String,
            default: 'large',
        },
        searchKey: {
            type: String,
            default: 'search'
        },
        virtual: {
            type: Boolean,
            default: true,
        },
        allowClear: {
            type: Boolean,
            default: false,
        },
        listHeight: {
            type: Number,
            default: 256,
        },
        firstSelected: {
            type: Boolean,
            default: false,
        },
        infinity: {
            type: Boolean,
            default: false,
        },
        page_size: {
            type: [Number, String],
            default: 15,
        },
        useOptionsBadge: {
            type: Boolean,
            default: false,
        },
        badgeColorKey: {
            type: String,
            default: 'color',
        },
        showSearch: {
            type: Boolean,
            default: false,
        },
        useSearchApi: {
            type: Boolean,
            default: true
        },
        placement: {
            type: String,
            default: 'bottomLeft',
        },
        placeholder: {
            type: String,
            default: '',
        },
        autoClearSearchValue: {
            type: Boolean,
            default: true,
        },
        autofocus: {
            type: Boolean,
            default: false,
        },
        disabled: {
            type: Boolean,
            default: false,
        },
        popupClassName: {
            type: String,
            default: '',
        },
        maxTagCount: {
            type: Number,
            default: 30,
        },
        defaultOpen: {
            type: Boolean,
            default: false,
        },
        showDropdownClose: {
            type: Boolean,
            default: true,
        },
        drawerHeight: {
            type: [Number, String],
            default: '100%',
        },
        closeDrawerInSelect: {
            type: Boolean,
            default: true,
        },
        forceDrawer: {
            type: Boolean,
            default: false,
        },
        listObject: {
            type: [String, Boolean],
            default: 'selectList',
        },
        useFilterSort: {
            type: Boolean,
            default: false,
        },
        defaultSelectCode: {
            type: String,
            default: '',
        },
        suffixIcon: {
            type: String,
            default: 'fi-rr-angle-small-down',
        },
        changeFullObject: {
            type: Boolean,
            default: false,
        },
        usePopupContainer: {
            type: Boolean,
            default: false
        },
        getPContainer: {
            type: Function,
            default: () => {}
        },
        resultsKey: {
            type: String,
            default: "results"
        },
        showPlaceholder: {
            type: Boolean,
            default: false
        },
        inputType: {
            type: String,
            default: "default"
        },
        selectUID: {
            type: [String, Object],
            default: () => null
        },
        disallowCustomValues: {
            type: Boolean,
            default: false
        },
        cacheSelectedList: {
            type: Boolean,
            default: true
        }
    },
    components: {
        VNodes: {
            functional: true,
            render: (h, ctx) => ctx.props.vnodes,
        }
    },
    data() {
        return {
            openSelect: false,
            loading: false,
            search: "",
            exclude: null,
            list: {
                results: [],
                next: true,
                count: 0
            },
            page: 0,
            cachedOptions: []
        }
    },
    computed: {
        optionList() {
            const additionalOptions = []
            if (this.cacheSelectedList) {
                const missing = this.cachedOptions.filter(
                    initOption => !this.list.results.some(option => option[this.valueKey] === initOption[this.valueKey])
                )
                additionalOptions.push(...missing)
            }
            if (this.initOptionList.length) {
                const initOptionList = this.initOptionList    
                const missing = initOptionList.filter(
                    initOption => !this.list.results.some(option => option[this.valueKey] === initOption[this.valueKey])
                )
                return [...missing, ...this.list.results];
            }
            return [...this.list.results, ...additionalOptions]
        },
        usePlaceholder() {
            if (!this.showPlaceholder) return 'hide-placeholder'
            if(this.search.length) return 'selected'
            return this.multiple ? (this.value.length ? 'selected' : '') : (this.value ? 'selected' : '')
        },
        autoClearSearchValueCom() {
            return this.autoClearSearchValue !== undefined
                ? this.autoClearSearchValue
                : true;
        },
        scrollNum() {
            if(this.page_size >= 10) {
                return 100
            }
            return 50
        }
    },
    methods: {
        getItemTitle(item) {
            const parts = this.labelKey.split('.')
            let value = item
            for (const key of parts) {
                if (value && typeof value === 'object') {
                    value = value[key]
                } else {
                    return ''
                }
            }

            return value ?? ''
        },
        pushListData(data) {
            this.list.results.unshift(data)
            this.list.count += 1
        },
        searchHandler(value) {
            this.search = value
            if(this.exclude)
                this.exclude = null
            clearTimeout(searchTimer)
            searchTimer = setTimeout(() => {
                this.listReload()
                this.getList()
            }, 500)
        },
        getPopupContainer() {
            if(this.usePopupContainer) {
                return this.getPContainer()
            } else
                return this.$refs.selectWrapper
        },
        filterOptionHandler(input, option) {
            if(this.useSearchApi)
                return true
            if (this.useFilterSort && !this.infinity)
                return filterOption(input, option)
            return false
        },
        async getList() {
            try {
                this.loading = true;
                const params = { ...this.params };
                if (params.filters)
                    params.filters = JSON.stringify(params.filters);
                if (this.infinity) {
                    this.page += 1;
                    params.page = this.page;
                    params.page_size = this.page_size;
                }
                if(this.useSearchApi && this.search) {
                    params[this.searchKey] = this.search
                }

                const { data } = await this.$http.get(this.apiUrl, { params })
                if (this.infinity) {
                    if (data?.[this.resultsKey]?.length) {
                        this.list.results = [...this.list.results, ...data[this.resultsKey]];
                        if (this.firstSelected && !this.value) {
                            const find = this.list.results.find(
                                (item) => item[this.valueKey] === this.defaultSelectCode
                            );
                            this.$emit('input', find ? find[this.valueKey] : data[this.resultsKey][0][this.valueKey])
                            this.$emit('oneChange', find ? find[this.valueKey] : data[this.resultsKey][0][this.valueKey])
                        }
                        if(this.oneSelect && this.list.results.length === 1) {
                            this.$emit('input', this.list.results[0][this.valueKey])
                            this.$emit('oneChange', this.list.results[0][this.valueKey])
                        }
                    }
                    this.list.next = data.next;
                    this.list.count = data.count;
                } else if (data?.[this.listObject]?.length) {
                    this.list.results = data[this.listObject]
                    this.list.count = data[this.listObject].length;
                    if(this.oneSelect && data[this.listObject].length === 1) {
                        this.$emit('input', data[this.listObject][0][this.valueKey])
                        this.$emit('oneChange', data[this.listObject][0][this.valueKey])
                    } else {
                        if(this.firstSelected && data[this.listObject].length && !this.value) {
                            this.$emit('input', data[this.listObject][0][this.valueKey])
                            this.$emit('oneChange', data[this.listObject][0][this.valueKey])
                        }
                    }
                } else {
                    this.list.results = data
                    this.list.count = data.length
                    if(this.oneSelect && data.length === 1) {
                        this.$emit('input', data[0][this.valueKey])
                        this.$emit('oneChange', data[0][this.valueKey])
                    }
                }
            } catch (e) {
                console.error('Error fetching list:', e);
            } finally {
                this.loading = false;
            }
        },
        cacheSelectedOptions(selectedValue) {
            if (!this.cacheSelectedList) return;
            
            const selectedOptions = this.multiple 
                ? this.optionList.filter(option => selectedValue.includes(option[this.valueKey]))
                : this.optionList.filter(option => option[this.valueKey] === selectedValue);
            
            this.cachedOptions = selectedOptions
            // selectedOptions.forEach(option => {
            //     if (!this.cachedOptions.some(cached => cached[this.valueKey] === option[this.valueKey])) {
            //         this.cachedOptions.push(option);
            //     }
            // });
        },
        handleChange(value) {
            this.cacheSelectedOptions(value);
            this.$emit('input', value);
            
        },
        listChange(value) {
            if(!value) {
                if(this.search) {
                    this.search = ""
                    this.listReload()
                    this.getList()
                }
            }
            if (this.disallowCustomValues) {
                if (this.multiple) {
                    value = value.filter(item => item !== this.search)
                } else if (value === this.search) {
                    value = null;
                }
            }

            this.cacheSelectedOptions(value);

            if (this.changeFullObject) {
                const find = this.optionList.find((f) => f[this.valueKey] === value)
                this.$emit('input', { value, find });
            } else {
                this.$emit('input', value)
            }
            this.$emit('change', value)

            const find = this.optionList.find((f) => f[this.valueKey] === value)
            if(find) {
                this.$emit('changeFull', find)
            }

            if(this.multiple) {
                let selectedObj = []
                value.forEach(item => {
                    const find = this.optionList.find((f) => f[this.valueKey] === item)
                    if(find)
                        selectedObj.push(find)
                })
                this.$emit('changeGetObject', selectedObj)
            } else {
                const find = this.optionList.find((f) => f[this.valueKey] === value)
                this.$emit('changeGetObject', find || null)
            }
        },
        dropdownVisibleChange(open) {
            this.openSelect = open;
            this.$emit('dropdownVisibleChange', open);
            if (open && !this.$scopedSlots.options && !this.initList && !this.list.results.length) {
                this.getList()
            }
        },
        popupScroll(event) {
            this.$emit('popupScroll', event)
            if (this.infinity && this.list.next) {
                const target = event.target
                if (!this.loading && (target.scrollTop + target.offsetHeight) + this.scrollNum >= target.scrollHeight)
                    this.getList()
            }
        },
        deselect(value) {
            this.search = ""
            this.exclude = null
            this.$emit('deselect', value);
        },
        selectHandler(value) {
            this.$emit('select', value);
        },
        selectFocus() {
            this.$emit('focus');
        },
        selectBlur() {
            this.$emit('blur');
        },
        listReload() {
            // this.value = this.multiple ? [] : null;
            this.list = { results: [], next: true, count: 0 };
            this.page = 0;
        },
        unshiftItem(data) {
            const find = this.list.results.find(f => f.id === data.id)
            if(!find) {
                this.exclude = data[this.valueKey]
                this.list.results.unshift(data)
            }
        }
    },
    mounted() {
        if (!this.$scopedSlots.options && this.initList)
            this.getList()

        if(this.selectUID) {
            eventBus.$on(`push_select_data_${this.selectUID}`, data => {
                const find = this.list.results.find(f => f.id === data.id)
                if(!find) {
                    this.exclude = data[this.valueKey]
                    this.list.results.unshift(data)
                }
            })
            eventBus.$on(`select_exclude_${this.selectUID}`, () => {
                this.exclude = null
            })
        }
    },
    beforeDestroy() {
        if(this.selectUID) {
            eventBus.$off(`push_select_data_${this.selectUID}`)
            eventBus.$off(`select_exclude_${this.selectUID}`)
        }
    }
}
</script>

<style lang="scss" scoped>
.ant_select{
    &:not(.hide-placeholder):not(.selected) {
        &::v-deep{
            .ant-select-selection__placeholder{
                display: block!important;
            }
        }
    }
}
::v-deep {
    .ant-select-arrow-icon {
        transition: transform .3s;
    }
    .ant-select-open .ant-select-arrow-icon {
        transform: rotate(180deg);
    }
}
</style>