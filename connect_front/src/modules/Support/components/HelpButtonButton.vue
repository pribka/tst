<template>
    <a-button 
        v-tippy
        :content="$t('support.work_use')"
        flaticon
        icon="fi-rr-interrogation"
        type="ui"
        @click="open()" />
</template>

<script>
export default {
    props: {
        partType: {
            type: String,
            default: 'sections'
        },
        partCode: {
            type: String,
            required: true
        },
        type: {
            type: String,
            default: 'text'
        }
    },
    computed: {
        isMobile() { 
            return this.$store.state.isMobile
        }
    },
    methods: {
        open() {
            const query = this.$route.query
            this.$router.replace({ query: { ...query, help: true, [this.partType]: this.partCode }})
        }
    }
}
</script>