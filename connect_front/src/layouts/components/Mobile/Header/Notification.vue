<template>
    <Bell/>
</template>

<script>
export default {
    components: {
        Bell: () => import('@apps/Notifications/views/Bell')
    }
}
</script>