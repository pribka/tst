<template>
    <draggable
        :value="list"
        :options="dragOptions"
        :element="'div'"
        @change="draggableChange"
        class="columns-list">
        <GroupingListItem
            v-for="el in list"
            :key="el.name"
            :item="el"
            class="mb-4">
            <template slot="grab">
                <div class="mr-2 drag-handle w-8 h-8 grab-icon">
                    <i class="fi fi-rr-grip-dots-vertical text-sm"></i>
                </div>
            </template>
        </GroupingListItem>
    </draggable>
</template>

<script>
import draggable from 'vuedraggable'

export default {
    components: {
        GroupingListItem: () => import('./GroupingListItem.vue'),
        draggable
    },
    computed: {
        list() {
            return this.$store.state.reports.activeTemplate.metadata.grouping
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
        draggableChange(event) {
            if (event.moved) {
                const newList = JSON.parse(JSON.stringify(this.list))
                const [movedItem] = newList.splice(event.moved.oldIndex, 1)
                newList.splice(event.moved.newIndex, 0, movedItem)
                this.$store.commit('reports/SET_LIST', {
                    key: 'grouping',
                    list: newList
                })
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