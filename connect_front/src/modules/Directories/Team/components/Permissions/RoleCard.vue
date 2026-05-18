<template>
    <div 
        class="p-3 custom_card_border card"
        v-touch:longtap="longtapHandler"
        @click="openRoleDetailDrawer">
        <span 
            @click="openRoleDetailDrawer"
            class="cursor-pointer blue_color">
            {{ role.name }}
        </span>
        <template v-if="role.permission_types">
            <div class="mt-2">
                <div 
                    v-for="permission, index in role.permission_types"
                    :key="index">
                    {{ permission }}
                </div>
            </div>
        </template>
        <Members 
            class="mt-2"
            :visibleCount="5"
            :item="role"/>
        <RoleDetailDrawer
            :organization="organization"
            ref="roleDetailDrawer" />
        <RoleCardActions
            :role="role"
            :organization="organization"
            ref="roleCardActions" />
    </div>
</template>

<script>
import { mapActions } from 'vuex';

export default {
    name: 'RoleCard',
    components: {
        RoleDetailDrawer: () => import("./RoleDetailDrawer"),
        Members: () => import('./Members.vue'),
        RoleCardActions: () => import('./RoleCardActions.vue')
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
            loading: false,
        }
    },
    methods: {
        ...mapActions({
            getInfiniteRoles: 'organization/getInfiniteRoles',
            deleteRole: 'organization/deleteRole',
        }),
        longtapHandler() {
            this.$refs[`roleCardActions`].openDrawer()
        },
        openRoleDetailDrawer() {
            this.$refs.roleDetailDrawer.openDrawer({
                role: this.role
            })
        },
        sizeSwicth(current, pageSize) {
            this.page = 1
            this.pageSize = Number(pageSize)
            this.getRoleList()
        },
        onGridReady(params) {
            this.gridApi = params.api;
            this.gridApi.sizeColumnsToFit()
        },
        async getDetailRole() {
            const roleId = ''
            const url = `/contractor_permissions/roles/${roleId}/`
            
            await this.$http.get(url)
                .then(({ data }) => {
                    this.roles = data.results
                })
        },
        async openCreateRoleDrawer() {
            this.$refs.createRoleDrawer.openDrawer()
        }
    }
}
</script>

<style lang="scss" scoped>
.card {
    transition: all 0.5s cubic-bezier(0.645, 0.045, 0.355, 1);
    &.touch{
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
        transform: scale(0.97);
    }
}
.custom_card_border {
    border-radius: var(--borderRadius);
    border: 1px solid var(--border1);
}
.custom_card_margin:not(:last-child) {
    margin-bottom: 0.625rem;
}
</style>