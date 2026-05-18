<template>
    <div>
        <div v-tippy content="Категория" class="note_category note_category_dropdown" @click="openDrawer">
            <i class="fi" :class="categoryIcon" :style="{ color: categoryColor }" />
        </div>

        <ActivityDrawer v-model="visible">
            <li v-if="categoryLoading" class="category_drawer_loading">
                <a-spin size="small" />
            </li>
            <ActivityItem
                v-for="item in availableCategories"
                v-else
                :key="`mobile_category_${item.code}`"
                @click="emitAndClose(item.code)">
                <i class="fi mr-2" :class="item.icon || 'fi-rr-note-sticky'" :style="{ color: item.hex_color || '#8a94a6' }" />
                {{ item.name }}
            </ActivityItem>
            <li v-if="!categoryLoading && !availableCategories.length" class="category_drawer_empty">
                Нет доступных категорий
            </li>
        </ActivityDrawer>
    </div>
</template>

<script>
export default {
    components: {
        ActivityDrawer: () => import('@/components/ActivitySelect/ActivityDrawer.vue'),
        ActivityItem: () => import('@/components/ActivitySelect/ActivityItem.vue')
    },
    props: {
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
    },
    data() {
        return {
            visible: false
        }
    },
    methods: {
        openDrawer() {
            this.visible = true
            this.$emit('visible-change', true)
        },
        emitAndClose(code) {
            this.$emit('change-category', code)
            this.visible = false
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

.category_drawer_loading,
.category_drawer_empty {
    padding: 13px 15px;
}
</style>
