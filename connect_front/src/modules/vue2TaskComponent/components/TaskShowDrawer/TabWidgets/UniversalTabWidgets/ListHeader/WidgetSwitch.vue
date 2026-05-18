<template>
    <component 
        :is="itemWidget" 
        :task="task" 
        :item="item" />
</template>

<script>
import headerMixins from './headerMixins.js'
export default {
    mixins: [
        headerMixins
    ],
    computed: {
        itemWidget() {
            return () => import(`./${this.item}.vue`)
                .then(module => {
                    return module
                })
                .catch(e => {
                    console.log('error')
                    return import(`./NotWidget.vue`)
                })
        }
    }
}
</script>