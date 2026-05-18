<template>
    <Effects :item="record" />
</template>


<script>
export default {
    props: {
        record: {
            type: Object,
            required: true
        },
    },
    components: {
        Effects: () => import('../components/Effects.vue')
    }
}
</script>