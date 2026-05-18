<template>
    <div @click="changeSort">
        <div class="flex items-center" :class="[active && 'blue_color', isSortable && 'cursor-pointer']">
            {{ params.displayName }}
            <template v-if="active">
                <i class="ml-1 fi srt_ar" :class="`fi-rr-arrow-${sortDirection === 'asc' ? 'down' : 'up'}`"></i>
            </template>
        </div>
    </div>
</template>

<script>
export default {
    data() {
        return {
            sortDirection: null,
            active: null,
            isSortable: false
        }
    },
    mounted() {
        this.isSortable = !!this.params.column?.getColDef()?.sortable
        this.updateFromOrdering()
    },
    methods: {
        currentOrdering() {
            if (typeof this.params.getOrdering === 'function') return this.params.getOrdering()
            const parent = this.params.context && this.params.context.parent
            return parent && parent.tableInfo ? parent.tableInfo.ordering : null
        },
        updateFromOrdering() {
            let ordering = this.currentOrdering()
            if (ordering && ordering[0] === '-') {
                ordering = ordering.slice(1)
                this.sortDirection = 'desc'
            } else if (ordering) {
                this.sortDirection = 'asc'
            } else {
                this.sortDirection = null
            }
            this.active = (this.params.column?.getColId?.() === ordering)
        },
        changeSort() {
            if (!this.isSortable) return
            let next
            if (!this.active) next = 'asc'
            else if (this.sortDirection === 'asc') next = 'desc'
            else if (this.sortDirection === 'desc') next = null
            else next = 'asc'
            this.params.changeSort(this.params.column.getColId(), next)
        },
        refresh(params) {
            this.params = params
            this.isSortable = !!this.params.column?.getColDef()?.sortable
            this.updateFromOrdering()
            return true
        }
    }
}
</script>