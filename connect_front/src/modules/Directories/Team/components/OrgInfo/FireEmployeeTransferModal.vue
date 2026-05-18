<template>
    <a-modal
        :visible="visible"
        :title="modalTitle"
        :width="560"
        destroyOnClose
        @cancel="visible = false"
        @afterVisibleChange="afterVisibleChange">
        <div class="transfer_modal">
            <div class="transfer_modal__label">
                {{ $t('team.fire_employee_new_responsible') }}
            </div>
            <OrganizationUserMiniSelect
                v-model="selectedUser"
                :organizationId="organizationId"
                :excludedUserIds="excludedUserIds"
                :getPopupContainer="getPopupContainer"
                inputType="bordered_input"
                :showRecent="false"
                :showIcon="false"
                placement="bottomLeft"
                :placeholder="$t('team.select_employee')" />
        </div>
        <template #footer>
            <div class="flex items-center w-full gap-2 justify-end">
                <a-button
                    type="ui"
                    ghost
                    :block="isMobile"
                    size="large"
                    @click="visible = false">
                    {{ $t('team.cancel') }}
                </a-button>
                <a-button
                    type="primary"
                    size="large"
                    :block="isMobile"
                    :disabled="!selectedUser"
                    @click="submit">
                    {{ $t('team.fire_employee_transfer') }}
                </a-button>
            </div>
        </template>
    </a-modal>
</template>

<script>
export default {
    components: {
        OrganizationUserMiniSelect: () => import('./OrganizationUserMiniSelect.vue')
    },
    data() {
        return {
            visible: false,
            relation: null,
            selectedUser: null,
            notifyUser: true
        }
    },
    computed: {
        isMobile() {
            return this.$store.state.isMobile
        },
        modalTitle() {
            if (!this.relation?.entityLabel && !this.relation?.title) {
                return `${this.$t('team.fire_employee_transfer')}:`
            }

            if (this.relation?.isBulk) {
                return `${this.$t('team.fire_employee_transfer')}: ${this.relation.title}`
            }

            if (['director', 'admin'].includes(this.relation?.sectionKey)) {
                return `${this.$t('team.fire_employee_transfer')} ${this.relation.entityLabel.toLowerCase()}`
            }

            const entityLabel = this.relation?.entityLabel ? `${this.relation.entityLabel.toLowerCase()}:` : ''
            const title = this.relation?.title || ''

            return `${this.$t('team.fire_employee_transfer')} ${entityLabel} ${title}`.trim()
        },
        organizationId() {
            return this.relation?.organizationId || ''
        },
        excludedUserIds() {
            return this.relation?.excludedUserIds || []
        }
    },
    methods: {
        open(relation) {
            this.relation = relation
            this.selectedUser = relation?.selectedUser || null
            this.notifyUser = true
            this.visible = true
        },
        submit() {
            if (!this.selectedUser || !this.relation) return

            this.$emit('submit', {
                sectionKey: this.relation.sectionKey,
                items: this.relation.isBulk ? this.relation.items : null,
                assignmentKey: this.relation.isBulk
                    ? this.relation.items.map(item => item.assignmentKey)
                    : this.relation.assignmentKey,
                payloadKey: this.relation.isBulk
                    ? this.relation.items.map(item => item.payloadKey)
                    : this.relation.payloadKey,
                selectedUser: this.selectedUser
            })

            this.visible = false
        },
        getPopupContainer(trigger) {
            return trigger.parentNode
        },
        afterVisibleChange(vis) {
            if (!vis) {
                this.relation = null
                this.selectedUser = null
                this.notifyUser = true
            }
        }
    }
}
</script>

<style lang="scss" scoped>
.transfer_modal {
    width: 100%;
}

.transfer_modal__label {
    color: var(--gray);
    font-weight: 600;
    margin-bottom: 8px;
}

.transfer_modal ::v-deep {
    .ant-select,
    .ant-select-selection,
    .ant-select-selection__rendered {
        width: 100%;
    }

    .organization_user_trigger {
        min-height: 42px;
        padding-top: 6px;
        padding-bottom: 6px;
    }
}
</style>
