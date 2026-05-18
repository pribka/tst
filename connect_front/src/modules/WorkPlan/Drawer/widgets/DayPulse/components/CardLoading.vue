<template>
    <div class="skeleton_card rounded-lg" :style="`padding: 20px;background: ${useInject ? '#f7f9fc' : '#fff'};margin-bottom: 15px;`">
        <div class="flex items-center justify-between gap-3 mb-3">
            <div class="flex items-center gap-2">
                <a-skeleton active :paragraph="{ rows: 0 }" :title="{ width: '88px' }" />
                <a-skeleton active :paragraph="{ rows: 0 }" :title="{ width: '140px' }" />
            </div>
            <a-skeleton active :paragraph="{ rows: 0 }" :title="{ width: '20px' }" />
        </div>
        <div class="mb-3">
            <a-skeleton active :paragraph="{ rows: 0 }" :title="{ width: '90%' }" />
            <a-skeleton active :paragraph="{ rows: 0 }" :title="{ width: '70%' }" />
        </div>
        <div class="flex items-center justify-between">
            <a-skeleton active :paragraph="{ rows: 0 }" :title="{ width: '120px' }" />
            <a-skeleton active :paragraph="{ rows: 0 }" :title="{ width: '120px' }" />
        </div>
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
            margin-bottom: 8px;
        }
        .ant-skeleton-paragraph{
            display: none;
        }
    }
}
</style>
