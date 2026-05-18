<template>
    <div class="client_card" @click="openClient">
        <div class="client_card__top">
            <div class="client_card__name">
                {{ item.name || '-' }}
            </div>
            <a-tag
                v-if="item.status"
                :color="item.status.color || ''"
                size="small">
                {{ item.status.name || item.status.code }}
            </a-tag>
        </div>

        <div v-if="item.inn" class="client_card__row">
            <div class="client_card__label">{{ $t('directories.bin') }}:</div>
            <div class="client_card__value">{{ item.inn }}</div>
        </div>

        <div v-if="item.legal_address" class="client_card__row">
            <div class="client_card__label">{{ $t('directories.legal_address') }}:</div>
            <div class="client_card__value">{{ item.legal_address }}</div>
        </div>

        <div class="client_card__row client_card__row_col">
            <div class="client_card__label">{{ $t('directories.support_specialists') }}:</div>
            <div
                v-if="specialists.length"
                class="client_card__specialists">
                <Profiler
                    v-for="specialist in specialists"
                    :key="specialist.id || specialist.user?.id"
                    :user="specialist.user"
                    :showPopup="false"
                    :avatarSize="26"
                    wrapperClass="client_card__specialist" />
            </div>
            <div v-else class="client_card__value">-</div>
        </div>
    </div>
</template>

<script>
export default {
    name: 'DirectoriesClientsMobileCard',
    components: {
        Profiler: () => import('@/modules/Profiler/Profiler.vue')
    },
    props: {
        item: {
            type: Object,
            required: true
        }
    },
    computed: {
        specialists() {
            return (this.item?.actual_specialists || []).filter(specialist => specialist?.user)
        }
    },
    methods: {
        openClient() {
            const query = Object.assign({}, this.$route.query)
            if (query.client !== this.item.id) {
                query.client = this.item.id
                this.$router.push({ query })
            } else {
                delete query.client
                this.$router.replace({ query })
                    .then(() => {
                        query.client = this.item.id
                        this.$router.replace({ query })
                    })
            }
        }
    }
}
</script>

<style lang="scss" scoped>
.client_card {
    background: #fff;
    border-radius: var(--borderRadius);
    padding: 12px;
    margin-bottom: 10px;
    cursor: pointer;

    &__top {
        display: flex;
        align-items: flex-start;
        justify-content: space-between;
        gap: 8px;
        margin-bottom: 8px;
    }

    &__name {
        font-weight: 600;
        font-size: 15px;
        line-height: 1.4;
    }

    &__row {
        display: flex;
        align-items: flex-start;
        gap: 6px;
        font-size: 13px;
        line-height: 1.35;

        &:not(:last-child) {
            margin-bottom: 6px;
        }

        &_col {
            flex-direction: column;
            gap: 4px;
        }
    }

    &__label {
        color: var(--gray);
    }

    &__value {
        word-break: break-word;
    }

    &__specialists {
        display: flex;
        flex-direction: column;
        gap: 6px;
        width: 100%;
    }
}
</style>
