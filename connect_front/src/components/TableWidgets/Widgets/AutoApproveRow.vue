<template>
    <i v-if="record.auto_approve" class="fi fi-rr-checkbox"></i>
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