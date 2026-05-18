<template>
    <Calendar />
</template>

<script>
export default {
    components: {
        Calendar: () => import('@apps/Calendar/components/NavCalendar/index.vue')
    }
}
</script>