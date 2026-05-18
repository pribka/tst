<template>
    <transition name="slide-fade">
        <div v-if="approvals.rejection_reason && approvals.status.code === 'rejected'" class="mb-2 md:mb-4">
            <a-alert
                class="rejection_reason_alert"
                :message="$t('approvals.rejection_reason_placeholder')"
                showIcon
                :description="approvals.rejection_reason"
                type="error">
                <template #icon>
                    <i class="fi fi-rr-file-excel" />
                </template>
            </a-alert>
        </div>
    </transition>
</template>

<script>
export default {
    props: {
        approvals: {
            type: Object,
            required: true
        }
    }
}
</script>

<style lang="scss" scoped>
.slide-fade-enter-active {
    transition: all .3s ease;
}
.slide-fade-leave-active {
    transition: all .3s cubic-bezier(1.0, 0.5, 0.8, 1.0);
}
.slide-fade-enter,
.slide-fade-leave-to {
    transform: translateY(-10px);
    opacity: 0;
}
.rejection_reason_alert{
    border: 1px solid rgb(249, 154, 154);
    padding: 10px 15px 10px 65px;
    &::v-deep{
        .ant-alert-description{
            color: #000;
        }
    }
}
</style>