<template>
    <ContentListBase
        api-url="content_item_gos24/news_finance/"
        :title-keys="['title']"
        image-field="image"
        ordering="-publication_date"
        refresh-event="news_finance:refresh"
        create-event="create_news_finance"
        edit-event="edit_news_finance"
        edit-payload-type="news_finance"
        delete-confirm-title="Удалить?"/>
</template>
<script>
import ContentListBase from '../components/content/ContentListBase.vue'
export default { name: 'NewsPublications', components: { ContentListBase } }
</script>