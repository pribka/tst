<template>
    <div :id="`field_${field.key}`">
        <a-form-model-item 
            :ref="field.key" 
            :label="field.name"
            class="form_item"
            :prop="field.key"
            :rules="field.rules">
            <UserDrawer
                v-model="form[field.key]"
                inputSize="large"
                :filters="field.params ? field.params : {}"
                :multiple="field.multiple ? true : false"
                :apiPath="field.apiPath ? field.apiPath : '/user/list_by_task/'"
                :title="field.name" />
        </a-form-model-item>
    </div>
</template>

<script>
import UserDrawer from '../../UserDrawer'
export default {
    components: {
        UserDrawer
    },
    props: {
        field: {
            type: Object,
            required: true
        },
        form: {
            type: Object,
            required: true
        }
    },
    data() {
        return {
            loading: false,
            list: []
        }
    }
}
</script>