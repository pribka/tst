<template>
    <ContentListBase
        api-url="content_item_gos24/partition/"
        :title-keys="['name','title']"
        subtitle-field="code"
        ordering="name"
        refresh-event="partition:refresh"
        create-event="create_partition_gos24"
        edit-event="edit_partition_gos24"
        edit-payload-type="partition"
        delete-confirm-title="Удалить запись?"/>
</template>
<script>
import ContentListBase from '../components/content/ContentListBase.vue'
export default { name: 'PartitionList', components: { ContentListBase } }
</script>