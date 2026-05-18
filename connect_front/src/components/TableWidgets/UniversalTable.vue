<template>
    <div ref="tableWrapper" class="tableWrapper flex-grow relative flex flex-col" tabindex="0" @focusin="onWrapperFocus" @focusout="onWrapperBlur" @mousedown="onWrapperMouseDown">
        <a-spin class="table_loading_spin" :loading="tableLoading" />
        <ag-grid-vue
            class="ag-theme-alpine flex-grow opacity_transition"
            :class="tableLoading && 'table_loading'"
            :columnDefs="columnDefs"
            :rowData="tableRows"
            :rowSelection="rowSelection"
            :headerHeight="40"
            :domLayout="domLayout"
            :animateRows="false"
            :suppressAnimationFrame="true"
            :suppressRowVirtualisation="false"
            :suppressColumnVirtualisation="false"
            :suppressColumnMoveAnimation="true"
            :enableCellChangeFlash="false"
            :overlayNoRowsTemplate="overlayNoRowsTemplate"
            :context="gridContext"
            :frameworkComponents="gridFrameworkComponents"
            :rowClassRules="rowClassRules"
            suppressRowClickSelection
            @grid-ready="onGridReady"
            @first-data-rendered="onFirstDataRendered"
            @rowClicked="onRowClicked"
            @rowSelected="$emit('rowSelected', $event)"
            @selectionChanged="$emit('selectionChanged', $event)"
            @grid-size-changed="onGridSizeChanged"
            @displayed-columns-changed="onDisplayedColumnsChanged"
            @column-pinned="onColumnsChanged"
            @column-visible="onColumnsChanged"
            @column-moved="onColumnMoved"
            @column-resized="onColumnsChanged"
            @cell-focused="onCellFocused"
            @cell-clicked="onCellClicked"/>
        <div class="flex justify-end items-center mt-1">
            <div v-if="tableInfo" class="mr-2">
                <a-modal
                    @cancel="settingsVisible = false"
                    :visible="settingsVisible"
                    :zIndex="settingZIndex"
                    :title="$t('table.settings')"
                    :afterClose="afterClose">
                    <div class="columns_checkbox_group flex flex-col">
                        <div>
                            <div class="mb-2 flex justify-between font-medium">
                                <span>{{ $t('table.columns') }}</span>
                                <span>{{ $t('table.fixed') }}</span>
                            </div>
                            <a-checkbox
                                ref="columnsCheckbox"
                                class="mb-1 pb-1 border-gray-300"
                                :indeterminate="indeterminate"
                                :checked="checkAllColumns"
                                @change="onCheckAllChange">
                                {{ $t('table.all') }}
                            </a-checkbox>
                        </div>
                        <a-checkbox-group v-model="columnsActive" @change="onColumnCheckboxChange">
                            <a-row
                                v-for="column in columnOptions"
                                :key="column.value"
                                class="flex mt-1 first:mt-0">
                                <CheckboxColumn
                                    :tableName="model+pageName"
                                    :setColumnName="setColumnName"
                                    :tableColumns="tableColumns"
                                    :column="column"/>
                            </a-row>
                        </a-checkbox-group>
                    </div>
                    <template #footer>
                        <div class="flex">
                            <a-button class="mr-2" type="ui" block @click="dropColumns(); settingsVisible = false">
                                {{ $t('table.default') }}
                            </a-button>
                            <a-button block type="primary" @click="setColumns(); settingsVisible = false">
                                {{ $t('table.confirm') }}
                            </a-button>
                        </div>
                    </template>
                </a-modal>
            </div>
            <a-button
                v-if="showPager && tablePageSize"
                class="table_refresh_button mr-2"
                type="ui_ghost"
                shape="circle"
                flaticon
                icon="fi-rr-refresh"
                v-tippy
                :content="$t('refresh_data')"
                :disabled="tableLoading"
                @click="reloadTableData" />
            <Pager
                v-if="!hideSinglePagePager && showPager && tablePageSize"
                ref="Pager"
                :hash="hash"
                :changePage="changePage"
                :changeSize="changePageSize"
                :pageSize="tablePageSize"
                :page="page"
                :scrollElements="[
                    '.task_table .ant-table-body-inner',
                    '.task_table .ant-table-body'
                ]"
                :count="rowCount || 1"/>
        </div>
    </div>
</template>

<script>
import "ag-grid-community/styles/ag-grid.css"
import "@/assets/css/ui/ag-theme-alpine.scss"
import { AgGridVue } from "ag-grid-vue"
import CellRenderer from "./CellRenderer.vue"
import CustomHeaderCell from "./CustomHeaderCell.vue"
import eventBus from "@/utils/eventBus"
import { mapActions } from "vuex"
import axios from "axios"
const CHILD_CLASS = "row--child"

