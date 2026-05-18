<template>
    <iframe v-if="file" :src="file.path" width="100%" height="100%">
        {{ $t('files.browser_not_support_frames') }}
    </iframe>
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