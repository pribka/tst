<template>
    <a-dropdown :trigger="['click']" placement="bottomLeft">
        <a-tag class="status_tag status_tag_dropdown mb-0 flex items-center" :color="statusColor">
            {{ statusName }}
            <i class="fi fi-rr-angle-small-down ml-1 status_tag_arrow" />
        </a-tag>
        <a-menu slot="overlay">
            <a-menu-item v-if="isDraftStatus" key="publish_from_status" @click="$emit('publish')">
                <i class="fi fi-rr-paper-plane mr-2" />
                Опубликовать
            </a-menu-item>
            <a-menu-item v-else key="unpublish_from_status" @click="$emit('unpublish')">
                <i class="fi fi-rr-eye-crossed mr-2" />
                Отменить публикацию
            </a-menu-item>
        </a-menu>
    </a-dropdown>
</template>

<script>
export default {
    props: {
        statusName: {
            type: String,
            default: ''
        },
        statusColor: {
            type: String,
            default: 'default'
        },
        isDraftStatus: {
            type: Boolean,
            default: false
        }
    }
}
</script>

<style scoped lang="scss">
.status_tag {
    margin-right: 0;
    line-height: 24px;
    padding-left: 10px;
    padding-right: 10px;
    border-radius: 30px;
    font-size: 13px;
}

.status_tag_dropdown {
    cursor: pointer;
}
</style>
