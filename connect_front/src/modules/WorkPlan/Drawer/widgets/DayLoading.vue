<template>
    <div>
        <div class="list_item rounded-lg">
            <div class="icon_wrapper rounded-lg">
                <a-skeleton active :paragraph="{ rows: 0 }" :title="{width: '100%'}" style="width: 100%;" /> 
            </div>
            <div class="info_wrapper">
                <div class="info_wrapper__label mb-2">
                    <a-skeleton active :paragraph="{ rows: 0 }" :title="{width: '100%'}" style="width: 180px;" /> 
                </div>
                <div class="info_wrapper__value">
                    <a-skeleton active :paragraph="{ rows: 0 }" :title="{width: '100%'}" style="width: 120px;" /> 
                </div>
            </div>
        </div>
        <div class="list_item rounded-lg">
            <div class="icon_wrapper rounded-lg">
                <a-skeleton active :paragraph="{ rows: 0 }" :title="{width: '100%'}" style="width: 100%;" /> 
            </div>
            <div class="info_wrapper">
                <div class="info_wrapper__label mb-2">
                    <a-skeleton active :paragraph="{ rows: 0 }" :title="{width: '100%'}" style="width: 180px;" /> 
                </div>
                <div class="info_wrapper__value">
                    <a-skeleton active :paragraph="{ rows: 0 }" :title="{width: '100%'}" style="width: 120px;" /> 
                </div>
            </div>
        </div>
        <div class="list_item rounded-lg">
            <div class="icon_wrapper rounded-lg">
                <a-skeleton active :paragraph="{ rows: 0 }" :title="{width: '100%'}" style="width: 100%;" /> 
            </div>
            <div class="info_wrapper">
                <div class="info_wrapper__label mb-2">
                    <a-skeleton active :paragraph="{ rows: 0 }" :title="{width: '100%'}" style="width: 180px;" /> 
                </div>
                <div class="info_wrapper__value">
                    <a-skeleton active :paragraph="{ rows: 0 }" :title="{width: '100%'}" style="width: 120px;" /> 
                </div>
            </div>
        </div>
        <div class="list_item rounded-lg">
            <div class="icon_wrapper rounded-lg">
                <a-skeleton active :paragraph="{ rows: 0 }" :title="{width: '100%'}" style="width: 100%;" /> 
            </div>
            <div class="info_wrapper">
                <div class="info_wrapper__label mb-2">
                    <a-skeleton active :paragraph="{ rows: 0 }" :title="{width: '100%'}" style="width: 180px;" /> 
                </div>
                <div class="info_wrapper__value">
                    <a-skeleton active :paragraph="{ rows: 0 }" :title="{width: '100%'}" style="width: 120px;" /> 
                </div>
            </div>
        </div>
        <a-divider class="mb-2" />
        <div class="mb-2">
            <a-skeleton active :paragraph="{ rows: 0 }" :title="{width: '100%'}" style="width: 160px;" /> 
        </div>
        <div class="progress_line">
            <div class="progress_line__header">
                <div class="header_label">
                    <a-skeleton active :paragraph="{ rows: 0 }" :title="{width: '100%'}" style="width: 120px;" /> 
                </div>
                <div class="header_value">
                    <a-skeleton active :paragraph="{ rows: 0 }" :title="{width: '100%'}" style="width: 30px;" /> 
                </div>
            </div>
            <div class="progress_line__wrapper">
                <a-skeleton active :paragraph="{ rows: 0 }" :title="{width: '100%'}" style="width: 100%;" /> 
            </div>
        </div>
        <div class="progress_line">
            <div class="progress_line__header">
                <div class="header_label">
                    <a-skeleton active :paragraph="{ rows: 0 }" :title="{width: '100%'}" style="width: 120px;" /> 
                </div>
                <div class="header_value">
                    <a-skeleton active :paragraph="{ rows: 0 }" :title="{width: '100%'}" style="width: 30px;" /> 
                </div>
            </div>
            <div class="progress_line__wrapper">
                <a-skeleton active :paragraph="{ rows: 0 }" :title="{width: '100%'}" style="width: 100%;" /> 
            </div>
        </div>
    </div>
</template>

<style lang="scss" scoped>
.progress_line{
    &:not(:last-child){
        margin-bottom: 10px;
    }
    &__header{
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 5px;
    }
    &::v-deep{
        .ant-skeleton-title{
            margin-top: 0px;
        }
        .ant-skeleton-paragraph{
            display: none;
        }
    }
}
.list_item{
    display: flex;
    align-items: center;
    background: #F8F9FD;
    padding: 10px;
    &::v-deep{
        .ant-skeleton-title{
            margin-top: 0px;
        }
        .ant-skeleton-paragraph{
            display: none;
        }
    }
    &:not(:last-child){
        margin-bottom: 10px;
    }
    .icon_wrapper{
        width: 36px;
        height: 36px;
        display: flex;
        align-items: center;
        justify-content: center;
        margin-right: 15px;
        font-size: 18px;
        position: relative;
        overflow: hidden;
    }
}
</style>