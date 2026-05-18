<template>
    <div>
        <i v-if="record.is_result" class="fi fi-rr-check text_green" />
    </div>
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