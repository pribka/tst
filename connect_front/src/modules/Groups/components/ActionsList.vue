<template>
    <ActivityDrawer v-model="visible" @afterVisibleChange="afterVisibleChange">
        <template v-if="loading">
            <ActivityItem key="loader">
                <div class="w-full flex justify-center">
                    <a-spin size="small" />
                </div>
            </ActivityItem>
        </template>
        <template v-else-if="actions">
            <ActivityItem key="open" @click="openGroup">
                <i class="fi fi-rr-link-alt mr-2" />
                {{ $t('wgr.open') }}
            </ActivityItem>
            <ActivityItem key="share" @click="shareGroup">
                <i class="fi fi-rr-share mr-2" />
                {{ $t('wgr.share') }}
            </ActivityItem>
            <ActivityItem v-if="canEdit" key="edit" @click="goToEdit">
                <i class="fi fi-rr-edit mr-2" />
                {{ $t('wgr.edit') }}
            </ActivityItem>
            <ActivityItem v-if="canLeaveGroup" key="leave" @click="leaveGroup">
                <i class="fi fi-rr-exit mr-2" />
                {{ $t('wgr.exit') }}
            </ActivityItem>
            <ActivityItem v-if="canDelete" key="delete" redLink @click="deleteGroup">
                <i class="fi fi-rr-trash mr-2" />
                {{ $t('wgr.delete') }}
            </ActivityItem>
        </template>
    </ActivityDrawer>
</template>

<script>
import { mapState } from 'vuex'
import { ActivityDrawer, ActivityItem } from '@/components/ActivitySelect'
import eventBus from '@/utils/eventBus'
import { errorHandler } from '@/utils/index.js'

export default {
    components: {
        ActivityDrawer,
        ActivityItem
    },
    props: {
        item: {
            type: Object,
            required: true
        },
        reloadList: {
            type: Function,
            default: () => {}
        }
    },
    data() {
        return {
            visible: false,
            loading: false,
            actions: null
        }
    },
    watch: {
        'item.id'() {
            this.actions = null
            this.visible = false
            this.loading = false
        }
    },
    computed: {
        ...mapState({
            user: state => state.user.user
        }),
        founderId() {
            return this.item?.founder?.member?.id || this.item?.founder?.id || null
        },
        isMyGroup() {
            return Boolean(this.user?.id && this.founderId && this.user.id === this.founderId)
        },
        canEdit() {
            return this.hasAction('edit')
        },
        canDelete() {
            return this.hasAction('delete')
        },
        canLeaveGroup() {
            return !this.isMyGroup
        }
    },
    methods: {
        hasAction(key) {
            const action = this.actions?.[key]
            if (!action) {
                return false
            }
            if (typeof action === 'object' && Object.prototype.hasOwnProperty.call(action, 'availability')) {
                return Boolean(action.availability)
            }
            return Boolean(action)
        },
        openActionsDrawer() {
            this.visible = true
        },
        async afterVisibleChange(vis) {
            if (vis) {
                await this.loadMenuData()
            }
        },
        async loadMenuData() {
            if (this.actions) {
                return
            }
            try {
                this.loading = true
                const { data } = await this.$http.get(`/work_groups/workgroups/${this.item.id}/action_info/`)
                this.actions = data?.actions || null
            } catch (error) {
                errorHandler({ error, show: false })
            } finally {
                this.loading = false
            }
        },
        closeDrawer() {
            this.visible = false
        },
        openGroup() {
            const query = { ...this.$route.query, viewGroup: this.item.id }
            this.closeDrawer()
            this.$router.push({ query })
        },
        shareGroup() {
            this.closeDrawer()
            this.$store.commit('share/SET_SHARE_PARAMS', {
                model: 'workgroups.WorkGroupModel',
                shareId: this.item.id,
                object: this.item,
                shareUrl: `${window.location.origin}/?viewGroup=${this.item.id}`,
                shareTitle: `${this.$t('wgr.group_share')} - ${this.item.name}`,
            })
        },
        goToEdit() {
            const query = {
                ...this.$route.query,
                updateGroup: this.item.id,
                updateGroupFromList: '1'
            }
            this.closeDrawer()
            this.$router.replace({ query })
        },
        deleteGroup() {
            this.closeDrawer()
            this.$confirm({
                title: this.$t('wgr.warning'),
                content: this.$t('wgr.delete_confirm_text', {
                    type: this.$t('wgr.group_label'),
                }),
                zIndex: 2200,
                cancelText: this.$t('wgr.close'),
                okText: this.$t('wgr.delete'),
                okType: 'danger',
                onOk: () => {
                    return new Promise((resolve, reject) => {
                        this.$http.post(`/work_groups/workgroups/${this.item.id}/delete/`)
                            .then(() => {
                                this.$message.success(this.$t('wgr.group_delete'))
                                eventBus.$emit('update_filter_workgroups.WorkgroupModel')
                                eventBus.$emit('update_list_group')
                                this.reloadList()
                                resolve()
                            })
                            .catch((error) => {
                                errorHandler({ error })
                                reject()
                            })
                    })
                }
            })
        },
        leaveGroup() {
            this.closeDrawer()
            this.$confirm({
                title: this.$t('wgr.exit'),
                content: this.$t('wgr.leave_group_message'),
                cancelText: this.$t('wgr.no'),
                okText: this.$t('wgr.yes'),
                onOk: async () => {
                    try {
                        await this.$store.dispatch('workgroups/leaveGroup', this.item.id)
                        this.$message.warning(this.$t('wgr.you_not_member_group'))
                        eventBus.$emit('update_filter_workgroups.WorkgroupModel')
                        eventBus.$emit('update_list_group')
                        this.reloadList()
                    } catch (error) {
                        errorHandler({ error })
                    }
                }
            })
        }
    }
}
</script>
