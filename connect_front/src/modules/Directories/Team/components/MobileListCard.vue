<template>
    <div>
        <a-card
            v-touch:longtap="longtapHandler"
            size="small"
            :bordered="false"
            class="team_mobile_card mb-2"
            @click="handleCardClick">
            <div class="mb-3 team_mobile_card__header">
                <div class="team_mobile_card__title">
                    <div class="team_mobile_card__avatar">
                        <a-avatar
                            v-if="item.logo"
                            :size="25"
                            :src="item.logo" />
                        <a-avatar
                            v-else
                            :size="25"
                            icon="team" />
                    </div>
                    <div class="team_mobile_card__name">
                        {{ item.name || '-' }}
                    </div>
                </div>
                <div class="flex items-center">
                    <div class="child_badge_wrap" v-if="hasDescendants" @click.stop="openChildrenDrawer">
                        <div class="child_badge flex items-center justify-center">
                            {{ descendantsCount }}
                        </div>
                    </div>
                    <i class="fi fi-rr-angle-small-right mr-1"></i>
                </div>
            </div>

            <div class="team_mobile_card__row">
                <div class="team_mobile_card__label">{{ $t('table.inn') }}:</div>
                <div class="team_mobile_card__value">{{ item.inn || '-' }}</div>
            </div>

            <div class="team_mobile_card__row">
                <div class="team_mobile_card__label">{{ $t('team.director') }}:</div>
                <div class="team_mobile_card__value">
                    <Profiler
                        v-if="item.director"
                        :user="item.director"
                        :showPopup="false"
                        :avatarSize="18"
                        :showTaskButton="false"
                        :showChatButton="false"
                        wrapperClass="block"
                        nameClass="truncate"
                        trigger="click" />
                    <span v-else>-</span>
                </div>
            </div>

            <div class="team_mobile_card__row">
                <div class="team_mobile_card__label">{{ $t('team.employees') }}:</div>
                <div class="team_mobile_card__value">{{ item.members_count || 0 }}</div>
            </div>
        </a-card>

        <ActivityDrawer v-model="visibleActions">
            <ActivityItem
                v-if="actionLoading"
                key="loader">
                <div class="w-full flex justify-center">
                    <a-spin size="small" />
                </div>
            </ActivityItem>

            <template v-else>
                <ActivityItem @click="openDetails">
                    <i class="fi fi-rr-link-alt"></i>
                    {{ $t('open') }}
                </ActivityItem>

                <ActivityItem
                    v-if="canCopyId"
                    @click="copyId">
                    <i class="fi fi-rr-copy-alt"></i>
                    {{ $t('team.copy_identifier_tooltip') }}
                </ActivityItem>

                <ActivityItem
                    v-if="canInviteSubdivision"
                    @click="inviteSubdivision">
                    <i class="fi fi-rr-plus"></i>
                    {{ $t('team.invite_subdivision_tooltip') }}
                </ActivityItem>

                <ActivityItem
                    v-if="canEdit"
                    @click="editOrg">
                    <i class="fi fi-rr-edit"></i>
                    {{ $t('edit') }}
                </ActivityItem>

                <ActivityItem
                    v-if="!hasAnyAction"
                    key="empty">
                    {{ $t('team.no_available_actions') }}
                </ActivityItem>
            </template>
        </ActivityDrawer>

        <OrganizationChildrenDrawer
            v-model="childrenDrawerVisible"
            :organization="item" />
    </div>
</template>

<script>
import eventBus from '@/utils/eventBus'
import { ActivityItem, ActivityDrawer } from '@/components/ActivitySelect'
import { errorHandler } from '@/utils/index.js'

