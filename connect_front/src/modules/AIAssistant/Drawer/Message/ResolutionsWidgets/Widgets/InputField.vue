<template>
    <div>
        <a-input 
            v-if="isEdit"
            v-model="value" 
            inputType="ghost"
            class="wdg_input"
            @change="inputChange" />
        <div v-else>
            {{ value }}
        </div>
    </div>
</template>

<script>
import props from '../props.js'
import mixins from './mixins.js'
export default {
    props: {...props},
    mixins: [mixins],
    data() {
        return {
            value: ""
        }
    },
    created() {
        if(this.intents.resolutions?.[this.widgetKey]?.value) {
            this.value = this.intents.resolutions[this.widgetKey].value
        }
    }
}
</script>

<style lang="scss" scoped>
.wdg_input{
    &.ant-input{
        padding-top: 0px;
        padding-bottom: 0px;
        height: initial;
    }
}
</style>