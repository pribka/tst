<template>
    <div ref="treeWrapper">
        <a-tree-select
            ref="treeSelect"
            :value="value"
            :size="size"
            :tree-data-simple-mode="treeDataSimpleMode"
            style="width: 100%"
            :dropdownClassName="dropdownClassName"
            :treeDefaultExpandedKeys="treeDefaultExpandedKeys"
            :dropdown-style="dropdownStyle"
            :tree-data="treeData"
            :getPopupContainer="getPopupContainer"
            :load-data="onLoadData"
            :disabled="disabled"
            :labelInValue="labelInValue"
            :searchValue="searchValue"
            :placeholder="placeholder"
            :filterTreeNode="false"
            :treeCheckable="treeCheckable"
            :treeDefaultExpandAll="treeDefaultExpandAll"
            :dropdownMatchSelectWidth="dropdownMatchSelectWidth"
            :allowClear="allowClear"
            :showSearch="useSearch"
            :treeIcon="treeIcon"
            :searchPlaceholder="$t(searchPlaceholder)"
            @change="selectChange"
            @treeExpand="treeExpand"
            @select="treeSelect"
            @search="treeSearch">
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
let searchTimer;
export default {
    props: {
        value: {
            type: [Array, String, Number],
            default: null,
        },
        labelInValue: {
            type: Boolean,
            default: false
        },
        isLeafKey: {
            type: String,
            default: 'is_leaf'
        },
        transformData: {
            type: Function,
            default: () => {}
        },
        disabled: {
            type: Boolean,
            default: false
        },
        treeDefaultExpandAll: {
            type: Boolean,
            default: false
        },
        dropdownMatchSelectWidth: {
            type: Boolean,
            default: true
        },
        treeCheckable: {
            type: Boolean,
            default: false
        },
        treeIcon: {
            type: Boolean,
            default: false
        },
        apiUrl: {
            type: String,
            required: true
        },
        listObject: {
            type: [String, Boolean],
            default: 'selectList',
        },
        size: {
            type: String,
            default: 'large'
        },
        treeDataSimpleMode: {
            type: Boolean,
            default: true
        },
        params: {
            type: Object,
            default: () => {}
        },
        searchParams: {
            type: Object,
            default: () => {}
        },
        onLoadParams: {
            type: Object,
            default: () => {}
        },
        treeDefaultExpandedKeys: {
            type: Array,
            default: () => []
        },
        dropdownStyle: {
            type: Object,
            default: () => {
                return {
                    maxHeight: '250px', 
                    overflowY: 'auto',
                    maxWidth: '400px'
                }
            }
        },
        dropdownClassName: {
            type: String,
            default: ''
        },
        valueKey: {
            type: String,
            default: 'code'
        },
        idKey: {
            type: String,
            default: 'code'
        },
        titleKey: {
            type: String,
            default: 'name'
        },
        initPID: {
            type: [String, Number],
            default: 0
        },
        initLoaded: {
            type: Boolean,
            default: false
        },
        parentKey: {
            type: String,
            default: 'parent'
        },
        parentIdKey: {
            type: String,
            default: 'code'
        },
        usePopupContainer: {
            type: Boolean,
            default: false
        },
        getPContainer: {
            type: Function,
            default: () => {}
        },
        allowClear: {
            type: Boolean,
            default: false
        },
        placeholder: {
            type: String,
            default: ''
        },
        useSearch: {
            type: Boolean,
            default: false
        },
        searchPlaceholder: {
            type: String,
            default: 'find'
        },
        pidKey: {
            type: String,
            default: 'code'
        }
    },
    data() {
        return {
            treeData: [],
            searchValue: '',
            oldSearchValue: '',
            isSearch: false
        }
    },
    created() {
        this.getInitData()
    },
    methods: {
        async onSearch() {
            try {
                this.isSearch = true
                if(this.value?.length)
                    this.selectChange(null)
                this.treeData = []
                const params = {
                    ...this.searchParams,
                    text: this.searchValue
                }
                const { data } = await this.$http.get(this.apiUrl, { params })
                if (data?.[this.listObject]?.length) {
                    const listData = data[this.listObject].map(item => {
                        return {
                            ...item,
                            id: item[this.idKey],
                            value: item[this.valueKey],
                            title: item[this.titleKey],
                            isLeaf: true,
                            pId: this.initPID,
                            loaded: this.initLoaded
                        }
                    })
                    this.treeData = listData
                } else {
                    if(data?.length) {
                        const listData = data.map(item => {
                            return {
                                ...item,
                                id: item[this.idKey],
                                value: item[this.valueKey],
                                title: item[this.titleKey],
                                isLeaf: true,
                                pId: this.initPID,
                                loaded: this.initLoaded
                            }
                        })
                        this.treeData = listData
                    }
                }
            } catch(e) {
                console.log(e)
            }
        },
        treeSearch(value) {
            if(this.useSearch) {
                this.$emit('search', value)
                this.searchValue = value

                clearTimeout(searchTimer)
                if(!value?.length && this.oldSearchValue.length && this.value) {
                    this.oldSearchValue = ''
                    this.isSearch = false
                    this.selectChange(null)
                    this.getInitData()
                } else {
                    searchTimer = setTimeout(() => {
                        if(value?.length) {
                            this.oldSearchValue = this.searchValue
                            this.onSearch()
                        } else {
                            if(!this.value?.length) {
                                this.getInitData()
                            }
                        }
                    }, 500)
                }
                
            }
        },
        treeSelect(value, node, extra) {
            this.$emit('select', value, node, extra)
        },
        getPopupContainer() {
            if(this.usePopupContainer)
                return this.getPContainer()
            else
                return this.$refs.treeWrapper
        },
        onLoadData(treeNode) {
            return new Promise((resolve, reject) => {
                const dataRef = treeNode.dataRef
                if(!dataRef.loaded) {
                    const params = {
                        ...this.onLoadParams,
                        [this.parentKey]: dataRef[this.parentIdKey]
                    }
                    this.$http.get(this.apiUrl, { params })
                        .then(({data}) => {
                            if (data?.[this.listObject]?.length) {
                                const index = this.treeData.findIndex(f => f.value === dataRef.id)
                                if(index !== -1)
                                    this.$set(this.treeData[index], 'loaded', true)
                                data[this.listObject].forEach(item => {
                                    const find = this.treeData.find(f => f.value === item[this.valueKey])
                                    if(!find) {
                                        this.treeData.push({
                                            ...item,
                                            id: item[this.idKey],
                                            value: item[this.valueKey],
                                            title: item[this.titleKey],
                                            isLeaf: item[this.isLeafKey],
                                            pId: dataRef[this.pidKey],
                                            loaded: false
                                        })
                                    }
                                })
                            } else {
                                if(data?.length) {
                                    const index = this.treeData.findIndex(f => f.value === dataRef.id)
                                    if(index !== -1)
                                        this.$set(this.treeData[index], 'loaded', true)
                                    data.forEach(item => {
                                        const find = this.treeData.find(f => f.value === item[this.valueKey])
                                        if(!find) {
                                            this.treeData.push({
                                                ...item,
                                                id: item[this.idKey],
                                                value: item[this.valueKey],
                                                title: item[this.titleKey],
                                                isLeaf: item[this.isLeafKey],
                                                pId: dataRef[this.pidKey],
                                                loaded: false
                                            })
                                        }
                                    })
                                }
                            }
                            resolve()
                        })
                        .catch(e => {
                            console.log(e)
                            reject()
                        })
                }
            })
        },
        async getInitData() {
            try {
                if(this.isSearch)
                    this.isSearch = false
                if(this.isSearchSelected)
                    this.isSearchSelected = false
                if(this.treeData.length)
                    this.treeData = []
                const params = {
                    ...this.params
                }
                const { data } = await this.$http.get(this.apiUrl, { params })
                if (data?.[this.listObject]?.length) {
                    let listData = data[this.listObject].map(item => {
                        return {
                            ...item,
                            id: item[this.idKey],
                            value: item[this.valueKey],
                            title: item[this.titleKey],
                            isLeaf: item[this.isLeafKey],
                            pId: this.initPID,
                            loaded: this.initLoaded
                        }
                    })
                    this.treeData = listData
                } else {
                    if(data?.length) {
                        let listData = data.map(item => {
                            return {
                                ...item,
                                id: item[this.idKey],
                                value: item[this.valueKey],
                                title: item[this.titleKey],
                                isLeaf: item[this.isLeafKey],
                                pId: this.initPID,
                                loaded: this.initLoaded
                            }
                        })
                        this.treeData = listData
                    }
                }
                if(data)
                    this.$emit('initLoading', this.onLoadData)
            } catch(e) {
                console.log(e)
            }
        },
        selectChange(value) {
            this.$emit('input', value)
            this.$emit('change', value)

            if(this.isSearch)
                this.searchValue = this.oldSearchValue

            if(!value && this.isSearch && !this.oldSearchValue.length)
                this.getInitData()
        },
        treeExpand(expandedKeys) {
            this.$emit('treeExpand', expandedKeys)
        }
    }
}
</script>