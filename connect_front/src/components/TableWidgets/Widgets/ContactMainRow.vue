<template>
    <div v-if="record.is_main">
        <i class="fi fi-rr-check text_green" />
    </div>
</template>

<script>
export default {
    props: {
        record: {
            type: Object
        }
    }

}
</script>