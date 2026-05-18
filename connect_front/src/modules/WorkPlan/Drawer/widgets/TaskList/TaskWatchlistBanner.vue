<template>
    <div class="task_watchlist_banner" :class="{ mobile: isMobile }">
        <div class="task_watchlist_banner__content">
            <div v-if="!isMobile" class="task_watchlist_banner__icon">
                <i class="fi fi-rr-calendar-check"></i>
            </div>
            <div class="task_watchlist_banner__body">
                <div class="task_watchlist_banner__title">
                    {{ $t('workplan.task_watchlist_title') }}
                </div>
                <div v-if="formattedPeriod" class="task_watchlist_banner__period">
                    {{ $t('workplan.task_watchlist_period', { period: formattedPeriod }) }}
                </div>
                <div class="task_watchlist_banner__stats">
                    <div class="task_watchlist_banner__stat overdue">
                        <span class="task_watchlist_banner__badge" aria-hidden="true"></span>
                        <span>{{ $t('workplan.task_watchlist_overdue', { count: overdue, tasks: taskLabel(overdue) }) }}</span>
                    </div>
                    <div class="task_watchlist_banner__stat stalled">
                        <span class="task_watchlist_banner__badge" aria-hidden="true"></span>
                        <span>{{ $t('workplan.task_watchlist_stalled', { count: stalled }) }}</span>
                    </div>
                </div>
                <a-button
                    type="primary"
                    size="large"
                    :block="isMobile"
                    class="task_watchlist_banner__button"
                    @click="$emit('action')">
                    {{ $t('workplan.task_watchlist_action') }}
                </a-button>
            </div>
        </div>
    </div>
</template>

<script>
export default {
    props: {
        overdue: {
            type: Number,
            default: 0
        },
        stalled: {
            type: Number,
            default: 0
        },
        startDate: {
            type: String,
            default: null
        },
        endDate: {
            type: String,
            default: null
        }
    },
    computed: {
        isMobile() {
            return this.$store.state.isMobile
        },
        formattedPeriod() {
            if(!this.startDate || !this.endDate)
                return ''

            const locale = this.$i18n?.locale || 'ru'
            const start = this.$moment(this.startDate).locale(locale)
            const end = this.$moment(this.endDate).locale(locale)

            if(!start.isValid() || !end.isValid())
                return ''

            const startDay = start.format('DD')
            const startDayMonth = start.format('DD MMMM')
            const endDayMonth = end.format('DD MMMM')
            const startMonth = start.format('MMMM')
            const endMonth = end.format('MMMM')

            if(startMonth === endMonth)
                return `${startDay}-${endDayMonth}`

            return `${startDayMonth} - ${endDayMonth}`
        }
    },
    methods: {
        taskLabel(count) {
            const mod10 = count % 10
            const mod100 = count % 100

            if(mod10 === 1 && mod100 !== 11)
                return this.$t('workplan.task_watchlist_task_one')
            if(mod10 >= 2 && mod10 <= 4 && (mod100 < 12 || mod100 > 14))
                return this.$t('workplan.task_watchlist_task_few')

            return this.$t('workplan.task_watchlist_task_many')
        }
    }
}
</script>

<style lang="scss" scoped>
.task_watchlist_banner {
    display: flex;
    align-items: flex-start;
    gap: 24px;
    padding: 20px;
    border-radius: 0.5rem;
    background: #fff9e8;
    border: 1px solid #ffe39a;

    &.mobile {
        flex-direction: column;
        padding: 20px 15px;
    }

    &__content {
        display: flex;
        align-items: flex-start;
        gap: 24px;
        min-width: 0;
    }

    &__icon {
        width: 42px;
        min-width: 42px;
        height: 42px;
        border-radius: 0.5rem;
        background: linear-gradient(180deg, #fff3c9 0%, #ffe9a0 100%);
        display: flex;
        align-items: center;
        justify-content: center;
        color: #ea8a00;
        font-size: 24px;
    }

    &__body {
        min-width: 0;
        display: flex;
        flex-direction: column;
        align-items: flex-start;
        gap: 12px;
    }

    &__title {
        font-weight: 700;
        font-size: 18px;
        line-height: 1.2;
        color: #17213a;
    }

    &__period {
        font-size: 14px;
        line-height: 1.3;
        color: #667085;
    }

    &__stats {
        display: flex;
        align-items: center;
        flex-wrap: wrap;
        gap: 24px;
    }

    &__stat {
        display: flex;
        align-items: center;
        gap: 5px;
        line-height: 1.3;

        &.overdue {
            color: #ff2b2b;
        }

        &.stalled {
            color: #ea8a00;
        }
    }

    &__badge {
        width: 8px;
        min-width: 8px;
        height: 8px;
        border-radius: 50%;
        display: inline-flex;
        align-items: center;
        justify-content: center;
    }

    &__stat.overdue &__badge {
        background: #ff3939;
    }

    &__stat.stalled &__badge {
        background: #ffbf00;
    }

    &__button {
        min-width: 260px;
    }
}

@media (max-width: 768px) {
    .task_watchlist_banner {
        &__content {
            width: 100%;
        }

        &__title {
            font-size: 16px;
        }

        &__stats {
            gap: 16px;
        }

        &__stat {
            font-size: 15px;
        }

        &__button {
            min-width: 0;
            width: 100%;
        }
    }
}
</style>