export default {
    components: {
        /* eslint-disable */
        agColumnHeader: CustomHeaderCell,
        CellRenderer,
        CheckboxColumn: () => import("./CheckboxColumn.vue"),
        AgGridVue,
        Pager: () => import("./Pager")
    },
    props: {
        selectRowMode: { type: Boolean, default: false },
        selectRowModeMultiple: { type: Boolean, default: false },
        tableType: { type: String, required: true },
        model: { type: String, required: true },
        pageName: { type: String, required: true },
        endpoint: { type: String, default: null },
        autoHeight: { type: Boolean, default: false },
        openHandler: { type: Function, default: () => {} },
        showPager: { type: Boolean, default: true },
        hideSinglePagePager: { type: Boolean, default: false },
        taskType: { type: String, default: "" },
        main: { type: Boolean, default: false },
        getInvoicePayment: { type: Function, default: () => {} },
        showChildren: Boolean,
        excludeCol: { type: Array, default: () => [] },
        reloadTask: { type: Function, default: () => {} },
        extendDrawer: { type: Boolean, default: false },
        hash: { type: Boolean, default: false },
        startEdit: { type: Function, default: () => {} },
        deleteSprint: { type: Function, default: () => {} },
        updateStatus: { type: Function, default: () => {} },
        openDescModal: { type: Function, default: () => {} },
        openModalStat: { type: Function, default: () => {} },
        takeTask: { type: Function, default: () => {} },
        onRowClicked: { type: Function, default: () => {} },
        params: { type: Object, default: () => ({}) },
        organization: { type: Object, default: () => ({}) },
        hideActionColumn: { type: Boolean, default: false },
        useSelect: { type: Boolean, default: false },
        selectMode: { type: String, default: "multiple" },
        childParams: { type: Object, default: () => null },
        storeKey: { type: String, default: null },
        getDataHook: { type: Function, default: () => {} },
        colParams: { type: Object, default: () => null },
        rowNumbers: { type: Boolean, default: false },
        sprintInject: { type: Boolean, default: false },
        isSprint: { type: Boolean, default: false },
        selectedIds: {
            type: Array,
            default: () => []
        }
    },
    data() {
        return {
            gridFrameworkComponents: {
                agColumnHeader: CustomHeaderCell,
                CellRenderer
            },
            selectedRows: [],
            axiosCancel: null,
            state: {},
            expandedRowKeys: [],
            settingsVisible: false,
            settingZIndex: 1000,
            indeterminate: false,
            checkAllColumns: false,
            columnsActive: [],
            gridContext: null,
            gridApi: null,
            gridColumnApi: null,
            tableData: null,
            page: 1,
            tableLoading: false,
            activeRequestId: 0,
            overlayNoRowsTemplate: null,
            columnDefs: [],
            colIds: [],
            arrowHeight: 40,
            arrowMargin: 15,
            pinnedLeftWidth: 0,
            pinnedRightWidth: 0,
            bodyViewportEl: null,
            centerViewportEl: null,
            leftArrowEl: null,
            rightArrowEl: null,
            scrollRaf: null,
            scrollDir: 0,
            scrollSpeed: 10,
            onViewportScroll: null,
            onCenterScroll: null,
            arrowHandlers: null,
            onAnchorEnter: null,
            onAnchorLeave: null,
            refreshQueued: false,
            refreshRaf: null,
            lastFocusedColumn: null,
            lastFocusedColId: null,
            lastFocusedCellRowIndex: null,
            gridHasFocus: false
        }
    },
    computed: {
        isInject() {
            return this.sprintInject ? `_inject` : ''
        },
        computedStoreKey() { return this.storeKey || this.model + this.pageName },
        indent() { return { step: 16, levelField: "_level" } },
        rowSelection() { return this.useSelect ? this.selectMode : "singleRow" },
        rowCount() { return this.tableData?.count || 0 },
        domLayout() { return this.autoHeight ? "autoHeight" : "normal" },
        tableInfo() { return this.$store.state.table?.tablesInfo?.[this.model + this.pageName + this.tableType] },
        tableRows() { return this.$store.state.table?.tableRows?.[this.computedStoreKey] || [] },
        tableColumns() { return this.tableInfo?.columns?.length ? this.tableInfo.columns : [] },
        settingsColumn() {
            const found = this.tableColumns.find(c => c?.slots?.title === "titleWithSettings")
            return found.defaultTitle ? this.$t(found.defaultTitle) : ''
        },
        hasData() { return this.tableRows?.length },
        columnOptions() {
            return this.tableColumns.filter(c => c.hidable)
                .map(c => ({ label: c.title, value: c.dataIndex, fixed: c.fixed }))
        },
        tableOrdering() { return this.tableInfo?.ordering || null },
        tablePageSize() { return this.tableInfo?.page_size || null },
        rowClassRules() {
            return {
                [CHILD_CLASS]: p => !!p.data.parent_expand,
                'row--flash': p => !!p.data && !!p.data.__flash
            }
        }
    },
    watch: {
        tableColumns: {
            deep: true,
            handler(newCols) {
                if (!this.gridColumnApi) return
                const newIds = (newCols || []).map(c => c.dataIndex)
                const haveStructureChange =
          this.colIds.some(id => !newIds.includes(id)) || newIds.some(id => !this.colIds.includes(id))
                if (haveStructureChange) {
                    this.rebuildColumnDefsPreservingState()
                } else {
                    this.applyColumnStateFromModel(false)
                }
            }
        }
    },
    created() {
        this.gridContext = { parent: this }
        this.overlayNoRowsTemplate = `<span style="padding: 10px;">${this.$t("table.no_rows")}</span>`
        this.getTableInfo({
            page_name: this.pageName,
            model: this.model,
            table_type: this.tableType
        }).then(() => {
            this.buildColumnDefs()
            this.getTableData()
        })
    },
    mounted() {
        document.addEventListener('keydown', this.onGlobalKeyDown)
        this.$nextTick(() => {
            const wrapper = this.$refs.tableWrapper
            if (wrapper && typeof wrapper.addEventListener === 'function') {
                wrapper.addEventListener('focusin', this.onWrapperFocus)
                wrapper.addEventListener('focusout', this.onWrapperBlur)
                wrapper.addEventListener('mousedown', this.onWrapperMouseDown)
            }
        })

        eventBus.$on(`open_table_settings_${this.pageName}`, (zIndex) => {
            this.settingZIndex = zIndex
            this.openSettingsModal()
        })
        eventBus.$on(`update_table_row_data`, () => {
            if (this.gridApi) this.gridApi.refreshCells({ force: true })
        })
        eventBus.$on(`filter_start_${this.pageName}`, () => {
            this.cancelActiveTableRequest()
        })
        
        if(this.isSprint) {
            eventBus.$on('sprint_update_table', sprint => {
                //this.reloadTableData()
            })
            eventBus.$on('sprint_update_table_reload', () => {
                this.reloadTableData()
            })
            eventBus.$on(`update_sprints_list${this.isInject}`, () => {
                this.reloadTableData()
            })
            eventBus.$on('update_filter_tasks.TaskSprintModel', () => {
                this.reloadTableData()
            })
            eventBus.$on(`update_task_data${this.isInject}`, () => {
                this.reloadTableData()
            })
        }

        eventBus.$on(`update_filter_${this.model}_${this.pageName}`, () => this.reloadTableData())
        eventBus.$on(`update_filter_${this.pageName}`, () => this.reloadTableData())
        if (this.pageName !== this.model) {
            eventBus.$on(`update_filter_${this.model}`, () => this.reloadTableData())
        }
        eventBus.$on(`table_row_${this.pageName}`, ({ action, row = null, parentId = null }) => {
            if (["update", "delete", "create"].includes(action)) {
                this.getTableData()
            } else if (action === "expand") {
                const parentIndex = this.tableRows.findIndex(r => r.id === parentId)
                const parentRow = parentIndex !== -1 ? this.tableRows[parentIndex] : null
                const parentLevel = parentRow && typeof parentRow._level === "number" ? parentRow._level : 0
                if (Array.isArray(row)) {
                    row.forEach(item => { item.parent_expand = parentId; item._level = parentLevel + 1 })
                    if (parentIndex !== -1) this.tableRows.splice(parentIndex + 1, 0, ...row)
                }
            } else if (action === "collapse") {
                const parentIndex = this.tableRows.findIndex(r => r.id === parentId)
                if (parentIndex !== -1) {
                    const parentLevel = typeof this.tableRows[parentIndex]._level === "number" ? this.tableRows[parentIndex]._level : 0
                    const idsToRemove = new Set()
                    for (let i = parentIndex + 1; i < this.tableRows.length; i++) {
                        const r = this.tableRows[i]
                        const lvl = typeof r._level === "number" ? r._level : 0
                        if (lvl <= parentLevel) break
                        idsToRemove.add(r.id)
                    }
                    this.setTableData(this.tableRows.filter(item => !idsToRemove.has(item.id)))
                }
            }
        })
        eventBus.$on(`table_expand_row_${this.pageName}`, ({ action, row = null, anchor = null, parentId = null }) => {
            // Обрабатываем обновления
            if (["update", "delete", "create"].includes(action)) { this.getTableData(); return }

            // Нормализуем null/undefined, чтобы сравнение было корректным
            const norm = v => (v == null ? null : v)

            // Ищем именно тот экземпляр строки, который кликнули
            // Сначала по anchor (id + parent_expand), если не передан — fallback на старый parentId
            let parentIndex = -1
            if (anchor && typeof anchor.id !== 'undefined') {
                parentIndex = this.tableRows.findIndex(r =>
                r.id === anchor.id &&
                norm(r.parent_expand) === norm(anchor.parent_expand)
                )
            } else if (parentId != null) {
                parentIndex = this.tableRows.findIndex(r => r.id === parentId)
            }

            if (parentIndex === -1) return

            const parentLevel = Number(this.tableRows[parentIndex]._level || 0)

            if (action === "expand" && Array.isArray(row) && row.length) {
                const parentTaskId = (anchor && anchor.id) ?? parentId
                const prepared = row.map(item => ({
                ...item,
                parent_expand: parentTaskId,
                _level: parentLevel + 1
                }))

                // Вставляем дочерние рядом с тем экземпляром, который раскрывали
                this.tableRows.splice(parentIndex + 1, 0, ...prepared)
                if (this.gridApi) {
                    this.gridApi.applyTransaction({ add: prepared, addIndex: parentIndex + 1 })
                }
            }

            if (action === "collapse") {
                const toRemove = []
                for (let i = parentIndex + 1; i < this.tableRows.length; i++) {
                    const r = this.tableRows[i]
                    const lvl = Number(r._level || 0)
                    if (lvl <= parentLevel) break
                        toRemove.push(r)
                }
                if (toRemove.length) {
                    if (this.gridApi) this.gridApi.applyTransaction({ remove: toRemove })
                        this.$store.state.table.tableRows[this.computedStoreKey].splice(parentIndex + 1, toRemove.length)
                }
            }
        })
    },
    beforeDestroy() {
        if (this.pageName !== this.model) {
            eventBus.$off(`update_filter_${this.model}`)
        }

        if(this.isSprint) {
            eventBus.$off('sprint_update_table')
            eventBus.$off('sprint_update_table_reload')
            eventBus.$off(`update_sprints_list${this.isInject}`)
            eventBus.$off('update_filter_tasks.TaskSprintModel')
            eventBus.$off(`update_task_data${this.isInject}`)
        }

        eventBus.$off(`update_filter_${this.model}_${this.pageName}`)
        eventBus.$off(`update_filter_${this.pageName}`)
        eventBus.$off(`open_table_settings_${this.pageName}`)
        eventBus.$off(`update_table_row_data`)
        eventBus.$off(`filter_start_${this.pageName}`)
        eventBus.$off(`table_row_${this.pageName}`)
        eventBus.$off(`table_expand_row_${this.pageName}`)
        document.removeEventListener('keydown', this.onGlobalKeyDown)
        const wrapper = this.$refs.tableWrapper
        if (wrapper && typeof wrapper.removeEventListener === 'function') {
            wrapper.removeEventListener('focusin', this.onWrapperFocus)
            wrapper.removeEventListener('focusout', this.onWrapperBlur)
            wrapper.removeEventListener('mousedown', this.onWrapperMouseDown)
        }
        this.teardownScrollArrows()
        this.selectedRows.splice(0)
    },
    methods: {
        ...mapActions({
            getTableInfo: "table/getTableInfo",
            setTableInfo: "table/setTableInfo"
        }),
        normalizeRowIdPart(value) {
            return value == null ? null : value
        },
        findRowIndex(row) {
            if (!row || row.id == null) return -1

            const list = this.$store.state.table?.tableRows?.[this.computedStoreKey]
            if (!Array.isArray(list) || !list.length) return -1

            const hasParentExpand = Object.prototype.hasOwnProperty.call(row, 'parent_expand')
            const norm = v => (v == null ? null : v)

            return list.findIndex(item => {
                if (!item) return false
                if (String(item.id) !== String(row.id)) return false
                if (!hasParentExpand) return true
                return norm(item.parent_expand) === norm(row.parent_expand)
            })
        },
        getRowNodeByData(row) {
            if (!this.gridApi || !row) return null

            const hasParentExpand = Object.prototype.hasOwnProperty.call(row, 'parent_expand')
            const norm = v => (v == null ? null : v)
            let foundNode = null

            this.gridApi.forEachNode(node => {
                if (foundNode || !node?.data) return
                if (String(node.data.id) !== String(row.id)) return
                if (hasParentExpand && norm(node.data.parent_expand) !== norm(row.parent_expand)) return
                foundNode = node
            })

            return foundNode
        },
        refreshRow(row, force = true) {
            const node = this.getRowNodeByData(row)
            if (!node || !this.gridApi) return false

            this.gridApi.refreshCells({
                rowNodes: [node],
                force
            })
            if (typeof this.gridApi.redrawRows === 'function') {
                this.gridApi.redrawRows({
                    rowNodes: [node]
                })
            }

            return true
        },
        replaceRow(row) {
            if (!row || row.id == null) return

            const list = this.$store.state.table?.tableRows?.[this.computedStoreKey]
            if (!Array.isArray(list) || !list.length) return

            const norm = v => (v == null ? null : v)
            const hasParentExpand = Object.prototype.hasOwnProperty.call(row, 'parent_expand')
            const index = this.findRowIndex(row)

            if (index === -1) return

            const next = {
                ...list[index],
                ...row,
                __flash: true
            }
            Object.keys(next).forEach(key => {
                this.$set(list[index], key, next[key])
            })

            if (!this.gridApi) return

            const foundNode = this.getRowNodeByData(next)

            if (foundNode) {
                if (typeof foundNode.setData === 'function') foundNode.setData(list[index])
                else if (typeof foundNode.updateData === 'function') foundNode.updateData(list[index])

                this.gridApi.refreshCells({
                    rowNodes: [foundNode],
                    force: true
                })
                if (typeof this.gridApi.redrawRows === 'function') {
                    this.gridApi.redrawRows({
                        rowNodes: [foundNode]
                    })
                }
            } else {
                this.gridApi.refreshCells({ force: true })
            }

            setTimeout(() => {
                const freshList = this.$store.state.table?.tableRows?.[this.computedStoreKey]
                if (!Array.isArray(freshList)) return

                const idx2 = this.findRowIndex(next)
                if (idx2 === -1) return

                const cleared = freshList[idx2]
                if (!cleared) return

                this.$delete(cleared, '__flash')

                const node2 = this.getRowNodeByData(cleared)
                if (node2 && typeof node2.setData === 'function') {
                    node2.setData(cleared)
                    this.gridApi.refreshCells({
                        rowNodes: [node2],
                        force: true
                    })
                    if (typeof this.gridApi.redrawRows === 'function') {
                        this.gridApi.redrawRows({
                            rowNodes: [node2]
                        })
                    }
                } else this.gridApi.refreshCells({ force: true })
            }, 2000)
        },
        prependRow(row) {
            if (!row || row.id == null) return
            if (this.page !== 1) {
                this.replaceRow(row)
                return
            }

            let list = this.$store.state.table?.tableRows?.[this.computedStoreKey]
            if (!Array.isArray(list)) {
                list = []
                this.setTableData(list)
            }

            const existingIndex = list.findIndex(item => item && String(item.id) === String(row.id))
            const hadExistingItem = existingIndex !== -1
            const removedRows = []
            const nextRow = { ...row, __flash: true }

            if (hadExistingItem && existingIndex === 0) {
                Object.keys(nextRow).forEach(key => {
                    this.$set(list[0], key, nextRow[key])
                })
            } else {
                if (hadExistingItem)
                    removedRows.push(...list.splice(existingIndex, 1))

                list.unshift(nextRow)
            }

            if (!hadExistingItem && this.tablePageSize && list.length > this.tablePageSize)
                removedRows.push(...list.splice(this.tablePageSize))

            if (this.tableData) {
                const nextCount = Number(this.tableData.count || 0) + (hadExistingItem ? 0 : 1)
                this.tableData = {
                    ...this.tableData,
                    count: nextCount,
                    results: list
                }
            }

            if (this.gridApi) {
                const transaction = hadExistingItem && existingIndex === 0
                    ? { update: [list[0]] }
                    : { add: [list[0]], addIndex: 0 }

                if (removedRows.length)
                    transaction.remove = removedRows

                this.gridApi.applyTransaction(transaction)
                this.refreshRow(list[0])
            }

            setTimeout(() => {
                const freshList = this.$store.state.table?.tableRows?.[this.computedStoreKey]
                if (!Array.isArray(freshList)) return

                const flashIndex = freshList.findIndex(item => item && String(item.id) === String(row.id))
                if (flashIndex === -1) return

                const cleared = freshList[flashIndex]
                if (!cleared) return

                this.$delete(cleared, '__flash')

                if (this.gridApi) {
                    const node = this.getRowNodeByData(cleared)
                    if (node && typeof node.setData === 'function') node.setData(cleared)
                    this.refreshRow(cleared)
                }
            }, 2000)
        },
        restoreSelection() {
            if (!this.gridApi || !this.useSelect) return

            this.gridApi.forEachNode(node => {
                if (this.selectedIds.includes(node.data.id)) {
                    node.setSelected(true)
                }
            })
        },
        onWrapperMouseDown() {
            this.gridHasFocus = true
        },
        onWrapperFocus() {
            this.gridHasFocus = true
        },
        onWrapperBlur(event) {
            const related = event && event.relatedTarget
            if (related && this.$refs.tableWrapper && this.$refs.tableWrapper.contains(related))
                return
            this.gridHasFocus = false
        },

        onCellFocused(event) {
            if (!event || !event.column) return
            this.lastFocusedColumn = event.column
            this.lastFocusedColId = event.column.getColId()
            this.lastFocusedCellRowIndex = typeof event.rowIndex === 'number' ? event.rowIndex : null
        },
        onCellClicked(event) {
            if (!event || !event.column) return
            this.lastFocusedColumn = event.column
            this.lastFocusedColId = event.column.getColId()
            this.lastFocusedCellRowIndex = typeof event.rowIndex === 'number' ? event.rowIndex : null
        },
        onGlobalKeyDown(e) {
            if (!this.gridHasFocus) return
            const key = e.key || String.fromCharCode(e.keyCode || 0)
            const isCopy = (key.toLowerCase() === 'c' || e.keyCode === 67) && (e.ctrlKey || e.metaKey)
            if (!isCopy) return
            e.preventDefault()
            this.handleCopyAction()
        },
        async handleCopyAction() {
            if (!this.gridApi || !this.gridColumnApi) return
            const displayed = this.gridColumnApi.getAllDisplayedColumns ? this.gridColumnApi.getAllDisplayedColumns() : []
            if (!displayed || !displayed.length) return

            const colIdx = Number.isInteger(this.lastFocusedColumnIndex) ? this.lastFocusedColumnIndex : null
            const columnRef = (colIdx !== null && colIdx >= 0 && colIdx < displayed.length) ? displayed[colIdx] : (this.lastFocusedColumn || null)
            if (!columnRef) {
                this.showCopyToast()
                return
            }

            const rowIndex = Number.isInteger(this.lastFocusedCellRowIndex) ? this.lastFocusedCellRowIndex : null
            if (rowIndex !== null) {
                let node = null
                try {
                    node = this.gridApi.getDisplayedRowAtIndex(rowIndex)
                } catch (e) {
                    node = null
                }
                if (node && node.data) {
                    let val = ''
                    try {
                        val = this.gridApi.getValue(columnRef, node)
                    } catch (e) {
                        try {
                            const fallbackKey = columnRef && columnRef.getColId ? columnRef.getColId() : (columnRef && columnRef.field ? columnRef.field : null)
                            val = this.getValueFromRow(node.data, fallbackKey)
                        } catch (er) {
                            val = ''
                        }
                    }
                    if (val == null) val = ''
                    if (typeof val === 'object') {
                        val = this.extractFromObject(val) || ''
                    }
                    await this.copyToClipboard(String(val))
                    return
                }
            }

            const selectedRows = this.gridApi.getSelectedRows && this.gridApi.getSelectedRows()
            const selectedIds = (selectedRows && selectedRows.length) ? new Set(selectedRows.map(r => r.id)) : null
            const values = []
            this.gridApi.forEachNodeAfterFilterAndSort(node => {
                if (!node || !node.data) return
                if (selectedIds && !selectedIds.has(node.data.id)) return
                let val = ''
                try {
                    val = this.gridApi.getValue(columnRef, node)
                } catch (e) {
                try {
                    const fallbackKey = columnRef && columnRef.getColId ? columnRef.getColId() : (columnRef && columnRef.field ? columnRef.field : null)
                    val = this.getValueFromRow(node.data, fallbackKey)
                } catch (er) {
                    val = ''
                }
                }
                if (val == null) val = ''
                if (typeof val === 'object') {
                    val = this.extractFromObject(val) || ''
                }
                values.push(String(val))
            })
            const text = values.join('\n')
            await this.copyToClipboard(text)
        },
        serializeRowsColumn() {
            return ''
        },
        formatIfDate(val) {
            if (val == null) return ''
            if (typeof val === 'string' || val instanceof Date) {
                try {
                    const m = this.$moment(val)
                    if (m && typeof m.isValid === 'function' && m.isValid()) {
                        return m.format('DD.MM.YYYY HH:mm')
                    }
                } catch (e) {}
            }
            return String(val)
        },
        extractFromObject(obj) {
            if (!obj) return ''
            if (typeof obj === 'string') return this.formatIfDate(obj)
            if (typeof obj === 'number' || typeof obj === 'boolean') return String(obj)
            if (Array.isArray(obj)) {
                const parts = obj.map(item => this.extractFromObject(item)).filter(Boolean)
                return parts.join(', ')
            }
            const keysPriority = ['name', 'full_name', 'string_view', 'short_name', 'title', 'label', 'fullName']
            for (const k of keysPriority) {
                if (Object.prototype.hasOwnProperty.call(obj, k) && obj[k] != null) {
                    return this.extractFromObject(obj[k])
                }
            }
            const nestedCandidates = ['member', 'membership_role', 'membership_request_status', 'organization', 'owner', 'assignee', 'user', 'creator']
            for (const n of nestedCandidates) {
                if (obj[n]) return this.extractFromObject(obj[n])
            }
            for (const v of Object.values(obj)) {
                if (v == null) continue
                if (typeof v === 'string') {
                    const maybe = this.formatIfDate(v)
                    if (maybe && maybe !== '') return maybe
                }
                if (typeof v === 'object') {
                    const rec = this.extractFromObject(v)
                    if (rec) return rec
                }
            }
            return ''
        },
        getValueFromRow(row, colId) {
            if (!row) return ''
            const col = this.columnDefs.find(c => c.colId === colId || c.field === colId)
            const field = col ? (col.field || colId) : colId
            let raw = undefined
            if (field && typeof field === 'string') {
                if (field.indexOf('.') !== -1) {
                    raw = field.split('.').reduce((acc, part) => acc ? acc[part] : undefined, row)
                } else {
                    raw = row[field]
                }
            } else {
                raw = row[colId] ?? row[field]
            }
            if (raw == null) return ''
            if (typeof raw === 'string') return this.formatIfDate(raw)
            if (typeof raw === 'number' || typeof raw === 'boolean') return String(raw)
            return this.extractFromObject(raw)
        },

        async copyToClipboard(text) {
            if (!text) {
                this.showCopyToast()
                return
            }
            try {
                if (navigator.clipboard && navigator.clipboard.writeText) {
                    await navigator.clipboard.writeText(text)
                    this.showCopyToast()
                    return
                }
            } catch (e) {}
            const ta = document.createElement('textarea')
            ta.value = text
            ta.style.position = 'fixed'
            ta.style.left = '-9999px'
            document.body.appendChild(ta)
            ta.select()
            try {
                document.execCommand('copy')
                this.showCopyToast()
            } catch (e) {}
            document.body.removeChild(ta)
        },

        showCopyToast() {
            if (this.$message && typeof this.$message.success === 'function') {
                this.$message.success(this.$t('copied'))
                return
            }
            const el = document.createElement('div')
            el.textContent = this.$t('copied')
            Object.assign(el.style, {position: 'fixed', bottom: '12px', right: '12px', background: '#111', color: '#fff', padding: '8px 12px', borderRadius: '6px', zIndex: 2000})
            document.body.appendChild(el)
        setTimeout(() => { document.body.removeChild(el) }, 1200)
        },
        onColumnMoved(event) {
            if (!event?.finished) return

            const newOrder = event.columnApi.getAllGridColumns().map(col => col.getColId())
            this.tableColumns.sort((a, b) => {
                return newOrder.indexOf(a.key) - newOrder.indexOf(b.key)
            })

            this.sendTableInfo()
            this.onColumnsChanged()
        },
        getSelectedRows() {
            return this.selectedRows
        },
        afterClose() { this.settingZIndex = 1000 },
        changeState(value) { this.$set(this, "state", value) },
        cancelActiveTableRequest() {
            if (this.axiosCancel) {
                this.axiosCancel.cancel('Canceled stale table request')
                this.axiosCancel = null
            }
            this.activeRequestId += 1
            this.tableLoading = false
        },
        reloadTableData() { this.changeState(null); this.changePage(1) },
        async getTableData() {
            if (!this.endpoint) {
                this.tableData = []
                this.$store.state.table.tableRows?.[this.computedStoreKey]?.splice(0)
                delete this.$store.state.table.tableRows[this.computedStoreKey]
                return
            }
            this.cancelActiveTableRequest()
            const requestId = ++this.activeRequestId
            let axiosSource = null
            const params = {
                page_name: this.pageName,
                page_size: this.tablePageSize,
                page: this.page,
                ordering: this.tableOrdering,
                ...this.params
            }
            this.tableLoading = true
            try {
                axiosSource = axios.CancelToken.source()
                this.axiosCancel = axiosSource
                const { data } = await this.$http.get(this.endpoint, { cancelToken: this.axiosCancel.token, params })
                if (requestId !== this.activeRequestId) return
                this.tableData = data
                this.getDataHook(data)
                this.setTableData(data.results)
                this.$nextTick(() => {
                    this.queueRefreshArrows()
                    this.restoreSelection()
                })
            } catch (error) {
                if (!axios.isCancel(error))
                    console.error(error)
            } finally {
                if (this.axiosCancel === axiosSource) {
                    this.axiosCancel = null
                }
                if (requestId === this.activeRequestId)
                    this.tableLoading = false
            }
        },
        setTableData(rows) { this.$set(this.$store.state.table.tableRows, [this.computedStoreKey], rows) },
        onGridReady(params) {
            this.gridApi = params.api
            this.gridColumnApi = params.columnApi
            this.$nextTick(() => this.initScrollArrows())
        },
        onFirstDataRendered() {
            this.$nextTick(() => { this.initScrollArrows(); this.queueRefreshArrows() })
        },
        onGridSizeChanged() { this.$nextTick(() => this.queueRefreshArrows()) },
        onDisplayedColumnsChanged() { this.$nextTick(() => this.queueRefreshArrows()) },
        onColumnsChanged() { this.$nextTick(() => this.queueRefreshArrows()) },
        buildColumnDefs() {
            try {
                const exclude = Array.isArray(this.excludeCol) ? this.excludeCol : []
                const colsRaw = [...this.tableColumns].filter(c => {
                    if (!c) return false
                    const key = c.key ?? c.dataIndex ?? ''
                    const dataIndex = c.dataIndex ?? ''
                    return !exclude.includes(key) && !exclude.includes(dataIndex)
                })
                if (this.hideActionColumn) {
                    const actionsColumn = colsRaw.find(c => c.dataIndex === 'actions')
                    if (actionsColumn) actionsColumn.visible = false
                }
                const settingsCol = colsRaw.find(c => c?.slots?.title === 'titleWithSettings')
                const fallbackColId = (settingsCol && settingsCol.dataIndex) || (colsRaw[0] && colsRaw[0].dataIndex) || null
                const defs = []
                colsRaw.forEach((c) => {
                    defs.push({
                        colId: c.key,
                        field: c.dataIndex,
                        key: c.key,
                        format: c.format || null,
                        headerName: c.title ? this.$t(c.title) : '',
                        width: c.width || null,
                        minWidth: c.minWidth ?? 60,
                        pinned: c.fixed || null,
                        hide: !c.visible,
                        sortable: !!c.sorter,
                        resizable: true,
                        wrapText: true,
                        autoHeight: true,
                        comparator: () => {},
                        headerCheckboxSelection: c.headerCheckboxSelection,
                        checkboxSelection: c.checkboxSelection,
                        widget: c.cellRenderer,
                        textAlign: c.textAlign,
                        cellStyle: {
                            wordBreak: 'normal',
                            padding: '5px',
                            lineHeight: '1.4rem',
                            display: 'flex',
                            alignItems: 'center',
                            height: '100%'
                        },
                        headerComponent: 'agColumnHeader',
                        headerComponentParams: {
                            changeSort: this.changeSort,
                            getOrdering: () => this.tableInfo?.ordering
                        },
                        cellRenderer: 'CellRenderer',
                        cellRendererParams: (p) => {
                            const parent = p?.context?.parent
                            return {
                                colParams: this.colParams,
                                widget: c.cellRenderer,
                                textAlign: c.textAlign,
                                state: parent?.state,
                                changeState: parent?.changeState,
                                organization: parent?.organization,
                                tableType: parent?.tableType,
                                model: parent?.model,
                                childParams: parent?.childParams,
                                pageName: parent?.pageName,
                                pageModel: parent?.model,
                                reloadTableData: this.reloadTableData,
                                openHandler: parent?.openHandler,
                                taskType: parent?.taskType,
                                takeTask: parent?.takeTask,
                                startEdit: parent?.startEdit,
                                deleteSprint: parent?.deleteSprint,
                                updateStatus: parent?.updateStatus,
                                main: parent?.main,
                                expandedRowKeys: parent?.expandedRowKeys,
                                extendDrawer: parent?.extendDrawer,
                                reloadTask: parent?.reloadTask,
                                showChildren: parent?.showChildren,
                                expanded: parent?.expanded,
                                indent: parent?.indent,
                                getInvoicePayment: parent?.getInvoicePayment,
                                openModalStat: parent?.openModalStat,
                                openDescModal: parent?.openDescModal
                            }
                        }
                    })
                })
                if (this.selectRowMode || this.selectRowModeMultiple) {
                    defs.unshift({
                        key: 'select',
                        colId: 'select',
                        cellRenderer: 'CellRenderer',
                        widget: 'SelectRow',
                        cellRendererParams: () => {
                            const mode = this.selectRowModeMultiple ? 'multiple' : 'single'
                            if (this.selectedRows.length) {
                                this.$emit('rowSelect', mode === 'multiple' ? this.selectedRows : this.selectedRows[0])
                            }
                            return {
                                mode,
                                selectedRows: this.selectedRows,
                                onSelectChange: row => {
                                    if (mode === 'multiple') {
                                        const index = this.selectedRows.findIndex(r => r.id === row.id)
                                        if (index !== -1) {
                                            this.selectedRows.splice(index, 1)
                                        } else {
                                            this.selectedRows.push(row)
                                        }
                                        this.$emit('rowSelect', this.selectedRows)
                                    } else if (mode === 'single') {
                                        this.selectedRows.splice(0)
                                        this.selectedRows.push(row)
                                        this.$emit('rowSelect', row)
                                    }
                                    this.$nextTick(() => {
                                        this.gridApi?.refreshCells?.({ force: true })
                                    })
                                }
                            }
                        },
                        pinned: 'left',
                        width: 50,
                    })
                }
                if (this.rowNumbers) {
                    const offset = ((this.page - 1) * (this.tablePageSize || 0)) || 0
                    defs.unshift({
                        key: 'rowNumber',
                        colId: 'rowNumber',
                        field: 'rowNumber',
                        headerName: '#',
                        width: 60,
                        minWidth: 50,
                        resizable: false,
                        sortable: false,
                        lockPosition: true,
                        suppressMovable: true,
                        cellRenderer: function(params) {
                            const idx = params && params.node ? params.node.rowIndex : (params.rowIndex || 0)
                            return idx + 1 + offset
                        }
                    })
                }
                this.columnDefs = defs
                this.colIds = defs.map(d => d.field)
                this.$nextTick(() => {
                    this.applyColumnStateFromModel(false, fallbackColId)
                })
            } catch (e) {
                console.error("buildColumnDefs error", e)
            }
        },
        rebuildColumnDefsPreservingState() {
            if (!this.gridColumnApi) { this.buildColumnDefs(); return }
            const prevState = this.gridColumnApi.getColumnState() || []
            const prevPivotMode = this.gridColumnApi.isPivotMode()
            this.buildColumnDefs()
            this.$nextTick(() => {
                try {
                    this.gridColumnApi.applyColumnState({ state: prevState, applyOrder: true })
                    this.gridColumnApi.setPivotMode(prevPivotMode)
                    this.queueRefreshArrows()
                } catch (e) { console.warn("restore column state failed", e) }
            })
        },
        applyColumnStateFromModel(applyOrder = false, fallbackColId = null) {
            if (!this.gridColumnApi) return
            const state = this.tableColumns
                .filter(c => c.dataIndex)
                .map(c => ({
                    colId: c.key,
                    hide: !c.visible,
                    pinned: c.fixed || null
                }))
            const hasShown = state.some(s => !s.hide)
            if (!hasShown && state.length) {
                const settingsCol = this.tableColumns.find(c => c?.slots?.title === 'titleWithSettings')
                const mustShow = (fallbackColId) ||
          (settingsCol && settingsCol.dataIndex) ||
          state[0].colId
                const target = state.find(s => s.colId === mustShow)
                if (target) target.hide = false
            }
            this.gridColumnApi.applyColumnState({ state, applyOrder })
            this.$nextTick(() => this.queueRefreshArrows())
        },
        onColumnCheckboxChange(checkedList) {
            this.indeterminate = !!checkedList.length && checkedList.length < this.columnOptions.length
            this.checkAllColumns = checkedList.length === this.columnOptions.length
        },
        onCheckAllChange({ target }) {
            if (target.checked) {
                this.tableColumns.forEach(c => c.hidable && this.columnsActive.push(c.dataIndex))
            } else {
                this.columnsActive = []
            }
            this.indeterminate = false
            this.checkAllColumns = target.checked
        },
        setColumnName(columnValue, newName) {
            const column = this.tableColumns.find(c => c.dataIndex === columnValue)
            if (column) column.title = newName
        },
        async setColumns() {
            this.tableColumns.forEach((c, i) => {
                if (c.hidable) this.tableColumns[i].visible = this.columnsActive.includes(c.dataIndex)
            })
            await this.sendTableInfo()
            this.applyColumnStateFromModel(false)
        },
        async sendTableInfo() {
            const defaultPageSize = 15
            const settings = {
                columns: this.tableColumns,
                page_size: this.tablePageSize || defaultPageSize,
                ordering: this.tableOrdering
            }
            const params = {
                page_name: this.pageName,
                model: this.model,
                table_type: this.tableType,
                settings
            }
            try {
                await this.setTableInfo(params)
                await this.$http.post(`table_info/`, params)
            } catch (error) {
                console.error(error)
            }
        },
        columnsActiveInit() {
            this.columnsActive.splice(0)
            this.tableColumns.forEach(c => c.visible && c.hidable && this.columnsActive.push(c.dataIndex))
            this.indeterminate = !!this.columnsActive.length && this.columnsActive.length < this.columnOptions.length
            this.checkAllColumns = this.columnsActive.length === this.columnOptions.length
        },
        async changePageSize(size) {
            this.tableInfo.page_size = size
            await this.sendTableInfo()
            this.getTableData()
        },
        changePage(page) {
            this.page = page
            this.getTableData()
            this.$emit('change_page', page)
        },
        async changeSort(sortedColumn, sortDirection) {
            const idx = this.tableColumns.findIndex(c => (c.key === sortedColumn) || (c.dataIndex === sortedColumn))
            this.tableColumns.forEach(c => { if (c.sortOrder) delete c.sortOrder })
            if (idx !== -1) this.tableColumns[idx].sortOrder = sortDirection
            let ordering = null
            if (sortDirection) ordering = sortDirection === 'desc' ? ('-' + this.tableColumns[idx].key) : this.tableColumns[idx].key
            this.tableInfo.ordering = ordering
            this.changePage(1)
            this.sendTableInfo()
            if (this.gridApi) this.gridApi.refreshHeader()
        },
        async dropColumns() {
            const tableName = { model: this.model, page_name: this.pageName }
            try {
                const { data } = await this.$http.post("/table_info/", {
                    ...tableName,
                    table_type: this.tableType,
                    drop: true
                })
                const params = { ...tableName, table_type: this.tableType, settings: data }
                await this.setTableInfo(params)
                this.buildColumnDefs()
                this.columnsActiveInit()
                this.getTableData()
            } catch (error) {
                console.error(error)
            }
        },
        openSettingsModal() {
            this.settingsVisible = true
            this.columnsActiveInit()
        },
        setArrowVisual(el, hovered) {
            if (!el) return
            if (hovered) { el.style.background = '#4777FF'; el.style.color = '#fff' }
            else { el.style.background = '#e8ecfa'; el.style.color = '#4777FF' }
        },
        queueRefreshArrows() {
            if (this.refreshQueued) return
            this.refreshQueued = true
            this.refreshRaf = requestAnimationFrame(() => {
                this.refreshQueued = false
                this.refreshScrollArrows()
            })
        },
        computePinnedOffsets() {
            const leftVp  = this.$el.querySelector('.ag-pinned-left-cols-viewport');
            const rightVp = this.$el.querySelector('.ag-pinned-right-cols-viewport');
            this.pinnedLeftWidth  = leftVp  ? leftVp.getBoundingClientRect().width  : 0;
            this.pinnedRightWidth = rightVp ? rightVp.getBoundingClientRect().width : 0;
            if (this.leftArrowEl)  this.leftArrowEl.style.left  = `${this.pinnedLeftWidth  + this.arrowMargin}px`;
            if (this.rightArrowEl) this.rightArrowEl.style.right = `${this.pinnedRightWidth + this.arrowMargin}px`;
        },
        updateArrowsVerticalPosition() {
            const vp = this.bodyViewportEl;
            if (!vp || !this.leftArrowEl || !this.rightArrowEl) return;
            const top = vp.scrollTop + (vp.clientHeight - this.arrowHeight) / 2;
            this.leftArrowEl.style.top  = `${top}px`;
            this.rightArrowEl.style.top = `${top}px`;
        },
        initScrollArrows() {
            if (this.bodyViewportEl && this.leftArrowEl && this.rightArrowEl) {
                this.queueRefreshArrows();
                return;
            }
            const bodyVp = this.$el.querySelector('.ag-body-viewport');
            if (!bodyVp) return;
            const centerVp = this.$el.querySelector('.ag-center-cols-viewport');
            this.bodyViewportEl = bodyVp;
            this.centerViewportEl = centerVp || bodyVp;
            const cs = getComputedStyle(bodyVp);
            if (cs.position === 'static') bodyVp.style.position = 'relative';
            const mk = (side) => {
                const el = document.createElement('div');
                el.className = `g-scroll-arrow g-scroll-arrow--${side}`;
                Object.assign(el.style, {
                    position: 'absolute',
                    top: '0px',
                    height: `${this.arrowHeight}px`,
                    width: `${this.arrowHeight}px`,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    zIndex: '9',
                    opacity: '0',
                    pointerEvents: 'none',
                    borderRadius: '50%',
                    background: '#e8ecfa',
                    color: '#4777FF'
                });
                if (side === 'left') el.style.left = `${this.arrowMargin}px`;
                else el.style.right = `${this.arrowMargin}px`;
                const icon = document.createElement('i');
                icon.className = side === 'left' ? 'fi fi-rr-angle-small-left' : 'fi fi-rr-angle-small-right';
                Object.assign(icon.style, { fontSize: '18px', lineHeight: '1', userSelect: 'none', pointerEvents: 'none' });
                el.appendChild(icon);
                return el;
            };
            this.leftArrowEl = mk('left');
            this.rightArrowEl = mk('right');
            bodyVp.appendChild(this.leftArrowEl);
            bodyVp.appendChild(this.rightArrowEl);
            const show = () => this.queueRefreshArrows();
            const hide = () => {
                if (this.leftArrowEl)  { this.leftArrowEl.style.opacity = '0'; this.leftArrowEl.style.pointerEvents = 'none'; }
                if (this.rightArrowEl) { this.rightArrowEl.style.opacity = '0'; this.rightArrowEl.style.pointerEvents = 'none'; }
                this.setArrowVisual(this.leftArrowEl, false);
                this.setArrowVisual(this.rightArrowEl, false);
            };
            this.onAnchorEnter = show;
            this.onAnchorLeave = hide;
            bodyVp.addEventListener('mouseenter', this.onAnchorEnter);
            bodyVp.addEventListener('mouseleave', this.onAnchorLeave);
            this.onViewportScroll = () => { this.updateArrowsVerticalPosition(); this.queueRefreshArrows(); };
            bodyVp.addEventListener('scroll', this.onViewportScroll, { passive: true });
            this.onCenterScroll = () => this.queueRefreshArrows();
            if (this.centerViewportEl) {
                this.centerViewportEl.addEventListener('scroll', this.onCenterScroll, { passive: true });
            }
            const stop = () => { this.stopAutoScroll(); this.setArrowVisual(this.leftArrowEl, false); this.setArrowVisual(this.rightArrowEl, false); };
            const startLeft = () => { this.queueRefreshArrows(); this.setArrowVisual(this.leftArrowEl, true);  this.startAutoScroll(-1) };
            const startRight = () => { this.queueRefreshArrows(); this.setArrowVisual(this.rightArrowEl, true); this.startAutoScroll(1) };
            this.leftArrowEl.addEventListener('mouseenter', startLeft);
            this.rightArrowEl.addEventListener('mouseenter', startRight);
            this.leftArrowEl.addEventListener('mouseleave', stop);
            this.rightArrowEl.addEventListener('mouseleave', stop);
            this.leftArrowEl.addEventListener('mousedown', startLeft);
            this.rightArrowEl.addEventListener('mousedown', startRight);
            document.addEventListener('mouseup', stop);
            this.arrowHandlers = { startLeft, startRight, stop };
            this.computePinnedOffsets();
            this.updateArrowsVerticalPosition();
            this.queueRefreshArrows();
        },
        teardownScrollArrows() {
            this.stopAutoScroll();
            if (this.refreshRaf) { cancelAnimationFrame(this.refreshRaf); this.refreshRaf = null; this.refreshQueued = false }
            const anchor = this.bodyViewportEl;
            if (anchor && this.onViewportScroll) anchor.removeEventListener('scroll', this.onViewportScroll);
            if (this.centerViewportEl && this.onCenterScroll) this.centerViewportEl.removeEventListener('scroll', this.onCenterScroll);
            if (anchor && this.onAnchorEnter) {
                anchor.removeEventListener('mouseenter', this.onAnchorEnter);
                anchor.removeEventListener('mouseleave', this.onAnchorLeave);
            }
            if (this.leftArrowEl && this.leftArrowEl.parentNode) this.leftArrowEl.parentNode.removeChild(this.leftArrowEl)
            if (this.rightArrowEl && this.rightArrowEl.parentNode) this.rightArrowEl.parentNode.removeChild(this.rightArrowEl)
            if (this.arrowHandlers) document.removeEventListener('mouseup', this.arrowHandlers.stop)
            this.bodyViewportEl = null
            this.centerViewportEl = null
            this.leftArrowEl = null
            this.rightArrowEl = null
            this.onViewportScroll = null
            this.onCenterScroll = null
            this.arrowHandlers = null
            this.onAnchorEnter = null
            this.onAnchorLeave = null
        },
        refreshScrollArrows() {
            const hVp = this.centerViewportEl;
            const anchor = this.bodyViewportEl;
            if (!hVp || !anchor || !this.leftArrowEl || !this.rightArrowEl) return;
            this.computePinnedOffsets();
            const max = Math.max(0, hVp.scrollWidth - hVp.clientWidth);
            const canScroll = max > 0;
            const atStart = hVp.scrollLeft <= 1;
            const atEnd = hVp.scrollLeft >= max - 1;
            this.updateArrowsVerticalPosition();
            const over = anchor.matches(':hover');
            const showLeft  = canScroll && !atStart && over;
            const showRight = canScroll && !atEnd  && over;
            this.leftArrowEl.style.opacity = showLeft ? '1' : '0';
            this.leftArrowEl.style.pointerEvents = showLeft ? 'auto' : 'none';
            this.leftArrowEl.style.cursor = showLeft ? 'pointer' : 'default';
            this.rightArrowEl.style.opacity = showRight ? '1' : '0';
            this.rightArrowEl.style.pointerEvents = showRight ? 'auto' : 'none';
            this.rightArrowEl.style.cursor = showRight ? 'pointer' : 'default';
        },
        startAutoScroll(dir) {
            this.scrollDir = dir
            if (this.scrollRaf) cancelAnimationFrame(this.scrollRaf)
            const step = () => {
                if (this.scrollDir === 0) return
                const vp = this.centerViewportEl
                if (!vp) return
                const max = Math.max(0, vp.scrollWidth - vp.clientWidth)
                let next = vp.scrollLeft + (this.scrollSpeed * this.scrollDir)
                if (next < 0) next = 0
                if (next > max) next = max
                vp.scrollLeft = next
                this.queueRefreshArrows()
                this.scrollRaf = requestAnimationFrame(step)
            }
            this.scrollRaf = requestAnimationFrame(step)
        },
        stopAutoScroll() {
            this.scrollDir = 0
            if (this.scrollRaf) { cancelAnimationFrame(this.scrollRaf); this.scrollRaf = null }
        }
    }
}
</script>

<style lang="scss" scoped>
.table_loading { opacity: 0.4; }
.table_loading_spin {
  position: absolute;
  top: 80px;
  left: 50%;
  transform: translateX(-50%);
}
.opacity_transition { transition: opacity 0.3s ease; }
.row--child { background: #f7f9fc; }
.ant-btn.table_refresh_button {
  width: 32px;
  max-width: 32px;
  max-height: 32px;
  min-width: 32px;
  height: 32px;
  min-height: 32px;
  line-height: 32px;
  flex: 0 0 32px;
  flex-shrink: 0;
  padding: 0;
  border: 0;
  border-radius: 50%;
  background: #f0f1f6;
  box-shadow: none;
  align-items: center;
  justify-content: center;
  display: inline-flex;
}
.table_refresh_button:hover,
.table_refresh_button:focus {
  background: #f0f1f6;
}
</style>

<style lang="scss">
.row--flash {
  background: rgba(255, 213, 79, 0.15) !important;
  transition: background 0.3s ease;
}
</style>
