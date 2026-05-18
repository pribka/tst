<template>
    <ContentListBase
        api-url="content_item_gos24/tag/"
        :title-keys="['name','title']"
        ordering="name"
        refresh-event="tag:refresh"
        create-event="create_tag_gos24"
        edit-event="edit_tag_gos24"
        edit-payload-type="tag"
        delete-confirm-title="Удалить запись?"/>
</template>
<script>
import ContentListBase from '../components/content/ContentListBase.vue'
export default { name: 'TagList', components: { ContentListBase } }
</script>