<template>
    <HelpDeskRequest />
</template>

<script>
export default {
    components: {
        HelpDeskRequest: () => import('@apps/HelpDesk/views/Request/indexMobile.vue')
    }
}
</script>