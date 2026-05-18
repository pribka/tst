<template>
    <a-button 
        type="link" 
        ghost 
        icon="fi-rr-search-alt"
        :disabled="!file_viewing_is_available" 
        flaticon
        @click="clickHandler" />
</template>

<script>
export default {
    props: {
        record: {
            type: Object,
            required: true
        },
    },
    computed: {
        file_viewing_is_available() {
            return this.record.file_viewing_is_available
        }
    },
    methods: {
        clickHandler() {
            let query = Object.assign({}, this.$route.query)
            if(!query.consolidated_report) {
                query.consolidated_report = this.record.id
                this.$router.push({query})
            }
        }
    }
}
</script>