<template>
    <a-button 
        flaticon
        icon="fi-rr-interrogation"
        type="flat"
        class="hlp_mobile"
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
    methods: {
        open() {
            const query = this.$route.query
            this.$router.replace({ query: { ...query, help: true, [this.partType]: this.partCode }})
        }
    }
}
</script>

<style lang="scss" scoped>
.hlp_mobile{
    box-shadow: initial;
}
</style>