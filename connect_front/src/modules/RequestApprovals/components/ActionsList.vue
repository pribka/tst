<template>
    <ActivityDrawer 
        :vis="activity" 
        useVis
        @afterVisibleChange="afterVisibleChange"
        :cDrawer="closeDrawer">
        <ActivityItem v-if="loading" class="flex justify-center">
            <a-spin size="small" />
        </ActivityItem>
        <template v-if="actions">
            <ActivityItem @click="openView()">
                <i class="fi fi-rr-link-alt icon"></i> {{ $t('helpdesk.open') }}
            </ActivityItem>
            <ActivityItem v-if="actions.update" @click="editHandler()">
                <i class="fi fi-rr-edit" />
                {{ $t('edit') }}
            </ActivityItem>
            <ActivityItem v-if="actions.delete" @click="deleteItem()">
                <i class="fi fi-rr-trash" />
                {{ $t('remove') }} 
            </ActivityItem>
        </template>
    </ActivityDrawer>
</template>

<script>
import { ActivityItem, ActivityDrawer } from '@/components/ActivitySelect'
import eventBus from '@/utils/eventBus'
export default {
    components: {
        ActivityItem,
        ActivityDrawer
    },
    props: {
        item: {
            type: Object,
            required: true
        },
        open: {
            type: Function,
            default: () => {}
        },
        page_name: {
            type: String,
            required: true
        },
        pageModel: {
            type: String,
            required: true
        }
    },
    data() {
        return {
            activity: false,
            actions: null,
            loading: false
        }
    },
    methods: {
        editHandler() {
            this.closeDrawer()
            eventBus.$emit(`edit_request_approvals`, this.item)
        },
        deleteItem() {
            this.closeDrawer()
            this.$confirm({
                title: this.$t('approvals.delete_message'),
                closable: true,
                maskClosable: true,
                cancelText: this.$t('cancel'),
                okText: this.$t('remove'),
                okType: 'danger',
                zIndex: 999999,
                onOk: () => {
                    return new Promise((resolve, reject) => {
                        this.$http.post('/table_actions/update_is_active/', [{ id: this.item.id, is_active: false }])
                            .then(() => {
                                this.$message.success(this.$t('approvals.delete_success'))
                                eventBus.$emit(`update_filter_${this.pageModel}_${this.page_name}`)
                                this.visible = false
                                resolve()
                            })
                            .catch((error) => {
                                errorHandler({error})
                                reject()
                            })
                    })
                }
            })
        },
        openView() {
            this.closeDrawer()
            this.open()
        },
        closeDrawer() {
            this.activity = false
        },
        async getActions() {
            try {
                this.loading = true
                const { data } = await this.$http.get(`/processes/workflow_requests/${this.item.id}/action_info/`)
                if(data?.actions) {
                    console.log(data.actions, 'data.actions')
                    this.actions = data.actions
                }
            } catch(error) {
                console.log(error)
            } finally {
                this.loading = false
            }
        },
        afterVisibleChange(vis) {
            if(vis) {
                this.getActions()
            } else {
                this.actions = null
            }
        },
        openActionsDrawer() {
            this.activity = true
        }
    }
}
</script>