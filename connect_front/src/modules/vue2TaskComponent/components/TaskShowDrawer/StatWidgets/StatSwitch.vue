<template>
    <component 
        :is="statWidget" 
        :task="task" 
        :stat="stat" />
</template>

<script>
import statMixins from './statMixins.js'
export default {
    mixins: [
        statMixins
    ],
    computed: {
        statWidget() {
            return () => import(`./${this.stat.component}.vue`)
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