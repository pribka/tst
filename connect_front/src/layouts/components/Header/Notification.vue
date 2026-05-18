<template>
    <Bell/>
</template>

<script>
export default {
    name: 'HeaderNotification',
    components: {
        Bell: () => import('@apps/Notifications/views/Bell')
    }
}
</script>