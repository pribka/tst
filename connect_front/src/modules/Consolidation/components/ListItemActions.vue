<template>
    <div><ActivityDrawer 
        v-model="visible" 
        @afterVisibleChange="afterVisibleChange">
        <ActivityItem
            v-if="actionLoading"
            key="menu_loader">
            <div class="w-full flex justify-center">
                <a-spin size="small" />
            </div>
        </ActivityItem>
        <template v-if="dropActions">
            <ActivityItem
                v-if="dropActions?.open && dropActions?.open?.availability" 
                key="open"
                @click="openConsolidation()">
                <i class="fi fi-rr-search-alt mr-2"></i>
                {{ $t('Open') }}
            </ActivityItem>
            <ActivityItem
                v-if="dropActions?.edit && dropActions?.edit?.availability" 
                key="edit"
                @click="edit()">
                <i class="fi fi-rr-edit mr-2"></i>
                {{ $t('Edit') }}
            </ActivityItem>
            <ActivityItem
                v-if="dropActions?.download && dropActions?.download?.availability" 
                key="download"
                @click="documentDownload()">
                <i class="fi fi-rr-download mr-2"></i>
                {{ $t('Download') }}
            </ActivityItem>
            <ActivityItem 
                v-if="dropActions.delete && dropActions?.delete?.availability"
                key="delete" 
                @click="deleteHanlder()">
                <div class="text-red-500">
                    <i class="fi fi-rr-trash mr-2"></i>
                    {{ $t('Delete') }}
                </div>
            </ActivityItem>
        </template>
    </ActivityDrawer>

    </div>
</template>

<script>
import { ActivityItem, ActivityDrawer } from '@/components/ActivitySelect'
import mixins from './Actions/Consolidation/mixins.js'
export default {
    components: {
        ActivityItem, 
        ActivityDrawer
    },
    mixins: [
        mixins
    ],
    computed: {
        cStatusFiltered() {
            if(this.isAuthor  || (this.isLogistic && this.isOperator))
                return this.filteredList.filter(f => f.code !== this.item.status.code)
            else
                return this.filteredList.filter(f => f.code !== this.item.status.code && !f.is_complete)
        }
    },
    props: {
        item: {
            type: Object,
            required: true
        }
    },
    data() {
        return {
            visible: false,
            actionLoading: false,
            dropActions: {},
        }
    },
    methods: {
        open() {
            console.log('OPEN')
        },
        openDrawer() {
            this.visible = true
        },
        afterVisibleChange(visible) {
            if(visible) {
                this.getTaskActions()
            } else {
                this.dropActions = {}
            }
        },
        async getTaskActions() {
            try {
                this.actionLoading = true
                const { data } = await this.$http.get(`/consolidation/${this.item.id}/action_info/`)
                if(data?.actions) {
                    this.dropActions = data.actions
                }
            } catch(e) {
                this.$message.error(this.$t('error'))
            } finally {
                this.actionLoading = false
            }
        },
    }
}
</script>

<style scoped>
.open_button {
    display: flex;
    justify-content: center;
    align-items: center;

    line-height: 100%;
}
.active_option {
    color: var(--blue);
}
.mob_badge{
    width: 22px;
    height: 22px;
    margin-right: 10px;
    display: flex;
    align-items: center;
    justify-content: center;
    &::v-deep{
        .ant-badge{
            .ant-badge-status-dot{
                width: 10px;
                height: 10px;
            }
        }
    }
}
</style>