<template>
    <div class="h-full flex items-center">
        <Members 
            :item="{ users: record.visors }" />
    </div>
</template>

<script>
export default {
    props: {
        record: {
            type: Object,
            required: true
        },
        model: {
            type: String
        },
    },
    components: {
        Members: () => import('../components/Members.vue')
    }
}
</script>