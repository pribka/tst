<template>
    <div :class="isMobile ? 'column-item-mobile' : 'flex items-center rounded'">
        <template v-if="!isMobile">
            <a-switch 
                :checked="columnVisible"
                size="small"
                @change="toggleVisible" />

            <slot name="grab"></slot>

            <div class="flex-grow">
                <div v-if="edit">
                    <div class="flex">
                        <div>
                            <a-input 
                                class="h-full"
                                v-model="newTitle" 
                                @keyup.enter="save" />
                        </div>
                        <a-button 
                            @click="save" 
                            class="ml-2 shrink-0"
                            flaticon
                            icon="fi-rr-disk">
                        </a-button>
                        <a-button 
                            @click="cancelEdit" 
                            class="ml-2 shrink-0" 
                            flaticon
                            icon="fi-rr-cross">
                        </a-button>
                    </div>
                </div>
                <div v-else>
                    <div class="flex items-center">
                        <a-button
                            v-if="hasCustomTitle"
                            @click="setDefaultName"
                            class="ml-2 shrink-0"
                            flaticon
                            icon="fi-rr-rotate-left">
                        </a-button>
                        <div
                            @click="startEdit"
                            class="ml-2 relative flex-grow cursor-pointer">
                            {{ item.title || item.defaultTitle }}
                            <span
                                v-if="hasCustomTitle"
                                class="absolute left-0 bottom-0 translate-y-full opacity-40 text-xs">
                                {{ item.defaultTitle }}
                            </span>
                        </div>
                    </div>
                </div>
            </div>

            <div class="flex items-center">
                <SortingSelect 
                    v-if="item.sortable !== false"    
                    :item="item" />
                <a-button 
                    type="ui" 
                    ghost
                    shape="circle"
                    class="text_red" 
                    flaticon
                    icon="fi-rr-trash"
                    @click="removeItem">
                </a-button>
            </div>
        </template>

        <template v-else>
            <div class="column-item-mobile__top">
                <div class="column-item-mobile__controls">
                    <a-switch 
                        :checked="columnVisible"
                        size="small"
                        @change="toggleVisible" />
                    <slot name="grab"></slot>
                </div>
                <a-button 
                    type="ui" 
                    ghost
                    shape="circle"
                    class="text_red" 
                    flaticon
                    icon="fi-rr-trash"
                    @click="removeItem">
                </a-button>
            </div>

            <div class="column-item-mobile__title">
                <div v-if="edit" class="column-item-mobile__edit">
                    <a-input 
                        class="h-full"
                        v-model="newTitle" 
                        @keyup.enter="save" />
                    <div class="column-item-mobile__edit-actions">
                        <a-button 
                            @click="save" 
                            flaticon
                            icon="fi-rr-disk">
                        </a-button>
                        <a-button 
                            @click="cancelEdit" 
                            class="ml-2"
                            flaticon
                            icon="fi-rr-cross">
                        </a-button>
                    </div>
                </div>
                <div v-else class="column-item-mobile__title-row">
                    <a-button
                        v-if="hasCustomTitle"
                        @click="setDefaultName"
                        class="shrink-0"
                        flaticon
                        icon="fi-rr-rotate-left">
                    </a-button>
                    <div
                        @click="startEdit"
                        class="column-item-mobile__title-text"
                        :class="hasCustomTitle && 'ml-2'">
                        {{ item.title || item.defaultTitle }}
                    </div>
                </div>
                <div
                    v-if="hasCustomTitle && !edit"
                    class="column-item-mobile__default-title">
                    {{ item.defaultTitle }}
                </div>
            </div>

            <div v-if="item.sortable !== false" class="column-item-mobile__sorting">
                <SortingSelect :item="item" />
            </div>
        </template>
    </div>
</template>

<script>
export default {
    components: {
        SortingSelect: () => import('../SortingSelect.vue')
    },
    props: {
        item: {
            type: Object,
            required: true,
        },
        itemIndex: {
            type: Number,
            required: true,
        },
    },

    data() {
        return {
            edit: false,
            newTitle: '',
        };
    },

    computed: {
        isMobile() {
            return this.$store.state.isMobile
        },
        hasCustomTitle() {
            return this.item.title !== this.item.defaultTitle
        },
        activeTemplate() {
            return this.$store.state.reports.activeTemplate
        },
        activeMetadata() {
            return this.activeTemplate.metadata
        },
        columnVisible() {
            return this.item.is_visible !== false
        },
    },

    methods: {
        startEdit() {
            this.edit = true;
            this.newTitle = this.item.title || this.item.defaultTitle;
        },
        cancelEdit() {
            this.edit = false;
        },
        save() {
            this.$store.commit('reports/SET_COLUMN_CUSTOM_TITLE', { itemIndex: this.itemIndex, customTitle: this.newTitle })
            this.cancelEdit();
        },
        setDefaultName() {
            this.$store.commit('reports/SET_COLUMN_CUSTOM_TITLE', { itemIndex: this.itemIndex, customTitle: this.item.defaultTitle })
        },
        toggleVisible(visible) {
            this.$store.commit('reports/SET_COLUMN_FIELD', { itemIndex: this.itemIndex, fieldName: 'is_visible', value: visible })
        },
        removeItem() {
            this.$store.commit('reports/REMOVE_LIST_ITEM', { listKey: 'columns', item: this.item, itemIndex: this.itemIndex })
            // TODO переделать удаление из группировки если удаляется из списка колонок
            if (this.activeMetadata.grouping.findIndex(column => column.name === this.item.name) !== -1) {
                this.$store.commit('reports/REMOVE_LIST_ITEM', { listKey: 'grouping', item: this.item })
            }

        }

    },
};
</script>

<style lang="scss" scoped>
.column-item-mobile {
    display: flex;
    flex-direction: column;
    gap: 4px;
    padding-bottom: 8px;
    border-bottom: 1px solid #e5e7eb;
}

.column-item-mobile__top {
    display: flex;
    align-items: center;
    justify-content: space-between;
}

.column-item-mobile__controls {
    display: flex;
    align-items: center;
}

.column-item-mobile__title-row {
    display: flex;
    align-items: flex-start;
}

.column-item-mobile__title-text {
    cursor: pointer;
    line-height: 1.35;
}

.column-item-mobile__default-title {
    margin-top: 4px;
    opacity: 0.4;
    font-size: 12px;
    line-height: 1.3;
}

.column-item-mobile__sorting {
    display: flex;
    align-items: center;
}

.column-item-mobile__edit {
    display: flex;
    flex-direction: column;
    gap: 8px;
}

.column-item-mobile__edit-actions {
    display: flex;
    justify-content: flex-end;
}
</style>
