<template>
    <div v-if="text">
        <div class="status" :style="`background-color: ${text.hex_color}`">
            {{ text.name }}
        </div>
    </div>
    <div v-else class="no-data">
        Не указан
    </div>
</template>

<script>
export default {
    // Статус инвестиционного проекта
    props: {
        text: {
            type: Object,
            default: () => {}
        },
    }
}
</script>
<style lang="scss" scoped>
.status{
    min-height: 36px;
    width: 120px;
    font-size: 14px;
    font-weight: 400;
    line-height: 15.4px;
    text-align: center;
    color: rgba(255, 255, 255, 1);
    padding: 10px;
    border-radius: 4px;
    display: flex;
    align-items: center;
    justify-content: center;
}
.no-data{
    color: rgb(185, 185, 185);
}
</style>