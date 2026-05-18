<template>
    <UserInfo />
</template>

<script>
export default {
    components: {
        UserInfo: () => import('./Registration/UserInfo.vue')
    }
}
</script>