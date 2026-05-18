<template>
    <div>
        <a-form-model-item
            v-if="formInfo.priority"
            :rules="formInfo.priority.rules"
            class="mb-0"
            style="margin-bottom: 0px;"
            prop="priority">
            <Priority
                v-model="value.priority"
                :key="edit || visible"/>
        </a-form-model-item>
    </div>
</template>

<script>
export default {
    components: { 
        Priority: () => import("../../Priority.vue")
    },
    props: {
        value: { // form
            type: Object,
            required: true
        },
        formInfo: {
            type: Object,
            required: true
        },
        edit: {
            type: Boolean,
            required: true
        },
        visible: {
            type: Boolean,
            required: true
        },
    },
    data() {
        return {
        }
    },
    methods: {
    }
}
</script>
