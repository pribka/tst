<template>
    <div class="order_block">
        <h2 v-if="showTitle">Комментарии</h2>
        <vue2CommentsComponent
            bodySelector=".order_body"
            :related_object="id"
            model="order"
            @added="$emit('added')" />
    </div>
</template>

<script>
export default {
    components: {
        vue2CommentsComponent: () => import('@apps/vue2CommentsComponent')
    },
    props: {
        id: {
            type: [String, Number],
            required: true
        },
        showTitle: {
            type: Boolean,
            default: true
        }
    }
}
</script>