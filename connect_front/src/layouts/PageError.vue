<template>
    <div class="error_layout">
        <LogoBlock />
        <router-view />
    </div>
</template>

<script>
import LogoBlock from './components/LogoBlock.vue'
export default {
    components: {
        LogoBlock
    }
}
</script>

<style lang="scss" scoped>
.error_layout{
    max-width: 960px;
    margin: 0 auto;
    padding: 40px 15px;
}
</style>