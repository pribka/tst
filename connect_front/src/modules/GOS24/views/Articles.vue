<template>
    <ContentListBase
        api-url="content_item_gos24/article/"
        :title-keys="['title','name']"
        ordering="-publication_date"
        refresh-event="articles:refresh"
        create-event="create_article_gos24"
        edit-event="edit_article_gos24"
        edit-payload-type="article"
        delete-confirm-title="Удалить статью?"/>
</template>
<script>
import ContentListBase from '../components/content/ContentListBase.vue'
export default { name: 'ArticlesList', components: { ContentListBase } }
</script>