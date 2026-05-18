<template>
    <ContentListBase
        api-url="content_item_gos24/webinar/"
        :title-keys="['title']"
        ordering="-planned_date"
        refresh-event="webinars:refresh"
        create-event="create_webinar_gos24"
        edit-event="edit_webinar_gos24"
        edit-payload-type="webinar"
        delete-confirm-title="Удалить запись?"/>
</template>
<script>
import ContentListBase from '../components/content/ContentListBase.vue'
export default { name: 'WebinarList', components: { ContentListBase } }
</script>