<template>
    <div>
        {{ record.name }}
    </div>
</template>

<script>
export default {
    props: {
        record: {
            type: Object,
            default: () => null
        }
    }
}
</script>