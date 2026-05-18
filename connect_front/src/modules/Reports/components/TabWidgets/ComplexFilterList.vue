<template>
    <draggable
        :options="dragOptions"
        tag="div"
        :list="list"
        :value="value"
        @input="emitter">
        <div :key="el.id" v-for="el in realValue">
            <template v-if="el.filters">
                <div class="item mb-1">
                    <div class="flex items-center">
                        <div class="drag-handle w-8 h-8 grab-icon">
                            <i class="fi fi-rr-grip-dots-vertical text-sm"></i>
                        </div>
                        <div class="flex items-center">
                            <div class="">{{ $t('reports_mobule.group') }}</div>
                        </div>
                    </div>
                    <GroupLogicField
                        :parentPath="parentPath"
                        :item="el" />
                    <a-button 
                        type="ui" 
                        ghost
                        shape="circle"
                        class="text_red" 
                        flaticon
                        icon="fi-rr-trash"
                        @click="removeGroup(el)">
                    </a-button>
                </div>
                <ComplexFilterList 
                    class="ml-[30px]" 
                    :list="el.filters" 
                    :parentPath="parentPath.concat(el.id)" />
            </template>
            <template v-else>
                <ComplexFilterListItem :item="el" :parentPath="parentPath">
                    <template slot="grab">
                        <div class="shrink-0 mx-1 drag-handle w-8 h-8 grab-icon">
                            <i class="fi fi-rr-grip-dots-vertical text-sm"></i>
                        </div>
                    </template>
                </ComplexFilterListItem>
            </template>
        </div>
    </draggable>
</template>

<script>
import draggable from 'vuedraggable';
export default {
    name: 'ComplexFilterList',
    components: { 
        draggable,
        ComplexFilterListItem: () => import('./ComplexFilterListItem.vue'),
        GroupLogicField: () => import('../ComplexFilterWidgets/GroupLogicField.vue')
    },
    props: {
        value: {
            required: false,
            type: Array,
            default: null
        },
        list: {
            required: false,
            type: Array,
            default: null
        },
        parentPath: {
            required: true,
            type: Array
        }
    },
    computed: {
        dragOptions() {
            return {
                animation: 0,
                handle: '.drag-handle',
                group: 'nested',
                disabled: false,
                ghostClass: "ghost"
            };
        },
        // this.value when input = v-model
        // this.list  when input != v-model
        realValue() {
            return this.value || this.list;
        },
    },
    methods: {
        emitter(value) {
            this.$emit("input", value);
        },
        removeGroup(el) {
            this.$store.commit('reports/REMOVE_COMPLEX_FILTER_FIELD', { 
                path: [...this.parentPath, el.id], 
            })
        }
    }
};
</script>

<style scoped>
.item {
    display: grid;
    gap: 12px;
    align-items: center;
    grid-template-columns: 1fr 2fr 50px;
    
    padding: 8px 12px;
    border-radius: 8px;
    background-color: #fff;
}
.item__grid {
}

.grab-icon {
    display: flex;
    justify-content: center;
    align-items: center;
    cursor: grab
}
.ghost {
}
</style>
