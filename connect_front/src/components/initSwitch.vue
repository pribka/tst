<template>
    <component :is="initWidget"/>
</template>

<script>
export default {
    name: 'MainInitSwitch',
    props: {
        folder: {
            type: String,
            required: true
        }
    },
    computed: {
        initWidget() {
            return () => import(/* webpackMode: "lazy" */`@apps/${this.folder}/init`)
                .then(module => {
                    return module
                })
                .catch(e => {
                    console.error('error', this.folder)
                    return null
                })
        } 
    }
}
</script>