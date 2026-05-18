<template>
    <div class="year_day">
        <div class="crc" />
    </div>
</template>

<script>
export default {
    props: {
        arg: {
            type: Object,
            required: true
        }
    },
    created() {
        // console.log(this.arg, 'arg')
    }
}
</script>

<style lang="scss" scoped>
.year_day{
    display: flex;
    align-items: center;
    justify-content: center;
    .crc{
        height: 10px;
        width: 10px;
        background: var(--orange);
        border-radius: 50%;
    }
}
</style>