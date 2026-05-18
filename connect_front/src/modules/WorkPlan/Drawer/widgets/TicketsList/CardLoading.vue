<template>
    <div class="skeleton_card rounded-lg" :style="`padding: 20px;background: ${useInject ? '#f7f9fc' : '#fff'};margin-bottom: 15px;`">
        <div class="flex items-center justify-between gap-3 mb-3">
            <a-skeleton active :paragraph="{ rows: 0 }" :title="{width: '160px'}" />
            <a-skeleton active :paragraph="{ rows: 0 }" :title="{width: '20px'}" />
        </div>
        <a-skeleton active :paragraph="{ rows: 0 }" :title="{width: '80%'}" />
    </div>
</template>

<script>
export default {
    props: {
        useInject: {
            type: Boolean,
            default: false
        }
    }
}
</script>

<style lang="scss" scoped>
.skeleton_card{
    &::v-deep{
        .ant-skeleton-title{
            margin-top: 0px;
            margin-bottom: 0px;
        }
        .ant-skeleton-paragraph{
            display: none;
        }
    }
}
</style>
