<template>
    <ContentListBase
        api-url="content_item_gos24/organ/"
        :title-keys="['title']"
        ordering="title"
        refresh-event="organ:refresh"
        create-event="create_organ_gos24"
        edit-event="edit_organ_gos24"
        edit-payload-type="organ"
        delete-confirm-title="Удалить запись?"/>
</template>
<script>
import ContentListBase from '../components/content/ContentListBase.vue'
export default { name: 'OrganList', components: { ContentListBase } }
</script>