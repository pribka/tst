<template>
    <div v-if="text">
        {{ $moment(text).format('DD.MM.YYYY') }}
    </div>
</template>

<script>
export default {
    props: {
        text: {
            type: [String, Number, Boolean, Object]
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
    }
}
</script>