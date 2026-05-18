<template>
    <div
        class="employee_pulse_mobile_card"
        @click="openCard">
        <div class="flex items-center justify-between mb-3">
            <Profiler
                v-if="item.author"
                :user="item.author"
                :avatarSize="24"
                hideSupportTag
                nameClass="text-sm font-medium"
                wrapperClass="w-full" />

            <a-tag
                v-if="item.status"
                :color="item.status.color">
                {{ item.status.name || item.status.code }}
            </a-tag>
        </div>

        <div class="employee_pulse_mobile_card__row mb-2">
            <span class="employee_pulse_mobile_card__label">{{ $t('table.period') }}:</span>
            <span>{{ periodText }}</span>
        </div>

        <div class="employee_pulse_mobile_card__content mb-3">
            {{ item.content || '-' }}
        </div>

        <a-button
            type="flat_primary"
            block
            class="flex items-center justify-center">
            {{ $t('workplan.details') }}
            <i class="fi fi-rr-arrow-right ml-2" />
        </a-button>
    </div>
</template>

<script>
export default {
    components: {
        Profiler: () => import('@apps/Profiler/Profiler.vue')
    },
    props: {
        item: {
            type: Object,
            required: true
        },
        open: {
            type: Function,
            default: () => {}
        }
    },
    computed: {
        periodText() {
            if (!this.item?.date) return '-'
            return this.$moment(this.item.date).format('DD.MM.YYYY HH:mm')
        }
    },
    methods: {
        openCard() {
            this.open(this.item)
        }
    }
}
</script>

<style lang="scss" scoped>
.employee_pulse_mobile_card{
    background: #fff;
    border-radius: var(--borderRadius);
    margin-bottom: 10px;
    padding: 12px;
    cursor: pointer;
    &__row{
        display: flex;
        align-items: center;
        gap: 6px;
        font-size: 13px;
        line-height: 16px;
    }
    &__label{
        color: #656565;
    }
    &__content{
        font-size: 14px;
        line-height: 20px;
        display: -webkit-box;
        -webkit-line-clamp: 3;
        -webkit-box-orient: vertical;
        overflow: hidden;
        word-break: break-word;
    }
    &__details_btn{
        padding: 0 !important;
        height: auto;
    }
}
</style>
