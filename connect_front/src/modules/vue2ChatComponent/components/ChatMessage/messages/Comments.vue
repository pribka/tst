<template>
    <CommentItem 
        :user="user"
        useShare
        related_object="share"
        :item="messageItem.share" />
</template>

<script>
import { mapState } from 'vuex'
export default {
    props: {
        messageItem: {
            type: Object,
            required: true
        }
    },
    computed: {
        ...mapState({
            user: state => state.user.user
        })
    },
    components: {
        CommentItem: () => import('@apps/vue2CommentsComponent/CommentItem.vue')
    }
}
</script>

<style lang="scss" scoped>
::v-deep{
    .comment_item{
        color: var(--text);
    }
}
</style>