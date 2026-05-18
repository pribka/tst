<template>
    <div class="obj-list">
        <ListItem
            v-for="objective in objectives"
            :key="objective.id"
            :objective="objective" />
        <a-empty v-if="!objectives.length" :description="false" />
    </div>
</template>
<script>
import { mapState } from 'vuex'
export default {
    name: 'List',
    components: {
        ListItem: () => import('./components/ListItem.vue')
    },
    computed: {
        ...mapState({
            objectives: state => state.okr.objectives
        }),
    }

}
</script>
<style lang="scss" scoped>
.obj-list {
    height: 100%;
    width: 100%;
    flex: 1;
    overflow: auto;
    display: flex;
    flex-direction: column;
    gap: 12px;
}
</style>