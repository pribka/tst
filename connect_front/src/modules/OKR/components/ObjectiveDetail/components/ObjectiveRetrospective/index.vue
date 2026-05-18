<template>
    <Retrospective
        wrapperClass="objective-retro"
        :plusesBlockLabel="$t('okr.whatWeAchieved')"
        :minusesBlockLabel="$t('okr.existingProblems')"
        :ideasBlockLabel="$t('okr.nextSteps')"
        :related_object="objective" />
</template>
<script>
import Retrospective from '@/components/Retrospective'
import { mapState } from 'vuex'
 
export default {
    name: 'ObjectiveRetrospective',
    components: {
        Retrospective
    },
    computed: {
        ...mapState({
            objective: state => state.okr.objectiveDetail
        })
    }
}
</script>
<style lang="scss">
.objective-retro {
    height: 100%;
    .retrospective {
        min-height: 100%;
        width: 100%;
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        .item_card {
            max-width: unset;
        }
    }
}
</style>