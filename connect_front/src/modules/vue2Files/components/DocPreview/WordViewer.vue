<template>
    <div>
        {{ $t('files.no_widget') }}
    </div>
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