export default {
    name: 'TeamMobileListCard',
    components: {
        ActivityItem,
        ActivityDrawer,
        Profiler: () => import('@/modules/Profiler/Profiler.vue'),
        OrganizationChildrenDrawer: () => import('./OrganizationChildrenDrawer.vue')
    },
    props: {
        item: {
            type: Object,
            required: true
        }
    },
    data() {
        return {
            visibleActions: false,
            actionLoading: false,
            actions: null,
            longTapTriggered: false,
            childrenDrawerVisible: false
        }
    },
    computed: {
        descendantsCount() {
            return Number(this.item?.structural_division_count || 0)
        },
        hasDescendants() {
            return Boolean(this.item?.has_descendants) || this.descendantsCount > 0
        },
        canEdit() {
            return Boolean(this.actions?.edit?.availability)
        },
        canManage() {
            return Boolean(this.actions?.manage?.availability) && !Boolean(this.item?.is_department)
        },
        canCopyId() {
            return this.canManage
        },
        canInviteSubdivision() {
            return this.canManage
        },
        hasAnyAction() {
            return this.canEdit || this.canCopyId || this.canInviteSubdivision
        }
    },
    methods: {
        openChildrenDrawer() {
            this.childrenDrawerVisible = true
        },
        handleCardClick() {
            if (this.longTapTriggered) {
                this.longTapTriggered = false
                return
            }

            this.openDetails()
        },
        longtapHandler() {
            this.longTapTriggered = true
            this.openActions()
        },
        async openActions() {
            this.visibleActions = true
            await this.getActions()
        },
        async getActions() {
            if (this.actions || this.actionLoading) {
                return
            }

            try {
                this.actionLoading = true
                const { data } = await this.$http.get(`/users/my_organizations/${this.item.id}/action_info/`)
                if (data?.actions) {
                    this.actions = data.actions
                }
            } catch (error) {
                errorHandler({ error, show: false })
                this.$message.error(this.$t('team.error'))
            } finally {
                this.actionLoading = false
            }
        },
        closeActions() {
            this.visibleActions = false
        },
        openDetails() {
            const query = {
                organization_drawer: 'detail',
                organization_id: this.item.id
            }

            if (this.item?.parent_expand) {
                query.parent_id = this.item.parent_expand
            }

            this.closeActions()
            this.$router.push({ query })
        },
        copyId() {
            try {
                navigator.clipboard.writeText(this.item.id)
                this.$message.success(this.$t('team.organization_id_copied'))
            } catch (error) {
                this.$message.error(this.$t('team.error'))
            } finally {
                this.closeActions()
            }
        },
        inviteSubdivision() {
            eventBus.$emit('invite_organization', {
                organization: this.item,
                isSubdivision: false
            })
            this.closeActions()
        },
        editOrg() {
            const organizationParent = this.item?.parent_expand
                || this.item?.contractor_parent?.id
                || this.item?.contractor_parent
                || null
            const isDepartment = Boolean(this.item?.is_department)

            eventBus.$emit('edit_organization', {
                organization: this.item,
                organizationParent,
                organizationType: organizationParent && !isDepartment ? 'subdivision' : null,
                isDepartment
            })

            this.closeActions()
        }
    }
}
</script>

<style lang="scss" scoped>
.child_badge_wrap {
    margin-right: 8px;
    display: flex;
    align-items: center;
}

.child_badge {
    min-height: 25px;
    min-width: 25px;
    font-size: 12px;
    line-height: 12px;
    border-radius: 50%;
    background: #f9f0ff;
    color: #722ed1;
}
.team_mobile_card {
    border-radius: var(--borderRadius);
    user-select: none;

    &__header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 8px;
    }

    &__title {
        display: flex;
        align-items: center;
        gap: 8px;
        min-width: 0;
        flex: 1;
    }

    &__avatar {
        flex-shrink: 0;
    }

    &__name {
        font-weight: 600;
        font-size: 15px;
        line-height: 20px;
        min-width: 0;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
    }

    &__children_btn {
        flex-shrink: 0;
    }

    &__row {
        display: flex;
        align-items: center;
        gap: 6px;
        min-height: 24px;
        &:not(:last-child) {
            margin-bottom: 4px;
        }
    }

    &__label {
        color: var(--gray);
        flex-shrink: 0;
    }

    &__value {
        min-width: 0;
        word-break: break-word;
    }
}
</style>
