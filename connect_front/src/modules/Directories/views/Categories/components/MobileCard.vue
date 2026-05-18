<template>
    <div class="dir_card" @click="openEditForm">
        {{ item.name || '-' }}
    </div>
</template>

<script>
import eventBus from '@/utils/eventBus'

export default {
    name: 'DirectoriesCategoriesMobileCard',
    props: {
        item: {
            type: Object,
            required: true
        }
    },
    methods: {
        openEditForm() {
            eventBus.$emit('open_modal_category_create', { record: this.item })
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
}
</style>
