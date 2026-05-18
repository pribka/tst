<template>
    <div v-if="text.length">
        <div class="funding-sources" v-for="(source, index) in text" :key="index">
            {{ source.funding_source.short_name }} - {{ source.amount }} млн. тенге
        </div>
    </div>
    <div v-else class="no-data">
        Не указан
    </div>
</template>

<script>
export default {
    // Источники финансирования инвестиционных проектов
    props: {
        text: {
            type: Array,
            default: () => []
        },
    }
}
</script>
<style lang="scss" scoped>
.no-data{
    color: rgb(185, 185, 185);
}
</style>