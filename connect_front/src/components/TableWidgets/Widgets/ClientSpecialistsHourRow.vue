<template>
    <div>
        {{ text }} ч.
    </div>
</template>

<script>
export default {
    props: {
        main: {
            type: Boolean,
            default: false
        },
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