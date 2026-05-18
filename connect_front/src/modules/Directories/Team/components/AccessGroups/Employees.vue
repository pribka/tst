<template>
    <div>
        <component 
            :is="widget"
            :accessGroup="accessGroup"
            :organization="organization"
            :reloadAccessGroupList="reloadAccessGroupList" />
    </div>
</template>

<script>
export default {
    components: {
        DrawerSelectUser: () => import('../Drawers/DrawerSelectUser')
    },
    props: {
        accessGroup: {
            type: Object,
            required: true
        },
        organization: {
            type: Object,
            required: true
        },
        reloadAccessGroupList: {
            type: Function,
            default: () => {}
        }
    },
    computed: {
        isMobile() {
            return this.$store.state.isMobile
        },

        widget() {
            if (this.isMobile) {
                return () => import('./EmployeesList.vue')
            }
            return () => import('./EmployeesTable.vue')
        }
    },
}
</script>
