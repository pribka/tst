<template>
    <div class="h-full flex items-center">
        <a-dropdown
            :trigger="['click']"
            :getPopupContainer="getPopupContainer"
            @visibleChange="visibleChange">
            <a-button
                type="ui"
                ghost
                flaticon
                shape="circle"
                size="small"
                icon="fi-rr-menu-dots-vertical"
                :loading="loading && !dropdownVisible"
                :destroyPopupOnHide="false" />
            <a-menu slot="overlay">
                <template v-if="listLoading">
                    <a-menu-item key="loader">
                        <div class="flex justify-center">
                            <a-spin size="small" />
                        </div>
                    </a-menu-item>
                </template>
                <template v-else-if="actions">
                    <a-menu-item key="open" class="flex items-center" @click="openGroup">
                        <i class="fi fi-rr-link-alt mr-2" />
                        {{ $t('wgr.open') }}
                    </a-menu-item>
                    <a-menu-item key="share" class="flex items-center" @click="shareGroup">
                        <i class="fi fi-rr-share mr-2" />
                        {{ $t('wgr.share') }}
                    </a-menu-item>
                    <a-menu-item
                        v-if="canEdit"
                        key="edit"
                        class="flex items-center"
                        @click="goToEdit">
                        <i class="fi fi-rr-edit mr-2" />
                        {{ $t('wgr.edit') }}
                    </a-menu-item>
                    <a-menu-item
                        v-if="canLeaveGroup"
                        key="leave"
                        class="flex items-center"
                        @click="leaveGroup">
                        <i class="fi fi-rr-exit mr-2" />
                        {{ $t('wgr.exit') }}
                    </a-menu-item>
                    <template v-if="canDelete">
                        <a-menu-divider />
                        <a-menu-item
                            key="delete"
                            class="text-red-500 flex items-center"
                            @click="deleteGroup">
                            <i class="fi fi-rr-trash mr-2" />
                            {{ $t('wgr.delete') }}
                        </a-menu-item>
                    </template>
                </template>
            </a-menu>
        </a-dropdown>
    </div>
</template>

<script>
import { mapState } from 'vuex'
import eventBus from '@/utils/eventBus'
import { errorHandler } from '@/utils/index.js'

export default {
    props: {
        text: {
            type: [Object, String]
        },
        record: {
            type: Object,
            default: () => ({})
        },
        column: {
            type: Object
        },
        colParams: {
            type: Object,
            default: () => null
        },
        reloadTableData: {
            type: Function,
            default: () => {}
        }
    },
    data() {
        return {
            loading: false,
            listLoading: false,
            actions: null,
            dropdownVisible: false
        }
    },
    watch: {
        'record.id'() {
            this.actions = null
            this.listLoading = false
        }
    },
    computed: {
        ...mapState({
            user: state => state.user.user
        }),
        founderId() {
            return this.record?.founder?.member?.id || this.record?.founder?.id || null
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
        getPopupContainer() {
            return this.colParams?.getPopupContainer ? this.colParams.getPopupContainer() : document.body
        },
        visibleChange(visible) {
            this.dropdownVisible = visible
            if (visible) {
                this.getActions()
            }
        },
        openGroup() {
            const query = { ...this.$route.query, viewGroup: this.record.id }
            this.$router.push({ query })
        },
        shareGroup() {
            this.$store.commit('share/SET_SHARE_PARAMS', {
                model: 'workgroups.WorkGroupModel',
                shareId: this.record.id,
                object: this.record,
                shareUrl: `${window.location.origin}/?viewGroup=${this.record.id}`,
                shareTitle: `${this.$t('wgr.group_share')} - ${this.record.name}`,
            })
        },
        goToEdit() {
            const query = {
                ...this.$route.query,
                updateGroup: this.record.id,
                updateGroupFromList: '1'
            }
            this.$router.replace({ query })
        },
        deleteGroup() {
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
                        this.$http.post(`/work_groups/workgroups/${this.record.id}/delete/`)
                            .then(() => {
                                this.$message.success(this.$t('wgr.group_delete'))
                                eventBus.$emit('update_filter_workgroups.WorkgroupModel')
                                eventBus.$emit('update_list_group')
                                this.reloadTableData()
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
            this.$confirm({
                title: this.$t('wgr.exit'),
                content: this.$t('wgr.leave_group_message'),
                cancelText: this.$t('wgr.no'),
                okText: this.$t('wgr.yes'),
                onOk: async () => {
                    try {
                        this.loading = true
                        await this.$store.dispatch('workgroups/leaveGroup', this.record.id)
                        this.$message.warning(this.$t('wgr.you_not_member_group'))
                        eventBus.$emit('update_filter_workgroups.WorkgroupModel')
                        eventBus.$emit('update_list_group')
                        this.reloadTableData()
                    } catch (error) {
                        errorHandler({ error })
                    } finally {
                        this.loading = false
                    }
                }
            })
        },
        async getActions() {
            if (this.actions) {
                return
            }
            try {
                this.loading = true
                this.listLoading = true
                const { data } = await this.$http.get(`/work_groups/workgroups/${this.record.id}/action_info/`)
                if (data?.actions) {
                    this.actions = data.actions
                }
            } catch (error) {
                errorHandler({ error, show: false })
            } finally {
                this.loading = false
                this.listLoading = false
            }
        }
    }
}
</script>
