<template>
    <Support />
</template>

<script>
export default {
    name: 'HeaderSupport',
    components: {
        Support: () => import('@apps/Support/components/HeaderBtn.vue')
    }
}
</script>