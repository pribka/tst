<template>
    <div>
        {{ tarrifs }}
    </div>
</template>

<script>
export default {
    props: {
        text: {
            type: [String, Number, Boolean, Object, Array],
            default: () => []
        },
    },
    computed: {
        tarrifs() {
            return this.text.join(', ')
        }
    }
}
</script>
