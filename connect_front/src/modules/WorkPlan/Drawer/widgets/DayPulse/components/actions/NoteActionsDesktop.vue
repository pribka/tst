<template>
    <a-dropdown v-if="canShowActions" :trigger="['click']" placement="bottomRight">
        <a-button
            type="ui"
            ghost
            icon="fi-rr-menu-dots-vertical"
            flaticon
            shape="circle"
            size="small" />
        <a-menu slot="overlay">
            <a-menu-item v-if="canEditContent" key="edit" @click="$emit('edit')">
                <i class="fi fi-rr-edit mr-2" />
                Редактировать
            </a-menu-item>
            <a-menu-item v-if="canManageStatus && isDraftStatus" key="publish" @click="$emit('publish')">
                <i class="fi fi-rr-paper-plane mr-2" />
                Опубликовать
            </a-menu-item>
            <a-menu-item v-else-if="canManageStatus" key="unpublish" @click="$emit('unpublish')">
                <i class="fi fi-rr-eye-crossed mr-2" />
                Отменить публикацию
            </a-menu-item>
            <a-menu-item v-if="canDelete" key="delete" class="text-red-500" @click="$emit('delete')">
                <i class="fi fi-rr-trash mr-2" />
                Удалить
            </a-menu-item>
        </a-menu>
    </a-dropdown>
</template>

<script>
export default {
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
    }
}
</script>
