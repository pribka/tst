<template>
    <a-textarea
        v-model="form[field.key]"
        :size="field.size" 
        :auto-size="field.autoSIze"/>
</template>

<script>
import fieldData from './mixins.js'
export default {
    mixins: [fieldData]
}
</script>