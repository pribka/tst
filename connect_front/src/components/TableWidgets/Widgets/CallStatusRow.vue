<template>
    <a-tag :color="record?.status?.color || 'default'" block size="large">
        {{ record?.status?.name || "" }}
    </a-tag>
</template>

<script>
export default {
    props: {
        record: {
            type: Object,
            required: true
        }
    }
}
</script>
