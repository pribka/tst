<template>
    <ContentListBase
        api-url="content_item_gos24/official/"
        :title-keys="['title']"
        ordering="-publication_date"
        refresh-event="officials:refresh"
        create-event="create_official_gos24"
        edit-event="edit_official_gos24"
        edit-payload-type="official"
        delete-confirm-title="Удалить запись?"/>
</template>
<script>
import ContentListBase from '../components/content/ContentListBase.vue'
export default { name: 'OfficialList', components: { ContentListBase } }
</script>