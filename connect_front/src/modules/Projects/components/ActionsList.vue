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
            <ActivityItem key="open" @click="openProject">
                <i class="fi fi-rr-link-alt mr-2" />
                {{ $t('project.open') }}
            </ActivityItem>
            <ActivityItem key="share" @click="shareProject">
                <i class="fi fi-rr-share mr-2" />
                {{ $t('project.share') }}
            </ActivityItem>
            <ActivityItem v-if="canEdit" key="edit" @click="goToEdit">
                <i class="fi fi-rr-edit mr-2" />
                {{ $t('project.edit') }}
            </ActivityItem>
            <ActivityItem v-if="canLeaveProject" key="leave" @click="leaveProject">
                <i class="fi fi-rr-exit mr-2" />
                {{ $t('project.exit') }}
            </ActivityItem>
            <ActivityItem v-if="canFinishProject" key="finish" @click="toggleProjectFinished(false)">
                <i class="fi fi-rr-badge-check mr-2" />
                {{ $t('project.finished_project') }}
            </ActivityItem>
            <ActivityItem v-if="canResumeProject" key="resume" @click="toggleProjectFinished(true)">
                <i class="fi fi-rr-refresh mr-2" />
                {{ $t('project.resume_project') }}
            </ActivityItem>
            <ActivityItem v-if="canDelete" key="delete" redLink @click="deleteProject">
                <i class="fi fi-rr-trash mr-2" />
                {{ $t('project.delete') }}
            </ActivityItem>
        </template>
    </ActivityDrawer>
</template>

<script>
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
            actions: null,
            roles: []
        }
    },
    watch: {
        'item.id'() {
            this.actions = null
            this.roles = []
            this.visible = false
            this.loading = false
        }
    },
    computed: {
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
            return this.hasAction('project_finish') && this.isFounder && !this.item?.finished
        },
        canResumeProject() {
            return this.hasAction('project_finish') && this.isFounder && Boolean(this.item?.finished)
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
            if (this.actions && this.roles.length) {
                return
            }
            try {
                this.loading = true
                const [actionsRes, rolesRes] = await Promise.all([
                    this.$http.get(`/work_groups/workgroups/${this.item.id}/action_info/`),
                    this.$http.get(`/work_groups/workgroups/${this.item.id}/my_role/`)
                ])

                this.actions = actionsRes?.data?.actions || null
                this.roles = Array.isArray(rolesRes?.data) ? rolesRes.data : []
            } catch (error) {
                errorHandler({ error, show: false })
            } finally {
                this.loading = false
            }
        },
        closeDrawer() {
            this.visible = false
        },
        openProject() {
            const query = { ...this.$route.query, viewProject: this.item.id }
            this.closeDrawer()
            this.$router.push({ query })
        },
        shareProject() {
            this.closeDrawer()
            this.$store.commit('share/SET_SHARE_PARAMS', {
                model: 'workgroups.WorkGroupModel',
                shareId: this.item.id,
                object: this.item,
                shareUrl: `${window.location.origin}/?viewProject=${this.item.id}`,
                shareTitle: `${this.$t('project.project')} - ${this.item.name}`,
            })
        },
        goToEdit() {
            this.closeDrawer()
            eventBus.$emit('edit_project_modal', { id: this.item.id, source: 'list' })
        },
        deleteProject() {
            this.closeDrawer()
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
                        this.$http.post(`/work_groups/workgroups/${this.item.id}/delete/`)
                            .then(() => {
                                this.$message.success(this.$t('project.project_delete'))
                                eventBus.$emit('update_filter_workgroups.WorkgroupModel')
                                eventBus.$emit('update_list_project')
                                eventBus.$emit('project_deleted', this.item.id)
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
        leaveProject() {
            this.closeDrawer()
            this.$confirm({
                title: this.$t('project.exit'),
                content: this.$t('project.leave_project_message'),
                cancelText: this.$t('project.no'),
                okText: this.$t('project.yes'),
                onOk: async () => {
                    try {
                        await this.$store.dispatch('projects/leaveGroup', this.item.id)
                        this.$message.warning(this.$t('project.you_not_member_group'))
                        eventBus.$emit('update_filter_workgroups.WorkgroupModel')
                        eventBus.$emit('update_list_project')
                        this.reloadList()
                    } catch (error) {
                        errorHandler({ error })
                    }
                }
            })
        },
        toggleProjectFinished(resume) {
            this.closeDrawer()
            this.$confirm({
                title: resume
                    ? this.$t('project.project_finish_message2')
                    : this.$t('project.project_finish_message'),
                okText: this.$t('project.yes'),
                cancelText: this.$t('project.no'),
                onOk: async () => {
                    try {
                        await this.$store.dispatch('projects/finishedDate', {
                            id: this.item.id,
                            date: resume ? null : this.$moment()
                        })
                        this.$set(this.item, 'finished', !resume)
                        this.$set(this.item, 'finishedDate', resume ? null : this.$moment())
                        this.$message.success(
                            this.$t(resume ? 'project.project_finish2' : 'project.project_finish')
                        )
                        eventBus.$emit('update_filter_workgroups.WorkgroupModel')
                        eventBus.$emit('update_list_project')
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
