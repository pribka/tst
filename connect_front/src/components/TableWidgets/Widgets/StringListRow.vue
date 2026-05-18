<template>
    <div>
        {{ cellText }}
    </div>
</template>

<script>
export default {
    props: {
        text: {
            type: [String, Number, Boolean, Object, Array]
        },
        record: {
            type: Object
        },
        model: {
            type: String
        },
        column: {
            type: Object
        },
    },
    computed: {
        cellText() {
            return this?.text?.join(', ') || ''
        },
    }
}
</script>