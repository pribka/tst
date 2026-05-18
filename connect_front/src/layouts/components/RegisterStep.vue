<template>
    <div v-if="regStep > 1" class="reg_step">
        <div class="reg_step__crc" :class="regStep == 2 && 'active'"></div>
        <div class="reg_step__crc" :class="regStep == 3 && 'active'"></div>
        <div class="reg_step__crc" :class="regStep == 4 && 'active'"></div>
    </div>
</template>

<script>
export default {
    computed: {
        regStep() {
            return this.$store.state.user.regStep
        }
    }
}
</script>

<style lang="scss" scoped>
.reg_step{
    position: absolute;
    bottom: 20px;
    left: 30px;
    z-index: 5;
    display: flex;
    align-items: center;
    &__crc{
        background: #e3e6ea;
        width: 8px;
        height: 8px;
        border-radius: 50%;
        transition: all 0.3s cubic-bezier(0.645, 0.045, 0.355, 1);
        &:not(:last-child){
            margin-right: 15px;
        }
        &.active{
            background: var(--blue);
            transform: scale(1.5);
        }
    }
}
</style>