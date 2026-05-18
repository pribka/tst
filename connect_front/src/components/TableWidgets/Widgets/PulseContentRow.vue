<template>
    <div class="h-full flex items-center cursor-pointer truncate" :title="record.content" @click="openHandler(record)">
        <i
            v-if="record?.is_ai_summary === true"
            class="fi fi-ai-rr-sparkles status_ai_icon mr-2"
            v-tippy
            content="Сгенерировано через AI" />
        <div v-if="categoryName" v-tippy :content="categoryName" class="note_category mr-2">
            <i class="fi" :class="categoryIcon" :style="{ color: categoryColor }" />
        </div>
        <div class="truncate">{{ record.content }}</div>
    </div>
</template>

<script>
export default {
    props: {
        text: {
            type: [Object, String]
        },
        record: {
            type: Object
        },
        openHandler: {
            type: Function,
            default: () => {}
        }
    },
    computed: {
        category() {
            return this.record?.category && typeof this.record.category === 'object'
                ? this.record.category
                : null
        },
        categoryName() {
            return this.category?.name || ''
        },
        categoryIcon() {
            return this.category?.icon || 'fi-rr-note-sticky'
        },
        categoryColor() {
            return this.category?.hex_color || '#8a94a6'
        }
    }
}
</script>

<style scoped lang="scss">
.note_category {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 24px;
    min-width: 24px;
    height: 24px;
    border-radius: 999px;
    background: #f0f1f6;
    color: #6a768d;
}

.status_ai_icon {
    color: var(--blue);
    flex: 0 0 auto;
}
</style>
