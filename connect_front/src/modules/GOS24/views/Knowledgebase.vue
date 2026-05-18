<template>
    <ContentListBase
        api-url="content_item_gos24/knowledgebase/"
        :title-keys="['title']"
        ordering="-id"
        refresh-event="knowledgebase:refresh"
        create-event="create_knowledgebase_gos24"
        edit-event="edit_knowledgebase_gos24"
        edit-payload-type="knowledgebase"
        delete-confirm-title="Удалить запись?"/>
</template>
<script>
import ContentListBase from '../components/content/ContentListBase.vue'
export default { name: 'KnowledgebaseList', components: { ContentListBase } }
</script>