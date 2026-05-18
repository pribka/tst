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
                <template v-if="isLoadingDropdown">
                    <a-menu-item key="loader">
                        <div class="flex justify-center">
                            <a-spin size="small" />
                        </div>
                    </a-menu-item>
                </template>
                <template v-else-if="actions">
                    <a-menu-item key="open" class="flex items-center" @click="openProject">
                        <i class="fi fi-rr-link-alt mr-2" />
                        {{ $t('project.open') }}
                    </a-menu-item>
                    <a-menu-item key="share" class="flex items-center" @click="shareProject">
                        <i class="fi fi-rr-share mr-2" />
                        {{ $t('project.share') }}
                    </a-menu-item>
                    <a-menu-item
                        v-if="canEdit"
                        key="edit"
                        class="flex items-center"
                        @click="goToEdit">
                        <i class="fi fi-rr-edit mr-2" />
                        {{ $t('project.edit') }}
                    </a-menu-item>
                    <a-menu-item
                        v-if="canLeaveProject"
                        key="leave"
                        class="flex items-center"
                        @click="leaveProject">
                        <i class="fi fi-rr-exit mr-2" />
                        {{ $t('project.exit') }}
                    </a-menu-item>
                    <a-menu-item
                        v-if="canFinishProject"
                        key="finish"
                        class="flex items-center"
                        @click="toggleProjectFinished(false)">
                        <i class="fi fi-rr-badge-check mr-2" />
                        {{ $t('project.finished_project') }}
                    </a-menu-item>
                    <a-menu-item
                        v-if="canResumeProject"
                        key="resume"
                        class="flex items-center"
                        @click="toggleProjectFinished(true)">
                        <i class="fi fi-rr-refresh mr-2" />
                        {{ $t('project.resume_project') }}
                    </a-menu-item>
                    <template v-if="canDelete">
                        <a-menu-divider />
                        <a-menu-item
                            key="delete"
                            class="text-red-500 flex items-center"
                            @click="deleteProject">
                            <i class="fi fi-rr-trash mr-2" />
                            {{ $t('project.delete') }}
                        </a-menu-item>
                    </template>
                </template>
            </a-menu>
        </a-dropdown>
    </div>
</template>

<script>
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
            roles: [],
            rolesLoading: false,
            dropdownVisible: false
        }
    },
    watch: {
        'record.id'() {
            this.actions = null
            this.roles = []
            this.listLoading = false
            this.rolesLoading = false
        }
    },
    computed: {
        isLoadingDropdown() {
            return this.dropdownVisible && (this.listLoading || this.rolesLoading)
        },
        isFounder() {
            return this.roles.some(item => ['FOUNDER', 'MODERATOR'].includes(item.membership_role?.code))
        },
        isStudent() {
            return this.roles.some(item => ['FOUNDER', 'MODERATOR', 'MEMBER', 'ORG-COORDINATOR'].includes(item.membership_role?.code))
        },
        canEdit() {
            return this.hasAction('edit')
        },
        canDelete() {
            return this.hasAction('delete')
        },
        canLeaveProject() {
            return this.isStudent && !this.isFounder
        },
        canFinishProject() {
            return this.hasAction('project_finish') && this.isFounder && !this.record?.finished
        },
        canResumeProject() {
            return this.hasAction('project_finish') && this.isFounder && Boolean(this.record?.finished)
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
                this.getRoles()
            }
        },
        async getRoles() {
            if (this.roles.length) {
                return
            }
            try {
                this.rolesLoading = true
                const { data } = await this.$http.get(`/work_groups/workgroups/${this.record.id}/my_role/`)
                const roles = Array.isArray(data) ? data : []
                if (Array.isArray(roles)) {
                    this.roles = roles
                }
            } catch (error) {
                errorHandler({ error, show: false })
            } finally {
                this.rolesLoading = false
            }
        },
        openProject() {
            const query = { ...this.$route.query, viewProject: this.record.id }
            this.$router.push({ query })
        },
        shareProject() {
            this.$store.commit('share/SET_SHARE_PARAMS', {
                model: 'workgroups.WorkGroupModel',
                shareId: this.record.id,
                object: this.record,
                shareUrl: `${window.location.origin}/?viewProject=${this.record.id}`,
                shareTitle: `${this.$t('project.project')} - ${this.record.name}`,
            })
        },
        goToEdit() {
            eventBus.$emit('edit_project_modal', { id: this.record.id, source: 'list' })
        },
        deleteProject() {
            this.$confirm({
                title: this.$t('project.warning'),
                content: this.$t('project.delete_confirm_text', {
                    type: this.$t('project.project_label'),
                }),
                zIndex: 2200,
                cancelText: this.$t('project.close'),
                okText: this.$t('project.delete'),
                okType: 'danger',
                onOk: () => {
                    return new Promise((resolve, reject) => {
                        this.$http.post(`/work_groups/workgroups/${this.record.id}/delete/`)
                            .then(() => {
                                this.$message.success(this.$t('project.project_delete'))
                                eventBus.$emit('update_filter_workgroups.WorkgroupModel')
                                eventBus.$emit('update_list_project')
                                eventBus.$emit('project_deleted', this.record.id)
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
        leaveProject() {
            this.$confirm({
                title: this.$t('project.exit'),
                content: this.$t('project.leave_project_message'),
                cancelText: this.$t('project.no'),
                okText: this.$t('project.yes'),
                onOk: async () => {
                    try {
                        this.loading = true
                        await this.$store.dispatch('projects/leaveGroup', this.record.id)
                        this.$message.warning(this.$t('project.you_not_member_group'))
                        eventBus.$emit('update_filter_workgroups.WorkgroupModel')
                        eventBus.$emit('update_list_project')
                        this.reloadTableData()
                    } catch (error) {
                        errorHandler({ error })
                    } finally {
                        this.loading = false
                    }
                }
            })
        },
        toggleProjectFinished(resume) {
            this.$confirm({
                title: resume
                    ? this.$t('project.project_finish_message2')
                    : this.$t('project.project_finish_message'),
                okText: this.$t('project.yes'),
                cancelText: this.$t('project.no'),
                onOk: async () => {
                    try {
                        this.loading = true
                        await this.$store.dispatch('projects/finishedDate', {
                            id: this.record.id,
                            date: resume ? null : this.$moment()
                        })
                        this.$set(this.record, 'finished', !resume)
                        this.$set(this.record, 'finishedDate', resume ? null : this.$moment())
                        this.$message.success(
                            this.$t(resume ? 'project.project_finish2' : 'project.project_finish')
                        )
                        eventBus.$emit('update_filter_workgroups.WorkgroupModel')
                        eventBus.$emit('update_list_project')
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
