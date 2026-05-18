<template>
    <ul class="">
        <FieldTreeNode
            v-for="(node, index) in fields"
            :checkedFields="checkedFields"
            :key="index"
            :node="node"
            :loadData="loadData"
            @add="handleAdd"/>
    </ul>
</template>

<script>
export default {
    name: 'FieldTree',
    props: {
        fields: {
            type: Array,
            required: true,
        },
        checkedFields: {
            type: Array,
            default: () => [],
        },
        loadData: {
            type: Function,
            default: () => {},
        },
    },
    components: {
        FieldTreeNode: () => import('./FieldTreeNode.vue')
    },
    methods: {
        handleAdd(node) {
            this.$emit('add', node);
        },
    },
};
</script>

<style scoped>
.field-tree {
  list-style: none;
  margin: 0;
}
</style>
