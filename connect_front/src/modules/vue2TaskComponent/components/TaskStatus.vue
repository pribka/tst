<template>
    <a-tag :color="status.color === 'default' ? '' : status.color">
        {{ status.name }}
    </a-tag>
</template>

<script>
export default {
    props: {
        status: {
            type: Object,
            default: () => null
        }
    }
}
</script>
