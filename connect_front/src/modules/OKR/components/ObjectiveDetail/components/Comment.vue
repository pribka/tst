<template>
    <div class="comment">
        <!-- <div class="label">Комментарии</div> -->
        <div class="label">{{ $t('comments') }}</div>
        <vue2CommentsComponent
            class="comment-list"
            :related_object="objective.id" />
    </div>
</template>
<script>
import {  mapState } from 'vuex'
import vue2CommentsComponent from '@apps/vue2CommentsComponent'

export default {
    name: 'Comment',
    components: {
        vue2CommentsComponent
    },
    computed: {
        ...mapState({
            objective: state => state.okr.objectiveDetail
        })
    },

}
</script>
<style lang="scss" scoped>
.comment {
    flex: 1;
    min-height: 0;
    display: flex;
    flex-direction: column;
    gap: 10px;
    height: 100%;
    .label {
        font-weight: 400;
        font-size: 14px;
        line-height: 100%;
    }
    .comment-list {
        flex: 1;
        overflow-y: auto;
        overflow-x: hidden;
        width: 100%;
        padding-right: 1px;
    }
}
</style>