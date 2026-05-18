<template>
    <div>
        <a-dropdown 
            :destroyPopupOnHide="true">
            <a-button 
                icon="menu" 
                type="link" />
            <a-menu slot="overlay">
                <template v-if="true">
                    <a-menu-item
                        key="copy"
                        class="flex items-center"
                        @click="openEditRoleDrawer()">
                        <i class="fi fi-rr-edit mr-2"></i>
                        {{ $t('team.edit') }}
                    </a-menu-item>
                    <a-menu-item 
                        key="edit"
                        class="flex items-center"
                        @click="confirmDeleteRole()">
                        <i class="fi fi-rr-trash mr-2"></i>
                        {{ $t('team.delete') }}
                    </a-menu-item>
                </template>
            </a-menu>
        </a-dropdown>

        <CreateRoleDrawer 
            ref="createRoleDrawer"
            :pageName="pageName"
            :organization="organization"/>
    </div>
</template>

<script>
import { mapActions } from 'vuex'
import eventBus from '@/utils/eventBus'

export default {
    components: {
        CreateRoleDrawer: () => import('./CreateRoleDrawer.vue')
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
        pageName: {
            type: String,
            default: ''
        }
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
                    eventBus.$emit(`table_row_${self.pageName}`, {
                        action: 'delete',
                        row: self.role
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