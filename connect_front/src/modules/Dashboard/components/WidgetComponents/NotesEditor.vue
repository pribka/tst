<template>
    <CKEditor v-model="text" initFocus />
</template>

<script>
export default {
    props: {
        widget: {
            type: Object,
            required: true
        }
    },
    components: {
        CKEditor: () => import('@apps/CKEditor')
    },
    data() {
        return {
            text: ''
        }
    },
    created() {
        this.text = this.widget.random_html
    }
}
</script>