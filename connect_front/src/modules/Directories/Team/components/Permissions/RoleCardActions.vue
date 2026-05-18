<template>
    <div>
        <ActivityDrawer 
            v-model="visible">
            <ActivityItem
                key="leave"
                @click="openEditRoleDrawer()">
                <i class="fi fi-rr-edit mr-2"></i>
                {{ $t('team.edit') }}
            </ActivityItem>
            <ActivityItem
                key="deleteRole"
                @click="confirmDeleteRole()">
                <i class="fi fi-rr-trash mr-2"></i>
                {{ $t('team.delete') }}
            </ActivityItem>
        </ActivityDrawer>

        <CreateRoleDrawer 
            ref="createRoleDrawer"
            :organization="organization"/>
    </div>
</template>

<script>
import { ActivityItem, ActivityDrawer } from '@/components/ActivitySelect'
import { mapActions } from 'vuex'

export default {
    components: {
        CreateRoleDrawer: () => import('./CreateRoleDrawer.vue'),
        ActivityItem, 
        ActivityDrawer
    },
    props: {
        role: {
            type: Object,
            required: true
        },
        organization: {
            type: Object,
            required: true
        },
    },
    data() {
        return {
            visible: false,
        }
    },
    methods: {
        ...mapActions({
            deleteRole: 'organization/deleteRole'
        }),

        openDrawer() {
            this.visible = true
        },

        openEditRoleDrawer() {
            this.$refs.createRoleDrawer.openDrawer({
                edit: true,
                role: this.role,
            })
        },
        confirmDeleteRole() {
            const self = this
            this.$confirm({
                title: this.$t('team.confirm_delete_role'),
                content: '',
                okText: this.$t('team.yes'),
                cancelText: this.$t('team.no'),
                onOk() {
                    self.deleteRole({
                        roleId: self.role.id,
                        organizationId: self.organization.id
                    })
                },
                onCancel() {},
            })
        },
    }
}
</script>

<style scoped lang="scss">
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