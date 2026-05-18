<template>
    <div v-if="canShowActions">
        <a-button
            type="ui"
            ghost
            icon="fi-rr-menu-dots-vertical"
            flaticon
            shape="circle"
            size="small"
            @click="visible = true" />

        <ActivityDrawer v-model="visible">
            <ActivityItem v-if="canEditContent" @click="emitAndClose('edit')">
                <i class="fi fi-rr-edit mr-2" />
                Редактировать
            </ActivityItem>
            <ActivityItem v-if="canManageStatus && isDraftStatus" @click="emitAndClose('publish')">
                <i class="fi fi-rr-paper-plane mr-2" />
                Опубликовать
            </ActivityItem>
            <ActivityItem v-else-if="canManageStatus" @click="emitAndClose('unpublish')">
                <i class="fi fi-rr-eye-crossed mr-2" />
                Отменить публикацию
            </ActivityItem>
            <ActivityItem v-if="canDelete" @click="emitAndClose('delete')">
                <div class="text-red-500">
                    <i class="fi fi-rr-trash mr-2" />
                    Удалить
                </div>
            </ActivityItem>
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
        canShowActions: {
            type: Boolean,
            default: false
        },
        canEditContent: {
            type: Boolean,
            default: false
        },
        canManageStatus: {
            type: Boolean,
            default: false
        },
        canDelete: {
            type: Boolean,
            default: false
        },
        isDraftStatus: {
            type: Boolean,
            default: false
        }
    },
    data() {
        return {
            visible: false
        }
    },
    methods: {
        emitAndClose(action) {
            this.$emit(action)
            this.visible = false
        }
    }
}
</script>
