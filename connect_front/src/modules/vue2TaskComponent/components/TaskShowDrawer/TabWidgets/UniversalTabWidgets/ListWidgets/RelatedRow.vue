<template>
    <span>
        {{ widgetRender }}
    </span>
</template>

<script>
import widgetMixins from './widgetMixins.js'
export default {
    mixins: [
        widgetMixins
    ],
    computed: {
        widgetRender() {
            return this.item?.[this.column.string_view] ? this.item[this.column.string_view] : ''
        }
    }
}
</script>
