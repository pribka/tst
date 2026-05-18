<template>
    <div class="form">
        <template v-if="item.fields && item.fields.length">
            <a-form-model-item
                v-for="field in item.fields"
                :key="field.key"
                :ref="field.key" 
                :label="field.name"
                :rules="field.rules"
                class="form_item"
                :prop="field.key">
                <FieldSwitch 
                    :item="item" 
                    :form="form" 
                    :field="field" />
            </a-form-model-item>
        </template>
    </div>
</template>

<script>
import FieldSwitch from './fields/FieldSwitch.vue'
export default {
    components: {
        FieldSwitch
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