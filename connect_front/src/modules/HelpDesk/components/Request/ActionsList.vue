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
        </template>
    </ActivityDrawer>
</template>

<script>
import { ActivityItem, ActivityDrawer } from '@/components/ActivitySelect'
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
                const { data } = await this.$http.get(`/help_desk/tickets/${this.item.id}/for_client/action_info/`)
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