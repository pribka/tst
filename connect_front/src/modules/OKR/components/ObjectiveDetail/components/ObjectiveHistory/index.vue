<template>
    <History
        class="objective-history"
        :related_object="objective.id"
        :modelLabel="model" />
</template>

<script>
import History from '@apps/History/index.vue'
import { mapState } from 'vuex'

export default {
    name: "ObjectiveHistory",
    components: {
        History
    },
    computed: {
        ...mapState({
            objective: state => state.okr.objectiveDetail,
            model: state => state.okr.model,
        })
    }
}
</script>
<style lang="scss" scoped>
.objective-history {
    height: 100%;
    &::v-deep {
        .timeline {
            padding-left: 5px;
        }
    }
}
</style>