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
    },
    created () {
        if(this.form?.[this.field.key]) {
            const files = JSON.parse(JSON.stringify(this.form[this.field.key]))
            this.fileList = files.map((item) => {
                return {
                    uid: item.id,
                    name: item.name,
                    status: 'done',
                    url: item.path,
                }
            })
        }
    }
}
</script>