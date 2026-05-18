<template>
    <ContentListBase
        api-url="content_item_gos24/news_publications/"
        :title-keys="['title']"
        image-field="image"
        ordering="-publication_date"
        refresh-event="news:refresh"
        create-event="create_news_gos24"
        edit-event="edit_news_gos24"
        edit-payload-type="news_publications_gos24"
        delete-confirm-title="Удалить новость?"/>
</template>
<script>
import ContentListBase from '../components/content/ContentListBase.vue'
export default { name: 'NewsPublications', components: { ContentListBase } }
</script>