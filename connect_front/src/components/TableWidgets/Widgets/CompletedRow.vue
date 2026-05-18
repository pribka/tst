<template>
    <div v-if="text"></div>
    <a-tag v-else :color="statusColor">
        {{ statusText }}
    </a-tag>
</template>

<script>
export default {
    props: {
        text: {
            type: [Object, Boolean, String, Array]
        },
    },
    computed: {
        statusText() {
            return this.text ? this.$t('completed') : this.$t('returned')
        },
        statusColor() {
            return this.text ? 'green' : 'red'
        }
    }
}
</script>

<style lang="scss" scoped>
</style>