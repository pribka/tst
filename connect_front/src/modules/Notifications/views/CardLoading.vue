<template>
    <div>
        <div class="skeleton_card" style="margin-bottom: 15px;">
            <a-skeleton avatar active :paragraph="{ rows: 1 }" />
        </div>
        <div class="skeleton_card" style="margin-bottom: 15px;">
            <a-skeleton avatar active :paragraph="{ rows: 1 }" />
        </div>
        <div class="skeleton_card" style="margin-bottom: 15px;">
            <a-skeleton avatar active :paragraph="{ rows: 1 }" />
        </div>
        <div class="skeleton_card" style="margin-bottom: 15px;">
            <a-skeleton avatar active :paragraph="{ rows: 1 }" />
        </div>
        <div class="skeleton_card" style="margin-bottom: 15px;">
            <a-skeleton avatar active :paragraph="{ rows: 1 }" />
        </div>
        <div class="skeleton_card" style="margin-bottom: 15px;">
            <a-skeleton avatar active :paragraph="{ rows: 1 }" />
        </div>
        <div class="skeleton_card" style="margin-bottom: 15px;">
            <a-skeleton avatar active :paragraph="{ rows: 1 }" />
        </div>
        <div class="skeleton_card" style="margin-bottom: 15px;">
            <a-skeleton avatar active :paragraph="{ rows: 1 }" />
        </div>
        <div class="skeleton_card" style="margin-bottom: 15px;">
            <a-skeleton avatar active :paragraph="{ rows: 1 }" />
        </div>
    </div>
</template>

<style lang="scss" scoped>
.skeleton_card{
    &::v-deep{
        .ant-skeleton-header{
            padding-right: 10px;
        }
        .ant-skeleton-header .ant-skeleton-avatar-lg{
            @media (max-width: 575.98px) {
                width: 35px;
                height: 35px;
                line-height: 35px;
            }
        }
        .ant-skeleton-title{
            margin-top: 0px;
            width: 40%!important;
            @media (min-width: 576px) {
                width: 20%!important;
            }
        }
        .ant-skeleton-with-avatar .ant-skeleton-content .ant-skeleton-title + .ant-skeleton-paragraph{
            margin-top: 10px;
            li{
                width: 60%;
            }
        }
    }
    padding-bottom: 10px;
    @media (min-width: 576px) {
        padding-bottom: 16px;
        padding-top: 10px;
    }
    &:not(:last-child){
        border-bottom: 1px solid #e8e8e8;
    }
}
</style>