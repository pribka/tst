<template>
    <div v-if="text">
        <i class="fi fi-rr-check text_green" />
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