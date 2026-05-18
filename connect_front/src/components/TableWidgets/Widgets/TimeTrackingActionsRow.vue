<template>
    <div class="actions_cell">
        <a-dropdown v-if="canAny(record)" :trigger="['click']" :getPopupContainer="getPopupContainer">
            <a-button type="ui_ghost" flaticon shape="circle" icon="fi-rr-menu-dots-vertical" />
            <a-menu slot="overlay">
                <a-menu-item v-if="canEdit(record)" class="flex items-center" @click="colParams.editHandler(record)">
                    <i class="fi fi-rr-edit mr-2" />
                    {{ $t('task.edit') }}
                </a-menu-item>
                <template v-if="canDelete(record)">
                    <a-menu-divider v-if="canEdit(record)" />
                    <a-menu-item class="text_red flex items-center" @click="deleteTime(record)">
                        <i class="fi fi-rr-trash mr-2" />
                        {{ $t('task.remove') }}
                    </a-menu-item>
                </template>
            </a-menu>
        </a-dropdown>
        <i 
            v-if="record.is_result" 
            class="fi fi-rr-checkbox text-green-500" 
            v-tippy="{ inertia : true, duration : '[600,300]'}"
            :content="$t('task.is_results')"
            style="font-size: 16px;" />
    </div>
</template> 

<script>
import { errorHandler } from '@/utils/index.js'
export default {
    props: {
        record: {
            type: Object,
            required: true
        },
        colParams: {
            type: Object,
            default: () => null
        },
        pageName: {
            type: String,
            default: ''
        },
        pageModel: {
            type: String,
            default: ''
        },
        reloadTableData: {
            type: Function,
            default: () => {}
        }
    },
    computed: {
        listType() {
            return this.colParams?.listType || ""
        },
        workObj() {
            return this.colParams?.workObj || ""
        },
        actions() {
            return this.colParams.actions || null
        }
    },
    methods: {
        isAuthor(item) {
            const u = this.$store.state.user.user
            return !!(u && item && item.author && u.id === item.author.id)
        },
        canEdit(item) {
            if(this.actions?.edit_accounting?.availability)
                return true
            return this.isAuthor(item)
        },
        canDelete(item) {
            if(this.actions?.delete_accounting?.availability)
                return true
            return this.isAuthor(item)
        },
        canAny(item) {
            return this.canEdit(item) || this.canDelete(item)
        },
        getPopupContainer() {
            return this.colParams.getPopupContainer()
        },
        deleteTime(item) {
            this.$confirm({
                title: this.$t('task.warning'),
                content: this.$t('task.item_delete_message'),
                zIndex: 9999,
                cancelText: this.$t('task.close'),
                okText: this.$t('task.remove'),
                okType: 'danger',
                onOk: () => {
                    return new Promise((resolve, reject) => {
                        this.$http.post('/table_actions/update_is_active/', [{ id: item.id, is_active: false }])
                            .then(() => {
                                this.$message.success(this.$t('task.item_removed'))
                                if (this.$store.hasModule('workplan')) {
                                    this.$store.dispatch('workplan/updateItem', {
                                        item: this.workObj,
                                        list: this.listType
                                    })
                                    if(item.related_object && item.related_object.type === 'tasks.TaskModel') {
                                        this.$store.dispatch('workplan/updateItem', {
                                            item: item.related_object,
                                            list: 'taskList'
                                        })
                                    }
                                }
                                this.reloadTableData()
                                this.colParams.deleteHandler(item)
                                resolve()
                            })
                            .catch((error) => {
                                errorHandler({error})
                                reject()
                            })
                    })
                },
                onCancel() {}
            })
        },
    }
}
</script>

<style lang="scss" scoped>
.actions_cell {
  display: flex;
  align-items: center;
  gap: 12px;
}
</style>