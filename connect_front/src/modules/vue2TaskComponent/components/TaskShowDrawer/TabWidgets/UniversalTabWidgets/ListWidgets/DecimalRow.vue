<template>
    <span>
        {{ valueFormat }}
    </span>
</template>

<script>
import widgetMixins from './widgetMixins.js'
export default {
    mixins: [
        widgetMixins
    ],
    computed: {
        valueFormat(){
            return this.item ? this.item.toString().replace(/(\d)(?=(\d{3})+(?!\d))/g, "$1 ").replace(',', '.') : ''
        }
    }
}
</script>