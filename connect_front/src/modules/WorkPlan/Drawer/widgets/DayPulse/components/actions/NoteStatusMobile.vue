<template>
    <div>
        <a-tag class="status_tag status_tag_dropdown mb-0 flex items-center" :color="statusColor" @click="visible = true">
            {{ statusName }}
            <i class="fi fi-rr-angle-small-down ml-1 status_tag_arrow" />
        </a-tag>

        <ActivityDrawer v-model="visible">
            <ActivityItem v-if="isDraftStatus" @click="emitAndClose('publish')">
                <i class="fi fi-rr-paper-plane mr-2" />
                Опубликовать
            </ActivityItem>
            <ActivityItem v-else @click="emitAndClose('unpublish')">
                <i class="fi fi-rr-eye-crossed mr-2" />
                Отменить публикацию
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
