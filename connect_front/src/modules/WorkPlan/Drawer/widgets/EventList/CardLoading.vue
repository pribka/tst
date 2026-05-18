<template>
    <div class="skeleton_card rounded-lg" :style="`padding: 20px;background: ${useInject ? '#f7f9fc' : '#fff'};margin-bottom: 15px;`">
        <div class="task_card__wrapper">
            <div class="flex items-center gap-5 mb-2 justify-between">
                <div class="flex items-center gap-3 w-full">
                    <a-skeleton active :paragraph="{ rows: 0 }" :title="{width: '100%'}" style="width: 65%;" />
                </div>
                <div class="flex items-center gap-2">
                    <a-skeleton active :paragraph="{ rows: 0 }" :title="{width: '100%'}" style="width: 100px" />
                    <a-skeleton active :paragraph="{ rows: 0 }" :title="{width: '100%'}" style="width: 100px" />
                </div>
            </div>
            <div class="flex items-center gap-4">
                <a-skeleton active :paragraph="{ rows: 0 }" style="width: 20px;" :title="{width: '100%'}" /> 
                <a-skeleton active :paragraph="{ rows: 0 }" style="width: 150px;" :title="{width: '100%'}" /> 
            </div>
            <div class="flex items-center gap-4 mt-2">
                <a-skeleton active :paragraph="{ rows: 0 }" style="width: 20px;" :title="{width: '100%'}" /> 
                <a-skeleton active :paragraph="{ rows: 0 }" style="width: 120px;" :title="{width: '100%'}" />
            </div>
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
        }
        .ant-skeleton-paragraph{
            display: none;
        }
    }
}
</style>