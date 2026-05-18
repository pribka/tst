<template>
    <a-modal
        :visible="visible"
        :title="$t('task.meeting_invite_title')"
        :width="560"
        @cancel="handleCancel()">
        <div class="meeting_invite_modal">
            <a-alert
                class="meeting_invite_modal__alert"
                type="warning"
                :message="$t('task.meeting_invite_no_selection_alert')"
                show-icon />
            <div class="meeting_invite_modal__header">
                <div>
                    {{ $t('task.meeting_invite_participants') }}
                </div>
                <a-button
                    size="small"
                    type="ui"
                    @click="toggleSelectAll()">
                    {{ allSelected ? $t('task.meeting_invite_unselect_all') : $t('task.meeting_invite_select_all') }}
                </a-button>
            </div>

            <div class="meeting_invite_modal__list">
                <div
                    v-for="user in users"
                    :key="user.id"
                    class="meeting_invite_modal__row cursor-pointer"
                    @click="toggleUserById(user.id)">
                    <div class="meeting_invite_modal__user">
                        <a-avatar
                            :size="32"
                            icon="user"
                            :src="getAvatar(user)" />
                        <span class="meeting_invite_modal__name">{{ getUserName(user) }}</span>
                    </div>
                    <a-checkbox
                        :checked="isSelected(user.id)"
                        @click.stop
                        @change="toggleUser(user.id, $event)" />
                </div>
            </div>
        </div>

        <template #footer>
            <div class="meeting_invite_modal__footer flex items-center w-full flex-wrap gap-x-2 gap-y-2">
                <a-button
                    type="primary"
                    :block="isMobile"
                    :loading="loading"
                    @click="invite()">
                    {{ $t('task.meeting_invite_submit_and_start', { count: selectedCount }) }}
                </a-button>
            </div>
        </template>
    </a-modal>
</template>

<script>
export default {
    props: {
        visible: {
            type: Boolean,
            default: false
        },
        users: {
            type: Array,
            default: () => []
        },
        loading: {
            type: Boolean,
            default: false
        }
    },
    data() {
        return {
            selectedUserIds: []
        }
    },
    computed: {
        isMobile() { 
            return this.$store.state.isMobile
        },
        selectedCount() {
            return this.selectedUserIds.length
        },
        allSelected() {
            if (!this.users.length) return false
            return this.selectedUserIds.length === this.users.length
        }
    },
    methods: {
        getAvatar(user) {
            return user?.avatar?.path || user?.avatar || ''
        },
        getUserName(user) {
            return user?.full_name || user?.fio || user?.name || [user?.last_name, user?.first_name].filter(Boolean).join(' ') || '-'
        },
        isSelected(id) {
            return this.selectedUserIds.includes(String(id))
        },
        toggleUser(id, event) {
            const checked = event?.target?.checked
            const userId = String(id)

            if (checked && !this.selectedUserIds.includes(userId)) {
                this.selectedUserIds.push(userId)
                return
            }

            if (!checked) {
                this.selectedUserIds = this.selectedUserIds.filter(item => item !== userId)
            }
        },
        toggleUserById(id) {
            const userId = String(id)
            if (this.selectedUserIds.includes(userId)) {
                this.selectedUserIds = this.selectedUserIds.filter(item => item !== userId)
                return
            }
            this.selectedUserIds.push(userId)
        },
        toggleSelectAll() {
            if (this.allSelected) {
                this.selectedUserIds = []
                return
            }

            this.selectedUserIds = this.users.map(user => String(user.id))
        },
        resetSelection() {
            this.selectedUserIds = []
        },
        handleCancel() {
            this.resetSelection()
            this.$emit('cancel')
        },
        invite() {
            const selectedUserIds = [...this.selectedUserIds]
            this.resetSelection()
            this.$emit('invite', selectedUserIds)
        }
    }
}
</script>

<style scoped lang="scss">
.meeting_invite_modal {
    &__alert {
        margin-bottom: 12px;
    }

    &__header {
        margin-bottom: 12px;
        display: flex;
        align-items: center;
        justify-content: space-between;
    }

    &__row {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 10px 0;
        &:not(:last-child){
            border-bottom: 1px solid #f0f0f0;
        }
    }

    &__user {
        display: flex;
        align-items: center;
        min-width: 0;
    }

    &__name {
        margin-left: 10px;
        line-height: 1.25;
        word-break: break-word;
    }
}
</style>
