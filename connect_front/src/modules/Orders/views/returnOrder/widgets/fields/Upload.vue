<template>
    <Upload
        v-model="form[field.key]"
        :defaultList="fileList"
        :limit="field.limit"
        :multiple="field.multiple" />
</template>

<script>
import fieldData from './mixins.js'
import Upload from '@apps/Upload'
export default {
    mixins: [fieldData],
    components: {
        Upload
    },
    data() {
        return {
            fileList: []
        }
    }
}
</script>