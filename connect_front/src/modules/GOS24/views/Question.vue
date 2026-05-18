<template>
    <ContentListBase
        api-url="content_item_gos24/question/"
        :title-keys="['title']"
        ordering="-id"
        refresh-event="questions:refresh"
        create-event="create_question_gos24"
        edit-event="edit_question_gos24"
        edit-payload-type="qa"
        delete-confirm-title="Удалить запись?"/>
</template>
<script>
import ContentListBase from '../components/content/ContentListBase.vue'
export default { name: 'QuestionList', components: { ContentListBase } }
</script>