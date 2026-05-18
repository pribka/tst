<template>
    <Profiler 
        :user="item" 
        :showAvatar="!isMobile"
        :subtitle="!isMobile && {text: $t('task.author'), class: 'font-light text-xs'}" />
</template>

<script>
import widgetMixins from './widgetMixins.js'
export default {
    mixins: [
        widgetMixins
    ],
    computed: {
        isMobile() {
            return this.$store.state.isMobile
        }
    }
}
</script>