<template>
    <div class="mb-3">
        <div class="intent_card rounded-lg">
            <div class="intent_card__header flex items-center justify-between truncate skeleton_card">
                <a-skeleton active :paragraph="{ rows: 0 }" :title="{width: '100%'}" style="width: 50%;" />
                <a-skeleton active :paragraph="{ rows: 0 }" :title="{width: '100%'}" style="width: 30px;" />
            </div>
            <div class="intent_card__body">
                <div class="intent_card__divider" />
                <a-row :gutter="isMobile ? 0 : 30" >
                    <a-col :sm="isMobile ? 24 : 12" :lg="isMobile ? 24 : 12" :xl="isMobile ? 24 : 12" :xxl="isMobile ? 24 : 12">
                        <div class="skeleton_card mb-3">
                            <a-skeleton active :paragraph="{ rows: 0 }" :title="{width: '100%'}" style="width: 30%;" />
                        </div>
                        <a-skeleton active :paragraph="{ rows: 18 }" />
                    </a-col>
                    <a-col :sm="isMobile ? 24 : 12" :lg="isMobile ? 24 : 12" :xl="isMobile ? 24 : 12" :xxl="isMobile ? 24 : 12">
                        <div class="skeleton_card mb-3">
                            <a-skeleton active :paragraph="{ rows: 0 }" :title="{width: '100%'}" style="width: 30%;" />
                        </div>
                        <a-skeleton active :paragraph="{ rows: 18 }" />
                    </a-col>
                </a-row>
            </div>
        </div>
        <div v-if="!isMobile" class="intent_card rounded-lg">
            <div class="intent_card__header flex items-center justify-between truncate skeleton_card">
                <a-skeleton active :paragraph="{ rows: 0 }" :title="{width: '100%'}" style="width: 50%;" />
                <a-skeleton active :paragraph="{ rows: 0 }" :title="{width: '100%'}" style="width: 30px;" />
            </div>
            <div class="intent_card__body">
                <div class="intent_card__divider" />
                <a-row :gutter="isMobile ? 0 : 30" >
                    <a-col :sm="12" :lg="12" :xl="12" :xxl="12">
                        <div class="skeleton_card mb-3">
                            <a-skeleton active :paragraph="{ rows: 0 }" :title="{width: '100%'}" style="width: 30%;" />
                        </div>
                        <a-skeleton active :paragraph="{ rows: 18 }" />
                    </a-col>
                    <a-col :sm="12" :lg="12" :xl="12" :xxl="12">
                        <div class="skeleton_card mb-3">
                            <a-skeleton active :paragraph="{ rows: 0 }" :title="{width: '100%'}" style="width: 30%;" />
                        </div>
                        <a-skeleton active :paragraph="{ rows: 18 }" />
                    </a-col>
                </a-row>
            </div>
        </div>
    </div>
</template>

<script>
export default {
    computed: {
        isMobile() { 
            return this.$store.state.isMobile
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
.intent_card{
    background: #fff;
    &:not(:last-child){
        margin-bottom: 15px;
    }
    &__header{
        padding: 20px;
        cursor: pointer;
    }
    &__body{
        padding-left: 20px;
        padding-right: 20px;
        padding-bottom: 20px;
    }
    .intent_card__divider{
        margin-bottom: 15px;
        height: 1px;
        background: #e8e8e8;
        @media (min-width: 768px) {
            margin-bottom: 20px;
        }
    }
}
</style>