<template>
    <div class="flex flex-col min-h-[600px]">
        <div
            ref="header"
            class="flex items-center justify-between">
            <div class="flex items-center gap-2 w-full">
                <PageFilter
                    :model="model"
                    :key="pageName"
                    size="large"
                    :popoverMaxWidth="400"
                    :getPopupContainer="() => $refs.header"
                    :page_name="pageName" />
                <slot name="headerLeft" :rowSelected="rowSelected" />
            </div>
            <div class="flex items-center gap-2">
                <slot name="add">
                    <a-button
                        v-if="add"
                        type="primary"
                        @click="add">
                        {{ addButtonTextOrDefault }}
                    </a-button>
                </slot>
                <SettingsButton
                    :pageName="pageName" />
            </div>
        </div>
        <div class="pt-2.5 flex flex-grow" ref="tableWrapRef">
            <UniversalTable
                ref="tableRef"
                class="flex-grow"
                :tableType="tableType"
                :model="model"
                :selectRowMode="!multiple"
                :selectRowModeMultiple="multiple"
                :params="params"
                :colParams="{
                    getPopupContainer: getPopupContainer
                }"

                :pageName="pageName"
                :endpoint="endpoint"
                @rowSelect="rowSelect" />
        </div>
        <div class="mt-4 flex justify-end">
            <a-button
                @click="select"
                type="flat_primary">
                {{ $t('select') }} 
            </a-button>
        </div>
    </div>
</template>

<script>
export default {
    components: {
        UniversalTable: () => import('@/components/TableWidgets/UniversalTable'),
        PageFilter: () => import('@/components/PageFilter'),
        SettingsButton: () => import('@/components/TableWidgets/SettingsButton')
    },
    props: {
        addButtonText: {
            type: String,
            default: ""
        },
        tableType: {
            type: String,
            required: true
        },
        model: {
            type: String,
            default: ""
        },
        pageName: {
            type: String,
            default: ""
        },
        endpoint: {
            type: String,
            required: true
        },
        params: {
            type: Object,
            default: () => ({})
        },
        add: {
            type: [Function, Boolean],
            default: false
        },
        multiple: {
            type: Boolean,
            default: false
        },
        selectedItems: {
            type: Array,
            default: () => []
        }
    },
    computed: {
        addButtonTextOrDefault() {
            return this.addButtonText || this.$t('Add')
        }
    },
    data() {
        return {
            rowSelected: null
        }
    },
    methods: {
        rowSelect(row) {
            this.rowSelected = row
        },
        syncSelectedItems() {
            if (!this.$refs.tableRef || !this.multiple) return
            this.$refs.tableRef.selectedRows = Array.isArray(this.selectedItems)
                ? [...this.selectedItems]
                : []
            this.$refs.tableRef.gridApi?.refreshCells?.({ force: true })
        },
        getPopupContainer() {
            return this.$refs.tableWrapRef
        },
        select() {
            const selectedRows = this.$refs.tableRef.getSelectedRows()
            this.$emit('select', this.multiple ? selectedRows : selectedRows?.[0])
        }
    },
    mounted() {
        this.$nextTick(() => {
            this.syncSelectedItems()
        })
    },
    watch: {
        selectedItems: {
            deep: true,
            handler() {
                this.$nextTick(() => {
                    this.syncSelectedItems()
                })
            }
        }
    },
    beforeDestroy() {
        this.rowSelected = null
    }
}
</script>
