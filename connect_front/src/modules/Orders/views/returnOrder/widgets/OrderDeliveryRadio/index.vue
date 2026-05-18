<template>
    <div class="form">
        <a-radio-group
            v-if="item.radio && item.radio.length"
            v-model="form[item.key]"
            class="w-full"
            :class="isMobile || 'flex'">
            <div 
                v-for="radio in item.radio" 
                :key="radio.key" 
                class="radio_item"
                :class="isMobile && 'radio_item_mobile'">
                <a-radio :value="radio.value">
                    {{ radio.name }}
                </a-radio>
            </div>
        </a-radio-group>
        <template v-if="item.fields && item.fields.length">
            <template v-for="field in item.fields">
                <div 
                    v-if="form[item.key] === field.requireRadio" 
                    :key="field.widget" 
                    class="del_item mt-4">
                    <FieldsSwitch 
                        :field="field" 
                        :form="form" />
                </div>
            </template>
        </template>
    </div>
</template>

<script>
import FieldsSwitch from './fields/FieldsSwitch.vue'
export default {
    components: {
        FieldsSwitch
    },
    computed: {
        isMobile() {
            return this.$store.state.isMobile
        }
    },
    props: {
        item: {
            type: Object,
            required: true
        },
        form: {
            type: Object,
            required: true
        }
    }
}
</script>

<style lang="scss" scoped>
.radio_item{
    &:not(:last-child){
        margin-right: 20px;
    }
}
.radio_item_mobile {
    &:not(:last-child){
        margin: 0;
        margin-bottom: 8px;
    }
}
</style>