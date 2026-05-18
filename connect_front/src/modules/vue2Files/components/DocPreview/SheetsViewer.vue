<template>
    <iframe :src="`https://docs.google.com/gview?url=https:${file.path}&embedded=true`" width="100%" height="100%"></iframe>
</template>

<script>
export default {
    props: {
        file: {
            type: Object,
            required: true
        }
    }
}
</script>
