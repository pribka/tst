<template>
    <div class="pj_padding bsp_page">
        <router-view :page_name="page_name">
            <slot />
        </router-view>
    </div>
</template>

<script>
export default {
    props: {
        page_name: {
            type: [String, Number],
            default: ''
        }
    }
}
// test
</script>

<style lang="scss" scoped>
.bsp_page{
    height: 100%;
}
</style>