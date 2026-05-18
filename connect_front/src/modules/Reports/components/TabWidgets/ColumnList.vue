<template>
    <draggable
        :value="list"
        :options="dragOptions"
        :element="'div'"
        @change="draggableChange"
        class="columns-list">
        <ColumnListItem
            v-for="(el, index) in list"
            :key="getItemKey(el, index)"
            :item="el"
            :itemIndex="index"
            class="mb-4">
            <template slot="grab">
                <div class="drag-handle w-8 h-8 grab-icon">
                    <i class="fi fi-rr-grip-dots-vertical text-sm"></i>
                </div>
            </template>
        </ColumnListItem>
    </draggable>
</template>

<script>
export default {
    components: {
        draggable: () => import('vuedraggable'),
        ColumnListItem: () => import('./ColumnListItem.vue')
    },
    computed: {
        list() {
            return this.$store.state.reports.activeTemplate.metadata.columns
        }
    },
    data() {
        return {
            dragOptions: {
                handle: '.drag-handle',
                group: 'shared',
                ghostClass: 'drag-ghost',
                chosenClass: 'drag-chosen',
                dragClass: 'drag-dragging',
            },
        }
    },
    methods: {
        getItemKey(item, index) {
            return `${item.name}-${item.order ?? index}-${item.aggregate ? 'aggregate' : 'field'}`
        },
        draggableChange(event) {
            if (event.moved) {
                const newList = JSON.parse(JSON.stringify(this.list))
                const [movedItem] = newList.splice(event.moved.oldIndex, 1)
                newList.splice(event.moved.newIndex, 0, movedItem)
                this.$store.commit('reports/SET_LIST', {
                    key: 'columns',
                    list: newList
                })
                this.$store.commit('reports/REORDER_COLUMN_LIST')
            }
        }
    }
}
</script>

<style lang="scss" scoped>
.grab-icon {
    display: flex;
    justify-content: center;
    align-items: center;
    cursor: grab
}
</style>
