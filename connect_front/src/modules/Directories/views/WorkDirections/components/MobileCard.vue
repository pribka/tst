<template>
    <div class="dir_card" @click="openEditForm">
        <div class="dir_card__title">
            {{ item.name || '-' }}
        </div>
        <div v-if="item.contractor" class="dir_card__organization">
            <div :key="item.contractor.logo" class="dir_card__organization-logo">
                <a-avatar
                    :size="24"
                    :src="item.contractor.logo"
                    icon="fi-rr-users-alt"
                    flaticon />
            </div>
            <div class="dir_card__organization-name">
                {{ item.contractor.name || item.contractor.full_name || '-' }}
            </div>
        </div>
    </div>
</template>

<script>
import eventBus from '@/utils/eventBus'

export default {
    name: 'DirectoriesWorkDirectionsMobileCard',
    props: {
        item: {
            type: Object,
            required: true
        }
    },
    methods: {
        openEditForm() {
            eventBus.$emit('open_modal_work_direction_edit', { record: this.item })
        }
    }
}
</script>

<style lang="scss" scoped>
.dir_card {
    background: #fff;
    border-radius: var(--borderRadius);
    padding: 12px;
    margin-bottom: 10px;
    font-size: 14px;
    font-weight: 600;
    line-height: 1.35;
    word-break: break-word;
    cursor: pointer;
    &__title{
        font-size: 14px;
        font-weight: 600;
    }
    &__organization{
        display: flex;
        align-items: center;
        margin-top: 10px;
        font-size: 13px;
        font-weight: 400;
        color: var(--gray);
    }
    &__organization-logo{
        padding-right: 8px;
        display: flex;
        align-items: center;
    }
    &__organization-name{
        min-width: 0;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
    }
}
</style>
