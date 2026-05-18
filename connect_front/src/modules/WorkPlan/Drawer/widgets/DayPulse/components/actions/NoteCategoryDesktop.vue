<template>
    <a-dropdown
        :trigger="['click']"
        placement="bottomLeft"
        @visibleChange="$emit('visible-change', $event)">
        <div v-tippy content="Категория" class="note_category note_category_dropdown">
            <i class="fi" :class="categoryIcon" :style="{ color: categoryColor }" />
            <span class="truncate">{{ categoryName }}</span>
            <i class="fi fi-rr-angle-small-down status_tag_arrow" />
        </div>
        <a-menu slot="overlay">
            <a-menu-item v-if="categoryLoading" key="category_loading">
                <a-spin size="small" />
            </a-menu-item>
            <a-menu-item
                v-for="item in availableCategories"
                v-else
                :key="`category_${item.code}`"
                @click="$emit('change-category', item.code)">
                <i class="fi mr-2" :class="item.icon || 'fi-rr-note-sticky'" :style="{ color: item.hex_color || '#8a94a6' }" />
                {{ item.name }}
            </a-menu-item>
            <a-menu-item v-if="!categoryLoading && !availableCategories.length" key="category_empty" disabled>
                Нет доступных категорий
            </a-menu-item>
        </a-menu>
    </a-dropdown>
</template>

<script>
export default {
    props: {
        categoryName: {
            type: String,
            default: ''
        },
        categoryIcon: {
            type: String,
            default: 'fi-rr-note-sticky'
        },
        categoryColor: {
            type: String,
            default: '#8a94a6'
        },
        categoryLoading: {
            type: Boolean,
            default: false
        },
        availableCategories: {
            type: Array,
            default: () => []
        }
    }
}
</script>

<style scoped lang="scss">
.note_category {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    min-width: 0;
    color: #6a768d;
    font-size: 13px;
    background: #f0f1f6;
    line-height: 24px;
    padding-left: 10px;
    padding-right: 10px;
    border-radius: 30px;
    min-height: 24px;
}

.note_category_dropdown {
    cursor: pointer;
}
</style>
