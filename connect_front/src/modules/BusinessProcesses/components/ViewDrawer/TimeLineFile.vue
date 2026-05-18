<template>
    <div class="file_item">
        <a 
            v-if="file.is_image" 
            class="file_wrap lht_l" 
            :href="file.path">
            <img
                :src="file.path" 
                :alt="file.name" />
        </a>
        <a 
            v-else
            :href="file.path"
            target="_blank"
            class="file_wrap">
            <div class="file_doc">
                <a-icon type="file" />
                <span>{{ $t('file') }}</span>
            </div>
        </a>
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