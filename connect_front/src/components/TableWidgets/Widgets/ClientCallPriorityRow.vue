<template>
    <div>
        {{ record.call_priority ?? text ?? '-' }}
    </div>
</template>

<script>
export default {
    props: {
        record: {
            type: Object,
            required: true
        },
        text: {
            type: [Object, Number, String],
        }
    }
}
</script>
