<template>
    <component
        :is="actionComponent"
        :id="id"
        :record="record"
        :toggleChildren="toggleChildren"
        :expanded="expanded"
        :pageName="pageName" />
</template>

<script>
export default {
    props: {
        id: {
            type: [String, Number],
            required: true
        },
        record: {
            type: Object,
            required: true
        },
        toggleChildren: {
            type: Function,
            default: () => {}
        },
        expanded: {
            type: Number,
            default: null
        },
        pageName: {
            type: String,
            default: ''
        }
    },
    computed: {
        isMobile() {
            return this.$store.state.isMobile
        },
        actionComponent() {
            if(this.isMobile)
                return () => import(/* webpackMode: "lazy" */'./Drawer.vue')
            else
                return () => import(/* webpackMode: "lazy" */'./List.vue')
        }
    }
}
</script>