<template>
    <div ref="groupLightWrap">
        <Files
            :sourceId="task.id"
            :isFounder="isOperator || isAuthor"
            widgetEmbed
            isStudent />
    </div>
</template>

<script>
export default {
    name: "TaskFiles",
    props: {
        task: {
            type: Object,
            required: true
        },
        id: {
            type: [String, Number],
            default: null
        },
        isOperator: {
            type: Boolean,
            required: true
        },
        isAuthor: {
            type: Boolean,
            required: true
        },
    },
    components: {
        Files: () => import('@apps/vue2Files')
    }
   
}
</script>