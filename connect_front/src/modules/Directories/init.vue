<template>
    <Fragment>
        <component :is="clientDrawerAsync" v-if="$route.query.client" />
        <component :is="universalDrawerAsync" v-if="$route.query.organization_id" />

        <CreateOrganization />
        <InviteDrawer />
        <InviteModal />
        <OrganizationInvite />
        <OrganizationMap />
        <InviteOrganizationModal />
        <OrgInfoDrawer />

        <ClientForm />
    </Fragment>
</template>

<script>
import Fragment from '@apps/UIModules/Fragment.js'
import eventBus from '@/utils/eventBus'
import organizationStore from '@apps/Directories/Team/store/index'
export default {
    name: 'DirectoriesInit',
    components: {
        Fragment,
        ClientForm: () => import('@apps/Directories/components/ClientForm.vue'),
        CreateOrganization: () => import('@apps/Directories/Team/components/CreateOrganization.vue'),
        InviteDrawer: () => import('@apps/Directories/Team/components/InviteDrawer'),
        InviteModal: () => import('@apps/Directories/Team/components/InviteModal'),
        OrganizationInvite: () => import('@apps/Directories/Team/components/OrganizationInvite'),
        OrganizationMap: () => import('@apps/Directories/Team/components/OrganizationMap'),
        InviteOrganizationModal: () => import('@apps/Directories/Team/components/InviteOrganizationModal'),
        OrgInfoDrawer: () => import('@apps/Directories/Team/components/OrgInfo/OrgInfoDrawer.vue')
    },
    data() {
        return {
            clientDrawerAsync: null,
            universalDrawerAsync: null,
        }
    },
    created() {
        if (!this.$store.hasModule('organization')) {
            this.$store.registerModule('organization', organizationStore)
        }
    },
    watch: {
        '$route.query.client': {
            immediate: true,
            handler(v) {
                if (v && !this.clientDrawerAsync)
                    this.clientDrawerAsync = () => import('./components/ClientDrawer')
            }
        },
        '$route.query.organization_id': {
            immediate: true,
            handler(v) {
                if (v && !this.universalDrawerAsync)
                    this.universalDrawerAsync = () => import('@apps/Directories/Team/components/Drawers/UniversalDrawer')
            }
        },
    },
    mounted() {
        eventBus.$on('add_organization_task', ({ task }) => {
            this.$store.commit('organization/ADD_ORGANIZATION_TASK', {
                task,
                organization: task.organization
            })
        })
    },
    beforeDestroy() {
        eventBus.$off('add_organization_task')
    }
}
</script>
